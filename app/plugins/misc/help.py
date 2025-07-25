"""
Comprehensive help system for all userbot modules
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional

from app import BOT, Message, bot
from app.plugins.core.decorators import error_handler
from app.plugins.core.loader import plugin_loader


class HelpSystem:
    """Comprehensive help system for all modules"""
    
    def __init__(self):
        self.help_data = {}
        self.module_commands = {}
        self._load_help_data()
    
    def _load_help_data(self):
        """Load help data for all modules"""
        self.help_data = {
            # Admin Commands
            "admin": {
                "title": "Admin Commands",
                "description": "Administrative tools for managing groups and users",
                "commands": {
                    "ban": "Ban users from the group",
                    "unban": "Unban users from the group", 
                    "kick": "Kick users from the group",
                    "mute": "Mute users in the group",
                    "unmute": "Unmute users in the group",
                    "promote": "Promote users to admin",
                    "demote": "Remove admin privileges",
                    "zombies": "Remove deleted accounts from group",
                    "fbans": "Federation ban management"
                },
                "usage": [
                    ".ban [reply/username] [reason]",
                    ".kick [reply/username] [reason]",
                    ".mute [reply/username] [time]",
                    ".promote [reply/username]"
                ]
            },
            
            # AI Commands
            "ai": {
                "title": "AI Commands", 
                "description": "AI-powered features using Gemini",
                "commands": {
                    "ai": "Simple AI query",
                    "aic": "Interactive AI chat mode",
                    "lh": "Load AI chat history",
                    "aistatus": "Check AI module status",
                    "aihelp": "Show AI commands help"
                },
                "flags": {
                    "-s": "Use search functionality",
                    "-i": "Generate image instead of text", 
                    "-a": "Generate audio response",
                    "-m": "Use male voice (with -a)"
                },
                "usage": [
                    ".ai What is Python?",
                    ".ai -s Latest news about AI",
                    ".ai -i A beautiful sunset",
                    ".aic Hello [interactive mode]"
                ]
            },
            
            # File Commands
            "files": {
                "title": "File Management",
                "description": "File upload, download, and management tools",
                "commands": {
                    "upload": "Upload files to various services",
                    "download": "Download files from URLs",
                    "rename": "Rename files",
                    "leech": "Download and upload files",
                    "spoiler": "Send files as spoilers",
                    "catbox": "Upload to catbox.moe",
                    "gofile": "Upload to gofile.io",
                    "anonfiles": "Upload to anonfiles.com",
                    "pixeldrain": "Upload to pixeldrain.com",
                    "torrent": "Torrent download and management"
                },
                "usage": [
                    ".upload [reply to file]",
                    ".download <url>",
                    ".rename <new_name> [reply to file]",
                    ".leech <url>"
                ]
            },
            
            # System Commands
            "system": {
                "title": "System Commands",
                "description": "System information and management tools", 
                "commands": {
                    "neofetch": "Display system information",
                    "sysinfo": "Detailed system information",
                    "speedtest": "Internet speed test",
                    "shell": "Execute shell commands",
                    "termux": "Termux-specific commands",
                    "plugins": "Plugin management",
                    "listmodules": "List all available modules",
                    "pluginfo": "Get plugin information"
                },
                "usage": [
                    ".neofetch",
                    ".speedtest",
                    ".shell <command>",
                    ".plugins status"
                ]
            },
            
            # Telegram Tools
            "tg_tools": {
                "title": "Telegram Tools",
                "description": "Telegram-specific utilities and tools",
                "commands": {
                    "ping": "Check bot response time",
                    "chat": "Chat management tools",
                    "delete": "Delete messages",
                    "reply": "Reply to messages",
                    "respond": "Auto-respond tools",
                    "click": "Click inline buttons",
                    "kang": "Steal stickers",
                    "get_message": "Get message information",
                    "pm_permit": "PM permission system"
                },
                "usage": [
                    ".ping",
                    ".delete [count]",
                    ".kang [reply to sticker]",
                    ".chat info"
                ]
            },
            
            # Utilities
            "utils": {
                "title": "Utilities",
                "description": "General utility commands",
                "commands": {
                    "calc": "Calculator",
                    "encode": "Text encoding/decoding",
                    "qr": "QR code generation"
                },
                "usage": [
                    ".calc 2+2*3",
                    ".encode base64 <text>",
                    ".qr <text>"
                ]
            },
            
            # Miscellaneous  
            "misc": {
                "title": "Miscellaneous",
                "description": "Various useful commands",
                "commands": {
                    "alive": "Check if bot is alive",
                    "song": "Search and download songs",
                    "help": "Show this help system"
                },
                "usage": [
                    ".alive",
                    ".song <song name>",
                    ".help [module_name]"
                ]
            },
            
            # Network Tools
            "network": {
                "title": "Network Tools", 
                "description": "Network utilities and tools",
                "commands": {
                    "network": "Network diagnostic tools"
                },
                "usage": [
                    ".network ping <host>",
                    ".network trace <host>"
                ]
            },
            
            # Sudo Commands
            "sudo": {
                "title": "Sudo Commands",
                "description": "Superuser management commands",
                "commands": {
                    "sudo": "Execute commands as superuser",
                    "users": "Manage sudo users",
                    "superuser": "Toggle superuser mode"
                },
                "usage": [
                    ".sudo <command>",
                    ".users add <user_id>",
                    ".superuser toggle"
                ]
            }
        }
    
    def get_main_help(self) -> str:
        """Get main help page with all modules"""
        help_text = """**PLAIN-UB Help System**

