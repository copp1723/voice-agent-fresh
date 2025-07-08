# 🚀 Starting the Voice Agent Dashboard

## Option 1: Docker (Recommended for Quick Start)

```bash
# Navigate to project directory
cd /Users/copp1723/Desktop/working_projects/voice-agent-fresh-main

# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

## Option 2: Manual Start (Development)

### Terminal 1: Backend
```bash
# Navigate to project directory
cd /Users/copp1723/Desktop/working_projects/voice-agent-fresh-main

# Install Python dependencies
pip3 install -r requirements.txt

# Create admin user (first time only)
python3 init_admin.py

# Start Flask backend
python3 src/main.py
```

### Terminal 2: Frontend
```bash
# Navigate to frontend directory
cd /Users/copp1723/Desktop/working_projects/voice-agent-fresh-main/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

## Option 3: Production Mode

```bash
# Navigate to project directory
cd /Users/copp1723/Desktop/working_projects/voice-agent-fresh-main

# Use production Docker compose
docker-compose -f docker-compose.prod.yml up -d --build
```

## 📍 Access Points

- **Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **WebSocket**: ws://localhost:5000/socket.io

## 🔑 Default Login

- **Email**: admin@akillionvoice.xyz
- **Password**: admin123

## ⚠️ First Time Setup

Before starting, make sure your `.env` file has API keys:

```bash
# Edit .env file
OPENROUTER_API_KEY=your-key-here
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
```

## 🛑 Stopping Services

```bash
# If using Docker
docker-compose down

# If running manually
# Press Ctrl+C in each terminal
```

## 🔧 Troubleshooting

If you encounter issues:

```bash
# Clear Docker volumes and rebuild
docker-compose down -v
docker-compose up --build

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Reset database
docker-compose exec backend python init_admin.py
```