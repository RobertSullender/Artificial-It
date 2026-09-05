import unittest
from pathlib import Path

from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline

from core.model_manager import ModelManager


class ModelSupportTests(unittest.TestCase):
    def setUp(self):
        self.manager = ModelManager()

    def test_known_checkpoints_are_registered(self):
        self.assertIn("sd15", self.manager.models)
        self.assertIn("sdxl", self.manager.models)
        self.assertEqual(self.manager.models["sd15"].family, "sd15")
        self.assertEqual(self.manager.models["sdxl"].family, "sdxl")

    def test_model_defaults_are_family_specific(self):
        sd15 = self.manager.models["sd15"]
        sdxl = self.manager.models["sdxl"]
        self.assertEqual((sd15.default_width, sd15.default_height), (512, 512))
        self.assertEqual((sdxl.default_width, sdxl.default_height), (1024, 1024))
        self.assertEqual(sdxl.prompt_limit, 77)

    def test_pipeline_classes_match_model_family(self):
        self.assertIs(
            self.manager.get_pipeline_class(self.manager.models["sd15"]),
            StableDiffusionPipeline,
        )
        self.assertIs(
            self.manager.get_pipeline_class(self.manager.models["sdxl"]),
            StableDiffusionXLPipeline,
        )

    def test_checkpoint_paths_are_local(self):
        for metadata in self.manager.models.values():
            self.assertTrue(Path(metadata.path).is_file())


if __name__ == "__main__":
    unittest.main()
