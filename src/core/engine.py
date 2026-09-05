# SPDX-License-Identifier: MIT
import asyncio
import json
import re
import threading
from typing import Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal
from core.model_manager import ModelManager
from core.loop_manager import instance as loop_manager
from diffusers import (
    DDIMScheduler,
    DPMSolverMultistepScheduler,
    EulerAncestralDiscreteScheduler,
    EulerDiscreteScheduler,
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    UniPCMultistepScheduler,
)
import torch
import os
from datetime import datetime
from pathlib import Path
from utils.config_manager import settings
import numpy as np
from PIL import Image, PngImagePlugin
import tempfile  # ADD: Import for temporary directory handling

class ExecutionEngine(QObject):
    # Signals to communicate with the UI
    progress_updated = pyqtSignal(dict)
    task_completed = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str, str)

    @staticmethod
    def format_error(error: Exception, operation: str = "Generation") -> str:
        """Return a concise single-line message for the UI."""
        message = str(error).replace("\n", " ").strip()
        if isinstance(error, torch.cuda.OutOfMemoryError) or "out of memory" in message.lower():
            return "Out of memory"
        if operation == "Model load":
            return "Model load failed"
        return f"{operation} failed"

    @staticmethod
    def create_scheduler(current_scheduler, sampler):
        """Create the requested scheduler while preserving pipeline config."""
        scheduler_classes = {
            "Euler a": EulerAncestralDiscreteScheduler,
            "DPM++ 2M": DPMSolverMultistepScheduler,
            "DDIM": DDIMScheduler,
            "Euler": EulerDiscreteScheduler,
            "UniPC": UniPCMultistepScheduler,
        }
        scheduler_class = scheduler_classes.get(sampler)
        if scheduler_class is None:
            raise ValueError(f"Unsupported sampler: {sampler}")
        return scheduler_class.from_config(current_scheduler.config)

    @staticmethod
    def resolve_batch_seed(seed, batch_index, timestamp=None):
        """Return a stable per-image seed for a batch."""
        base_seed = int(timestamp if timestamp is not None else datetime.now().timestamp()) if seed == -1 else int(seed)
        return base_seed + int(batch_index)

    @staticmethod
    def seed_runtime(seed):
        torch.manual_seed(int(seed))
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(int(seed))

    @staticmethod
    def pipeline_device(pipeline):
        try:
            return next(pipeline.unet.parameters()).device
        except (AttributeError, StopIteration):
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @staticmethod
    def prepare_seeded_latents(pipeline, seed, width, height):
        """Create the exact initial noise tensor used by a seeded generation."""
        device = ExecutionEngine.pipeline_device(pipeline)
        dtype = next(pipeline.unet.parameters()).dtype
        shape = (
            1,
            pipeline.unet.config.in_channels,
            height // pipeline.vae_scale_factor,
            width // pipeline.vae_scale_factor,
        )
        generator = torch.Generator(device=device).manual_seed(int(seed))
        return torch.randn(shape, generator=generator, device=device, dtype=dtype)

    def save_generated_image(self, image, model_name, model_meta, precision, prompt,
                             negative_prompt, steps, guidance_scale, seed, sampler,
                             width, height):
        """Save an image with monotonic naming and CivitAI-compatible metadata."""
        output_dir = Path(settings.get("paths.output_dir", "outputs"))
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata = {
            "family": model_meta.family if model_meta else None,
            "model": model_name,
            "width": width,
            "height": height,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "precision": precision,
            "guidance_scale": guidance_scale,
            "sampler": sampler,
            "seed": seed,
            "steps": steps,
        }
        parameters = "\n".join(
            f"{key}: {value}" for key, value in metadata.items()
        )

        with self.output_lock:
            highest = 0
            for path in output_dir.glob("img_*.png"):
                match = re.fullmatch(r"img_(\d+)\.png", path.name)
                if match:
                    highest = max(highest, int(match.group(1)))
            image_path = output_dir / f"img_{highest + 1}.png"
            image_path.touch(exist_ok=False)
            png_info = PngImagePlugin.PngInfo()
            png_info.add_text("parameters", parameters)
            png_info.add_text("artificial_it_metadata", json.dumps(metadata))
            image.save(str(image_path), pnginfo=png_info)
            image_path.with_suffix(".json").write_text(
                json.dumps(metadata, indent=2),
                encoding="utf-8",
            )
        return image_path

    def __init__(self, model_manager: ModelManager):
        super().__init__()
        self.model_manager = model_manager
        self.current_tasks: Dict[str, asyncio.Task] = {}
        self.output_lock = threading.Lock()
        
        # ✅ NEW: Create temp directory for all temporary files (previews, cache, etc.)
        # This moves away from outputs/ to use OS standard temp location
        self.temp_dir = Path(tempfile.gettempdir()) / "artificial_it_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # ✅ Preview folder inside temp location (not visible in user's outputs/)
        self.preview_dir = self.temp_dir / "previews"
        self.preview_dir.mkdir(parents=True, exist_ok=True)


    async def run_task(self, task_id: str, params: Dict[str, Any]):
        batch_count = max(1, int(params.get("batch_count", 1)))
        base_seed = self.resolve_batch_seed(params.get("seed", settings.get("defaults.seed")), 0)
        if batch_count == 1:
            return await self._run_task_once(
                task_id,
                {**params, "seed": base_seed, "batch_index": 0},
                emit_completion=True,
            )

        for image_index in range(batch_count):
            self.progress_updated.emit({
                "task_id": task_id,
                "status": f"Batch image {image_index + 1}/{batch_count}",
                "percentage": (image_index / batch_count) * 100,
            })
            result = await self._run_task_once(
                task_id,
                {
                    **params,
                    "seed": base_seed + image_index,
                    "batch_index": image_index,
                    "batch_count": batch_count,
                },
                emit_completion=False,
            )
            if result is None:
                return None

        self.progress_updated.emit({
            "task_id": task_id,
            "status": "Batch Complete!",
            "percentage": 100,
        })
        self.task_completed.emit(task_id, result)
        return result

    async def _run_task_once(
        self,
        task_id: str,
        params: Dict[str, Any],
        emit_completion: bool,
    ):
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
            precision = params.get(
                "precision",
                settings.get("hardware.precision", "fp16"),
            )
            model_obj = await asyncio.to_thread(
                self.model_manager.load_model,
                model_name,
                precision,
            )
            
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
                effective_seed = int(params.get("seed", settings.get("defaults.seed")))
                self.progress_updated.emit({
                    "task_id": task_id,
                    "status": f"Seed {effective_seed}",
                })
                default_width = model_meta.default_width if model_meta else settings.get('defaults.resolution.width')
                default_height = model_meta.default_height if model_meta else settings.get('defaults.resolution.height')
                width = params.get('width', default_width)
                height = params.get('height', default_height)
                sampler = params.get('sampler', settings.get('defaults.sampler'))
                original_scheduler = model_obj.scheduler
                selected_scheduler = self.create_scheduler(original_scheduler, sampler)
                model_obj.scheduler = selected_scheduler

                initial_latents = self.prepare_seeded_latents(
                    model_obj,
                    effective_seed,
                    width,
                    height,
                )
                self.seed_runtime(effective_seed)

                # Define a callback to capture intermediate previews
                # NOTE: Diffusers v0.31+ uses signature: callback(step_idx, t, latents)
                def callback_on_step_end(pipe, step_idx, t, callback_kwargs):
                    latents = callback_kwargs.get("latents")
                    clean_latents = None
                    preview_path = None
                    if latents is not None and settings.get("ui.live_preview", True):
                        with torch.no_grad():
                            preview_latent = latents.detach().clone()
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
                            else:
                                preview_latent = preview_latent.to(
                                    next(iter(model_obj.vae.post_quant_conv.parameters())).dtype
                                )
                            try:
                                decoded = model_obj.vae.decode(preview_latent, return_dict=False)[0]
                            finally:
                                if needs_upcasting:
                                    model_obj.vae.to(dtype=torch.float16)
                            image = (decoded / 2 + 0.5).clamp(0, 1).float().cpu().numpy()

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
                        print(f'DEBUG Scheduler selected: {sampler}')

                        # Pass the professional parameters into the pipeline call
                        output = model_obj(
                            prompt=prompt,
                            negative_prompt=negative_prompt,
                            num_inference_steps=num_inference_steps,
                            guidance_scale=guidance_scale,
                            width=width,
                            height=height,
                            latents=initial_latents,
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
                        model_obj.scheduler = original_scheduler
                
                save_path = self.save_generated_image(
                    image=image,
                    model_name=model_name,
                    model_meta=model_meta,
                    precision=precision,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    seed=effective_seed,
                    sampler=sampler,
                    width=width,
                    height=height,
                )

                result = str(save_path)
                if emit_completion:
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
            if emit_completion:
                self.task_completed.emit(task_id, result)
            return result

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            short_error = self.format_error(e, "Model load" if "load model" in str(e).lower() else "Generation")
            self.error_occurred.emit(task_id, short_error)
            self.progress_updated.emit({"task_id": task_id, "status": f"Error: {short_error}"})
            return None
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
