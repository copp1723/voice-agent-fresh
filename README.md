# A Killion Voice - AI Voice Agent System

🎯 **Professional AI voice agent with smart routing, SMS follow-up, and natural conversations**

## 📞 Live System
- **Phone:** (978) 643-2034
- **Domain:** akillionvoice.xyz
- **API:** https://api.akillionvoice.xyz

## ✨ Features

### 🧠 Smart Call Routing
- **5 Specialized Agents:** General, Billing, Support, Sales, Scheduling
- **Keyword Detection:** Automatically routes calls based on customer intent
- **Confidence Scoring:** Tracks routing accuracy and improves over time

### 💬 Professional SMS Follow-up
- **Automatic SMS** after every call with conversation summary
- **Branded Messages** with A Killion Voice branding
- **Agent-Specific Templates** for different call types
- **Delivery Tracking** and reply handling

### 🎙️ Natural Voice Conversations
- **OpenAI TTS** for natural speech synthesis
- **Whisper STT** for accurate transcription
- **Voice Optimization** for phone conversations
- **Multiple Voice Options** per agent type

### 📊 Complete Analytics
- **Call Tracking** with duration and routing data
- **Conversation Logging** with confidence scores
- **SMS Delivery Metrics** and response rates
- **Agent Performance** analytics

## 🏗️ Architecture

### Backend (Flask)
```
src/
├── main.py                 # Flask application entry point
├── models/
│   └── call.py            # Database models (Call, Message, AgentConfig, SMSLog)
├── services/
│   ├── agent_brain.py     # AI conversation processing
│   ├── call_router.py     # Smart call routing logic
│   ├── sms_service.py     # SMS follow-up service
│   └── voice_processor.py # Voice synthesis and transcription
└── routes/
    └── voice.py           # Twilio webhook endpoints
```

### Database Schema
- **Call:** Track phone calls with routing and analytics
- **Message:** Store conversation turns with transcription
- **AgentConfig:** Manage agent types and prompts
- **SMSLog:** Track SMS delivery and responses

### API Endpoints
- `POST /api/twilio/inbound` - Incoming call webhook
- `POST /api/twilio/process/{call_sid}` - Voice processing
- `POST /api/twilio/status` - Call status updates
- `GET /health` - System health check
- `GET /api/calls` - Call history
- `GET /api/agents` - Agent configurations

## 🚀 Deployment

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Twilio account with phone number
- OpenRouter API key

### Environment Variables
```bash
# AI Processing
OPENROUTER_API_KEY=your-openrouter-key

# Twilio Integration
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+19786432034

# Production Settings
FLASK_ENV=production
DOMAIN=akillionvoice.xyz
API_BASE_URL=https://api.akillionvoice.xyz
COMPANY_NAME=A Killion Voice
PORT=10000

# Database (auto-configured in production)
DATABASE_URL=postgresql://...
```

### Local Development
```bash
# Clone repository
git clone https://github.com/copp1723/voice-agent-fresh.git
cd voice-agent-fresh

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Run locally
python src/main.py
```

### Production Deployment (Render)
```bash
# Deploy to Render
python deploy-fresh.py

# Configure Twilio webhooks:
# - Incoming: https://api.akillionvoice.xyz/api/twilio/inbound
# - Status: https://api.akillionvoice.xyz/api/twilio/status
```

## 🎭 Agent Types

### General Assistant
- **Keywords:** hello, hi, help, general, information
- **Voice:** alloy (neutral)
- **Purpose:** General customer service

### Billing Specialist  
- **Keywords:** billing, payment, invoice, charge, refund, subscription
- **Voice:** nova (friendly)
- **Purpose:** Payment and billing inquiries

### Technical Support
- **Keywords:** help, problem, issue, error, broken, not working, bug
- **Voice:** echo (calm)
- **Purpose:** Technical troubleshooting

### Sales Representative
- **Keywords:** buy, purchase, pricing, demo, trial, features, plans
- **Voice:** fable (warm)
- **Purpose:** Sales and product information

### Scheduling Coordinator
- **Keywords:** appointment, schedule, meeting, book, calendar, available
- **Voice:** shimmer (gentle)
- **Purpose:** Appointment scheduling

