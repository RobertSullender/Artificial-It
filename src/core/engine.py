# SPDX-License-Identifier: MIT
import asyncio
from typing import Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal
from core.model_manager import ModelManager
from core.loop_manager import instance as loop_manager
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline
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
            is_sd = isinstance(model_obj, (StableDiffusionPipeline, StableDiffusionXLPipeline))
            model_meta = self.model_manager.models.get(model_name)
            
            if is_sd:
                self.progress_updated.emit({"task_id": task_id, "status": "Starting Diffusion..."})
                
                # Extract all professional parameters with defaults from settings
                prompt = params.get('prompt', '')
                negative_prompt = params.get('negative_prompt', '')
                num_inference_steps = params.get('steps', settings.get('defaults.steps'))
                guidance_scale = params.get('guidance_scale', settings.get('defaults.guidance_scale'))
                seed = params.get('seed', settings.get('defaults.seed'))
                default_width = model_meta.default_width if model_meta else settings.get('defaults.resolution.width')
                default_height = model_meta.default_height if model_meta else settings.get('defaults.resolution.height')
                width = params.get('width', default_width)
                height = params.get('height', default_height)
                sampler = params.get('sampler', settings.get('defaults.sampler'))
                preview_latents = {"value": None}

                original_scheduler_step = model_obj.scheduler.step

                def scheduler_step_for_preview(*args, **kwargs):
                    requested_return_dict = kwargs.get("return_dict", True)
                    kwargs["return_dict"] = True
                    scheduler_output = original_scheduler_step(*args, **kwargs)
                    preview_latents["value"] = getattr(
                        scheduler_output, "pred_original_sample", None
                    )
                    if requested_return_dict:
                        return scheduler_output
                    return (scheduler_output.prev_sample,)

                model_obj.scheduler.step = scheduler_step_for_preview

                # Handle Seed logic (reproducibility)
                if seed == -1:
                    generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(int(datetime.now().timestamp()))
                else:
                    generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(int(seed))

                # Define a callback to capture intermediate previews
                # NOTE: Diffusers v0.31+ uses signature: callback(step_idx, t, latents)
                def callback_on_step_end(pipe, step_idx, t, callback_kwargs):
                    latents = callback_kwargs.get("latents")
                    clean_latents = preview_latents["value"]
                    preview_path = None
                    if latents is not None:
                        with torch.no_grad():
                            preview_latent = clean_latents if clean_latents is not None else latents
                            has_latents_mean = getattr(model_obj.vae.config, "latents_mean", None) is not None
                            has_latents_std = getattr(model_obj.vae.config, "latents_std", None) is not None
                            if has_latents_mean and has_latents_std:
                                latents_mean = torch.tensor(
                                    model_obj.vae.config.latents_mean,
                                    device=preview_latent.device,
                                    dtype=preview_latent.dtype,
                                ).view(1, 4, 1, 1)
                                latents_std = torch.tensor(
                                    model_obj.vae.config.latents_std,
                                    device=preview_latent.device,
                                    dtype=preview_latent.dtype,
                                ).view(1, 4, 1, 1)
                                preview_latent = preview_latent * latents_std / model_obj.vae.config.scaling_factor + latents_mean
                            else:
                                preview_latent = preview_latent / model_obj.vae.config.scaling_factor
                            needs_upcasting = (
                                model_obj.vae.dtype == torch.float16
                                and getattr(model_obj.vae.config, "force_upcast", False)
                            )
                            if needs_upcasting:
                                model_obj.vae.to(dtype=torch.float32)
                                preview_latent = preview_latent.to(
                                    next(iter(model_obj.vae.post_quant_conv.parameters())).dtype
                                )
                            try:
                                decoded = model_obj.vae.decode(preview_latent, return_dict=False)[0]
                            finally:
                                if needs_upcasting:
                                    model_obj.vae.to(dtype=torch.float16)
                            image = (decoded / 2 + 0.5).clamp(0, 1).cpu().numpy()

                            if image.ndim == 4:
                                image = image[0]

                            if image.ndim == 3 and image.shape[0] == 3:
                                image = image.transpose(1, 2, 0)
                            elif image.ndim == 3 and image.shape[2] == 3:
                                pass

                            image = (image * 255).round().astype(np.uint8)
                            # FIX: Resize to target dimensions instead of hardcoded 512x512
                            preview_img = Image.fromarray(image).resize((width, height), Image.Resampling.LANCZOS)

                            preview_path = self.preview_dir / f"prev_{task_id}_{step_idx:03d}.png"
                            preview_img.save(str(preview_path))

                    progress = {
                        "task_id": task_id,
                        "status": f"Step {step_idx + 1}/{num_inference_steps}",
                        "percentage": ((step_idx + 1) / num_inference_steps) * 100,
                    }
                    if preview_path is not None:
                        progress["image_path"] = str(preview_path)
                    self.progress_updated.emit(progress)
                    return callback_kwargs

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
                            callback_on_step_end=callback_on_step_end,
                            callback_on_step_end_tensor_inputs=["latents"],
                        )
                        return output.images[0]
                
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(perform_inference)
                    try:
                        image = future.result()
                    finally:
                        model_obj.scheduler.step = original_scheduler_step
                
                # Save final result
                output_dir = Path("outputs")
                output_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"gen_{task_id}_{timestamp}.png"
                save_path = output_dir / filename
                image.save(str(save_path))

                result = str(save_path)
                self.progress_updated.emit({
                    "task_id": task_id,
                    "status": "Generation Complete!",
                    "percentage": 100,
                })

                # Clean up intermediate preview files only after generation is complete.
                if self.preview_dir.exists():
                    for f in self.preview_dir.glob("prev_*"):
                        try:
                            f.unlink()
                        except Exception:
                            pass
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
