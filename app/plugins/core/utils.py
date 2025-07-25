"""
Utility functions for common operations
"""

import re
import time
from pathlib import Path
from typing import Optional, Union


def format_time(seconds: float) -> str:
    """Format seconds into human readable time"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{int(minutes)}m {int(secs)}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes"""
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def safe_filename(filename: str) -> str:
    """Convert filename to safe format"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple consecutive spaces/underscores
    filename = re.sub(r'[_\s]+', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Ensure it's not empty
    if not filename:
        filename = f"file_{int(time.time())}"
    
    return filename


def extract_flags(text: str) -> tuple[str, list[str]]:
    """Extract flags from command text"""
    flags = []
    # Find all flags (words starting with -)
    flag_pattern = r'-\w+'
    found_flags = re.findall(flag_pattern, text)
    flags.extend(found_flags)
    
    # Remove flags from text
    clean_text = re.sub(flag_pattern, '', text).strip()
    # Clean up multiple spaces
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    return clean_text, flags


def parse_time_string(time_str: str) -> Optional[int]:
    """Parse time string like '1h30m' into seconds"""
    if not time_str:
        return None
    
    total_seconds = 0
    
    # Match patterns like 1h, 30m, 45s
    patterns = [
        (r'(\d+)h', 3600),  # hours
        (r'(\d+)m', 60),    # minutes  
        (r'(\d+)s', 1),     # seconds
        (r'(\d+)d', 86400), # days
    ]
    
    for pattern, multiplier in patterns:
        matches = re.findall(pattern, time_str.lower())
        if matches:
            total_seconds += int(matches[0]) * multiplier
    
    return total_seconds if total_seconds > 0 else None


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def is_url(text: str) -> bool:
    """Check if text is a valid URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(text) is not None