## 📱 SMS Templates

Each agent sends personalized follow-up messages:

**Billing:** "Thanks for calling A Killion Voice about your billing inquiry. [Summary] If you need further assistance, please reply or call us back."

**Support:** "Thanks for calling A Killion Voice technical support. [Summary] We've provided troubleshooting steps. Reply if you need more assistance!"

**Sales:** "Thanks for your interest in A Killion Voice services! [Summary] I'll follow up with more information. Questions? Just reply!"

## 🔧 Configuration

### Twilio Setup
1. Purchase phone number: (978) 643-2034
2. Configure webhooks in Twilio Console:
   - Voice URL: `https://api.akillionvoice.xyz/api/twilio/inbound`
   - Status Callback: `https://api.akillionvoice.xyz/api/twilio/status`

### Voice Settings
- **Default Voice:** alloy (OpenAI TTS)
- **Speech Model:** whisper-1 (OpenAI STT)
- **Response Timeout:** 30 seconds
- **Max Conversation Turns:** 20

## 📊 Monitoring

### Health Check
```bash
curl https://api.akillionvoice.xyz/health
```

Response:
```json
{
  "status": "healthy",
  "service": "A Killion Voice Agent",
  "domain": "akillionvoice.xyz",
  "phone": "(978) 643-2034",
  "active_calls": 0,
  "webhook_url": "https://api.akillionvoice.xyz/api/twilio/inbound",
  "openrouter_configured": true,
  "twilio_configured": true,
  "sms_enabled": true
}
```

### Call Analytics
- View call history: `GET /api/calls`
- Agent performance: `GET /api/agents`
- SMS delivery rates: Database queries

## 🛠️ Development

### Adding New Agents
1. Create agent configuration in database
2. Add keywords and routing logic
3. Define specialized system prompt
4. Create SMS template
5. Assign voice preference

### Extending Functionality
- **Voice Providers:** Add ElevenLabs, Azure Speech
- **SMS Providers:** Add SendGrid, Mailgun
- **Analytics:** Add call sentiment analysis
- **Integrations:** Connect to CRM systems

## 📞 Testing

### Test Call Flow
1. Call (978) 643-2034
2. Say "I have a billing question"
3. Verify routing to Billing Specialist
4. Complete conversation
5. Check SMS follow-up received

### Test Endpoints
```bash
# Health check
curl https://api.akillionvoice.xyz/health

# Call history
curl https://api.akillionvoice.xyz/api/calls

# Agent configurations
curl https://api.akillionvoice.xyz/api/agents
```

### Running Automated Tests

This project uses `pytest` for automated testing. Tests cover API endpoints, call routing logic, and SMS service functionality.

**Prerequisites:**
- Ensure you have followed the "Local Development" setup steps, including creating a virtual environment and installing dependencies from `requirements.txt`. The test dependencies (`pytest`, `pytest-flask`, `pytest-mock`) are included in this file.

**Running Tests:**
1. Activate your virtual environment:
   ```bash
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```
2. Navigate to the project root directory (if you aren't already there).
3. Run pytest:
   ```bash
   pytest
   ```
   Or, for more verbose output:
   ```bash
   pytest -v
   ```
   Pytest will automatically discover and run tests located in the `tests/` directory. Test results will be displayed in the console.

**Test Environment:**
- Tests run against an in-memory SQLite database, separate from your development or production database, ensuring no real data is affected.
- External services like Twilio and OpenAI are typically mocked or run in test modes to avoid actual external API calls and associated costs during testing. Refer to `tests/conftest.py` and individual test files for specific mocking strategies.

## 🔐 Security

- **Environment Variables:** Sensitive data in environment
- **HTTPS:** SSL certificates via Render
- **API Authentication:** Twilio webhook validation
- **Database:** Encrypted PostgreSQL connections

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Support

- **Technical Issues:** Check Render dashboard logs
- **Twilio Problems:** Verify webhook configuration
- **Voice Quality:** Monitor OpenRouter API usage

---

**A Killion Voice - Professional AI voice agent system ready for production use.**

