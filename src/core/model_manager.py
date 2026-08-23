import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from diffusers import StableDiffusionPipeline
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

class ModelManager:
    def __init__(self):
        # Maps model names to their metadata and the actual loaded object
        self.models: Dict[str, ModelMetadata] = {}
        self._loaded_objects: Dict[str, object] = {}
        
        # Get base path from config manager
        self.base_path = os.path.abspath(settings.get('paths.models_dir'))
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

        # Register the actual SD 1.5 model provided by user
        sd15_path = os.path.join(self.base_path, "v1-5-pruned.safetensors")
        if os.path.exists(sd15_path):
            # Added professional defaults for SD1.5
            self.register_model("sd15", "checkpoint", sd15_path, "Stable Diffusion v1.5 Pruned", 
                                 default_sampler="Euler a", default_scheduler="normal")
        else:
            print(f"Warning: SD 1.5 model not found at {sd15_path}")

    def register_model(self, name: str, model_type: str, path: str, description: str = "", 
                        default_sampler: str = "Euler a", default_scheduler: str = "normal"):
        """Register a model's metadata without loading it into memory."""
        if not os.path.exists(path):
            print(f"Warning: Path {path} for model {name} does not exist.")
        
        self.models[name] = ModelMetadata(
            name=name,
            type=model_type,
            path=path,
            description=description,
            default_sampler=default_sampler,
            default_scheduler=default_scheduler
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
        
        # Specific logic for SD 1.5 .safetensors files
        if meta.type == 'checkpoint' and meta.path.endswith('.safetensors'):
            try:
                model = StableDiffusionPipeline.from_single_file(
                    meta.path,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    use_safetensors=True
                )
                if torch.cuda.is_available():
                    model.to("cuda")
                else:
                    model.to("cpu")
                
                self._loaded_objects[name] = model
                return model
            except Exception as e:
                print(f"Failed to load SD model: {e}")
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