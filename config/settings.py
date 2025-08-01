import yaml
import os
from typing import Dict, Any
from pathlib import Path

class Settings:
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.weights_config = self._load_weights_config()
        self.default_model = "gpt-4o"
    
    def _load_weights_config(self) -> Dict[str, Any]:
        weights_file = self.config_dir / "weights.yaml"
        with open(weights_file, 'r') as f:
            return yaml.safe_load(f)
    
    def get_default_weights(self, mode: str = None) -> Dict[str, float]:
        """Get weights for specified mode or default mode"""
        if mode is None:
            mode = self.weights_config.get("default_mode", "professional")
        return self.weights_config["weight_modes"][mode]["weights"]
    
    def get_weight_modes(self) -> Dict[str, Any]:
        """Get all available weight modes with their metadata"""
        return self.weights_config["weight_modes"]
    
    def get_weight_mode_info(self, mode: str) -> Dict[str, Any]:
        """Get information about a specific weight mode"""
        return self.weights_config["weight_modes"].get(mode, {})
    
    def get_default_mode(self) -> str:
        """Get the default weight mode"""
        return self.weights_config.get("default_mode", "professional")
    
    def get_platform_weights(self, platform: str) -> Dict[str, float]:
        return self.weights_config["platform_weights"].get(platform, {})
    
    def get_scoring_thresholds(self) -> Dict[str, int]:
        return self.weights_config["scoring_thresholds"]
    
    def update_weights(self, custom_weights: Dict[str, float]) -> Dict[str, float]:
        default_weights = self.get_default_weights()
        default_weights.update(custom_weights)
        return default_weights
    
    def get_model(self) -> str:
        """Get the default model name"""
        return os.getenv("DEFAULT_MODEL", self.default_model)

settings = Settings()