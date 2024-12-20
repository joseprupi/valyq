# config/__init__.py
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Root directory of the project
ROOT_DIR = Path(__file__).parent.parent

# Config directory
CONFIG_DIR = ROOT_DIR / 'config'

# Load environment variables from .env file
load_dotenv(ROOT_DIR / '.env')

# Import settings class
from .settings import Settings

# Import environment-specific settings
from .development import development_settings

# These would be uncommented when you add those files
# from .production import production_settings
# from .testing import testing_settings

def load_env_settings() -> Dict[str, Any]:
    """Load settings based on environment"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    if env == 'production':
        # return production_settings
        raise NotImplementedError("Production settings not configured")
    elif env == 'testing':
        # return testing_settings
        raise NotImplementedError("Test settings not configured")
    return development_settings

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings.load()

__all__ = ['Settings', 'get_settings', 'ROOT_DIR', 'CONFIG_DIR']