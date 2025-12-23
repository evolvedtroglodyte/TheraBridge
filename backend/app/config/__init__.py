"""Configuration module for TherapyBridge backend"""

# This __init__.py re-exports settings from app/config.py
# so that both `from app.config import settings` and
# `from app.config.model_config import get_model_name` work

# We need to import from the parent app.config module (config.py file)
# Use absolute import to avoid circular reference
import importlib.util
import sys
from pathlib import Path

# Dynamically load config.py from parent directory
config_path = Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("app_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

# Re-export settings
settings = config_module.settings

__all__ = ['settings']
