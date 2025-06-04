import yaml
import os
from pathlib import Path
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)  # Only log errors in production
logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, config_dir: str = None):
        """Initialize the config loader with the config directory path"""
        if config_dir is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, Dict[str, Any]] = {}

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load a specific configuration file"""
        if config_name in self.configs:
            return self.configs[config_name]

        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            self.configs[config_name] = config
            return config

    def get_app_config(self) -> Dict[str, Any]:
        """Get the application configuration"""
        return self.load_config('app_config')

    def get_rag_config(self) -> Dict[str, Any]:
        """Get the RAG service configuration"""
        return self.load_config('rag_config')

# Create a singleton instance
config_loader = ConfigLoader() 