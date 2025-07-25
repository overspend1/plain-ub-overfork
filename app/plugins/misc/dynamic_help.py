"""
Dynamic help system that automatically extracts command information from docstrings
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app import BOT, Message, bot
from app.plugins.core.decorators import error_handler
from app.plugins.core.loader import plugin_loader


class DynamicHelpExtractor:
    """Automatically extract help information from plugin files"""
    
    def __init__(self):
        self.plugins_dir = Path("app/plugins")
        self.extracted_commands = {}
    
    def extract_command_info(self, file_path: Path) -> List[Dict]:
        """Extract command information from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            commands = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Look for @bot.add_cmd decorators
                    for decorator in node.decorator_list:
                        if self._is_add_cmd_decorator(decorator):
                            cmd_info = self._extract_cmd_info(decorator, node, content)
                            if cmd_info:
                                commands.append(cmd_info)
            
            return commands
            
        except Exception as e:
            print(f"Error extracting from {file_path}: {e}")
            return []
    
    def _is_add_cmd_decorator(self, decorator) -> bool:
        """Check if decorator is @bot.add_cmd"""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return (decorator.func.attr == "add_cmd" and 
                       isinstance(decorator.func.value, ast.Name) and 
                       decorator.func.value.id == "bot")
        return False
    
    def _extract_cmd_info(self, decorator, func_node, content) -> Optional[Dict]:
        """Extract command information from decorator and function"""
        try:
            # Extract command name from decorator
            cmd_name = None
            for keyword in decorator.keywords:
                if keyword.arg == "cmd":
                    if isinstance(keyword.value, ast.Constant):
                        cmd_name = keyword.value.value
                    elif isinstance(keyword.value, ast.List):
                        # Multiple commands
                        cmd_name = [elt.value for elt in keyword.value.elts if isinstance(elt, ast.Constant)]
            
            if not cmd_name:
                return None
            
            # Extract docstring
            docstring = ast.get_docstring(func_node) or ""
            
            # Parse docstring for structured info
            info = self._parse_docstring(docstring)
            
            return {
                "command": cmd_name,
                "function": func_node.name,
                "docstring": docstring,
                "info": info.get("INFO", ""),
                "usage": info.get("USAGE", ""),
                "flags": info.get("FLAGS", ""),
                "examples": info.get("EXAMPLES", "")
            }
            
        except Exception as e:
            print(f"Error extracting command info: {e}")
            return None
    
    def _parse_docstring(self, docstring: str) -> Dict[str, str]:
        """Parse structured docstring"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in docstring.split('\n'):
            line = line.strip()
            
            # Check for section headers
            if line.endswith(':') and line.replace(':', '').strip().upper() in ['CMD', 'INFO', 'USAGE', 'FLAGS', 'EXAMPLES']:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.replace(':', '').strip().upper()
                current_content = []
            elif current_section:
                current_content.append(line)
            elif not current_section and line:
                # Description before any sections
                sections['INFO'] = line
        
        # Add final section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def scan_all_plugins(self) -> Dict[str, List[Dict]]:
        """Scan all plugin files and extract command information"""
        all_commands = {}
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_') and plugin_dir.name != 'core':
                plugin_commands = []
                
                for py_file in plugin_dir.glob("*.py"):
                    if not py_file.name.startswith('_'):
                        file_commands = self.extract_command_info(py_file)
                        plugin_commands.extend(file_commands)
                
                if plugin_commands:
                    all_commands[plugin_dir.name] = plugin_commands
        
        return all_commands
    
    def generate_help_text(self, plugin_name: Optional[str] = None) -> str:
        """Generate help text for all plugins or a specific plugin"""
        all_commands = self.scan_all_plugins()
        
        if plugin_name:
            if plugin_name not in all_commands:
                return f"Plugin '{plugin_name}' not found or has no commands."
            
            return self._format_plugin_help(plugin_name, all_commands[plugin_name])
        else:
            return self._format_all_help(all_commands)
    
    def _format_plugin_help(self, plugin_name: str, commands: List[Dict]) -> str:
        """Format help text for a specific plugin"""
        help_text = f"📁 **{plugin_name.title()} Commands**\n\n"
        
        for cmd_info in commands:
            cmd_name = cmd_info["command"]
            if isinstance(cmd_name, list):
                cmd_name = ", ".join(cmd_name)
            
            help_text += f"**• `.{cmd_name}`**\n"
            
            if cmd_info["info"]:
                help_text += f"   {cmd_info['info']}\n"
            
            if cmd_info["usage"]:
                help_text += f"   **Usage:** `{cmd_info['usage']}`\n"
            
            if cmd_info["flags"]:
                help_text += f"   **Flags:** {cmd_info['flags']}\n"
            
            help_text += "\n"
        
        return help_text
    
    def _format_all_help(self, all_commands: Dict[str, List[Dict]]) -> str:
        """Format help text for all plugins"""
        help_text = "🤖 **All Available Commands**\n\n"
        
        total_commands = sum(len(commands) for commands in all_commands.values())
        help_text += f"**Total:** {len(all_commands)} plugins, {total_commands} commands\n\n"
        
        for plugin_name, commands in sorted(all_commands.items()):
            help_text += f"**📂 {plugin_name.title()}** ({len(commands)} commands)\n"
            
            cmd_names = []
            for cmd_info in commands:
                cmd_name = cmd_info["command"]
                if isinstance(cmd_name, list):
                    cmd_names.extend(cmd_name)
                else:
                    cmd_names.append(cmd_name)
            
            # Show commands in rows
            for i in range(0, len(cmd_names), 4):
                row_commands = cmd_names[i:i+4]
                help_text += "   • " + " • ".join(f"`.{cmd}`" for cmd in row_commands) + "\n"
            
            help_text += "\n"
        
        help_text += "**Usage:**\n"
        help_text += "• `.autohelp` - Show this list\n"
        help_text += "• `.autohelp <plugin>` - Show plugin details\n"
        help_text += "• `.help` - Show manual help system\n"
        
        return help_text


# Global extractor instance
help_extractor = DynamicHelpExtractor()


@bot.add_cmd(cmd="autohelp")
@error_handler("Auto help command failed")
async def auto_help(bot: BOT, message: Message):
    """
    CMD: AUTOHELP
    INFO: Automatically generated help from command docstrings
    USAGE: 
        .autohelp - Show all commands
        .autohelp <plugin> - Show specific plugin commands
    """
    
    plugin_name = message.input.strip().lower() if message.input else None
    
    processing_msg = await message.reply("🔍 Scanning plugins for commands...")
    
    try:
        help_text = help_extractor.generate_help_text(plugin_name)
        
        await processing_msg.delete()
        
        # Split long messages
        if len(help_text) > 4000:
            parts = [help_text[i:i+4000] for i in range(0, len(help_text), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await message.reply(part)
                else:
                    await message.reply(f"**Continued...**\n\n{part}")
        else:
            await message.reply(help_text)
            
    except Exception as e:
        await processing_msg.edit(f"Error generating help: {str(e)}")


@bot.add_cmd(cmd="searchcmd")
@error_handler("Search command failed")
async def search_command(bot: BOT, message: Message):
    """
    CMD: SEARCHCMD
    INFO: Search for commands across all plugins
    USAGE: .searchcmd <command_name>
    """
    
    if not message.input:
        await message.reply("Please provide a command name to search for.")
        return
    
    search_term = message.input.strip().lower()
    processing_msg = await message.reply(f"🔍 Searching for command: `.{search_term}`...")
    
    try:
        all_commands = help_extractor.scan_all_plugins()
        found_commands = []
        
        for plugin_name, commands in all_commands.items():
            for cmd_info in commands:
                cmd_names = cmd_info["command"]
                if not isinstance(cmd_names, list):
                    cmd_names = [cmd_names]
                
                for cmd_name in cmd_names:
                    if search_term in cmd_name.lower():
                        found_commands.append({
                            "plugin": plugin_name,
                            "command": cmd_name,
                            "info": cmd_info
                        })
        
        await processing_msg.delete()
        
        if not found_commands:
            await message.reply(f"No commands found matching: `.{search_term}`")
            return
        
        result_text = f"🔍 **Search Results for: `.{search_term}`**\n\n"
        result_text += f"Found {len(found_commands)} matching command(s):\n\n"
        
        for match in found_commands:
            result_text += f"**• `.{match['command']}`** (from `{match['plugin']}`)\n"
            if match['info']['info']:
                result_text += f"   {match['info']['info']}\n"
            if match['info']['usage']:
                result_text += f"   Usage: `{match['info']['usage']}`\n"
            result_text += "\n"
        
        await message.reply(result_text)
        
    except Exception as e:
        await processing_msg.edit(f"Error searching commands: {str(e)}")


@bot.add_cmd(cmd="cmdinfo")
@error_handler("Command info failed")
async def command_info(bot: BOT, message: Message):
    """
    CMD: CMDINFO
    INFO: Get detailed information about a specific command
    USAGE: .cmdinfo <command_name>
    """
    
    if not message.input:
        await message.reply("Please provide a command name.")
        return
    
    cmd_name = message.input.strip().lower()
    processing_msg = await message.reply(f"📋 Getting info for: `.{cmd_name}`...")
    
    try:
        all_commands = help_extractor.scan_all_plugins()
        found_command = None
        
        for plugin_name, commands in all_commands.items():
            for cmd_info in commands:
                cmd_names = cmd_info["command"]
                if not isinstance(cmd_names, list):
                    cmd_names = [cmd_names]
                
                if cmd_name in [c.lower() for c in cmd_names]:
                    found_command = {
                        "plugin": plugin_name,
                        "info": cmd_info
                    }
                    break
            
            if found_command:
                break
        
        await processing_msg.delete()
        
        if not found_command:
            await message.reply(f"Command `.{cmd_name}` not found.")
            return
        
        info = found_command["info"]
        cmd_names = info["command"]
        if not isinstance(cmd_names, list):
            cmd_names = [cmd_names]
        
        info_text = f"📋 **Command Information**\n\n"
        info_text += f"**Command:** {', '.join(f'`.{c}`' for c in cmd_names)}\n"
        info_text += f"**Plugin:** `{found_command['plugin']}`\n"
        info_text += f"**Function:** `{info['function']}`\n\n"
        
        if info["info"]:
            info_text += f"**Description:**\n{info['info']}\n\n"
        
        if info["usage"]:
            info_text += f"**Usage:**\n`{info['usage']}`\n\n"
        
        if info["flags"]:
            info_text += f"**Flags:**\n{info['flags']}\n\n"
        
        if info["examples"]:
            info_text += f"**Examples:**\n{info['examples']}\n\n"
        
        if info["docstring"]:
            info_text += f"**Full Documentation:**\n```\n{info['docstring'][:500]}{'...' if len(info['docstring']) > 500 else ''}\n```"
        
        await message.reply(info_text)
        
    except Exception as e:
        await processing_msg.edit(f"Error getting command info: {str(e)}")