**Available Modules:**

"""
        
        for module_key, module_data in self.help_data.items():
            title = module_data["title"]
            cmd_count = len(module_data["commands"])
            help_text += f"{title} - `{cmd_count} commands`\n"
        
        help_text += f"""

**Usage:**
• `.help` - Show this main help
• `.help <module>` - Show specific module help
• `.listmodules` - List all available modules  
• `.plugins` - Manage plugins

**Examples:**
• `.help ai` - Show AI commands
• `.help admin` - Show admin commands
• `.help files` - Show file commands

**Module Names:**
{', '.join(f'`{key}`' for key in self.help_data.keys())}
"""
        
        return help_text
    
    def get_module_help(self, module_name: str) -> Optional[str]:
        """Get help for a specific module"""
        module_name = module_name.lower()
        
        if module_name not in self.help_data:
            return None
        
        module_data = self.help_data[module_name]
        help_text = f"""{module_data["title"]}

**Description:** {module_data["description"]}

**Commands:**
"""
        
        for cmd, desc in module_data["commands"].items():
            help_text += f"• `.{cmd}` - {desc}\n"
        
        # Add flags if available
        if "flags" in module_data:
            help_text += f"\n**Flags:**\n"
            for flag, desc in module_data["flags"].items():
                help_text += f"• `{flag}` - {desc}\n"
        
        # Add usage examples
        if "usage" in module_data:
            help_text += f"\n**Usage Examples:**\n"
            for usage in module_data["usage"]:
                help_text += f"• `{usage}`\n"
        
        return help_text
    
    def search_command(self, command: str) -> Optional[str]:
        """Search for a command across all modules"""
        command = command.lower().replace(".", "")
        found_in = []
        
        for module_key, module_data in self.help_data.items():
            if command in module_data["commands"]:
                found_in.append({
                    "module": module_key,
                    "title": module_data["title"], 
                    "description": module_data["commands"][command]
                })
        
        if not found_in:
            return None
        
        result = f"**Command Search: `.{command}`**\n\n"
        
        for item in found_in:
            result += f"**{item['title']}**\n"
            result += f"• `.{command}` - {item['description']}\n"
            result += f"• Module: `{item['module']}`\n\n"
        
        result += f"Use `.help {found_in[0]['module']}` for more details."
        
        return result


# Global help system instance
help_system = HelpSystem()


@bot.add_cmd(cmd="help")
@error_handler("Help command failed")
async def show_help(bot: BOT, message: Message):
    """
    CMD: HELP
    INFO: Show comprehensive help for all modules
    USAGE: 
        .help - Show main help page
        .help <module> - Show specific module help
        .help search <command> - Search for a command
    """
    
    if not message.input:
        # Show main help
        help_text = help_system.get_main_help()
        await message.reply(help_text)
        return
    
    args = message.input.strip().split()
    
    if args[0].lower() == "search" and len(args) > 1:
        # Search for command
        command = args[1]
        result = help_system.search_command(command)
        
        if result:
            await message.reply(result)
        else:
            await message.reply(f"Command `.{command}` not found in help system.")
        return
    
    # Show specific module help
    module_name = args[0].lower()
    module_help = help_system.get_module_help(module_name)
    
    if module_help:
        # Split long messages
        if len(module_help) > 4000:
            parts = [module_help[i:i+4000] for i in range(0, len(module_help), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await message.reply(part)
                else:
                    await message.reply(f"**Continued...**\n\n{part}")
        else:
            await message.reply(module_help)
    else:
        available_modules = ", ".join(f"`{key}`" for key in help_system.help_data.keys())
        await message.reply(f"Module `{module_name}` not found.\n\nAvailable modules: {available_modules}")


@bot.add_cmd(cmd="commands")
@error_handler("Commands list failed")
async def list_commands(bot: BOT, message: Message):
    """
    CMD: COMMANDS
    INFO: List all available commands
    USAGE: .commands [module_name]
    """
    
    if message.input:
        # Show commands for specific module
        module_name = message.input.strip().lower()
        module_help = help_system.get_module_help(module_name)
        
        if module_help:
            await message.reply(module_help)
        else:
            await message.reply(f"Module `{module_name}` not found.")
        return
    
    # Show all commands
    commands_text = "**All Available Commands:**\n\n"
    
    for module_key, module_data in help_system.help_data.items():
        commands_text += f"**{module_data['title']}**\n"
        
        commands_list = list(module_data["commands"].keys())
        commands_per_line = 4
        
        for i in range(0, len(commands_list), commands_per_line):
            line_commands = commands_list[i:i+commands_per_line]
            commands_text += "• " + " • ".join(f"`.{cmd}`" for cmd in line_commands) + "\n"
        
        commands_text += "\n"
    
    commands_text += "Use `.help <module>` for detailed information about each module."
    
    # Split if too long
    if len(commands_text) > 4000:
        parts = [commands_text[i:i+4000] for i in range(0, len(commands_text), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await message.reply(part)
            else:
                await message.reply(f"**Continued...**\n\n{part}")
    else:
        await message.reply(commands_text)