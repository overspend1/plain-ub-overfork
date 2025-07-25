"""
Simple Gemini AI commands using modular structure
"""

from app import BOT, Message, bot
from app.plugins.core.decorators import error_handler
from app.plugins.core.utils import extract_flags, truncate_text
from .modular import gemini_ai


@bot.add_cmd(cmd="ai")
@error_handler("AI command failed")
async def simple_ai_query(bot: BOT, message: Message):
    """
    CMD: AI
    INFO: Simple AI query using Gemini
    USAGE: .ai <your question>
    FLAGS:
        -i: Generate image instead of text
        -s: Use search functionality
        -a: Generate audio response
    """
    
    if not message.input:
        await message.reply("Please provide a question for AI")
        return
    
    # Initialize AI if not already done
    if not await gemini_ai.is_available():
        if not await gemini_ai.initialize():
            await message.reply("Gemini AI is not available. Please check API key configuration.")
            return
    
    # Extract flags from message
    query, flags = extract_flags(message.input)
    
    if not query:
        await message.reply("Please provide a question for AI")
        return
    
    # Show processing message
    processing_msg = await message.reply("🤖 Processing your request...")
    
    try:
        # Handle different request types based on flags
        if "-i" in flags:
            # Image generation
            image_data = await gemini_ai.generate_image(query)
            if image_data:
                import io
                image_file = io.BytesIO(image_data)
                image_file.name = "ai_generated.png"
                await processing_msg.delete()
                await message.reply_photo(
                    photo=image_file,
                    caption=f"Generated image for: {truncate_text(query, 50)}"
                )
            else:
                await processing_msg.edit("Failed to generate image")
                
        elif "-a" in flags:
            # Audio generation
            voice_type = "male" if "-m" in flags else "female"
            audio_data = await gemini_ai.generate_audio(query, voice_type)
            if audio_data:
                import io
                from .client import Response
                
                # Convert to proper audio format
                audio_file = Response.save_wave_file(audio_data)
                await processing_msg.delete()
                await message.reply_voice(
                    voice=audio_file,
                    caption=f"Audio response for: {truncate_text(query, 50)}",
                    duration=getattr(audio_file, 'duration', 0),
                    waveform=getattr(audio_file, 'waveform', None)
                )
            else:
                await processing_msg.edit("Failed to generate audio")
                
        else:
            # Text response
            response = await gemini_ai.generate_response(query, flags=flags)
            if response:
                # Format response nicely
                formatted_response = f"🤖 **AI Response:**\n\n{response}"
                
                # Split long responses if needed
                if len(formatted_response) > 4000:
                    parts = [formatted_response[i:i+4000] for i in range(0, len(formatted_response), 4000)]
                    await processing_msg.delete()
                    for i, part in enumerate(parts):
                        if i == 0:
                            await message.reply(part)
                        else:
                            await message.reply(f"**Continued...**\n\n{part}")
                else:
                    await processing_msg.edit(formatted_response)
            else:
                await processing_msg.edit("Failed to generate response")
                
    except Exception as e:
        await processing_msg.edit(f"Error: {str(e)}")


@bot.add_cmd(cmd="aistatus")
async def ai_status(bot: BOT, message: Message):
    """
    CMD: AISTATUS  
    INFO: Check AI module status
    USAGE: .aistatus
    """
    
    status_text = "🤖 **AI Module Status**\n\n"
    
    # Check Gemini availability
    is_available = await gemini_ai.is_available()
    status_text += f"**Gemini AI:** {'✅ Available' if is_available else '❌ Not Available'}\n"
    
    if is_available:
        status_text += f"**API Key:** {'✅ Configured' if gemini_ai.api_key else '❌ Missing'}\n"
        status_text += f"**Client:** {'✅ Connected' if gemini_ai.async_client else '❌ Not Connected'}\n"
    else:
        status_text += "**Issue:** API key missing or client not initialized\n"
        status_text += "**Solution:** Set GEMINI_API_KEY in your environment\n"
    
    await message.reply(status_text)


@bot.add_cmd(cmd="aihelp")  
async def ai_help(bot: BOT, message: Message):
    """
    CMD: AIHELP
    INFO: Show AI commands help
    USAGE: .aihelp
    """
    
    help_text = """🤖 **AI Commands Help**

**Basic Usage:**
• `.ai <question>` - Ask AI anything
• `.aistatus` - Check AI module status  
• `.aihelp` - Show this help

**Flags:**
• `-s` - Use search functionality
• `-i` - Generate image instead of text
• `-a` - Generate audio response  
• `-m` - Use male voice (with -a)

**Examples:**
• `.ai What is Python?`
• `.ai -s Latest news about AI`
• `.ai -i A beautiful sunset over mountains`
• `.ai -a -m Tell me a joke`

**Advanced:**
• `.aic` - Interactive chat mode
• `.lh` - Load chat history
"""
    
    await message.reply(help_text)