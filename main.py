#!/usr/bin/env python3
"""
Telegram Bot with AI-powered image editing capabilities
Main application entry point with Flask webhook server
"""

import os
import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import asyncio
from threading import Thread
from bot_handlers import BotHandlers
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize bot application
bot_app = None
bot_handlers = None

def create_bot_application():
    """Create and configure the Telegram bot application"""
    global bot_app, bot_handlers
    
    # Initialize bot application
    bot_app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    bot_handlers = BotHandlers()
    
    # Register handlers
    bot_app.add_handler(CommandHandler("start", bot_handlers.start_command))
    bot_app.add_handler(CommandHandler("help", bot_handlers.help_command))
    bot_app.add_handler(MessageHandler(filters.PHOTO, bot_handlers.handle_photo))
    bot_app.add_handler(MessageHandler(filters.Document.IMAGE, bot_handlers.handle_document))
    bot_app.add_handler(CallbackQueryHandler(bot_handlers.handle_callback))
    
    logger.info("Bot application created and handlers registered")
    return bot_app

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Telegram Image AI Bot is running",
        "bot_username": Config.BOT_USERNAME if hasattr(Config, 'BOT_USERNAME') else "Unknown"
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests from Telegram"""
    try:
        # Get the update from Telegram
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No JSON data received"}), 400
        
        # Create Update object
        update = Update.de_json(json_data, bot_app.bot)
        
        # Process the update asynchronously
        asyncio.create_task(bot_app.process_update(update))
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Set the webhook URL for the bot"""
    try:
        webhook_url = request.json.get('webhook_url')
        if not webhook_url:
            return jsonify({"error": "webhook_url is required"}), 400
        
        # Set webhook
        asyncio.create_task(bot_app.bot.set_webhook(url=webhook_url))
        
        return jsonify({
            "status": "ok",
            "message": f"Webhook set to {webhook_url}"
        })
    
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"error": "Failed to set webhook"}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "telegram_bot": "active",
            "image_processor": "active",
            "api_clients": "configured"
        }
    })

def run_bot_polling():
    """Run bot in polling mode for development"""
    async def start_polling():
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        
    # Run in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_polling())

if __name__ == '__main__':
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed. Please check your environment variables.")
        exit(1)
    
    # Create bot application
    create_bot_application()
    
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
