# 📞 Voice Agent Testing Guide - Step by Step

## Prerequisites

Before testing voice calls, you need:
1. **Twilio Account** (free trial works)
2. **Twilio Phone Number** 
3. **OpenRouter API Key** (or OpenAI API key)
4. **ngrok** for local testing (or deploy to a public server)

## Step 1: Set Up Your Environment

### 1.1 Update your `.env` file with real credentials:

```bash
cd /Users/copp1723/Desktop/working_projects/voice-agent-fresh-main
nano .env
```

Add your real credentials:
```env
# REQUIRED - Get from OpenRouter.ai
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here

# REQUIRED - Get from Twilio Console
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1234567890  # Your Twilio number

# Optional but recommended
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx  # For better voice transcription
```

### 1.2 Install ngrok (for local testing):

```bash
# On Mac
brew install ngrok

# Or download from https://ngrok.com/download
```

## Step 2: Start the Backend

```bash
# Terminal 1
cd /Users/copp1723/Desktop/working_projects/voice-agent-fresh-main
python3 start_simple.py
```

You should see:
```
✅ Database created at: /Users/copp1723/Desktop/working_projects/voice-agent-fresh-main/app.db

🚀 Voice Agent Backend Starting...

📍 API URL: http://localhost:10000
📍 Basic UI: http://localhost:10000
📍 Health Check: http://localhost:10000/health
```

## Step 3: Expose Your Local Server

```bash
# Terminal 2
ngrok http 10000
```

You'll see something like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:10000
```

**SAVE THIS URL** - You'll need it for Twilio.

## Step 4: Configure Twilio Webhooks

1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Click on your phone number
4. In the Voice Configuration section:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://abc123.ngrok.io/api/twilio/inbound` (use YOUR ngrok URL)
   - **HTTP Method**: POST
5. Save the configuration

## Step 5: Test Each Agent

### Test 1: General Agent
Call your Twilio number and say:
- "Hello, I need help"
- "Can you give me some information?"

Expected: Routed to General Assistant

### Test 2: Billing Agent  
Call and say:
- "I have a question about my bill"
- "I need help with payment"

Expected: Routed to Billing Specialist

### Test 3: Support Agent
Call and say:
- "I have a problem with my service"
- "Something is broken"

Expected: Routed to Support Agent

### Test 4: Sales Agent
Call and say:
- "I want to buy something"
- "What's the price?"

Expected: Routed to Sales Representative

### Test 5: Scheduling Agent
Call and say:
- "I need to schedule an appointment"
- "Can I book a service?"

Expected: Routed to Scheduling Assistant

## Step 6: Monitor the Results

### 6.1 Check Terminal Output
Your backend terminal will show:
```
Incoming call from: +1234567890
Routing call to: billing agent
Confidence score: 0.85
```

### 6.2 Check the Dashboard
```bash
# Terminal 3
cd /Users/copp1723/Desktop/working_projects/voice-agent-fresh-main/frontend
npm run dev
```

Open http://localhost:3000 to see:
- Active calls in real-time
- Which agent handled each call
- Call duration and status

### 6.3 Check SMS Follow-ups
After each call ends, check your phone for the SMS follow-up message.

## Troubleshooting Common Issues

### "I hear nothing when I call"
- Check your .env has valid API keys
- Check terminal for error messages
- Verify ngrok is still running

### "Call disconnects immediately"
- Check Twilio webhook URL is correct
- Ensure `/api/twilio/inbound` is included in URL
- Check backend is running on port 10000

### "Wrong agent answers"
- Check keywords in agent configuration
- Speak clearly when testing
- Try more specific keywords

### "No SMS received"
- Verify TWILIO_AUTH_TOKEN is correct
- Check terminal for SMS sending errors
- Ensure phone number format is correct

## Step 7: View Call Logs

To see all your test calls:

```bash
# In another terminal
curl http://localhost:10000/api/calls -H "x-api-key: your-api-key"
```

Or check the dashboard's Call History tab.

## Testing Tips

1. **Test Different Accents**: The system should handle various accents
2. **Test Interruptions**: Try interrupting the AI mid-sentence
3. **Test Silence**: Stay silent to see how it handles no input
4. **Test Multiple Keywords**: "I have a billing issue and need support"
5. **Test Edge Cases**: Mumble, speak very fast/slow

## Production Deployment

Once testing is complete:

1. Deploy to Render/Heroku/AWS
2. Update Twilio webhooks to production URL
3. Remove ngrok, use real domain
4. Set up monitoring/alerts

## Success Metrics

Your voice agent is working correctly when:
- ✅ Calls connect within 2 seconds
- ✅ Correct agent routing 90%+ of the time
- ✅ Natural conversation flow
- ✅ SMS follow-ups send reliably
- ✅ No crashes or disconnections

---

**Remember**: Start with simple tests, then gradually test more complex scenarios. The system is designed to handle real customer service calls, but thorough testing ensures reliability.