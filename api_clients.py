"""
API clients for external image processing services
"""

import logging
import aiohttp
import asyncio
from typing import Optional
import io
from config import Config

logger = logging.getLogger(__name__)

class APIClient:
    """Base class for API clients"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()

class PhotoRoomClient(APIClient):
    """Client for PhotoRoom API"""
    
    def __init__(self):
        super().__init__(Config.PHOTOROOM_API_URL, Config.PHOTOROOM_API_KEY)
    
    async def enhance_image(self, image_bytes: bytes) -> Optional[bytes]:
        """Enhance image using PhotoRoom API"""
        if not self.api_key:
            logger.warning("PhotoRoom API key not configured")
            return None
        
        try:
            session = await self._get_session()
            
            # Prepare form data for PhotoRoom v2 API
            data = aiohttp.FormData()
            data.add_field('imageFile', 
                          io.BytesIO(image_bytes), 
                          filename='image.jpg',
                          content_type='image/jpeg')
            data.add_field('referenceBox', 'originalImage')
            
            headers = {
                'x-api-key': self.api_key
            }
            
            # Use the correct v2 edit endpoint
            url = f"{self.base_url}/v2/edit"
            
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    result_bytes = await response.read()
                    logger.info("PhotoRoom image enhancement successful")
                    return result_bytes
                else:
                    error_text = await response.text()
                    logger.error(f"PhotoRoom API error {response.status}: {error_text}")
                    return None
        
        except asyncio.TimeoutError:
            logger.error("PhotoRoom API request timed out")
            return None
        except Exception as e:
            logger.error(f"PhotoRoom API error: {e}")
            return None
    
    async def remove_background(self, image_bytes: bytes) -> Optional[bytes]:
        """Remove background using PhotoRoom API"""
        return await self.enhance_image(image_bytes)  # Same endpoint for now
    
    async def apply_effects(self, image_bytes: bytes, effect: str = "enhance") -> Optional[bytes]:
        """Apply effects using PhotoRoom API"""
        if not self.api_key:
            logger.warning("PhotoRoom API key not configured")
            return None
        
        try:
            session = await self._get_session()
            
            data = aiohttp.FormData()
            data.add_field('image_file', 
                          io.BytesIO(image_bytes), 
                          filename='image.jpg',
                          content_type='image/jpeg')
            data.add_field('effect', effect)
            
            headers = {
                'X-Api-Key': self.api_key
            }
            
            url = f"{self.base_url}/effects"
            
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    result_bytes = await response.read()
                    logger.info(f"PhotoRoom effect '{effect}' applied successfully")
                    return result_bytes
                else:
                    error_text = await response.text()
                    logger.error(f"PhotoRoom effects API error {response.status}: {error_text}")
                    return None
        
        except Exception as e:
            logger.error(f"PhotoRoom effects API error: {e}")
            return None

class RemoveBGClient(APIClient):
    """Client for Remove.bg API"""
    
    def __init__(self):
        super().__init__(Config.REMOVEBG_API_URL, Config.REMOVEBG_API_KEY)
    
    async def remove_background(self, image_bytes: bytes, size: str = "auto") -> Optional[bytes]:
        """Remove background using Remove.bg API"""
        if not self.api_key:
            logger.warning("Remove.bg API key not configured")
            return None
        
        try:
            session = await self._get_session()
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('image_file', 
                          io.BytesIO(image_bytes), 
                          filename='image.jpg',
                          content_type='image/jpeg')
            data.add_field('size', size)
            
            headers = {
                'X-Api-Key': self.api_key
            }
            
            url = f"{self.base_url}/removebg"
            
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    result_bytes = await response.read()
                    logger.info("Remove.bg background removal successful")
                    return result_bytes
                else:
                    error_text = await response.text()
                    logger.error(f"Remove.bg API error {response.status}: {error_text}")
                    
                    # Handle specific error cases
                    if response.status == 402:
                        logger.error("Remove.bg API: Insufficient credits")
                    elif response.status == 403:
                        logger.error("Remove.bg API: Invalid API key")
                    elif response.status == 429:
                        logger.error("Remove.bg API: Rate limit exceeded")
                    
                    return None
        
        except asyncio.TimeoutError:
            logger.error("Remove.bg API request timed out")
            return None
        except Exception as e:
            logger.error(f"Remove.bg API error: {e}")
            return None
    
    async def remove_background_url(self, image_url: str, size: str = "auto") -> Optional[bytes]:
        """Remove background from image URL using Remove.bg API"""
        if not self.api_key:
            logger.warning("Remove.bg API key not configured")
            return None
        
        try:
            session = await self._get_session()
            
            data = aiohttp.FormData()
            data.add_field('image_url', image_url)
            data.add_field('size', size)
            
            headers = {
                'X-Api-Key': self.api_key
            }
            
            url = f"{self.base_url}/removebg"
            
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    result_bytes = await response.read()
                    logger.info("Remove.bg URL background removal successful")
                    return result_bytes
                else:
                    error_text = await response.text()
                    logger.error(f"Remove.bg URL API error {response.status}: {error_text}")
                    return None
        
        except Exception as e:
            logger.error(f"Remove.bg URL API error: {e}")
            return None

# Custom upscaling client (placeholder for future integration)
class UpscaleClient:
    """Client for image upscaling services"""
    
    def __init__(self):
        self.available = False  # Set to True when upscaling service is configured
    
    async def upscale_image(self, image_bytes: bytes, scale_factor: int = 2) -> Optional[bytes]:
        """Upscale image using AI upscaling service"""
        if not self.available:
            logger.warning("Upscaling service not configured")
            return None
        
        # Placeholder for future implementation
        # Could integrate with services like:
        # - Real-ESRGAN API
        # - Waifu2x API
        # - Adobe API
        # - Custom AI upscaling service
        
        logger.info(f"Upscaling image with factor {scale_factor}")
        return None
