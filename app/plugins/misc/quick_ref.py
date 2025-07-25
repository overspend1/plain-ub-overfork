"""
Quick reference commands for commonly used features
"""

from app import BOT, Message, bot
from app.plugins.core.decorators import error_handler


@bot.add_cmd(cmd="quickhelp")
@error_handler("Quick help command failed")
async def quick_help(bot: BOT, message: Message):
 """
 CMD: QUICKHELP
 INFO: Quick reference for most commonly used commands
 USAGE: .quickhelp
 """
 
 quick_ref = """ **Quick Reference**

**🔥 Most Used:**
• `.alive` - Check if bot is working
• `.ping` - Check response time
• `.help` - Full help system
• `.plugins` - Manage plugins

** AI Commands:**
• `.ai <question>` - Ask AI anything
• `.ai -i <prompt>` - Generate image
• `.aistatus` - Check AI status

** Files:**
• `.upload` (reply to file) - Upload to cloud
• `.download <url>` - Download from URL
• `.leech <url>` - Download and send

** Admin:**
• `.ban` (reply) - Ban user
• `.kick` (reply) - Kick user
• `.mute` (reply) - Mute user

** Telegram:**
• `.kang` (reply to sticker) - Steal sticker
• `.delete <count>` - Delete messages
• `.chat info` - Get chat info

** System:**
• `.neofetch` - System info
• `.speedtest` - Internet speed
• `.shell <cmd>` - Run command

** Management:**
• `.listmodules` - List all modules
• `.autohelp` - Auto-generated help
• `.searchcmd <name>` - Search commands

**Need more help?**
• `.help` - Full help system
• `.help <module>` - Module-specific help
• `.autohelp <plugin>` - Plugin details
"""
 
 await message.reply(quick_ref)


@bot.add_cmd(cmd="basics")
@error_handler("Basics command failed")
async def show_basics(bot: BOT, message: Message):
 """
 CMD: BASICS
 INFO: Show basic setup and getting started information
 USAGE: .basics
 """
 
 basics_text = """📚 **Getting Started with PLAIN-UB**

**🔐 Setup:**
1. Set your environment variables in config
2. Add `GEMINI_API_KEY` for AI features
3. Set `OWNER_ID` to your user ID
4. Configure `LOG_CHAT` for logging

** First Steps:**
• `.alive` - Verify bot is working
• `.help` - Explore all commands
• `.plugins discover` - See available plugins
• `.aistatus` - Check if AI is configured

**📖 Command Structure:**
• Commands start with your trigger (default: `.`)
• Use `.help <module>` for detailed help
• Many commands work by replying to messages
• Use flags like `-i`, `-s`, `-a` for options

** Configuration Files:**
• `sample-config.env` - Main configuration
• Copy to `.env` and fill your details
• Restart bot after config changes

**🆘 Getting Help:**
• `.quickhelp` - This reference
• `.help` - Full help system 
• `.autohelp` - Auto-generated help
• `.searchcmd <name>` - Find specific commands
• `.cmdinfo <name>` - Detailed command info

** Plugin System:**
• `.plugins` - Manage plugins
• `.listmodules` - See all available modules
• Plugins auto-load from `app/plugins/`

** AI Features (requires API key):**
• Text: `.ai What is Python?`
• Images: `.ai -i A beautiful sunset`
• Audio: `.ai -a Tell me a joke`
• Interactive: `.aic Hello there`

** File Management:**
• Upload: Reply to file with `.upload`
• Download: `.download <url>`
• Cloud services: `.catbox`, `.gofile`, etc.

Ready to explore? Try `.help` for the full command list!
"""
 
 await message.reply(basics_text)


@bot.add_cmd(cmd="examples")
@error_handler("Examples command failed")
async def show_examples(bot: BOT, message: Message):
 """
 CMD: EXAMPLES
 INFO: Show practical usage examples for common tasks
 USAGE: .examples [category]
 """
 
 category = message.input.strip().lower() if message.input else None
 
 examples = {
 "ai": """ **AI Usage Examples**

**Basic Questions:**
• `.ai What is Python programming?`
• `.ai Explain quantum computing`
• `.ai Write a haiku about coding`

**With Search:**
• `.ai -s Latest news about AI`
• `.ai -s Weather in New York`

**Image Generation:**
• `.ai -i A futuristic city at sunset`
• `.ai -i Cute cat wearing sunglasses`
• `.ai -i Abstract art with blue and gold`

**Audio Generation:**
• `.ai -a Tell me a funny joke`
• `.ai -a -m Read this text (male voice)`
• `.ai -a Sing happy birthday`

**Interactive Chat:**
• `.aic Hello, let's have a conversation`
• Then just reply to AI's messages
• Chat times out after 5 minutes of inactivity
""",
 
 "admin": """ **Admin Examples**

**Banning Users:**
• `.ban` (reply to user) - Permanent ban
• `.ban @username Spam` - Ban with reason
• `.ban 5 minutes` (reply) - Temporary ban

**Kicking & Muting:**
• `.kick` (reply to user)
• `.mute 30 minutes` (reply to user)
• `.mute @username 1 hour Disrupting chat`

**Promotions:**
• `.promote` (reply to user) - Make admin
• `.demote` (reply to admin) - Remove admin

**Group Cleanup:**
• `.zombies` - Remove deleted accounts
• `.delete 10` - Delete last 10 messages
""",
 
 "files": """ **File Management Examples**

**Uploading:**
• Reply to any file with `.upload`
• `.catbox` (reply to file) - Upload to catbox.moe
• `.gofile` (reply to file) - Upload to gofile.io

**Downloading:**
• `.download https://example.com/file.zip`
• `.leech https://example.com/video.mp4`

**File Operations:**
• `.rename newname.txt` (reply to file)
• `.spoiler` (reply to file) - Send as spoiler

**Torrents:**
• `.torrent https://example.com/file.torrent`
• `.torrent magnet:?xt=urn:btih:...`
""",
 
 "system": """ **System Examples**

**Information:**
• `.neofetch` - Stylish system info
• `.sysinfo` - Detailed system info
• `.speedtest` - Internet speed test

**Shell Commands:**
• `.shell ls -la` - List files
• `.shell df -h` - Check disk space
• `.shell top` - Show running processes

**Plugin Management:**
• `.plugins discover` - See all available
• `.plugins load ai` - Load AI plugin
• `.plugins status` - Check plugin status
"""
 }
 
 if category and category in examples:
 await message.reply(examples[category])
 elif category:
 available = ", ".join(f"`{cat}`" for cat in examples.keys())
 await message.reply(f"Category `{category}` not found.\n\nAvailable: {available}")
 else:
 # Show all categories
 categories_text = """ **Usage Examples**

**Available Categories:**
• `.examples ai` - AI command examples
• `.examples admin` - Admin command examples 
• `.examples files` - File management examples
• `.examples system` - System command examples

**Quick Examples:**
• `.ai What is Python?` - Ask AI
• `.ban` (reply) - Ban user
• `.upload` (reply to file) - Upload file
• `.neofetch` - Show system info

Choose a category above for detailed examples!
"""
 await message.reply(categories_text)