#!/usr/bin/env python3
"""
Telegram Bot with AI-powered image editing capabilities
Main bot application with all features
"""

import os
import logging
import asyncio
from typing import Dict, Any
import io
import time
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode

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

class TelegramBot:
    """Main Telegram bot class"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.photoroom_client = PhotoRoomClient() if Config.PHOTOROOM_API_KEY else None
        self.removebg_client = RemoveBGClient() if Config.REMOVEBG_API_KEY else None
        self.rate_limiter = RateLimiter()
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        
    async def start_command(self, update: Update, context):
        """Handle /start command"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "User"
        
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
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context):
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
        
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _create_image_options_keyboard(self) -> InlineKeyboardMarkup:
        """Create inline keyboard with image processing options"""
        keyboard = []
        
        # Background removal
        if self.removebg_client:
            keyboard.append([InlineKeyboardButton("🎯 Remove Background", callback_data="remove_bg")])
        
        # AI editing
        if self.photoroom_client:
            keyboard.append([InlineKeyboardButton("🎨 AI Image Editing", callback_data="ai_edit")])
        
        # Quality enhancement
        keyboard.append([InlineKeyboardButton("⬆️ Enhance Quality", callback_data="enhance_quality")])
        
        # Wallpaper conversion
        keyboard.append([InlineKeyboardButton("🖼️ Convert to Wallpaper", callback_data="wallpaper")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def _create_quality_keyboard(self) -> InlineKeyboardMarkup:
        """Create keyboard for quality selection"""
        keyboard = []
        for key, value in Config.QUALITY_OPTIONS.items():
            keyboard.append([InlineKeyboardButton(value['label'], callback_data=f"quality_{key}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back to Options", callback_data="back_to_options")])
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_photo(self, update: Update, context):
        """Handle photo uploads"""
        user_id = update.effective_user.id
        
        # Check rate limiting
        if not self.rate_limiter.check_rate_limit(user_id):
            await update.message.reply_text(
                "⚠️ You've reached the rate limit. Please try again later.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Get the largest photo size
        photo = update.message.photo[-1]
        
        # Check file size
        if photo.file_size > Config.MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ File too large! Maximum size is {format_file_size(Config.MAX_FILE_SIZE)}.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Store image info in user session
        self.user_sessions[user_id] = {
            'file_id': photo.file_id,
            'file_size': photo.file_size,
            'timestamp': time.time(),
            'type': 'photo'
        }
        
        # Send options
        keyboard = self._create_image_options_keyboard()
        await update.message.reply_text(
            "📸 *Image received!* What would you like to do?",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_document(self, update: Update, context):
        """Handle document uploads (images)"""
        user_id = update.effective_user.id
        document = update.message.document
        
        # Check if it's an image
        if not document.mime_type or document.mime_type not in Config.SUPPORTED_FORMATS:
            await update.message.reply_text(
                "❌ Unsupported file format! Please send JPEG, PNG, or WebP images.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Check rate limiting
        if not self.rate_limiter.check_rate_limit(user_id):
            await update.message.reply_text(
                "⚠️ You've reached the rate limit. Please try again later.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Check file size
        if document.file_size > Config.MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ File too large! Maximum size is {format_file_size(Config.MAX_FILE_SIZE)}.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Store document info in user session
        self.user_sessions[user_id] = {
            'file_id': document.file_id,
            'file_size': document.file_size,
            'timestamp': time.time(),
            'type': 'document',
            'mime_type': document.mime_type
        }
        
        # Send options
        keyboard = self._create_image_options_keyboard()
        await update.message.reply_text(
            "📄 *Document received!* What would you like to do?",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_callback(self, update: Update, context):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        await query.answer()
        
        # Check if user has an active session
        if user_id not in self.user_sessions:
            await query.edit_message_text(
                "❌ Session expired. Please send a new image.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            if data == "remove_bg":
                await self._handle_remove_background(query, user_id)
            elif data == "ai_edit":
                await self._handle_ai_edit(query, user_id)
            elif data == "enhance_quality":
                await self._show_quality_options(query)
            elif data == "wallpaper":
                await self._handle_wallpaper_conversion(query, user_id)
            elif data.startswith("quality_"):
                quality = data.replace("quality_", "")
                await self._handle_quality_enhancement(query, user_id, quality)
            elif data == "back_to_options":
                keyboard = self._create_image_options_keyboard()
                await query.edit_message_text(
                    "📸 What would you like to do with your image?",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error handling callback {data}: {e}")
            await query.edit_message_text(
                "❌ An error occurred while processing your request. Please try again.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_quality_options(self, query):
        """Show quality enhancement options"""
        keyboard = self._create_quality_keyboard()
        await query.edit_message_text(
            "⬆️ *Choose Quality Enhancement Level:*",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_remove_background(self, query, user_id: int):
        """Handle background removal"""
        if not self.removebg_client:
            await query.edit_message_text(
                "❌ Background removal service is not available.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await query.edit_message_text(
            "🎯 *Removing background...*\nThis may take a few moments.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Download image
            file_id = self.user_sessions[user_id]['file_id']
            file = await query.bot.get_file(file_id)
            image_bytes = await file.download_as_bytearray()
            
            # Process with Remove.bg
            result_bytes = await self.removebg_client.remove_background(image_bytes)
            
            if result_bytes:
                # Send processed image
                await query.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=io.BytesIO(result_bytes),
                    filename="background_removed.png",
                    caption="✅ Background removed successfully!"
                )
                await query.edit_message_text("✅ *Background removal completed!*", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text(
                    "❌ Failed to remove background. Please try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error removing background: {e}")
            await query.edit_message_text(
                "❌ An error occurred during background removal.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_ai_edit(self, query, user_id: int):
        """Handle AI image editing"""
        if not self.photoroom_client:
            await query.edit_message_text(
                "❌ AI editing service is not available.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await query.edit_message_text(
            "🎨 *Processing with AI...*\nThis may take a few moments.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Download image
            file_id = self.user_sessions[user_id]['file_id']
            file = await query.bot.get_file(file_id)
            image_bytes = await file.download_as_bytearray()
            
            # Process with PhotoRoom
            result_bytes = await self.photoroom_client.enhance_image(image_bytes)
            
            if result_bytes:
                # Send processed image
                await query.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=io.BytesIO(result_bytes),
                    filename="ai_edited.png",
                    caption="✅ AI editing completed successfully!"
                )
                await query.edit_message_text("✅ *AI editing completed!*", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text(
                    "❌ Failed to process image with AI. Please try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error with AI editing: {e}")
            await query.edit_message_text(
                "❌ An error occurred during AI editing.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_quality_enhancement(self, query, user_id: int, quality: str):
        """Handle quality enhancement"""
        if quality not in Config.QUALITY_OPTIONS:
            await query.edit_message_text(
                "❌ Invalid quality option.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        quality_info = Config.QUALITY_OPTIONS[quality]
        await query.edit_message_text(
            f"⬆️ *Enhancing to {quality_info['label']}...*\nThis may take a few moments.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Download image
            file_id = self.user_sessions[user_id]['file_id']
            file = await query.bot.get_file(file_id)
            image_bytes = await file.download_as_bytearray()
            
            # Enhance quality
            result_bytes = await self.image_processor.enhance_quality(
                image_bytes, 
                quality_info['width'], 
                quality_info['height']
            )
            
            if result_bytes:
                # Send enhanced image
                await query.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=io.BytesIO(result_bytes),
                    filename=f"enhanced_{quality.lower()}.png",
                    caption=f"✅ Enhanced to {quality_info['label']} successfully!"
                )
                await query.edit_message_text(f"✅ *Quality enhanced to {quality_info['label']}!*", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text(
                    "❌ Failed to enhance quality. Please try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error enhancing quality: {e}")
            await query.edit_message_text(
                "❌ An error occurred during quality enhancement.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_wallpaper_conversion(self, query, user_id: int):
        """Handle wallpaper conversion"""
        await query.edit_message_text(
            "🖼️ *Converting to wallpaper format...*\nThis may take a few moments.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Download image
            file_id = self.user_sessions[user_id]['file_id']
            file = await query.bot.get_file(file_id)
            image_bytes = await file.download_as_bytearray()
            
            # Convert to wallpaper
            result_bytes = await self.image_processor.convert_to_wallpaper(image_bytes)
            
            if result_bytes:
                # Send wallpaper
                await query.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=io.BytesIO(result_bytes),
                    filename="wallpaper.png",
                    caption="✅ Wallpaper conversion completed successfully!"
                )
                await query.edit_message_text("✅ *Wallpaper conversion completed!*", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text(
                    "❌ Failed to convert to wallpaper. Please try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error converting to wallpaper: {e}")
            await query.edit_message_text(
                "❌ An error occurred during wallpaper conversion.",
                parse_mode=ParseMode.MARKDOWN
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
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No JSON data received"}), 400
        
        # Create Update object and process asynchronously
        update = Update.de_json(json_data, bot_instance.bot)
        asyncio.create_task(bot_instance.process_update(update))
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500

def run_bot_polling():
    """Run bot in polling mode for development"""
    async def start_polling():
        await bot_instance.initialize()
        await bot_instance.start()
        await bot_instance.updater.start_polling()
        
    # Run in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_polling())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        loop.close()

if __name__ == '__main__':
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed. Please check your environment variables.")
        exit(1)
    
    # Create Telegram bot
    telegram_bot = TelegramBot()
    
    # Create bot application
    bot_instance = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    bot_instance.add_handler(CommandHandler("start", telegram_bot.start_command))
    bot_instance.add_handler(CommandHandler("help", telegram_bot.help_command))
    bot_instance.add_handler(MessageHandler(filters.PHOTO, telegram_bot.handle_photo))
    bot_instance.add_handler(MessageHandler(filters.Document.IMAGE, telegram_bot.handle_document))
    bot_instance.add_handler(CallbackQueryHandler(telegram_bot.handle_callback))
    
    logger.info("Bot application created and handlers registered")
    
    # Determine run mode
    use_webhook = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    
    if use_webhook:
        # Run with webhook (production mode)
        logger.info("Starting bot with webhook mode")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        # Run with polling (development mode)
        logger.info("Starting bot with polling mode")
        
        # Start Flask app in a separate thread
        flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
        flask_thread.daemon = True
        flask_thread.start()
        
        # Run bot polling in main thread
        run_bot_polling()