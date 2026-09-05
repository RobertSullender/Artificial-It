import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import torch
from PIL import Image

from diffusers import (
    DDIMScheduler,
    DPMSolverMultistepScheduler,
    EulerAncestralDiscreteScheduler,
    EulerDiscreteScheduler,
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    UniPCMultistepScheduler,
)

from core.model_manager import ModelManager, ModelMetadata
from core.engine import ExecutionEngine
from utils.config_manager import settings


class ModelSupportTests(unittest.TestCase):
    def setUp(self):
        self.manager = ModelManager()

    def test_known_checkpoints_are_registered(self):
        self.assertIn("v1-5-pruned.safetensors", self.manager.models)
        self.assertIn("sd_xl_base_1.0.safetensors", self.manager.models)
        self.assertEqual(self.manager.models["v1-5-pruned.safetensors"].family, "sd15")
        self.assertEqual(self.manager.models["sd_xl_base_1.0.safetensors"].family, "sdxl")

    def test_model_defaults_are_family_specific(self):
        sd15 = self.manager.models["v1-5-pruned.safetensors"]
        sdxl = self.manager.models["sd_xl_base_1.0.safetensors"]
        self.assertEqual((sd15.default_width, sd15.default_height), (512, 512))
        self.assertEqual((sdxl.default_width, sdxl.default_height), (1024, 1024))
        self.assertEqual(sdxl.prompt_limit, 77)

    def test_pipeline_classes_match_model_family(self):
        self.assertIs(
            self.manager.get_pipeline_class(self.manager.models["v1-5-pruned.safetensors"]),
            StableDiffusionPipeline,
        )
        self.assertIs(
            self.manager.get_pipeline_class(self.manager.models["sd_xl_base_1.0.safetensors"]),
            StableDiffusionXLPipeline,
        )

    def test_checkpoint_paths_are_local(self):
        for metadata in self.manager.models.values():
            self.assertTrue(Path(metadata.path).is_file())

    def test_switching_models_unloads_previous_model(self):
        class FakePipeline:
            def to(self, device):
                return self

        first = object()
        second = FakePipeline()
        self.manager._loaded_objects["first"] = first
        self.manager._active_model_name = "first"
        with patch.object(self.manager, "_load_checkpoint", return_value=second), patch(
            "core.model_manager.torch.cuda.is_available", return_value=False
        ):
            self.manager.models["second"] = ModelMetadata(
                name="second",
                type="checkpoint",
                path=self.manager.models["v1-5-pruned.safetensors"].path,
            )
            loaded = self.manager.load_model("second")
        self.assertIs(loaded, second)
        self.assertNotIn("first", self.manager._loaded_objects)

    def test_error_formatter_compacts_oom(self):
        error = RuntimeError("CUDA out of memory\nallocation details")
        self.assertEqual(ExecutionEngine.format_error(error), "Out of memory")

    def test_sequential_output_metadata_does_not_backtrack(self):
        engine = ExecutionEngine(self.manager)
        with tempfile.TemporaryDirectory() as temp_dir:
            original_output_dir = settings.get("paths.output_dir")
            settings.set("paths.output_dir", temp_dir)
            try:
                Path(temp_dir, "img_1.png").touch()
                Path(temp_dir, "img_10.png").touch()
                Path(temp_dir, "img_15.png").touch()
                path = engine.save_generated_image(
                    Image.new("RGB", (8, 8), "black"),
                    "test-model.safetensors",
                    self.manager.models["v1-5-pruned.safetensors"],
                    "fp16",
                    "a prompt",
                    "bad quality",
                    20,
                    7,
                    123,
                    "Euler a",
                    512,
                    512,
                )
                self.assertEqual(path.name, "img_16.png")
                self.assertTrue(path.with_suffix(".json").is_file())
                metadata = json.loads(path.with_suffix(".json").read_text())
                self.assertEqual(list(metadata), [
                    "family", "model", "width", "height", "prompt",
                    "negative_prompt", "precision", "guidance_scale", "sampler",
                    "seed", "steps",
                ])
                self.assertEqual(metadata["seed"], 123)
                embedded = Image.open(path).text["parameters"]
                self.assertEqual(
                    list(line.split(": ", 1)[0] for line in embedded.splitlines()),
                    list(metadata),
                )
                self.assertEqual(
                    embedded.splitlines()[0],
                    "family: sd15",
                )
            finally:
                settings.set("paths.output_dir", original_output_dir)

    def test_precision_resolution(self):
        self.assertEqual(self.manager.normalize_precision("float16"), "fp16")
        self.assertIs(self.manager.resolve_dtype("fp16"), torch.float16)
        self.assertIs(self.manager.resolve_dtype("bf16"), torch.bfloat16)
        self.assertIs(self.manager.resolve_dtype("fp32"), torch.float32)

    def test_fp8_is_rejected_until_supported(self):
        with self.assertRaisesRegex(ValueError, "FP8"):
            self.manager.resolve_dtype("fp8")
        self.assertFalse(self.manager.precision_supported("fp8"))

    def test_resource_guard_rejects_insufficient_system_memory(self):
        meta = self.manager.models["sd_xl_base_1.0.safetensors"]
        memory = type("Memory", (), {"available": 1 * 1024 ** 3})()
        with patch("core.model_manager.psutil.virtual_memory", return_value=memory), patch(
            "core.model_manager.torch.cuda.is_available", return_value=False
        ), self.assertRaisesRegex(RuntimeError, "Not enough system memory"):
            self.manager._check_load_resources(meta, "fp16")

    def test_resource_guard_rejects_sdxl_fp32_on_small_gpu(self):
        meta = self.manager.models["sd_xl_base_1.0.safetensors"]
        memory = type("Memory", (), {"available": 32 * 1024 ** 3})()
        with patch("core.model_manager.psutil.virtual_memory", return_value=memory), patch(
            "core.model_manager.torch.cuda.is_available", return_value=True
        ), patch(
            "core.model_manager.torch.cuda.mem_get_info",
            return_value=(15 * 1024 ** 3, 15.5 * 1024 ** 3),
        ), self.assertRaisesRegex(RuntimeError, "SDXL FP32 requires"):
            self.manager._check_load_resources(meta, "fp32")

    def test_same_model_different_precision_does_not_reuse(self):
        class FakePipeline:
            def to(self, device):
                return self

        first = FakePipeline()
        second = FakePipeline()
        self.manager._loaded_objects["v1-5-pruned.safetensors"] = first
        self.manager._active_model_name = "v1-5-pruned.safetensors"
        self.manager._active_precision = "fp16"
        with patch.object(self.manager, "_load_checkpoint", return_value=second), patch(
            "core.model_manager.torch.cuda.is_available", return_value=False
        ):
            loaded = self.manager.load_model("v1-5-pruned.safetensors", "fp32")
        self.assertIs(loaded, second)
        self.assertIsNot(loaded, first)
        self.assertEqual(self.manager._active_precision, "fp32")

    def test_precision_transition_moves_previous_pipeline_off_gpu(self):
        class FakePipeline:
            def __init__(self):
                self.devices = []

            def to(self, device):
                self.devices.append(device)
                return self

        previous = FakePipeline()
        replacement = FakePipeline()
        self.manager._loaded_objects["v1-5-pruned.safetensors"] = previous
        self.manager._active_model_name = "v1-5-pruned.safetensors"
        self.manager._active_precision = "bf16"
        with patch.object(self.manager, "_load_checkpoint", return_value=replacement), patch(
            "core.model_manager.torch.cuda.is_available", return_value=True
        ), patch("core.model_manager.torch.cuda.mem_get_info", return_value=(16 * 1024**3, 16 * 1024**3)), patch(
            "core.model_manager.torch.cuda.synchronize"
        ), patch("core.model_manager.torch.cuda.empty_cache"), patch("core.model_manager.torch.cuda.ipc_collect"), patch(
            "core.model_manager.psutil.virtual_memory",
            return_value=type("Memory", (), {"available": 32 * 1024**3})(),
        ):
            loaded = self.manager.load_model("v1-5-pruned.safetensors", "fp16")
        self.assertIs(loaded, replacement)
        self.assertEqual(previous.devices, ["cpu"])
        self.assertEqual(self.manager._active_precision, "fp16")

    def test_sampler_selection_creates_requested_scheduler(self):
        from diffusers import EulerDiscreteScheduler

        current = EulerDiscreteScheduler(num_train_timesteps=1000)
        expected = {
            "Euler a": EulerAncestralDiscreteScheduler,
            "DPM++ 2M": DPMSolverMultistepScheduler,
            "DDIM": DDIMScheduler,
            "Euler": EulerDiscreteScheduler,
            "UniPC": UniPCMultistepScheduler,
        }
        for sampler, scheduler_class in expected.items():
            scheduler = ExecutionEngine.create_scheduler(current, sampler)
            self.assertIsInstance(scheduler, scheduler_class)

    def test_unknown_sampler_is_rejected(self):
        current = EulerDiscreteScheduler(num_train_timesteps=1000)
        with self.assertRaises(ValueError):
            ExecutionEngine.create_scheduler(current, "Unknown")

    def test_same_model_reuses_loaded_object(self):
        loaded = object()
        self.manager._loaded_objects["v1-5-pruned.safetensors"] = loaded
        self.manager._active_model_name = "v1-5-pruned.safetensors"
        self.manager._active_precision = "fp16"
        with patch.object(self.manager, "_load_checkpoint") as load_checkpoint:
            self.assertIs(
                self.manager.load_model("v1-5-pruned.safetensors"),
                loaded,
            )
        load_checkpoint.assert_not_called()

    def test_failed_load_clears_active_model(self):
        self.manager._loaded_objects["old"] = object()
        self.manager._active_model_name = "old"
        with patch.object(
            self.manager,
            "_load_checkpoint",
            side_effect=RuntimeError("conversion failed"),
        ), patch("core.model_manager.torch.cuda.is_available", return_value=False):
            self.manager.models["broken"] = ModelMetadata(
                name="broken",
                type="checkpoint",
                path=self.manager.models["v1-5-pruned.safetensors"].path,
            )
            self.assertIsNone(self.manager.load_model("broken"))
        self.assertNotIn("broken", self.manager._loaded_objects)
        self.assertIsNone(self.manager._active_model_name)


if __name__ == "__main__":
    unittest.main()
