# SPDX-License-Identifier: MIT
import os
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

    def load_model(self, name: str) -> Optional[object]:
        """Lazy-load a model into memory/GPU."""
        if name not in self.models:
            print(f"Error: Model {name} is not registered.")
            return None
        
        if name in self._loaded_objects:
            return self._loaded_objects[name]

        meta = self.models[name]
        print(f"Loading model: {meta.name} from {meta.path}...")
        
        if meta.type == 'checkpoint' and meta.path.endswith('.safetensors'):
            try:
                pipeline_class = self.get_pipeline_class(meta)
                model = pipeline_class.from_single_file(
                    meta.path,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    use_safetensors=True,
                    local_files_only=True
                )
                if torch.cuda.is_available():
                    model.to("cuda")
                else:
                    model.to("cpu")
                
                self._loaded_objects[name] = model
                return model
            except Exception as e:
                print(f"Failed to load {meta.family} model '{name}': {e}")
                return None
        
        # Fallback for other types (placeholders)
        loaded_obj = f"LoadedObject({meta.name})"
        self._loaded_objects[name] = loaded_obj
        return loaded_obj

    def unload_model(self, name: str):
        """Unload a model from memory/GPU to free up resources."""
        if name in self._loaded_objects:
            del self._loaded_objects[name]
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