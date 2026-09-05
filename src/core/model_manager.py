# SPDX-License-Identifier: MIT
import os
import gc
import psutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline
from safetensors import safe_open
import torch
from utils.config_manager import settings

@dataclass
class ModelMetadata:
    name: str
    type: str  # e.g., 'checkpoint', 'lora', 'llm', 'controlnet'
    path: str
    description: str = ""
    params: dict = field(default_factory=dict)
    default_sampler: str = "Euler a"
    default_scheduler: str = "normal"
    family: str = "sd15"
    prompt_limit: int = 77
    default_width: int = 512
    default_height: int = 512

class ModelManager:
    def __init__(self):
        # Maps model names to their metadata and the actual loaded object
        self.models: Dict[str, ModelMetadata] = {}
        self._loaded_objects: Dict[str, object] = {}
        self._active_model_name: Optional[str] = None
        self._active_precision: Optional[str] = None
        
        # Get base path from config manager
        self.base_path = os.path.abspath(settings.get('paths.models_dir'))
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

        self.discover_models()

    def discover_models(self):
        """Register supported checkpoint files without loading tensor data."""
        self.models.clear()
        for model_path in sorted(Path(self.base_path).glob("*.safetensors")):
            try:
                family = self.classify_checkpoint(model_path)
            except Exception as error:
                print(f"Warning: Could not inspect model {model_path.name}: {error}")
                continue

            if family == "unknown":
                print(f"Warning: Unsupported model architecture: {model_path.name}")
                continue

            if family == "sdxl":
                defaults = {
                    "default_sampler": "Euler",
                    "default_width": 1024,
                    "default_height": 1024,
                    "description": "Stable Diffusion XL checkpoint",
                }
            else:
                defaults = {
                    "default_sampler": "Euler a",
                    "default_width": 512,
                    "default_height": 512,
                    "description": "Stable Diffusion 1.x checkpoint",
                }

            self.register_model(
                model_path.name,
                "checkpoint",
                str(model_path),
                defaults["description"],
                default_sampler=defaults["default_sampler"],
                default_scheduler="normal",
                family=family,
                prompt_limit=77,
                default_width=defaults["default_width"],
                default_height=defaults["default_height"],
            )

    @staticmethod
    def classify_checkpoint(path: Path) -> str:
        """Classify a checkpoint from its safetensors header and key names."""
        with safe_open(str(path), framework="pt", device="cpu") as checkpoint:
            metadata = checkpoint.metadata() or {}
            keys = tuple(checkpoint.keys())

        normalized_metadata = {
            str(key).lower(): str(value).lower()
            for key, value in metadata.items()
        }
        architecture = normalized_metadata.get("modelspec.architecture", "")
        base_version = normalized_metadata.get("ss_base_model_version", "")

        if "stable-diffusion-xl" in architecture or base_version.startswith("sdxl"):
            return "sdxl"
        if "stable-diffusion-v1" in architecture or base_version in {"sd1", "sd1x", "sd_1x"}:
            return "sd15"

        sdxl_markers = (
            "conditioner.embedders.1.model.transformer.",
            "conditioner.embedders.1.model.token_embedding.",
            "conditioner.embedders.1.model.positional_embedding.",
            "text_encoder_2.text_model.encoder.layers.",
            "text_encoder_2.text_model.embeddings.",
            "text_encoder_2.text_projection.",
        )
        sd15_markers = (
            "cond_stage_model.transformer.text_model.encoder.layers.",
            "cond_stage_model.transformer.text_model.embeddings.",
            "text_encoder.text_model.encoder.layers.",
            "text_encoder.text_model.embeddings.",
            "text_encoder.text_projection.",
        )
        has_sdxl = any(key.startswith(marker) for key in keys for marker in sdxl_markers)
        has_sd15 = any(key.startswith(marker) for key in keys for marker in sd15_markers)
        if has_sdxl and not has_sd15:
            return "sdxl"
        if has_sd15 and not has_sdxl:
            return "sd15"
        return "unknown"

    def register_model(self, name: str, model_type: str, path: str, description: str = "", 
                        default_sampler: str = "Euler a", default_scheduler: str = "normal",
                        family: str = "sd15", prompt_limit: int = 77,
                        default_width: int = 512, default_height: int = 512):
        """Register a model's metadata without loading it into memory."""
        if not os.path.exists(path):
            print(f"Warning: Path {path} for model {name} does not exist.")
        
        self.models[name] = ModelMetadata(
            name=name,
            type=model_type,
            path=path,
            description=description,
            default_sampler=default_sampler,
            default_scheduler=default_scheduler,
            family=family,
            prompt_limit=prompt_limit,
            default_width=default_width,
            default_height=default_height
        )

    def get_model_list(self, model_type: Optional[str] = None) -> List[ModelMetadata]:
        """Return a list of registered models, optionally filtered by type."""
        if model_type:
            return [m for m in self.models.values() if m.type == model_type]
        return list(self.models.values())

    def load_model(self, name: str, precision: Optional[str] = None) -> Optional[object]:
        """Lazy-load a model into memory/GPU."""
        if name not in self.models:
            print(f"Error: Model {name} is not registered.")
            return None
        
        requested_precision = self.normalize_precision(
            precision or settings.get("hardware.precision", "fp16")
        )

        if name in self._loaded_objects and self._active_precision == requested_precision:
            return self._loaded_objects[name]

        meta = self.models[name]
        try:
            self._check_load_resources(meta, requested_precision, check_available_gpu=False)
        except Exception as error:
            print(f"Refusing unsafe load for {meta.name}: {error}")
            return None

        if self._active_model_name:
            self.unload_model(self._active_model_name)

        try:
            self._check_load_resources(meta, requested_precision, check_available_gpu=True)
        except Exception as error:
            print(f"Refusing load after cleanup for {meta.name}: {error}")
            return None

        print(f"Loading model: {meta.name} from {meta.path}...")
        
        if meta.type == 'checkpoint' and meta.path.endswith('.safetensors'):
            try:
                model = self._load_checkpoint(meta, requested_precision)
                if torch.cuda.is_available():
                    model.to("cuda")
                else:
                    model.to("cpu")
                
                self._loaded_objects[name] = model
                self._active_model_name = name
                self._active_precision = requested_precision
                return model
            except Exception as e:
                print(f"Failed to load {meta.family} model '{name}': {e}")
                self._loaded_objects.pop(name, None)
                self._active_model_name = None
                self._active_precision = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                return None
        
        # Fallback for other types (placeholders)
        loaded_obj = f"LoadedObject({meta.name})"
        self._loaded_objects[name] = loaded_obj
        self._active_model_name = name
        self._active_precision = requested_precision
        return loaded_obj

    @staticmethod
    def normalize_precision(precision: str) -> str:
        normalized = str(precision).strip().lower()
        aliases = {"float16": "fp16", "float32": "fp32", "bfloat16": "bf16"}
        normalized = aliases.get(normalized, normalized)
        if normalized not in {"fp8", "fp16", "bf16", "fp32"}:
            raise ValueError(f"Unsupported precision: {precision}")
        return normalized

    @staticmethod
    def resolve_dtype(precision: str):
        precision = ModelManager.normalize_precision(precision)
        if precision == "fp8":
            raise ValueError("FP8 is not supported for standard Diffusers pipeline inference")
        return {
            "fp16": torch.float16,
            "bf16": torch.bfloat16,
            "fp32": torch.float32,
        }[precision]

    @staticmethod
    def precision_supported(precision: str) -> bool:
        precision = ModelManager.normalize_precision(precision)
        if precision == "fp8":
            return False
        if precision == "bf16" and torch.cuda.is_available():
            return torch.cuda.is_bf16_supported()
        return True

    def _load_checkpoint(self, meta: ModelMetadata, precision: str):
        pipeline_class = self.get_pipeline_class(meta)
        return pipeline_class.from_single_file(
            meta.path,
            torch_dtype=self.resolve_dtype(precision),
            use_safetensors=True,
            local_files_only=True
        )

    @staticmethod
    def _check_load_resources(
        meta: ModelMetadata,
        precision: str,
        check_available_gpu: bool = True,
    ) -> None:
        """Reject high-risk native loads before Torch can fail outside Python."""
        checkpoint_size_gb = os.path.getsize(meta.path) / (1024 ** 3)
        available_ram_gb = psutil.virtual_memory().available / (1024 ** 3)
        required_ram_gb = max(4.0, checkpoint_size_gb * 1.15)
        if available_ram_gb < required_ram_gb:
            raise RuntimeError(
                f"Not enough system memory to load {meta.name} "
                f"({available_ram_gb:.1f} GB available, {required_ram_gb:.1f} GB required)"
            )

        if torch.cuda.is_available():
            free_bytes, _ = torch.cuda.mem_get_info()
            available_gpu_gb = free_bytes / (1024 ** 3)
            _, total_bytes = torch.cuda.mem_get_info()
            total_gpu_gb = total_bytes / (1024 ** 3)
            if meta.family == "sdxl":
                required_gpu_gb = 20.0 if precision == "fp32" else 8.0
            else:
                required_gpu_gb = 7.0 if precision == "fp32" else 4.0
            if meta.family == "sdxl" and precision == "fp32" and total_gpu_gb < required_gpu_gb:
                raise RuntimeError(
                    f"SDXL FP32 requires a GPU with at least {required_gpu_gb:.0f} GB; "
                    f"detected {total_gpu_gb:.1f} GB"
                )
            if check_available_gpu and available_gpu_gb < required_gpu_gb:
                raise RuntimeError(
                    f"Not enough GPU memory to load {meta.name} "
                    f"({available_gpu_gb:.1f} GB available, {required_gpu_gb:.1f} GB required)"
                )

    def unload_model(self, name: str):
        """Unload a model from memory/GPU to free up resources."""
        if name in self._loaded_objects:
            model = self._loaded_objects.pop(name)
            if torch.cuda.is_available() and hasattr(model, "to"):
                try:
                    model.to("cpu")
                    torch.cuda.synchronize()
                except Exception as error:
                    print(f"Warning: Could not move {name} to CPU during unload: {error}")
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                if hasattr(torch.cuda, "ipc_collect"):
                    torch.cuda.ipc_collect()
            if self._active_model_name == name:
                self._active_model_name = None
                self._active_precision = None
            print(f"Unloaded model: {name}")

    def list_all_models(self) -> List[str]:
        return list(self.models.keys())

    @staticmethod
    def get_pipeline_class(meta: ModelMetadata):
        """Return the Diffusers pipeline class required by a model family."""
        if meta.family == "sdxl":
            return StableDiffusionXLPipeline
        if meta.family == "sd15":
            return StableDiffusionPipeline
        raise ValueError(f"Unsupported diffusion model family: {meta.family}")