"""
Utility functions and classes for the Telegram Image AI Bot
"""

import logging
import time
from typing import Dict, Optional, Tuple
from collections import defaultdict
from config import Config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation for API usage control"""
    
    def __init__(self):
        self.user_requests: Dict[int, list] = defaultdict(list)
        self.max_requests = Config.MAX_REQUESTS_PER_USER
        self.window_size = Config.RATE_LIMIT_WINDOW
    
    def check_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded rate limit"""
        current_time = time.time()
        
        # Clean old requests outside the window
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < self.window_size
        ]
        
        # Check if user has exceeded limit
        if len(self.user_requests[user_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        return True
    
    def get_remaining_requests(self, user_id: int) -> int:
        """Get remaining requests for user"""
        current_time = time.time()
        
        # Clean old requests
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < self.window_size
        ]
        
        return max(0, self.max_requests - len(self.user_requests[user_id]))
    
    def get_reset_time(self, user_id: int) -> Optional[float]:
        """Get time when rate limit resets for user"""
        if not self.user_requests[user_id]:
            return None
        
        oldest_request = min(self.user_requests[user_id])
        return oldest_request + self.window_size

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def get_file_info(file_size: int, mime_type: str = None) -> Dict[str, str]:
    """Get formatted file information"""
    info = {
        "size": format_file_size(file_size),
        "size_bytes": str(file_size)
    }
    
    if mime_type:
        info["type"] = mime_type
        info["format"] = mime_type.split('/')[-1].upper()
    
    return info

def validate_image_format(mime_type: str) -> bool:
    """Validate if the image format is supported"""
    return mime_type in Config.SUPPORTED_FORMATS

def get_image_dimensions_from_quality(quality: str) -> Tuple[int, int]:
    """Get image dimensions for quality setting"""
    if quality in Config.QUALITY_OPTIONS:
        quality_info = Config.QUALITY_OPTIONS[quality]
        return quality_info['width'], quality_info['height']
    return 1920, 1080  # Default to Full HD

def calculate_processing_time_estimate(file_size: int, operation: str) -> int:
    """Estimate processing time in seconds based on file size and operation"""
    base_times = {
        "remove_bg": 5,      # Remove background: 5-15 seconds
        "ai_edit": 8,        # AI editing: 8-20 seconds
        "enhance_quality": 3, # Quality enhancement: 3-10 seconds
        "wallpaper": 2       # Wallpaper conversion: 2-8 seconds
    }
    
    base_time = base_times.get(operation, 5)
    
    # Adjust based on file size (rough estimation)
    size_mb = file_size / (1024 * 1024)
    if size_mb > 10:
        base_time *= 2
    elif size_mb > 5:
        base_time *= 1.5
    
    return min(base_time, 30)  # Cap at 30 seconds

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    # Ensure it's not empty
    if not sanitized:
        sanitized = "image"
    return sanitized

def create_progress_message(operation: str, progress: int = 0) -> str:
    """Create progress message for long-running operations"""
    operations = {
        "remove_bg": "🎯 Removing background",
        "ai_edit": "🎨 AI processing",
        "enhance_quality": "⬆️ Enhancing quality",
        "wallpaper": "🖼️ Converting to wallpaper",
        "download": "⬇️ Downloading image",
        "upload": "⬆️ Uploading result"
    }
    
    operation_text = operations.get(operation, f"Processing {operation}")
    
    if progress > 0:
        progress_bar = "▓" * (progress // 10) + "░" * (10 - progress // 10)
        return f"{operation_text}...\n[{progress_bar}] {progress}%"
    else:
        return f"{operation_text}...\nThis may take a few moments."

class ImageCache:
    """Simple in-memory cache for processed images"""
    
    def __init__(self, max_size: int = 50):
        self.cache: Dict[str, Tuple[bytes, float]] = {}
        self.max_size = max_size
    
    def _generate_key(self, file_id: str, operation: str, params: str = "") -> str:
        """Generate cache key"""
        return f"{file_id}_{operation}_{params}"
    
    def get(self, file_id: str, operation: str, params: str = "") -> Optional[bytes]:
        """Get cached result"""
        key = self._generate_key(file_id, operation, params)
        if key in self.cache:
            data, timestamp = self.cache[key]
            # Cache expires after 1 hour
            if time.time() - timestamp < 3600:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, file_id: str, operation: str, data: bytes, params: str = "") -> None:
        """Set cached result"""
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        key = self._generate_key(file_id, operation, params)
        self.cache[key] = (data, time.time())
    
    def clear(self) -> None:
        """Clear all cached data"""
        self.cache.clear()

# Global cache instance
image_cache = ImageCache()

def log_user_action(user_id: int, action: str, details: str = "") -> None:
    """Log user actions for monitoring and debugging"""
    logger.info(f"User {user_id} action: {action} {details}")

def format_processing_stats(processing_time: float, file_size: int, operation: str) -> str:
    """Format processing statistics for user feedback"""
    return (
        f"✅ Processing completed in {processing_time:.1f}s\n"
        f"📁 File size: {format_file_size(file_size)}\n"
        f"🔧 Operation: {operation}"
    )
