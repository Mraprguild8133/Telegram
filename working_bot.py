#!/usr/bin/env python3
"""
Working Telegram Bot with AI-powered image editing capabilities
Uses direct API calls to avoid import conflicts
"""

import os
import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any
import io
import time
from threading import Thread

from flask import Flask, request, jsonify, render_template

from image_processor import ImageProcessor
from api_clients import PhotoRoomClient, RemoveBGClient
from config import Config
from utils import RateLimiter, get_file_info, format_file_size

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBotAPI:
    """Direct Telegram Bot API client to avoid library conflicts"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def send_message(self, chat_id: int, text: str, reply_markup=None, parse_mode="Markdown"):
        """Send a text message"""
        await self._ensure_session()
        
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        async with self.session.post(f"{self.base_url}/sendMessage", data=data) as response:
            return await response.json()
    
    async def send_document(self, chat_id: int, document_bytes: bytes, filename: str, caption: str = ""):
        """Send a document"""
        await self._ensure_session()
        
        data = aiohttp.FormData()
        data.add_field('chat_id', str(chat_id))
        data.add_field('caption', caption)
        data.add_field('document', document_bytes, filename=filename)
        
        async with self.session.post(f"{self.base_url}/sendDocument", data=data) as response:
            return await response.json()
    
    async def get_file(self, file_id: str):
        """Get file information"""
        await self._ensure_session()
        
        async with self.session.get(f"{self.base_url}/getFile?file_id={file_id}") as response:
            return await response.json()
    
    async def download_file(self, file_path: str):
        """Download file content"""
        await self._ensure_session()
        
        download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
        async with self.session.get(download_url) as response:
            return await response.read()
    
    async def edit_message_text(self, chat_id: int, message_id: int, text: str, reply_markup=None, parse_mode="Markdown"):
        """Edit message text"""
        await self._ensure_session()
        
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        async with self.session.post(f"{self.base_url}/editMessageText", data=data) as response:
            return await response.json()
    
    async def answer_callback_query(self, callback_query_id: str, text: str = ""):
        """Answer callback query"""
        await self._ensure_session()
        
        data = {
            'callback_query_id': callback_query_id,
            'text': text
        }
        
        async with self.session.post(f"{self.base_url}/answerCallbackQuery", data=data) as response:
            return await response.json()

class WorkingTelegramBot:
    """Main Telegram bot class using direct API calls"""
    
    def __init__(self):
        self.bot_api = TelegramBotAPI(Config.TELEGRAM_BOT_TOKEN)
        self.image_processor = ImageProcessor()
        self.photoroom_client = PhotoRoomClient() if Config.PHOTOROOM_API_KEY else None
        self.removebg_client = RemoveBGClient() if Config.REMOVEBG_API_KEY else None
        self.rate_limiter = RateLimiter()
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        
    def _create_image_options_keyboard(self):
        """Create inline keyboard with image processing options"""
        keyboard = []
        
        # Background removal
        if self.removebg_client:
            keyboard.append([{"text": "🎯 Remove Background", "callback_data": "remove_bg"}])
        
        # AI editing
        if self.photoroom_client:
            keyboard.append([{"text": "🎨 AI Image Editing", "callback_data": "ai_edit"}])
        
        # Quality enhancement
        keyboard.append([{"text": "⬆️ Enhance Quality", "callback_data": "enhance_quality"}])
        
        # Wallpaper conversion
        keyboard.append([{"text": "🖼️ Convert to Wallpaper", "callback_data": "wallpaper"}])
        
        return {"inline_keyboard": keyboard}
    
    def _create_quality_keyboard(self):
        """Create keyboard for quality selection"""
        keyboard = []
        for key, value in Config.QUALITY_OPTIONS.items():
            keyboard.append([{"text": value['label'], "callback_data": f"quality_{key}"}])
        
        keyboard.append([{"text": "⬅️ Back to Options", "callback_data": "back_to_options"}])
        return {"inline_keyboard": keyboard}
    
    async def handle_start_command(self, chat_id: int, user_name: str):
        """Handle /start command"""
        welcome_message = f"""
🎨 *Welcome to AI Image Editor Bot, {user_name}!*

I can help you with:
• 🖼️ AI-powered image editing
• 🎯 Background removal
• ⬆️ Image quality enhancement (HD, 4K, 8K)
• 🖼️ Wallpaper conversion

