"""
Image processing utilities for quality enhancement and format conversion
"""

import logging
import io
import asyncio
from typing import Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handle image processing operations"""
    
    def __init__(self):
        self.max_processing_size = (4096, 4096)  # Maximum size for processing
    
    async def enhance_quality(self, image_bytes: bytes, target_width: int, target_height: int) -> Optional[bytes]:
        """Enhance image quality and resize to target dimensions"""
        try:
            # Run in thread pool to avoid blocking
            return await asyncio.get_event_loop().run_in_executor(
                None, 
                self._enhance_quality_sync, 
                image_bytes, 
                target_width, 
                target_height
            )
        except Exception as e:
            logger.error(f"Error in enhance_quality: {e}")
            return None
    
    def _enhance_quality_sync(self, image_bytes: bytes, target_width: int, target_height: int) -> Optional[bytes]:
        """Synchronous quality enhancement"""
        try:
            # Open image
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Handle transparency
                    if img.mode == 'RGBA':
                        # Create white background
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                        img = background
                    else:
                        img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get original dimensions
                orig_width, orig_height = img.size
                logger.info(f"Original size: {orig_width}x{orig_height}")
                
                # Calculate aspect ratio preserving dimensions
                target_ratio = target_width / target_height
                orig_ratio = orig_width / orig_height
                
                if orig_ratio > target_ratio:
                    # Image is wider - fit to width
                    new_width = target_width
                    new_height = int(target_width / orig_ratio)
                else:
                    # Image is taller - fit to height
                    new_height = target_height
                    new_width = int(target_height * orig_ratio)
                
                # Use high-quality resampling
                if new_width > orig_width or new_height > orig_height:
                    # Upscaling - use Lanczos for better quality
                    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    # Downscaling - use Lanczos as well
                    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Apply enhancement filters
                img_enhanced = self._apply_enhancement_filters(img_resized)
                
                # If we need exact target dimensions, pad with black or crop
                if new_width != target_width or new_height != target_height:
                    img_final = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                    # Center the image
                    paste_x = (target_width - new_width) // 2
                    paste_y = (target_height - new_height) // 2
                    img_final.paste(img_enhanced, (paste_x, paste_y))
                    img_enhanced = img_final
                
                # Save to bytes
                output = io.BytesIO()
                img_enhanced.save(output, format='PNG', optimize=True, quality=95)
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Error in _enhance_quality_sync: {e}")
            return None
    
    def _apply_enhancement_filters(self, img: Image.Image) -> Image.Image:
        """Apply enhancement filters to improve image quality"""
        try:
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.2)  # Increase sharpness by 20%
            
            # Enhance contrast slightly
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)  # Increase contrast by 10%
            
            # Enhance color saturation slightly
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.05)  # Increase saturation by 5%
            
            return img
            
        except Exception as e:
            logger.error(f"Error applying enhancement filters: {e}")
            return img
    
    async def convert_to_wallpaper(self, image_bytes: bytes) -> Optional[bytes]:
        """Convert image to wallpaper format (16:9 aspect ratio, high quality)"""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, 
                self._convert_to_wallpaper_sync, 
                image_bytes
            )
        except Exception as e:
            logger.error(f"Error in convert_to_wallpaper: {e}")
            return None
    
    def _convert_to_wallpaper_sync(self, image_bytes: bytes) -> Optional[bytes]:
        """Synchronous wallpaper conversion"""
        try:
            # Common wallpaper sizes (16:9 aspect ratio)
            wallpaper_sizes = [
                (1920, 1080),  # Full HD
                (2560, 1440),  # QHD
                (3840, 2160),  # 4K UHD
            ]
            
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    if img.mode in ('RGBA', 'LA', 'P'):
                        if img.mode == 'RGBA':
                            background = Image.new('RGB', img.size, (0, 0, 0))  # Black background for wallpapers
                            background.paste(img, mask=img.split()[-1])
                            img = background
                        else:
                            img = img.convert('RGB')
                    else:
                        img = img.convert('RGB')
                
                # Choose target size based on original image size
                orig_width, orig_height = img.size
                orig_pixels = orig_width * orig_height
                
                # Select appropriate wallpaper size
                target_width, target_height = wallpaper_sizes[0]  # Default to Full HD
                for size in wallpaper_sizes:
                    if orig_pixels >= (size[0] * size[1] * 0.5):  # If original has at least 50% of target pixels
                        target_width, target_height = size
                
                logger.info(f"Converting to wallpaper size: {target_width}x{target_height}")
                
                # Calculate scaling to fill the target while maintaining aspect ratio
                scale_x = target_width / orig_width
                scale_y = target_height / orig_height
                scale = max(scale_x, scale_y)  # Scale to fill
                
                # Calculate new dimensions
                new_width = int(orig_width * scale)
                new_height = int(orig_height * scale)
                
                # Resize image
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create final wallpaper canvas
                wallpaper = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                
                # Center and crop if necessary
                paste_x = (target_width - new_width) // 2
                paste_y = (target_height - new_height) // 2
                
                if new_width > target_width or new_height > target_height:
                    # Need to crop
                    crop_x = max(0, -paste_x)
                    crop_y = max(0, -paste_y)
                    crop_width = min(new_width, target_width)
                    crop_height = min(new_height, target_height)
                    
                    img_resized = img_resized.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
                    paste_x = max(0, paste_x)
                    paste_y = max(0, paste_y)
                
                wallpaper.paste(img_resized, (paste_x, paste_y))
                
                # Apply wallpaper-specific enhancements
                wallpaper = self._apply_wallpaper_enhancements(wallpaper)
                
                # Save to bytes
                output = io.BytesIO()
                wallpaper.save(output, format='PNG', optimize=True, quality=95)
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Error in _convert_to_wallpaper_sync: {e}")
            return None
    
    def _apply_wallpaper_enhancements(self, img: Image.Image) -> Image.Image:
        """Apply enhancements specific to wallpapers"""
        try:
            # Slightly enhance contrast for better visual impact
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.15)
            
            # Enhance color saturation for more vivid colors
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)
            
            # Slight sharpening
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)
            
            return img
            
        except Exception as e:
            logger.error(f"Error applying wallpaper enhancements: {e}")
            return img
    
    async def optimize_image(self, image_bytes: bytes, max_size: Tuple[int, int] = None) -> Optional[bytes]:
        """Optimize image for faster processing"""
        try:
            if max_size is None:
                max_size = self.max_processing_size
                
            return await asyncio.get_event_loop().run_in_executor(
                None, 
                self._optimize_image_sync, 
                image_bytes, 
                max_size
            )
        except Exception as e:
            logger.error(f"Error in optimize_image: {e}")
            return None
    
    def _optimize_image_sync(self, image_bytes: bytes, max_size: Tuple[int, int]) -> Optional[bytes]:
        """Synchronous image optimization"""
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Check if resizing is needed
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save optimized
                output = io.BytesIO()
                img.save(output, format='JPEG', optimize=True, quality=85)
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Error in _optimize_image_sync: {e}")
            return None
