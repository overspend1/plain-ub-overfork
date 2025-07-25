"""
Base classes for plugins
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app import BOT, Message


class BasePlugin(ABC):
    """Base class for all plugins"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.config = {}
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources when plugin is disabled/unloaded."""
        pass
    
    async def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors in a consistent way"""
        error_msg = f"Error in {self.name}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        print(error_msg)  # Could be replaced with proper logging
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Set configuration for the plugin"""
        self.config.update(config)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)


class BaseCommand(BasePlugin):
    """Base class for command plugins"""
    
    def __init__(self, name: str, commands: List[str], description: str = ""):
        super().__init__(name)
        self.commands = commands
        self.description = description
        self.usage = ""
        self.flags = []
    
    @abstractmethod
    async def execute(self, bot: BOT, message: Message) -> None:
        """Execute the command"""
        pass
    
    def get_help_text(self) -> str:
        """Get formatted help text for the command"""
        help_text = f"**{self.name}**\n"
        help_text += f"Commands: {', '.join(self.commands)}\n"
        if self.description:
            help_text += f"Description: {self.description}\n"
        if self.usage:
            help_text += f"Usage: {self.usage}\n"
        if self.flags:
            help_text += f"Flags: {', '.join(self.flags)}\n"
        return help_text


class BaseFileHandler(BasePlugin):
    """Base class for file handling plugins"""
    
    def __init__(self, name: str, supported_types: List[str]):
        super().__init__(name)
        self.supported_types = supported_types
    
    @abstractmethod
    async def process_file(self, file_path: str, **kwargs) -> Optional[str]:
        """Process a file and return result path or None if failed"""
        pass
    
    def supports_file(self, file_path: str) -> bool:
        """Check if this handler supports the given file type"""
        file_ext = file_path.split('.')[-1].lower()
        return file_ext in self.supported_types


class BaseAI(BasePlugin):
    """Base class for AI integration plugins"""
    
    def __init__(self, name: str, api_key: Optional[str] = None):
        super().__init__(name)
        self.api_key = api_key
        self.client = None
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate AI response for given prompt"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if AI service is available"""
        pass