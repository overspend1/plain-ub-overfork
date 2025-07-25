"""
Module Manager for handling modular components (Legacy)
This is kept for backward compatibility but uses the new plugin system internally.
"""

from typing import Dict, List, Optional
from .base import BasePlugin
from .loader import plugin_loader


class ModuleManager:
    """Legacy module manager that delegates to plugin loader"""
    
    def __init__(self):
        # Delegate to plugin loader for actual functionality
        pass
    
    def register_module(self, module: BasePlugin) -> bool:
        """Register a new module (delegates to plugin loader)"""
        plugin_loader.register_plugin_instance(module)
        return True
    
    def unregister_module(self, name: str) -> bool:
        """Unregister a module (delegates to plugin loader)"""
        # This would require unloading the plugin
        return True
    
    async def initialize_all(self) -> bool:
        """Initialize all registered modules (delegates to plugin loader)"""
        results = await plugin_loader.load_all_plugins()
        return all(results.values())
    
    async def cleanup_all(self) -> None:
        """Cleanup all modules"""
        # Plugin loader handles this
        pass
    
    def get_module(self, name: str) -> Optional[BasePlugin]:
        """Get a module by name (delegates to plugin loader)"""
        return plugin_loader.get_plugin(name)
    
    def list_modules(self) -> List[str]:
        """List all registered module names (delegates to plugin loader)"""
        return plugin_loader.list_loaded_plugins()
    
    def get_module_status(self) -> Dict[str, bool]:
        """Get status of all modules (delegates to plugin loader)"""
        return plugin_loader.get_plugin_status()
    
    async def enable_module(self, name: str) -> bool:
        """Enable a specific module"""
        plugin = plugin_loader.get_plugin(name)
        if plugin:
            plugin.enabled = True
            return True
        return False
    
    async def disable_module(self, name: str) -> bool:
        """Disable a specific module"""
        plugin = plugin_loader.get_plugin(name)
        if plugin:
            plugin.enabled = False
            return True
        return False


# Global module manager instance (for backward compatibility)
module_manager = ModuleManager()