import unittest
from pathlib import Path
from unittest.mock import patch

from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline

from core.model_manager import ModelManager, ModelMetadata
from core.engine import ExecutionEngine


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

    def test_same_model_reuses_loaded_object(self):
        loaded = object()
        self.manager._loaded_objects["v1-5-pruned.safetensors"] = loaded
        self.manager._active_model_name = "v1-5-pruned.safetensors"
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
