"""
Configuration management for the Telegram Image AI Bot
"""

import os
from typing import Optional

class Config:
    """Configuration class for bot settings and API keys"""
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    BOT_USERNAME: str = os.getenv('BOT_USERNAME', 'ImageAIBot')
    
    # API Keys
    PHOTOROOM_API_KEY: str = os.getenv('PHOTOROOM_API_KEY', '')
    REMOVEBG_API_KEY: str = os.getenv('REMOVEBG_API_KEY', '')
    
    # Rate Limiting
    MAX_REQUESTS_PER_USER: int = int(os.getenv('MAX_REQUESTS_PER_USER', '10'))
    RATE_LIMIT_WINDOW: int = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # 1 hour in seconds
    
    # Image Processing Settings
    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', '20971520'))  # 20MB default
    SUPPORTED_FORMATS: list = ['image/jpeg', 'image/png', 'image/webp']
    
    # Quality Enhancement Settings
    QUALITY_OPTIONS = {
        'HD': {'width': 1280, 'height': 720, 'label': 'HD (720p)'},
        '1080p': {'width': 1920, 'height': 1080, 'label': 'Full HD (1080p)'},
        '4K': {'width': 3840, 'height': 2160, 'label': '4K UHD'},
        '8K': {'width': 7680, 'height': 4320, 'label': '8K UHD'}
    }
    
    # API Endpoints
    PHOTOROOM_API_URL: str = 'https://image-api.photoroom.com'
    REMOVEBG_API_URL: str = 'https://api.remove.bg/v1.0'
    
    # Webhook Configuration
    WEBHOOK_URL: Optional[str] = os.getenv('WEBHOOK_URL')
    WEBHOOK_SECRET: Optional[str] = os.getenv('WEBHOOK_SECRET')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_vars = [
            ('TELEGRAM_BOT_TOKEN', cls.TELEGRAM_BOT_TOKEN),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        # Check if at least one API key is provided
        if not cls.PHOTOROOM_API_KEY and not cls.REMOVEBG_API_KEY:
            print("Warning: No API keys provided. Some features will not be available.")
        
        return True
    
    @classmethod
    def get_quality_options_keyboard(cls) -> list:
        """Get quality options formatted for inline keyboard"""
        options = []
        for key, value in cls.QUALITY_OPTIONS.items():
            options.append({
                'text': value['label'],
                'callback_data': f'quality_{key}'
            })
        return options
