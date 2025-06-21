# A Killion Voice - Complete Deployment Checklist

## 🎯 Overview
Deploy A Killion Voice AI agent system to production with custom domain and phone integration.

## ✅ Phase 1: Render Deployment

### 1.1 Login to Render
- [ ] Go to https://dashboard.render.com
- [ ] Email: josh@atsglobal.ai
- [ ] Password: crn_TRC_euj3pgd_qdr

### 1.2 Create PostgreSQL Database
- [ ] Click "New +" → "PostgreSQL"
- [ ] Name: `akillion-voice-db`
- [ ] Plan: Free (testing) or Starter ($7/month production)
- [ ] Click "Create Database"
- [ ] **Copy Database URL** (Internal Database URL)

### 1.3 Create Web Service
- [ ] Click "New +" → "Web Service"
- [ ] Connect GitHub: `copp1723/voice-agent-fresh`
- [ ] Name: `akillion-voice-agent`
- [ ] Environment: `Python 3`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `python src/main.py`
- [ ] Plan: Free (testing) or Starter ($7/month production)

### 1.4 Environment Variables
Add these in the "Environment" tab:
```
OPENROUTER_API_KEY=[your-openrouter-api-key]
DATABASE_URL=[paste PostgreSQL URL from step 1.2]
COMPANY_NAME=A Killion Voice
DOMAIN=akillionvoice.xyz
API_BASE_URL=https://api.akillionvoice.xyz
TWILIO_PHONE_NUMBER=+19786432034
FLASK_ENV=production
PORT=10000
API_KEY=[generate-secure-random-key-for-admin-api-access]
```

### 1.5 Deploy & Test
- [ ] Click "Create Web Service"
- [ ] Wait for deployment (5-10 minutes)
- [ ] **Copy Render URL** (e.g., akillion-voice-agent.onrender.com)
- [ ] Test health: https://[your-render-url]/health

## ✅ Phase 2: Namecheap DNS Configuration

### 2.1 Login to Namecheap
- [ ] Go to https://www.namecheap.com/myaccount/login/
- [ ] Use your Namecheap account credentials

### 2.2 Access Domain Management
- [ ] Click "Domain List"
- [ ] Find "akillionvoice.xyz"
- [ ] Click "Manage"

### 2.3 Configure DNS Records
- [ ] Click "Advanced DNS" tab
- [ ] Delete existing A/CNAME records for @ and www
- [ ] Add these records:

```
Type: CNAME | Host: @ | Value: [your-render-url] | TTL: Automatic
Type: CNAME | Host: www | Value: [your-render-url] | TTL: Automatic  
Type: CNAME | Host: api | Value: [your-render-url] | TTL: Automatic
```

### 2.4 Custom Domain in Render
- [ ] In Render dashboard, go to your web service
- [ ] Click "Settings" → "Custom Domains"
- [ ] Add: `akillionvoice.xyz`
- [ ] Add: `www.akillionvoice.xyz`
- [ ] Add: `api.akillionvoice.xyz`

## ✅ Phase 3: Twilio Configuration

### 3.1 Add Twilio Credentials to Render
In Environment Variables, add:
```
TWILIO_ACCOUNT_SID=[your-twilio-sid]
TWILIO_AUTH_TOKEN=[your-twilio-token]
```

### 3.2 Configure Twilio Webhooks
- [ ] Login to Twilio Console
- [ ] Go to Phone Numbers → Manage → Active Numbers
- [ ] Click on (978) 643-2034
- [ ] Set Webhook URL: `https://api.akillionvoice.xyz/api/twilio/inbound`
- [ ] Set Status Callback: `https://api.akillionvoice.xyz/api/twilio/status`
- [ ] HTTP Method: POST
- [ ] Save configuration

## ✅ Phase 4: Testing & Verification

### 4.1 Health Checks
- [ ] Test: https://akillionvoice.xyz/health
- [ ] Test: https://api.akillionvoice.xyz/health
- [ ] Verify all services show "healthy"

### 4.2 Call Testing
- [ ] Call (978) 643-2034
- [ ] Test routing: "I have a billing question"
- [ ] Verify SMS follow-up received
- [ ] Check call logs: https://api.akillionvoice.xyz/api/calls

### 4.3 Agent Testing
Test each agent type:
- [ ] "Hello" → General Agent
- [ ] "I have a billing question" → Billing Specialist
- [ ] "My service isn't working" → Technical Support
- [ ] "I want to buy something" → Sales Representative
- [ ] "I need to schedule an appointment" → Scheduling Coordinator

## 🎯 Production URLs

After completion, these URLs will be live:
- **Main Site:** https://akillionvoice.xyz
- **API Base:** https://api.akillionvoice.xyz
- **Health Check:** https://akillionvoice.xyz/health
- **Twilio Webhook:** https://api.akillionvoice.xyz/api/twilio/inbound
- **Phone Number:** (978) 643-2034

## 🔧 Troubleshooting

### Common Issues:
1. **DNS not resolving:** Wait 30 minutes for propagation
2. **Health check fails:** Check Render logs for errors
3. **Calls not connecting:** Verify Twilio webhook URLs
4. **SMS not sending:** Add Twilio credentials to Render

### Support Resources:
- **Render Logs:** Dashboard → Service → Logs
- **Twilio Console:** https://console.twilio.com
- **GitHub Repo:** https://github.com/copp1723/voice-agent-fresh

## 🎉 Success Criteria

✅ **Deployment Complete When:**
- Health check returns "healthy" status
- Domain resolves to Render service
- Phone calls route to correct agents
- SMS follow-ups are sent automatically
- All 5 agent types respond correctly

**A Killion Voice is now ready for production use!**

