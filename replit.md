# Overview

This is a Telegram bot application that provides AI-powered image editing capabilities. The bot allows users to upload images and perform various enhancement operations including background removal, quality enhancement (HD, 4K, 8K upscaling), and wallpaper conversion. The application uses external API services for advanced image processing while also providing local image processing capabilities through PIL.

## Current Status (Updated August 7, 2025)
- All required API keys are properly configured (TELEGRAM_BOT_TOKEN, PHOTOROOM_API_KEY, REMOVEBG_API_KEY)
- Flask web interface is fully functional and cleaned up (bot status section removed as requested)
- Complete Telegram bot code has been written with all features implemented
- Telegram bot is now fully operational using direct API calls (avoiding library conflicts)
- Bot username: @Mraprguildaitebot (ID: 7524833544)
- Both Flask web server and Telegram bot polling are running successfully on port 5000
- Docker configuration and Render.com deployment files created
- PhotoRoom API integration fixed and working properly
- Complete deployment documentation and setup guides created

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Framework**: Python Telegram Bot (PTB) library with async/await support
- **Architecture Pattern**: Handler-based command processing with callback query support
- **Session Management**: In-memory user session storage for tracking user interactions

## Image Processing Pipeline
- **Local Processing**: PIL (Python Imaging Library) for basic image operations, format conversion, and quality enhancement
- **External APIs**: Integration with PhotoRoom and RemoveBG APIs for advanced AI-powered processing
- **Async Processing**: Non-blocking image processing using asyncio and thread pools

## Web Server Integration
- **Framework**: Flask web server for webhook handling and status endpoints
- **Deployment Model**: Hybrid polling/webhook support for flexible deployment options
- **Threading**: Separate threads for Flask server and Telegram bot application

## Rate Limiting & Security
- **Rate Limiting**: Custom time-window based rate limiter per user
- **File Validation**: Size and format restrictions for uploaded images
- **Error Handling**: Comprehensive logging and graceful error recovery

## Configuration Management
- **Environment Variables**: All sensitive configuration through environment variables
- **Quality Presets**: Predefined quality enhancement options (HD, 1080p, 4K, 8K)
- **API Configuration**: Centralized API endpoint and key management

# External Dependencies

## Third-Party APIs
- **PhotoRoom API**: AI-powered image enhancement and background removal
- **RemoveBG API**: Specialized background removal service
- **Telegram Bot API**: Core messaging and file handling capabilities

## Python Libraries
- **aiohttp**: Async HTTP client for external API communication
- **PIL (Pillow)**: Image processing and manipulation
- **python-telegram-bot**: Telegram bot framework
- **Flask**: Web server for webhook handling
- **numpy**: Numerical operations for image processing

## Infrastructure Requirements
- **Environment Variables**: TELEGRAM_BOT_TOKEN, PHOTOROOM_API_KEY, REMOVEBG_API_KEY
- **Optional Webhook**: WEBHOOK_URL and WEBHOOK_SECRET for production deployment
- **File Storage**: Temporary in-memory file handling (no persistent storage)