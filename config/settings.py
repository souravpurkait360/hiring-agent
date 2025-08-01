import yaml
import os
from typing import Dict, Any
from pathlib import Path

class Settings:
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.weights_config = self._load_weights_config()
    
    def _load_weights_config(self) -> Dict[str, Any]:
        weights_file = self.config_dir / "weights.yaml"
        with open(weights_file, 'r') as f:
            return yaml.safe_load(f)
    
    def get_default_weights(self) -> Dict[str, float]:
        return self.weights_config["default_weights"]
    
    def get_platform_weights(self, platform: str) -> Dict[str, float]:
        return self.weights_config["platform_weights"].get(platform, {})
    
    def get_scoring_thresholds(self) -> Dict[str, int]:
        return self.weights_config["scoring_thresholds"]
    
    def update_weights(self, custom_weights: Dict[str, float]) -> Dict[str, float]:
        default_weights = self.get_default_weights()
        default_weights.update(custom_weights)
        return default_weights

settings = Settings()