# Telegram Image AI Bot

A powerful Telegram bot that provides AI-powered image editing capabilities including background removal, quality enhancement, and professional image processing.

## Features

- **🎯 Background Removal** - Remove backgrounds automatically using Remove.bg API
- **🎨 AI Image Enhancement** - Professional image editing using PhotoRoom API
- **⬆️ Quality Enhancement** - Upscale images to HD, 4K, and 8K resolutions
- **🖼️ Wallpaper Conversion** - Convert images to optimized wallpaper formats
- **📱 Interactive Interface** - User-friendly inline keyboard menus
- **⚡ Rate Limiting** - Built-in protection against abuse
- **🔧 Multi-format Support** - JPEG, PNG, WebP support

## Bot Information

- **Username**: @Mraprguildaitebot
- **Bot ID**: 7524833544
- **Status**: ✅ Active

## Quick Start

### 1. Using the Bot

1. Open Telegram and search for `@Mraprguildaitebot`
2. Send `/start` to begin
3. Upload any image (photo or document)
4. Choose from available editing options:
   - Remove Background
   - AI Image Editing
   - Enhance Quality (HD/4K/8K)
   - Convert to Wallpaper
5. Download your processed image

### 2. Supported Commands

- `/start` - Initialize the bot and see welcome message
- `/help` - Display help information and feature list

## Deployment Options

### Option 1: Render.com (Recommended for Production)

1. **Fork this repository** to your GitHub account

2. **Create a new Render service**:
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository
   - Choose "Web Service"
   - Select this repository

3. **Configure environment variables**:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   PHOTOROOM_API_KEY=your_photoroom_api_key
   REMOVEBG_API_KEY=your_removebg_api_key
   USE_WEBHOOK=true
   PORT=5000
   ```

4. **Deploy**: Render will automatically build and deploy using the included `Dockerfile`

### Option 2: Docker

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd telegram-image-ai-bot
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Build and run with Docker**:
   ```bash
   docker-compose up -d
   ```

4. **Check status**:
   ```bash
   docker-compose logs -f
   ```

### Option 3: Manual Installation

1. **Requirements**:
   - Python 3.11+
   - UV package manager

2. **Install dependencies**:
   ```bash
   pip install uv
   uv sync
   ```

3. **Set environment variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token"
   export PHOTOROOM_API_KEY="your_key" 
   export REMOVEBG_API_KEY="your_key"
   ```

4. **Run the application**:
   ```bash
   python working_bot.py
   ```

## Configuration

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | ✅ Yes |
| `PHOTOROOM_API_KEY` | PhotoRoom API key for AI editing | ⚠️ Optional |
| `REMOVEBG_API_KEY` | Remove.bg API key for background removal | ⚠️ Optional |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_WEBHOOK` | `false` | Enable webhook mode for production |
| `PORT` | `5000` | Port number for the web server |
| `MAX_REQUESTS_PER_USER` | `10` | Rate limiting per user |
| `RATE_LIMIT_WINDOW` | `3600` | Rate limit window in seconds |
| `MAX_FILE_SIZE` | `20971520` | Maximum file size (20MB) |

## API Keys Setup

### 1. Telegram Bot Token

1. Message @BotFather on Telegram
2. Use `/newbot` command
3. Follow instructions to create your bot
4. Copy the provided token

### 2. PhotoRoom API Key

1. Visit [PhotoRoom API](https://www.photoroom.com/api)
2. Sign up for an account
3. Get your API key from the dashboard
4. Free tier includes 10 API calls

### 3. Remove.bg API Key

1. Visit [Remove.bg API](https://www.remove.bg/api)
2. Create an account
3. Get your API key
4. Free tier includes 50 API calls per month

## Architecture

- **Framework**: Direct Telegram Bot API integration (no library dependencies)
- **Image Processing**: PIL for local operations, external APIs for AI features
- **Web Server**: Flask for webhook handling and status endpoints
- **Deployment**: Docker-ready with Render.com optimization
- **Session Management**: In-memory user session tracking
- **Rate Limiting**: Time-window based protection

## File Structure

```
├── working_bot.py          # Main bot application
├── config.py               # Configuration management
├── api_clients.py          # External API integrations
├── image_processor.py      # Local image processing
├── utils.py                # Utility functions
├── templates/
│   └── index.html          # Web interface template
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── render.yaml             # Render.com deployment config
└── start.sh                # Production startup script
```

## Monitoring

### Health Check Endpoint

- **URL**: `/health`
- **Method**: GET
- **Response**: JSON with service status

### Web Interface

- **URL**: `/`
- **Features**: Bot information and feature overview

## Development

### Local Development

1. **Start in polling mode**:
   ```bash
   export USE_WEBHOOK=false
   python working_bot.py
   ```

2. **Access web interface**: http://localhost:5000

3. **Test bot**: Message your bot on Telegram

### Production Deployment

1. **Enable webhook mode**:
   ```bash
   export USE_WEBHOOK=true
   export WEBHOOK_URL=https://your-domain.com/webhook
   ```

2. **Deploy to your platform of choice**

## Quality Options

| Option | Resolution | Description |
|--------|------------|-------------|
| HD | 1280x720 | Standard HD quality |
| 1080p | 1920x1080 | Full HD quality |
| 4K | 3840x2160 | Ultra HD 4K |
| 8K | 7680x4320 | Ultra HD 8K |

## Support

- **Issues**: Create an issue in this repository
- **Features**: Submit a feature request
- **Documentation**: Check this README and code comments

## License

This project is open source. Check the license file for details.

---

**Bot Status**: ✅ Online and fully operational
**Last Updated**: August 7, 2025