"""
Modular Gemini AI implementation
"""

from typing import Optional

from app import extra_config
from app.plugins.core.base import BaseAI
from app.plugins.core.decorators import error_handler
from .client import async_client, client
from .config import AIConfig


class GeminiAI(BaseAI):
    """Modular Gemini AI implementation"""
    
    def __init__(self):
        super().__init__("Gemini", extra_config.GEMINI_API_KEY)
        self.async_client = async_client
        self.sync_client = client
    
    async def initialize(self) -> bool:
        """Initialize Gemini AI module"""
        try:
            if not self.api_key:
                print("Gemini API key not found in config")
                return False
            
            if not await self.is_available():
                print("Gemini API is not available")
                return False
            
            print("Gemini AI module initialized successfully")
            return True
            
        except Exception as e:
            await self.handle_error(e, "initialization")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup Gemini resources"""
        # Close any open connections if needed
        pass
    
    @error_handler("Failed to generate Gemini response")
    async def generate_response(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate response using Gemini AI"""
        if not await self.is_available():
            return "Gemini AI is not available"
        
        try:
            # Get configuration based on flags
            flags = kwargs.get('flags', [])
            ai_kwargs = AIConfig.get_kwargs(flags)
            
            # Create chat session
            chat = self.async_client.chats.create(**ai_kwargs)
            
            # Send message and get response
            response = await chat.send_message(prompt)
            
            # Extract text from response
            if hasattr(response, 'text') and response.text:
                return response.text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        return candidate.content.parts[0].text
            
            return "No response generated"
            
        except Exception as e:
            await self.handle_error(e, "response generation")
            return f"Error generating response: {str(e)}"
    
    async def is_available(self) -> bool:
        """Check if Gemini AI is available"""
        return (
            self.api_key is not None and 
            self.async_client is not None and 
            self.sync_client is not None
        )
    
    @error_handler("Failed to generate image")
    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """Generate image using Gemini AI"""
        if not await self.is_available():
            return None
        
        try:
            # Use image generation configuration
            chat = self.async_client.chats.create(
                model=AIConfig.IMAGE_MODEL,
                config=AIConfig.IMAGE_CONFIG
            )
            
            response = await chat.send_message(prompt)
            
            # Extract image data if available
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            return part.inline_data.data
            
            return None
            
        except Exception as e:
            await self.handle_error(e, "image generation")
            return None
    
    @error_handler("Failed to generate audio")
    async def generate_audio(self, prompt: str, voice_config: str = "female") -> Optional[bytes]:
        """Generate audio using Gemini AI"""
        if not await self.is_available():
            return None
        
        try:
            # Set up audio configuration
            config = AIConfig.AUDIO_CONFIG.copy() if hasattr(AIConfig.AUDIO_CONFIG, 'copy') else AIConfig.AUDIO_CONFIG
            
            # Adjust voice based on parameter
            if voice_config == "male":
                from .config import MALE_SPEECH_CONFIG
                config.speech_config = MALE_SPEECH_CONFIG
            else:
                from .config import FEMALE_SPEECH_CONFIG  
                config.speech_config = FEMALE_SPEECH_CONFIG
            
            chat = self.async_client.chats.create(
                model=AIConfig.AUDIO_MODEL,
                config=config
            )
            
            response = await chat.send_message(prompt)
            
            # Extract audio data if available
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            if "audio" in part.inline_data.mime_type:
                                return part.inline_data.data
            
            return None
            
        except Exception as e:
            await self.handle_error(e, "audio generation")
            return None


# Global instance
gemini_ai = GeminiAI()