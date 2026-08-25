import asyncio
from typing import Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal
from core.model_manager import ModelManager
from core.loop_manager import instance as loop_manager
from diffusers import StableDiffusionPipeline
import torch
import os
from datetime import datetime
from pathlib import Path
from utils.config_manager import settings
import numpy as np
from PIL import Image
import tempfile  # ADD: Import for temporary directory handling

class ExecutionEngine(QObject):
    # Signals to communicate with the UI
    progress_updated = pyqtSignal(dict)
    task_completed = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, model_manager: ModelManager):
        super().__init__()
        self.model_manager = model_manager
        self.current_tasks: Dict[str, asyncio.Task] = {}
        
        # ✅ NEW: Create temp directory for all temporary files (previews, cache, etc.)
        # This moves away from outputs/ to use OS standard temp location
        self.temp_dir = Path(tempfile.gettempdir()) / "artificial_it_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # ✅ Preview folder inside temp location (not visible in user's outputs/)
        self.preview_dir = self.temp_dir / "previews"
        self.preview_dir.mkdir(parents=True, exist_ok=True)


    async def run_task(self, task_id: str, params: Dict[str, Any]):
        """
        The main entry point for any AI generation request.
        params might look like: {'model': 'flux_dev', 'prompt': 'a cat...', 'steps': 20}
        """
        try:
            self.progress_updated.emit({"task_id": task_id, "status": "Initializing..."})
            
            # 1. Model Retrieval & Loading
            model_name = params.get('model')
            if not model_name:
                raise ValueError("No model specified in task parameters.")
            
            self.progress_updated.emit({"task_id": task_id, "status": f"Loading {model_name}..."})
            
            # FIX: Run the synchronous load_model call in a separate thread to avoid blocking the event loop.
            # This prevents the UI from freezing and avoids race conditions during initialization.
            model_obj = await asyncio.to_thread(self.model_manager.load_model, model_name)
            
            if not model_obj:
                raise RuntimeError(f"Failed to load model: {model_name}")

            # 2. Execution Pipeline (Real AI logic for SD)
            is_sd = isinstance(model_obj, StableDiffusionPipeline)
            
            if is_sd:
                self.progress_updated.emit({"task_id": task_id, "status": "Starting Diffusion..."})
                
                # Extract all professional parameters with defaults from settings
                prompt = params.get('prompt', '')
                negative_prompt = params.get('negative_prompt', '')
                num_inference_steps = params.get('steps', settings.get('defaults.steps'))
                guidance_scale = params.get('guidance_scale', settings.get('defaults.guidance_scale'))
                seed = params.get('seed', settings.get('defaults.seed'))
                width = params.get('width', settings.get('defaults.resolution.width'))
                height = params.get('height', settings.get('defaults.resolution.height'))
                sampler = params.get('sampler', settings.get('defaults.sampler'))

                # Handle Seed logic (reproducibility)
                if seed == -1:
                    generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(int(datetime.now().timestamp()))
                else:
                    generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(int(seed))

                # Define a callback to capture intermediate previews
                # NOTE: Diffusers v0.31+ uses signature: callback(step_idx, t, latents)
                def callback_on_step_end(step_idx, t, latents):
                    print(f'DEBUG Callback called: step={step_idx}')  # DEBUG
                    
                    if latents is not None:
                        with torch.no_grad():
                            decoded = model_obj.vae.decode(latents / model_obj.vae.config.scaling_factor, return_dict=False)[0]
                            image = decoded.cpu().numpy()

                            if image.ndim == 4:
                                image = image[0]

                            if image.ndim == 3 and image.shape[0] == 3:
                                image = image.transpose(1, 2, 0)
                            elif image.ndim == 3 and image.shape[2] == 3:
                                pass

                            image = (image * 255).astype(np.uint8)
                            # FIX: Resize to target dimensions instead of hardcoded 512x512
                            preview_img = Image.fromarray(image).resize((width, height), Image.Resampling.LANCZOS)

                            preview_path = self.preview_dir / f"prev_{task_id}_{step_idx:03d}.png"
                            preview_img.save(str(preview_path))

                            # Minimal sleep to ensure disk I/O is complete before signaling the UI
                            asyncio.sleep(0.01) 

                            self.progress_updated.emit({
                                "task_id": task_id, 
                                "status": f"Step {step_idx}/{num_inference_steps}",
                                "image_path": str(preview_path),
                                "percentage": (step_idx / num_inference_steps) * 100
                            })

                def perform_inference():
                    with torch.no_grad():
                        # NOTE: Samplers in Diffusers v0.31+ are determined at pipeline creation time,
                        # not per-call. The sampler parameter is stored for future use or model-specific overrides.
                        print(f'DEBUG Sampler selected: {sampler}')

                        # Pass the professional parameters into the pipeline call
                        output = model_obj(
                            prompt=prompt,
                            negative_prompt=negative_prompt,
                            num_inference_steps=num_inference_steps,
                            guidance_scale=guidance_scale,
                            width=width,
                            height=height,
                            generator=generator,
                            callback=callback_on_step_end,
                            callback_steps=1,  # Trigger callback after every step
                        )
                        return output.images[0]
                
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(perform_inference)
                    image = future.result()
                
                # Save final result
                output_dir = Path("outputs")
                output_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"gen_{task_id}_{timestamp}.png"
                save_path = output_dir / filename
                image.save(str(save_path))
                
                # FIX: Clean up intermediate preview files (they were temporary)
                if self.preview_dir.exists():
                    for f in self.preview_dir.glob("prev_*"):
                        try:
                            f.unlink()  # Delete intermediate previews
                        except:
                            pass  # Ignore cleanup errors

                result = str(save_path)
                self.progress_updated.emit({"task_id": task_id, "status": "Generation Complete!"})
            else:
                # Fallback for non-diffusion models (placeholders)
                self.progress_updated.emit({"task_id": task_id, "status": "Executing placeholder pipeline..."})
                
                steps = params.get('steps', settings.get('defaults.steps'))
                for i in range(steps):
                    await asyncio.sleep(0.1)  # Faster simulation for testing
                    self.progress_updated.emit({
                        "task_id": task_id, 
                        "status": f"Processing step {i+1}/{steps}",
                        "progress": (i + 1) / steps * 100
                    })
                
                result = f"Placeholder Success for {params.get('prompt', 'N/A')}"
                self.progress_updated.emit({"task_id": task_id, "status": "Completed"})

            # 3. Completion
            self.task_completed.emit(task_id, result)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            self.error_occurred.emit(str(e))
            self.progress_updated.emit({"task_id": task_id, "status": f"Error: {str(e)}"})
        finally:
            pass

    def submit_task(self, task_id: str, params: Dict[str, Any]):
        """Submit a task to be run in the background loop."""
        if task_id in self.current_tasks and not self.current_tasks[task_id].done():
            print(f"Task {task_id} is already running.")
            return

        # Submit to the shared LoopManager instead of creating a local task
        future = loop_manager.submit(self.run_task(task_id, params))
        self.current_tasks[task_id] = future