*How to use:*
1. Send me an image (photo or document)
2. Choose from the editing options
3. Wait for processing
4. Download your enhanced image!

*Supported formats:* JPEG, PNG, WebP
*Max file size:* {format_file_size(Config.MAX_FILE_SIZE)}

Send me an image to get started! 📸
        """
        
        await self.bot_api.send_message(chat_id, welcome_message)
    
    async def handle_help_command(self, chat_id: int):
        """Handle /help command"""
        help_message = """
🔧 *Available Commands:*

/start - Start the bot and see welcome message
/help - Show this help message

*Features Available:*

🎨 *AI Image Editing* (PhotoRoom API)
• Professional image enhancement
• Object removal and editing
• Style transfer and effects

🎯 *Background Removal* (Remove.bg API)  
• Automatic background detection
• Clean cutout generation
• Transparent background option

⬆️ *Quality Enhancement*
• HD (720p) - 1280x720
• Full HD (1080p) - 1920x1080
• 4K UHD - 3840x2160
• 8K UHD - 7680x4320

🖼️ *Wallpaper Conversion*
• Aspect ratio adjustment
• Resolution optimization
• Quality enhancement

*How to use:*
Simply send me an image and select your desired operation from the menu!
        """
        
        await self.bot_api.send_message(chat_id, help_message)
    
    async def handle_photo(self, chat_id: int, user_id: int, photo_data: dict):
        """Handle photo uploads"""
        # Check rate limiting
        if not self.rate_limiter.check_rate_limit(user_id):
            await self.bot_api.send_message(
                chat_id,
                "⚠️ You've reached the rate limit. Please try again later."
            )
            return
        
        # Get the largest photo size
        photo = photo_data[-1]  # Last element is largest
        
        # Check file size
        if photo.get('file_size', 0) > Config.MAX_FILE_SIZE:
            await self.bot_api.send_message(
                chat_id,
                f"❌ File too large! Maximum size is {format_file_size(Config.MAX_FILE_SIZE)}."
            )
            return
        
        # Store image info in user session
        self.user_sessions[user_id] = {
            'file_id': photo['file_id'],
            'file_size': photo.get('file_size', 0),
            'timestamp': time.time(),
            'type': 'photo',
            'chat_id': chat_id
        }
        
        # Send options
        keyboard = self._create_image_options_keyboard()
        await self.bot_api.send_message(
            chat_id,
            "📸 *Image received!* What would you like to do?",
            reply_markup=keyboard
        )
    
    async def handle_document(self, chat_id: int, user_id: int, document_data: dict):
        """Handle document uploads (images)"""
        # Check if it's an image
        mime_type = document_data.get('mime_type', '')
        if not mime_type or mime_type not in Config.SUPPORTED_FORMATS:
            await self.bot_api.send_message(
                chat_id,
                "❌ Unsupported file format! Please send JPEG, PNG, or WebP images."
            )
            return
        
        # Check rate limiting
        if not self.rate_limiter.check_rate_limit(user_id):
            await self.bot_api.send_message(
                chat_id,
                "⚠️ You've reached the rate limit. Please try again later."
            )
            return
        
        # Check file size
        if document_data.get('file_size', 0) > Config.MAX_FILE_SIZE:
            await self.bot_api.send_message(
                chat_id,
                f"❌ File too large! Maximum size is {format_file_size(Config.MAX_FILE_SIZE)}."
            )
            return
        
        # Store document info in user session
        self.user_sessions[user_id] = {
            'file_id': document_data['file_id'],
            'file_size': document_data.get('file_size', 0),
            'timestamp': time.time(),
            'type': 'document',
            'mime_type': mime_type,
            'chat_id': chat_id
        }
        
        # Send options
        keyboard = self._create_image_options_keyboard()
        await self.bot_api.send_message(
            chat_id,
            "📄 *Document received!* What would you like to do?",
            reply_markup=keyboard
        )
    
    async def handle_callback_query(self, callback_data: dict):
        """Handle callback queries from inline keyboards"""
        query_id = callback_data['id']
        data = callback_data['data']
        user_id = callback_data['from']['id']
        chat_id = callback_data['message']['chat']['id']
        message_id = callback_data['message']['message_id']
        
        await self.bot_api.answer_callback_query(query_id)
        
        # Check if user has an active session
        if user_id not in self.user_sessions:
            await self.bot_api.edit_message_text(
                chat_id, message_id,
                "❌ Session expired. Please send a new image."
            )
            return
        
        try:
            if data == "remove_bg":
                await self._handle_remove_background(chat_id, message_id, user_id)
            elif data == "ai_edit":
                await self._handle_ai_edit(chat_id, message_id, user_id)
            elif data == "enhance_quality":
                await self._show_quality_options(chat_id, message_id)
            elif data == "wallpaper":
                await self._handle_wallpaper_conversion(chat_id, message_id, user_id)
            elif data.startswith("quality_"):
                quality = data.replace("quality_", "")
                await self._handle_quality_enhancement(chat_id, message_id, user_id, quality)
            elif data == "back_to_options":
                keyboard = self._create_image_options_keyboard()
                await self.bot_api.edit_message_text(
                    chat_id, message_id,
                    "📸 What would you like to do with your image?",
                    reply_markup=keyboard
                )
        
        except Exception as e:
            logger.error(f"Error handling callback {data}: {e}")
            await self.bot_api.edit_message_text(
                chat_id, message_id,
                "❌ An error occurred while processing your request. Please try again."
            )
    
    async def _show_quality_options(self, chat_id: int, message_id: int):
        """Show quality enhancement options"""
        keyboard = self._create_quality_keyboard()
        await self.bot_api.edit_message_text(
            chat_id, message_id,
            "⬆️ *Choose Quality Enhancement Level:*",
            reply_markup=keyboard
        )
    
    async def _handle_remove_background(self, chat_id: int, message_id: int, user_id: int):
        """Handle background removal"""
        if not self.removebg_client:
            await self.bot_api.edit_message_text(
                chat_id, message_id,
                "❌ Background removal service is not available."
            )
            return
        
        await self.bot_api.edit_message_text(
            chat_id, message_id,
            "🎯 *Removing background...*\nThis may take a few moments."
        )
        
        try:
            # Download image
            file_id = self.user_sessions[user_id]['file_id']
            file_info = await self.bot_api.get_file(file_id)
            
            if file_info.get('ok'):
                file_path = file_info['result']['file_path']
                image_bytes = await self.bot_api.download_file(file_path)
                
                # Process with Remove.bg
                result_bytes = await self.removebg_client.remove_background(image_bytes)
                
                if result_bytes:
                    # Send processed image
                    await self.bot_api.send_document(
                        chat_id,
                        result_bytes,
                        "background_removed.png",
                        "✅ Background removed successfully!"
                    )
                    await self.bot_api.edit_message_text(
                        chat_id, message_id,
                        "✅ *Background removal completed!*"
                    )
                else:
                    await self.bot_api.edit_message_text(
                        chat_id, message_id,
                        "❌ Failed to remove background. Please try again."
                    )
            else:
                await self.bot_api.edit_message_text(
                    chat_id, message_id,
                    "❌ Failed to download image. Please try again."
                )
        
        except Exception as e:
            logger.error(f"Error removing background: {e}")
            await self.bot_api.edit_message_text(
                chat_id, message_id,
                "❌ An error occurred during background removal."
            )
    
    async def _handle_ai_edit(self, chat_id: int, message_id: int, user_id: int):
        """Handle AI image editing"""
        if not self.photoroom_client:
            await self.bot_api.edit_message_text(
                chat_id, message_id,
                "❌ AI editing service is not available."
            )
            return
        
        await self.bot_api.edit_message_text(
            chat_id, message_id,
            "🎨 *Processing with AI...*\nThis may take a few moments."
        )
        
        try:
            # Download image
            file_id = self.user_sessions[user_id]['file_id']
            file_info = await self.bot_api.get_file(file_id)
            
            if file_info.get('ok'):
                file_path = file_info['result']['file_path']
                image_bytes = await self.bot_api.download_file(file_path)
                
                # Process with PhotoRoom
                result_bytes = await self.photoroom_client.enhance_image(image_bytes)
                
                if result_bytes:
                    # Send processed image
                    await self.bot_api.send_document(
                        chat_id,
                        result_bytes,
                        "ai_edited.png",
                        "✅ AI editing completed successfully!"
                    )
                    await self.bot_api.edit_message_text(
                        chat_id, message_id,
                        "✅ *AI editing completed!*"
                    )
                else:
                    await self.bot_api.edit_message_text(
                        chat_id, message_id,
                        "❌ Failed to process image with AI. Please try again."
                    )
            else:
                await self.bot_api.edit_message_text(
                    chat_id, message_id,
                    "❌ Failed to download image. Please try again."
                )
        
        except Exception as e:
            logger.error(f"Error with AI editing: {e}")
            await self.bot_api.edit_message_text(
                chat_id, message_id,
                "❌ An error occurred during AI editing."
            )
    
    async def _handle_quality_enhancement(self, chat_id: int, message_id: int, user_id: int, quality: str):
        """Handle quality enhancement"""
        if quality not in Config.QUALITY_OPTIONS:
            await self.bot_api.edit_message_text(
                chat_id, message_id,
                "❌ Invalid quality option."
            )
            return
        
        quality_info = Config.QUALITY_OPTIONS[quality]
        await self.bot_api.edit_message_text(
            chat_id, message_id,
            f"⬆️ *Enhancing to {quality_info['label']}...*\nThis may take a few moments."
        )
        
        try:
            # Download image
            file_id = self.user_sessions[user_id]['file_id']
            file_info = await self.bot_api.get_file(file_id)
            
            if file_info.get('ok'):
                file_path = file_info['result']['file_path']
                image_bytes = await self.bot_api.download_file(file_path)
                
                # Enhance quality
                result_bytes = await self.image_processor.enhance_quality(
                    image_bytes, 
                    quality_info['width'], 
                    quality_info['height']
                )
                
                if result_bytes:
                    # Send enhanced image
                    await self.bot_api.send_document(
                        chat_id,
                        result_bytes,
                        f"enhanced_{quality.lower()}.png",
                        f"✅ Enhanced to {quality_info['label']} successfully!"
                    )
                    await self.bot_api.edit_message_text(
                        chat_id, message_id,
                        f"✅ *Quality enhanced to {quality_info['label']}!*"
                    )
                else:
                    await self.bot_api.edit_message_text(
                        chat_id, message_id,
                        "❌ Failed to enhance quality. Please try again."
                    )
            else:
                await self.bot_api.edit_message_text(
                    chat_id, message_id,
                    "❌ Failed to download image. Please try again."
                )
        
        except Exception as e:
            logger.error(f"Error enhancing quality: {e}")
            await self.bot_api.edit_message_text(
                chat_id, message_id,
                "❌ An error occurred during quality enhancement."
            )
    
    async def _handle_wallpaper_conversion(self, chat_id: int, message_id: int, user_id: int):
        """Handle wallpaper conversion"""
        await self.bot_api.edit_message_text(
            chat_id, message_id,
            "🖼️ *Converting to wallpaper format...*\nThis may take a few moments."
        )
        
        try:
            # Download image
            file_id = self.user_sessions[user_id]['file_id']
            file_info = await self.bot_api.get_file(file_id)
            
            if file_info.get('ok'):
                file_path = file_info['result']['file_path']
                image_bytes = await self.bot_api.download_file(file_path)
                
                # Convert to wallpaper
                result_bytes = await self.image_processor.convert_to_wallpaper(image_bytes)
                
                if result_bytes:
                    # Send wallpaper
                    await self.bot_api.send_document(
                        chat_id,
                        result_bytes,
                        "wallpaper.png",
                        "✅ Wallpaper conversion completed successfully!"
                    )
                    await self.bot_api.edit_message_text(
                        chat_id, message_id,
                        "✅ *Wallpaper conversion completed!*"
                    )
                else:
                    await self.bot_api.edit_message_text(
                        chat_id, message_id,
                        "❌ Failed to convert to wallpaper. Please try again."
                    )
            else:
                await self.bot_api.edit_message_text(
                    chat_id, message_id,
                    "❌ Failed to download image. Please try again."
                )
        
        except Exception as e:
            logger.error(f"Error converting to wallpaper: {e}")
            await self.bot_api.edit_message_text(
                chat_id, message_id,
                "❌ An error occurred during wallpaper conversion."
            )

# Initialize Flask app
app = Flask(__name__)
bot_instance = None

@app.route('/')
def index():
    """Main page with bot information"""
    try:
        return render_template('index.html')
    except:
        # Fallback if template is not found
        return jsonify({
            "status": "ok",
            "message": "Telegram Image AI Bot",
            "description": "AI-powered image editing bot with background removal, quality enhancement, and wallpaper conversion",
            "features": [
                "Background Removal (Remove.bg API)",
                "AI Image Editing (PhotoRoom API)", 
                "Quality Enhancement (HD, 4K, 8K)",
                "Wallpaper Conversion"
            ],
            "quality_options": ["HD (720p)", "Full HD (1080p)", "4K UHD", "8K UHD"]
        })

@app.route('/health')
def health():
    """Health check endpoint"""
    telegram_configured = bool(Config.TELEGRAM_BOT_TOKEN)
    photoroom_configured = bool(Config.PHOTOROOM_API_KEY)
    removebg_configured = bool(Config.REMOVEBG_API_KEY)
    
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "web_server": "active",
            "telegram_bot": "configured" if telegram_configured else "missing_token",
            "photoroom_api": "configured" if photoroom_configured else "missing_key",
            "removebg_api": "configured" if removebg_configured else "missing_key"
        },
        "configuration": {
            "telegram_bot_token": "configured" if telegram_configured else "missing",
            "photoroom_api_key": "configured" if photoroom_configured else "missing", 
            "removebg_api_key": "configured" if removebg_configured else "missing"
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests from Telegram"""
    try:
        # Get the update from Telegram
        update_data = request.get_json()
        if not update_data:
            return jsonify({"error": "No JSON data received"}), 400
        
        # Process update asynchronously
        asyncio.create_task(process_telegram_update(update_data))
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500

