# ✅ Quick Voice Agent Test Checklist

## 5-Minute Setup

### 1️⃣ Add Your Keys (Required)
```bash
# Edit .env file
OPENROUTER_API_KEY=sk-or-v1-xxxxx  # Get from openrouter.ai
TWILIO_ACCOUNT_SID=ACxxxxx         # From Twilio console
TWILIO_AUTH_TOKEN=xxxxxx           # From Twilio console
TWILIO_PHONE_NUMBER=+1234567890    # Your Twilio number
```

### 2️⃣ Start Backend
```bash
cd /Users/copp1723/Desktop/working_projects/voice-agent-fresh-main
python3 start_simple.py
```

### 3️⃣ Expose with ngrok
```bash
ngrok http 10000
# Copy the https URL (like https://abc123.ngrok.io)
```

### 4️⃣ Configure Twilio
1. Go to console.twilio.com
2. Phone Numbers → Your Number → Voice Configuration
3. Set webhook to: `https://YOUR-NGROK.ngrok.io/api/twilio/inbound`
4. Save

### 5️⃣ Make Test Call
Call your Twilio number and say: "Hello, I need help with my bill"

## What Should Happen

✅ **Success looks like:**
- Phone rings and connects
- AI voice greets you
- Your request is understood
- Routed to correct agent (billing)
- Natural conversation follows
- SMS sent after call ends

❌ **If it fails:**
- Check terminal for errors
- Verify all API keys are correct
- Ensure ngrok is still running
- Check Twilio webhook URL

## Quick Debug Commands

```bash
# Test if backend is working
curl http://localhost:10000/health

# See recent calls
curl http://localhost:10000/api/calls

# Check Twilio webhook manually
curl -X POST http://localhost:10000/api/twilio/inbound \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&CallSid=test123"
```

## Common First-Time Issues

1. **"Application error" voice message**
   - Your API keys are missing/invalid
   
2. **Call disconnects immediately**
   - Webhook URL is wrong in Twilio
   
3. **No AI response**
   - Check OPENROUTER_API_KEY is valid
   
4. **Can't hear anything**
   - Twilio credentials are incorrect

---

💡 **Pro tip**: Start with the simplest test - just saying "hello" - before testing complex routing scenarios.