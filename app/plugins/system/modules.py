"""
Module management commands
"""

from app import BOT, Message, bot
from app.plugins.core.loader import plugin_loader
from app.plugins.core.decorators import error_handler


@bot.add_cmd(cmd="plugins")
@error_handler("Plugin management command failed")
async def manage_plugins(bot: BOT, message: Message):
 """
 CMD: PLUGINS
 INFO: Manage bot plugins
 USAGE: 
 .plugins - List all plugins
 .plugins status - Show plugin status 
 .plugins load <name> - Load plugin
 .plugins unload <name> - Unload plugin
 .plugins reload - Reload all plugins
 .plugins discover - Discover available plugins
 """
 
 args = message.input.split() if message.input else []
 
 if not args or args[0] == "list":
 # List loaded plugins
 plugins = plugin_loader.list_loaded_plugins()
 if not plugins:
 await message.reply("No plugins loaded")
 return
 
 plugin_text = "**Loaded Plugins:**\n\n"
 for i, plugin_name in enumerate(plugins, 1):
 plugin = plugin_loader.get_plugin(plugin_name)
 status = "Enabled" if plugin and plugin.enabled else "Disabled"
 plugin_text += f"{i}. **{plugin_name}** - {status}\n"
 
 await message.reply(plugin_text)
 
 elif args[0] == "status":
 # Show detailed status
 status_dict = plugin_loader.get_plugin_status()
 if not status_dict:
 await message.reply("No plugins loaded")
 return
 
 status_text = "**Plugin Status:**\n\n"
 enabled_count = sum(status_dict.values())
 total_count = len(status_dict)
 
 status_text += f"**Summary:** {enabled_count}/{total_count} plugins enabled\n\n"
 
 for name, enabled in status_dict.items():
 status_icon = "[ENABLED]" if enabled else "[DISABLED]"
 status_text += f"{status_icon} **{name}**\n"
 
 await message.reply(status_text)
 
 elif args[0] == "load" and len(args) > 1:
 # Load specific plugin
 plugin_name = args[1]
 processing_msg = await message.reply(f"Loading plugin: **{plugin_name}**...")
 
 success = await plugin_loader.load_plugin(plugin_name)
 
 if success:
 await processing_msg.edit(f"Loaded plugin: **{plugin_name}**")
 else:
 await processing_msg.edit(f"Failed to load plugin: **{plugin_name}**")
 
 elif args[0] == "unload" and len(args) > 1:
 # Unload specific plugin
 plugin_name = args[1]
 processing_msg = await message.reply(f"Unloading plugin: **{plugin_name}**...")
 
 success = await plugin_loader.unload_plugin(plugin_name)
 
 if success:
 await processing_msg.edit(f"Unloaded plugin: **{plugin_name}**")
 else:
 await processing_msg.edit(f"Failed to unload plugin: **{plugin_name}**")
 
 elif args[0] == "reload":
 # Reload all plugins
 processing_msg = await message.reply("Reloading all plugins...")
 
 results = await plugin_loader.load_all_plugins()
 success_count = sum(results.values())
 total_count = len(results)
 
 if success_count == total_count:
 await processing_msg.edit("All plugins reloaded successfully")
 else:
 await processing_msg.edit(f"Reloaded {success_count}/{total_count} plugins. Check logs for details.")
 
 elif args[0] == "discover":
 # Discover available plugins
 available_plugins = plugin_loader.discover_plugins()
 loaded_plugins = plugin_loader.list_loaded_plugins()
 
 if not available_plugins:
 await message.reply("No plugins found in plugins directory")
 return
 
 discover_text = " **Available Plugins:**\n\n"
 for i, plugin_name in enumerate(available_plugins, 1):
 status = "Loaded" if plugin_name in loaded_plugins else "Not Loaded"
 discover_text += f"{i}. **{plugin_name}** - {status}\n"
 
 await message.reply(discover_text)
 
 else:
 # Show help
 help_text = """**Plugin Management Help**

**Commands:**
• `.plugins` - List loaded plugins
• `.plugins status` - Show detailed status
• `.plugins load <name>` - Load a plugin
• `.plugins unload <name>` - Unload a plugin 
• `.plugins reload` - Reload all plugins
• `.plugins discover` - Show available plugins

**Examples:**
• `.plugins status`
• `.plugins load ai`
• `.plugins unload torrent_leech`
"""
 await message.reply(help_text)


@bot.add_cmd(cmd="pluginfo")
@error_handler("Plugin info command failed") 
async def plugin_info(bot: BOT, message: Message):
 """
 CMD: PLUGINFO
 INFO: Get detailed information about a plugin
 USAGE: .pluginfo <plugin_name>
 """
 
 if not message.input:
 await message.reply("Please specify a plugin name")
 return
 
 plugin_name = message.input.strip()
 plugin = plugin_loader.get_plugin(plugin_name)
 
 if not plugin:
 available = ", ".join(plugin_loader.list_loaded_plugins())
 await message.reply(f"Plugin **{plugin_name}** not found.\n\nLoaded: {available}")
 return
 
 info_text = f"**Plugin Information**\n\n"
 info_text += f"**Name:** {plugin.name}\n"
 info_text += f"**Status:** {'Enabled' if plugin.enabled else 'Disabled'}\n"
 info_text += f"**Type:** {type(plugin).__name__}\n"
 
 # Show configuration if available
 if hasattr(plugin, 'config') and plugin.config:
 info_text += f"**Configuration:** {len(plugin.config)} settings\n"
 
 # Show additional info based on plugin type
 if hasattr(plugin, 'api_key'):
 info_text += f"**API Key:** {'Configured' if plugin.api_key else 'Missing'}\n"
 
 if hasattr(plugin, 'commands'):
 info_text += f"**Commands:** {', '.join(plugin.commands)}\n"
 
 if hasattr(plugin, 'supported_types'):
 info_text += f"**Supported Types:** {', '.join(plugin.supported_types)}\n"
 
 await message.reply(info_text)