async def process_telegram_update(update_data: dict):
    """Process a Telegram update"""
    global bot_instance
    
    try:
        if 'message' in update_data:
            message = update_data['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            user_name = message['from'].get('first_name', 'User')
            
            if 'text' in message:
                text = message['text']
                if text == '/start':
                    await bot_instance.handle_start_command(chat_id, user_name)
                elif text == '/help':
                    await bot_instance.handle_help_command(chat_id)
                else:
                    await bot_instance.bot_api.send_message(
                        chat_id,
                        "Please send me an image to get started! 📸"
                    )
            
            elif 'photo' in message:
                await bot_instance.handle_photo(chat_id, user_id, message['photo'])
            
            elif 'document' in message:
                await bot_instance.handle_document(chat_id, user_id, message['document'])
        
        elif 'callback_query' in update_data:
            await bot_instance.handle_callback_query(update_data['callback_query'])
    
    except Exception as e:
        logger.error(f"Error processing update: {e}")

def run_bot():
    """Run the bot with polling"""
    global bot_instance
    
    async def polling_loop():
        """Main polling loop"""
        offset = 0
        
        while True:
            try:
                # Get updates from Telegram
                url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getUpdates"
                params = {
                    'offset': offset,
                    'timeout': 30,
                    'limit': 100
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        result = await response.json()
                        
                        if result.get('ok'):
                            updates = result.get('result', [])
                            
                            for update in updates:
                                await process_telegram_update(update)
                                offset = update['update_id'] + 1
                        else:
                            logger.error(f"Error getting updates: {result}")
                            await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(10)
    
    # Run polling in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(polling_loop())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        loop.close()

async def setup_webhook():
    """Setup webhook for production deployment"""
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        # Auto-generate webhook URL for Render.com
        render_service = os.getenv('RENDER_SERVICE_NAME', 'telegram-image-ai-bot')
        webhook_url = f"https://{render_service}.onrender.com/webhook"
    
    logger.info(f"Setting up webhook: {webhook_url}")
    
    # Set webhook via Telegram API
    webhook_set_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/setWebhook"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_set_url, json={'url': webhook_url}) as response:
            result = await response.json()
            if result.get('ok'):
                logger.info("Webhook setup successful")
                return True
            else:
                logger.error(f"Webhook setup failed: {result}")
                return False

if __name__ == '__main__':
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed. Please check your environment variables.")
        exit(1)
    
    # Create bot instance
    bot_instance = WorkingTelegramBot()
    
    logger.info("Bot application created successfully")
    
    # Get port from environment (for Render.com compatibility)
    port = int(os.getenv('PORT', 5000))
    
    # Determine run mode
    use_webhook = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    
    if use_webhook:
        # Production mode with webhook
        logger.info(f"Starting bot with webhook mode on port {port}")
        
        # Setup webhook in background
        async def init_webhook():
            await setup_webhook()
        
        # Run webhook setup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(init_webhook())
        loop.close()
        
        # Start Flask app for webhook handling
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Development mode with polling
        logger.info(f"Starting bot with polling mode on port {port}")
        
        # Start Flask app in a separate thread
        flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False))
        flask_thread.daemon = True
        flask_thread.start()
        
        # Run bot polling in main thread
        run_bot()