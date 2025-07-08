# Voice Agent Deployment Guide

This guide covers deploying the Voice Agent system to production environments.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Deployment Options](#deployment-options)
- [Post-Deployment](#post-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis (optional, for caching)
- Docker (for containerized deployment)
- SSL certificates for HTTPS

## Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# OpenRouter Configuration
OPENROUTER_API_KEY=your-openrouter-api-key

# API Security
API_KEY=your-api-key-here

# Frontend Configuration
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
```

## Database Setup

1. **Create Production Database:**
```bash
psql -U postgres
CREATE DATABASE voice_agent_prod;
CREATE USER voice_agent_user WITH ENCRYPTED PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE voice_agent_prod TO voice_agent_user;
```

2. **Run Migrations:**
```bash
export DATABASE_URL=postgresql://voice_agent_user:password@localhost/voice_agent_prod
python -c "from src.main import create_app; app = create_app(); app.app_context().push(); from src.models import db; db.create_all()"
```

3. **Create Admin User:**
```bash
python create_admin_user.py
```

## Deployment Options

### Option 1: Docker Deployment

1. **Build Images:**
```bash
docker build -t voice-agent-backend .
docker build -t voice-agent-frontend ./frontend
```

2. **Run with Docker Compose:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Render Deployment

1. **Backend Service:**
   - Create a new Web Service on Render
   - Connect your GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT src.main:create_app()`
   - Add all environment variables

2. **Frontend Service:**
   - Create a Static Site on Render
   - Set build command: `cd frontend && npm install && npm run build`
   - Set publish directory: `frontend/dist`

3. **Database:**
   - Create a PostgreSQL database on Render
   - Copy the connection string to your backend environment

### Option 3: Manual Deployment (VPS)

1. **Install Dependencies:**
```bash
# System dependencies
sudo apt update
sudo apt install python3.10 python3-pip nodejs npm postgresql nginx

# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install
```

2. **Build Frontend:**
```bash
cd frontend
npm run build
```

3. **Configure Nginx:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /var/www/voice-agent/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /socket.io {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

4. **Create Systemd Service:**
```ini
[Unit]
Description=Voice Agent Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/voice-agent
Environment="PATH=/usr/local/bin:/usr/bin"
ExecStart=/usr/local/bin/gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:5000 src.main:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
```

5. **Start Services:**
```bash
sudo systemctl enable voice-agent
sudo systemctl start voice-agent
sudo systemctl restart nginx
```

## Post-Deployment

1. **Configure Twilio Webhooks:**
   - Log in to Twilio Console
   - Navigate to Phone Numbers
   - Configure your number with:
     - Voice webhook: `https://api.yourdomain.com/api/twilio/inbound`
     - Status callback: `https://api.yourdomain.com/api/twilio/status`

2. **SSL Certificate:**
```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

3. **Security Hardening:**
   - Enable firewall (UFW)
   - Configure fail2ban
   - Set up regular backups
   - Enable log rotation

## Monitoring

1. **Application Monitoring:**
   - Set up Sentry for error tracking
   - Configure application logs
   - Monitor API response times

2. **Infrastructure Monitoring:**
   - CPU and memory usage
   - Database performance
   - Network traffic

3. **Health Checks:**
   - Backend: `GET /api/health`
   - Frontend: `GET /health`

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed:**
   - Check nginx configuration for WebSocket proxy
   - Verify CORS settings
   - Check firewall rules

2. **Database Connection Error:**
   - Verify DATABASE_URL format
   - Check PostgreSQL is running
   - Verify network connectivity

3. **Twilio Webhooks Not Working:**
   - Verify webhook URLs are accessible
   - Check Twilio signature validation
   - Review Twilio error logs

4. **High Memory Usage:**
   - Adjust worker count in gunicorn
   - Enable connection pooling
   - Monitor for memory leaks

### Logs Location

- Backend logs: `/var/log/voice-agent/app.log`
- Nginx logs: `/var/log/nginx/`
- PostgreSQL logs: `/var/log/postgresql/`

### Performance Tuning

1. **Database Optimization:**
   - Add indexes for frequently queried fields
   - Enable query caching
   - Regular VACUUM and ANALYZE

2. **Application Optimization:**
   - Enable Redis caching
   - Optimize database queries
   - Use CDN for static assets

3. **Scaling Options:**
   - Horizontal scaling with load balancer
   - Database read replicas
   - Separate WebSocket servers

## Backup and Recovery

1. **Database Backup:**
```bash
# Automated daily backup
pg_dump -U voice_agent_user voice_agent_prod | gzip > backup_$(date +%Y%m%d).sql.gz
```

2. **Application Backup:**
   - Version control for code
   - Backup environment variables
   - Document infrastructure configuration

3. **Disaster Recovery:**
   - Test restore procedures
   - Document recovery steps
   - Maintain off-site backups