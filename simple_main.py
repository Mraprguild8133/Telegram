#!/usr/bin/env python3
"""
Simple Flask server for the Telegram Image AI Bot
This version runs the web interface without the Telegram bot functionality
"""

import os
import logging
from flask import Flask, request, jsonify, render_template

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

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
            "quality_options": ["HD (720p)", "Full HD (1080p)", "4K UHD", "8K UHD"],
            "note": "Bot requires TELEGRAM_BOT_TOKEN to be configured"
        })

@app.route('/health')
def health():
    """Health check endpoint"""
    telegram_configured = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
    photoroom_configured = bool(os.getenv('PHOTOROOM_API_KEY'))
    removebg_configured = bool(os.getenv('REMOVEBG_API_KEY'))
    
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

@app.route('/status')
def status():
    """Detailed status information"""
    return jsonify({
        "application": "Telegram Image AI Bot",
        "description": "AI-powered image editing with multiple enhancement options",
        "features": {
            "background_removal": {
                "available": bool(os.getenv('REMOVEBG_API_KEY')),
                "provider": "Remove.bg API"
            },
            "ai_editing": {
                "available": bool(os.getenv('PHOTOROOM_API_KEY')),
                "provider": "PhotoRoom API"
            },
            "quality_enhancement": {
                "available": True,
                "options": ["HD (720p)", "Full HD (1080p)", "4K UHD", "8K UHD"],
                "provider": "Local PIL processing"
            },
            "wallpaper_conversion": {
                "available": True,
                "provider": "Local PIL processing"
            }
        },
        "telegram_bot": {
            "configured": bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            "status": "ready" if os.getenv('TELEGRAM_BOT_TOKEN') else "missing_token"
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint (requires Telegram bot to be configured)"""
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        return jsonify({"error": "Telegram bot not configured"}), 501
    
    return jsonify({"message": "Telegram bot not started in this mode"}), 501

if __name__ == '__main__':
    logger.info("Starting simple Flask server for Telegram Image AI Bot")
    logger.info("Web interface available on port 5000")
    
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.warning("TELEGRAM_BOT_TOKEN not configured - bot functionality disabled")
    if not os.getenv('PHOTOROOM_API_KEY'):
        logger.warning("PHOTOROOM_API_KEY not configured - AI editing disabled")  
    if not os.getenv('REMOVEBG_API_KEY'):
        logger.warning("REMOVEBG_API_KEY not configured - background removal disabled")
    
    app.run(host='0.0.0.0', port=5000, debug=False)