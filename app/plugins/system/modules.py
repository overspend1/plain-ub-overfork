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
        
        plugin_text = "🔌 **Loaded Plugins:**\n\n"
        for i, plugin_name in enumerate(plugins, 1):
            plugin = plugin_loader.get_plugin(plugin_name)
            status = "✅ Enabled" if plugin and plugin.enabled else "❌ Disabled"
            plugin_text += f"{i}. **{plugin_name}** - {status}\n"
        
        await message.reply(plugin_text)
    
    elif args[0] == "status":
        # Show detailed status
        status_dict = plugin_loader.get_plugin_status()
        if not status_dict:
            await message.reply("No plugins loaded")
            return
        
        status_text = "📊 **Plugin Status:**\n\n"
        enabled_count = sum(status_dict.values())
        total_count = len(status_dict)
        
        status_text += f"**Summary:** {enabled_count}/{total_count} plugins enabled\n\n"
        
        for name, enabled in status_dict.items():
            status_icon = "✅" if enabled else "❌"
            status_text += f"{status_icon} **{name}**\n"
        
        await message.reply(status_text)
    
    elif args[0] == "load" and len(args) > 1:
        # Load specific plugin
        plugin_name = args[1]
        processing_msg = await message.reply(f"🔄 Loading plugin: **{plugin_name}**...")
        
        success = await plugin_loader.load_plugin(plugin_name)
        
        if success:
            await processing_msg.edit(f"✅ Loaded plugin: **{plugin_name}**")
        else:
            await processing_msg.edit(f"❌ Failed to load plugin: **{plugin_name}**")
    
    elif args[0] == "unload" and len(args) > 1:
        # Unload specific plugin
        plugin_name = args[1]
        processing_msg = await message.reply(f"🔄 Unloading plugin: **{plugin_name}**...")
        
        success = await plugin_loader.unload_plugin(plugin_name)
        
        if success:
            await processing_msg.edit(f"✅ Unloaded plugin: **{plugin_name}**")
        else:
            await processing_msg.edit(f"❌ Failed to unload plugin: **{plugin_name}**")
    
    elif args[0] == "reload":
        # Reload all plugins
        processing_msg = await message.reply("🔄 Reloading all plugins...")
        
        results = await plugin_loader.load_all_plugins()
        success_count = sum(results.values())
        total_count = len(results)
        
        if success_count == total_count:
            await processing_msg.edit("✅ All plugins reloaded successfully")
        else:
            await processing_msg.edit(f"⚠️ Reloaded {success_count}/{total_count} plugins. Check logs for details.")
    
    elif args[0] == "discover":
        # Discover available plugins
        available_plugins = plugin_loader.discover_plugins()
        loaded_plugins = plugin_loader.list_loaded_plugins()
        
        if not available_plugins:
            await message.reply("No plugins found in plugins directory")
            return
        
        discover_text = "🔍 **Available Plugins:**\n\n"
        for i, plugin_name in enumerate(available_plugins, 1):
            status = "✅ Loaded" if plugin_name in loaded_plugins else "⭕ Not Loaded"
            discover_text += f"{i}. **{plugin_name}** - {status}\n"
        
        await message.reply(discover_text)
    
    else:
        # Show help
        help_text = """🔌 **Plugin Management Help**

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
    
    info_text = f"ℹ️ **Plugin Information**\n\n"
    info_text += f"**Name:** {plugin.name}\n"
    info_text += f"**Status:** {'✅ Enabled' if plugin.enabled else '❌ Disabled'}\n"
    info_text += f"**Type:** {type(plugin).__name__}\n"
    
    # Show configuration if available
    if hasattr(plugin, 'config') and plugin.config:
        info_text += f"**Configuration:** {len(plugin.config)} settings\n"
    
    # Show additional info based on plugin type
    if hasattr(plugin, 'api_key'):
        info_text += f"**API Key:** {'✅ Configured' if plugin.api_key else '❌ Missing'}\n"
    
    if hasattr(plugin, 'commands'):
        info_text += f"**Commands:** {', '.join(plugin.commands)}\n"
    
    if hasattr(plugin, 'supported_types'):
        info_text += f"**Supported Types:** {', '.join(plugin.supported_types)}\n"
    
    await message.reply(info_text)