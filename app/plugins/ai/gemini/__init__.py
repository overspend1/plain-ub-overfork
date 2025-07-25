"""
Gemini AI Plugin Package
"""

# Auto-register the Gemini AI plugin when imported
try:
 from app.plugins.core.loader import plugin_loader
 from .modular import gemini_ai
 
 # Register the plugin instance
 plugin_loader.register_plugin_instance(gemini_ai)
 
except ImportError as e:
 print(f"Failed to register Gemini AI plugin: {e}")
except Exception as e:
 print(f"Error in Gemini AI plugin initialization: {e}")

# Import the main components for external use
from .client import client, async_client, Response
from .config import AIConfig, DB_SETTINGS
from .modular import gemini_ai

__all__ = ['client', 'async_client', 'Response', 'AIConfig', 'DB_SETTINGS', 'gemini_ai']
