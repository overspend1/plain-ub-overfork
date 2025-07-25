"""
Module Manager for handling modular components
"""

from typing import Dict, List, Optional, Type
from .base import BaseModule


class ModuleManager:
    """Manages all modular components"""
    
    def __init__(self):
        self.modules: Dict[str, BaseModule] = {}
        self.initialized = False
    
    def register_module(self, module: BaseModule) -> bool:
        """Register a new module"""
        if module.name in self.modules:
            print(f"Module {module.name} already registered")
            return False
        
        self.modules[module.name] = module
        print(f"Registered module: {module.name}")
        return True
    
    def unregister_module(self, name: str) -> bool:
        """Unregister a module"""
        if name not in self.modules:
            print(f"Module {name} not found")
            return False
        
        module = self.modules.pop(name)
        print(f"Unregistered module: {name}")
        return True
    
    async def initialize_all(self) -> bool:
        """Initialize all registered modules"""
        success_count = 0
        total_count = len(self.modules)
        
        for name, module in self.modules.items():
            try:
                if await module.initialize():
                    success_count += 1
                    print(f"✅ Initialized: {name}")
                else:
                    print(f"❌ Failed to initialize: {name}")
            except Exception as e:
                print(f"❌ Error initializing {name}: {e}")
        
        self.initialized = True
        print(f"Initialized {success_count}/{total_count} modules")
        return success_count == total_count
    
    async def cleanup_all(self) -> None:
        """Cleanup all modules"""
        for name, module in self.modules.items():
            try:
                await module.cleanup()
                print(f"Cleaned up: {name}")
            except Exception as e:
                print(f"Error cleaning up {name}: {e}")
    
    def get_module(self, name: str) -> Optional[BaseModule]:
        """Get a module by name"""
        return self.modules.get(name)
    
    def list_modules(self) -> List[str]:
        """List all registered module names"""
        return list(self.modules.keys())
    
    def get_module_status(self) -> Dict[str, bool]:
        """Get status of all modules"""
        return {
            name: module.enabled 
            for name, module in self.modules.items()
        }
    
    async def enable_module(self, name: str) -> bool:
        """Enable a specific module"""
        module = self.get_module(name)
        if not module:
            return False
        
        if not module.enabled:
            if await module.initialize():
                module.enabled = True
                print(f"Enabled module: {name}")
                return True
            else:
                print(f"Failed to enable module: {name}")
                return False
        
        return True
    
    async def disable_module(self, name: str) -> bool:
        """Disable a specific module"""
        module = self.get_module(name)
        if not module:
            return False
        
        if module.enabled:
            await module.cleanup()
            module.enabled = False
            print(f"Disabled module: {name}")
        
        return True


# Global module manager instance
module_manager = ModuleManager()