@bot.add_cmd(cmd="listmodules")
@error_handler("List modules command failed")
async def list_all_modules(bot: BOT, message: Message):
 """
 CMD: LISTMODULES
 INFO: List all available modules in the plugins directory
 USAGE: .listmodules [detailed]
 """
 
 show_detailed = message.input and "detailed" in message.input.lower()
 
 # Get comprehensive module information
 modules_info = plugin_loader.get_comprehensive_module_list()
 loaded_plugins = plugin_loader.list_loaded_plugins()
 
 if not modules_info:
 await message.reply("No modules found in plugins directory")
 return
 
 list_text = "**ALL AVAILABLE MODULES:**\n\n"
 
 total_plugins = 0
 total_modules = 0
 total_subdirs = 0
 
 for plugin_name, info in sorted(modules_info.items()):
 total_plugins += 1
 total_modules += info["total_files"]
 total_subdirs += info["subdirectories"]
 
 # Plugin status
 status = "Loaded" if plugin_name in loaded_plugins else "Not Loaded"
 
 # Show plugin header with details
 subdir_info = f" + {info['subdirectories']} subdirs" if info["subdirectories"] > 0 else ""
 list_text += f"**{plugin_name.upper()}** ({info['total_files']} files{subdir_info}) - {status}\n"
 
 if show_detailed:
 # Show all modules in detailed mode
 for module in info["modules"]:
 list_text += f" • `{module}.py`\n"
 else:
 # Show condensed view - just first few modules
 modules_to_show = info["modules"][:6] # Show first 6
 for module in modules_to_show:
 list_text += f" • `{module}.py`\n"
 
 if len(info["modules"]) > 6:
 remaining = len(info["modules"]) - 6
 list_text += f" • ... and {remaining} more modules\n"
 
 list_text += "\n"
 
 # Enhanced Summary
 list_text += f"**COMPLETE SUMMARY:**\n"
 list_text += f"• **{total_plugins}** plugin directories\n" 
 list_text += f"• **{total_modules}** total Python modules\n"
 list_text += f"• **{total_subdirs}** subdirectories\n"
 list_text += f"• **{len(loaded_plugins)}** plugins currently loaded\n\n"
 
 list_text += f"** Tips:**\n"
 list_text += f"• Use `.listmodules detailed` to see all modules\n"
 list_text += f"• Use `.plugins discover` to see plugin status\n"
 list_text += f"• Use `.help <module>` for module documentation\n"
 
 # Split message if too long
 if len(list_text) > 4000:
 parts = [list_text[i:i+4000] for i in range(0, len(list_text), 4000)]
 for i, part in enumerate(parts):
 if i == 0:
 await message.reply(part)
 else:
 await message.reply(f"**Continued ({i+1})...**\n\n{part}")
 else:
 await message.reply(list_text)


@bot.add_cmd(cmd="debugmodules")
@error_handler("Debug modules command failed")
async def debug_modules(bot: BOT, message: Message):
 """
 CMD: DEBUGMODULES
 INFO: Debug command to show detailed module discovery information
 USAGE: .debugmodules
 """
 
 debug_text = " **MODULE DISCOVERY DEBUG:**\n\n"
 
 # Show the plugins directory path
 debug_text += f"**Plugins Directory:** `{plugin_loader.plugins_dir}`\n\n"
 
 # List all directories found
 debug_text += "**All Directories Found:**\n"
 try:
 for item in plugin_loader.plugins_dir.iterdir():
 if item.is_dir():
 is_excluded = item.name.startswith('_') or item.name == 'core'
 status = "EXCLUDED" if is_excluded else "INCLUDED"
 debug_text += f"• `{item.name}` - {status}\n"
 debug_text += "\n"
 except Exception as e:
 debug_text += f"Error reading directory: {e}\n\n"
 
 # Show comprehensive module info
 try:
 modules_info = plugin_loader.get_comprehensive_module_list()
 debug_text += f"**Detailed Module Discovery:**\n"
 
 for plugin_name, info in sorted(modules_info.items()):
 debug_text += f"\n**{plugin_name}:**\n"
 debug_text += f" Direct modules: {info['direct_modules']}\n"
 debug_text += f" Subdirectories: {info['subdirectories']}\n"
 debug_text += f" Total files: {info['total_files']}\n"
 debug_text += f" Modules found:\n"
 
 for module in info["modules"][:10]: # Show first 10
 debug_text += f" • {module}.py\n"
 
 if len(info["modules"]) > 10:
 debug_text += f" • ... and {len(info['modules']) - 10} more\n"
 
 except Exception as e:
 debug_text += f"Error in comprehensive discovery: {e}\n"
 
 # Show old method for comparison
 try:
 debug_text += f"\n**Old Discovery Method:**\n"
 old_modules = plugin_loader.discover_all_modules()
 for plugin_name, modules in sorted(old_modules.items()):
 debug_text += f"• {plugin_name}: {len(modules)} modules\n"
 except Exception as e:
 debug_text += f"Error in old discovery: {e}\n"
 
 # Split if too long
 if len(debug_text) > 4000:
 parts = [debug_text[i:i+4000] for i in range(0, len(debug_text), 4000)]
 for i, part in enumerate(parts):
 if i == 0:
 await message.reply(part)
 else:
 await message.reply(f"** Debug ({i+1})...**\n\n{part}")
 else:
 await message.reply(debug_text)