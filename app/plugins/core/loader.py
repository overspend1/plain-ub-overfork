"""
Plugin Loader System
"""

import importlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import BasePlugin


class PluginLoader:
    """Manages loading and unloading of plugins"""
    
    def __init__(self, plugins_dir: str = "app/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.plugin_modules: Dict[str, any] = {}
        
    def discover_plugins(self) -> List[str]:
        """Discover all available plugins in the plugins directory"""
        plugins = []
        
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_') and item.name != 'core':
                # Check if it has plugin files
                if any(f.suffix == '.py' and not f.name.startswith('_') for f in item.iterdir()):
                    plugins.append(item.name)
        
        return plugins
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """Load a specific plugin"""
        try:
            plugin_path = self.plugins_dir / plugin_name
            if not plugin_path.exists():
                print(f"Plugin directory not found: {plugin_name}")
                return False
            
            # Look for plugin files
            plugin_files = []
            for file_path in plugin_path.glob("*.py"):
                if not file_path.name.startswith('_'):
                    plugin_files.append(file_path.stem)
            
            if not plugin_files:
                print(f"No plugin files found in: {plugin_name}")
                return False
            
            # Import the plugin modules
            success_count = 0
            for file_name in plugin_files:
                try:
                    module_name = f"app.plugins.{plugin_name}.{file_name}"
                    
                    # Import or reload the module
                    if module_name in self.plugin_modules:
                        importlib.reload(self.plugin_modules[module_name])
                    else:
                        module = importlib.import_module(module_name)
                        self.plugin_modules[module_name] = module
                    
                    success_count += 1
                    print(f"✅ Loaded: {module_name}")
                    
                except Exception as e:
                    print(f"❌ Failed to load {module_name}: {e}")
            
            if success_count > 0:
                print(f"Loaded {success_count}/{len(plugin_files)} files from {plugin_name}")
                return True
            else:
                print(f"Failed to load any files from {plugin_name}")
                return False
                
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        try:
            # Find and cleanup plugin instances
            plugin_keys_to_remove = []
            for key, plugin in self.loaded_plugins.items():
                if key.startswith(plugin_name):
                    await plugin.cleanup()
                    plugin_keys_to_remove.append(key)
            
            # Remove from loaded plugins
            for key in plugin_keys_to_remove:
                del self.loaded_plugins[key]
            
            # Remove module references (though Python will still cache them)
            module_keys_to_remove = []
            for module_name in self.plugin_modules.keys():
                if f".{plugin_name}." in module_name:
                    module_keys_to_remove.append(module_name)
            
            for key in module_keys_to_remove:
                del self.plugin_modules[key]
            
            print(f"Unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            print(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    async def load_all_plugins(self) -> Dict[str, bool]:
        """Load all discovered plugins"""
        plugins = self.discover_plugins()
        results = {}
        
        print(f"Discovered {len(plugins)} plugin directories")
        
        for plugin_name in plugins:
            print(f"Loading plugin: {plugin_name}")
            results[plugin_name] = await self.load_plugin(plugin_name)
        
        success_count = sum(results.values())
        print(f"Successfully loaded {success_count}/{len(plugins)} plugins")
        
        return results
    
    def register_plugin_instance(self, plugin: BasePlugin) -> None:
        """Register a plugin instance"""
        self.loaded_plugins[plugin.name] = plugin
        print(f"Registered plugin instance: {plugin.name}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin instance by name"""
        return self.loaded_plugins.get(name)
    
    def list_loaded_plugins(self) -> List[str]:
        """List all loaded plugin names"""
        return list(self.loaded_plugins.keys())
    
    def get_plugin_status(self) -> Dict[str, bool]:
        """Get status of all loaded plugins"""
        return {
            name: plugin.enabled 
            for name, plugin in self.loaded_plugins.items()
        }


# Global plugin loader instance
plugin_loader = PluginLoader()