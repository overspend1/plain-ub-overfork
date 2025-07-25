"""
Common decorators for modular functionality
"""

import functools
from typing import Any, Callable, Optional

from app import BOT, Message


def error_handler(error_message: str = "An error occurred", send_to_chat: bool = True):
    """Decorator to handle errors gracefully"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_text = f"{error_message}: {str(e)}"
                print(error_text)  # Log error
                
                # Try to send error to chat if possible
                if send_to_chat and len(args) >= 2:
                    try:
                        message = args[1]  # Assuming second arg is Message
                        if hasattr(message, 'reply'):
                            await message.reply(f"`{error_text}`")
                    except:
                        pass  # Ignore if we can't send to chat
                
                return None
        return wrapper
    return decorator


def require_config(*required_keys: str):
    """Decorator to check if required config keys are present"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need to be adapted based on how config is accessed
            # For now, just a placeholder
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def admin_only(func: Callable) -> Callable:
    """Decorator to restrict command to admins only"""
    @functools.wraps(func)
    async def wrapper(bot: BOT, message: Message, *args, **kwargs):
        # Check if user is admin (implementation depends on bot structure)
        # This is a placeholder - would need proper admin checking logic
        return await func(bot, message, *args, **kwargs)
    return wrapper


def rate_limit(max_calls: int = 5, period: int = 60):
    """Decorator to rate-limit function calls"""
    def decorator(func: Callable) -> Callable:
        calls = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import time
            now = time.time()
            
            # Get user ID (assuming it's in message)
            user_id = None
            if len(args) >= 2 and hasattr(args[1], 'from_user'):
                user_id = args[1].from_user.id
            
            if user_id:
                user_calls = calls.get(user_id, [])
                # Remove old calls outside the period
                user_calls = [call_time for call_time in user_calls if now - call_time < period]
                
                if len(user_calls) >= max_calls:
                    if hasattr(args[1], 'reply'):
                        await args[1].reply("Rate limit exceeded. Please try again later.")
                    return None
                
                user_calls.append(now)
                calls[user_id] = user_calls
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator