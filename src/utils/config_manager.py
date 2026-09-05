# SPDX-License-Identifier: MIT
import os
import json
from pathlib import Path
from typing import Any, Dict

class ConfigManager:
    # Default settings that will be used if no file is found
    DEFAULT_CONFIG = {
        "paths": {
            "models_dir": "models",
            "output_dir": "outputs"
        },
        "defaults": {
            "steps": 20,
            "guidance_scale": 7.5,
            "seed": -1,
            "resolution": {
                "width": 512,
                "height": 512
            },
            "sampler": "Euler a"
        },
        "hardware": {
            "use_cuda": True,
            "precision": "fp16",
            "available_precisions": ["fp8", "fp16", "bf16", "fp32"]
        },
        "ui": {
            "live_preview": True,
            "resource_monitor": True
        }
    }

    def __init__(self):
        # In a production app, we would try to load from ~/.artificial_it/config.json
        # but for now, we will stick with defaults to ensure stability during dev.
        self.config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()

    def get(self, key: str, default=None) -> Any:
        """Retrieve a value using dot notation (e.g., 'paths.models_dir')"""
        keys = key.split('.')
        val = self.config
        try:
            for k in keys:
                val = val[k]
            return val
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        target = self.config
        for part in keys[:-1]:
            target = target.setdefault(part, {})
        target[keys[-1]] = value

# Singleton instance for global access
settings = ConfigManager()