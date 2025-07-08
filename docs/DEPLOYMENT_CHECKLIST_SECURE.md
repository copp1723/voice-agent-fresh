# A Killion Voice - Secure Deployment Checklist

## 🔒 **SECURITY-HARDENED DEPLOYMENT**

**⚠️ IMPORTANT: This system now includes critical security fixes:**
- Twilio webhook signature validation
- API key authentication for admin endpoints  
- No hard-coded credentials
- Per-call state isolation for concurrent calls

---

## **Phase 1: Render Deployment (10 minutes)**

### 1.1 Login to Render
- [ ] Go to: https://dashboard.render.com
- [ ] Use your Render account credentials

### 1.2 Create PostgreSQL Database
- [ ] Click "New +" → "PostgreSQL"
- [ ] Name: `akillion-voice-db-secure`
- [ ] Plan: Free (for testing) or Starter ($7/month for production)
- [ ] Click "Create Database"
- [ ] **Copy the Database URL** (you'll need it)

### 1.3 Create Web Service
- [ ] Click "New +" → "Web Service"
- [ ] Connect GitHub account if needed
- [ ] Select Repository: `copp1723/voice-agent-fresh`
- [ ] Name: `akillion-voice-agent-secure`
- [ ] Environment: `Python 3`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `python src/main.py`
- [ ] Plan: Free (for testing) or Starter ($7/month)

### 1.4 Add Environment Variables (SECURE)
Click "Environment" tab and add:
```
OPENROUTER_API_KEY=[your-openrouter-api-key]
DATABASE_URL=[paste the PostgreSQL URL from step 1.2]
COMPANY_NAME=A Killion Voice
DOMAIN=akillionvoice.xyz
API_BASE_URL=https://api.akillionvoice.xyz
TWILIO_PHONE_NUMBER=+19786432034
TWILIO_ACCOUNT_SID=[your-twilio-account-sid]
TWILIO_AUTH_TOKEN=[your-twilio-auth-token]
FLASK_SECRET_KEY=[generate-random-secret-key]
API_KEY=[generate-admin-api-key]
FLASK_ENV=production
PORT=10000
```

### 1.5 Deploy
- [ ] Click "Create Web Service"
- [ ] Wait for deployment (5-10 minutes)
- [ ] **Copy your Render URL** (e.g., akillion-voice-agent-secure.onrender.com)

---

## **Phase 2: DNS Configuration (5 minutes)**

### 2.1 Login to Namecheap
- [ ] Go to https://www.namecheap.com/myaccount/login/
- [ ] Use your Namecheap account credentials

### 2.2 Configure DNS Records
- [ ] Click "Domain List" → Find "akillionvoice.xyz" → Click "Manage"
- [ ] Click "Advanced DNS" tab
- [ ] Delete any existing A/CNAME records for @ and www
- [ ] Add these new records:

```
Type: CNAME
Host: @
Value: [your-render-url-from-step-1.5]
TTL: Automatic

Type: CNAME  
Host: www
Value: [your-render-url-from-step-1.5]
TTL: Automatic

Type: CNAME
Host: api
Value: [your-render-url-from-step-1.5]  
TTL: Automatic
```

### 2.3 Wait for DNS Propagation
- [ ] Wait 5-30 minutes for DNS to propagate worldwide
- [ ] Test: https://akillionvoice.xyz/health

---

## **Phase 3: Twilio Configuration (5 minutes)**

### 3.1 Configure Webhooks
- [ ] Login to Twilio Console
- [ ] Go to Phone Numbers → Manage → Active Numbers
- [ ] Click your number: (978) 643-2034
- [ ] Set webhook URLs:

**Incoming Calls:**
```
https://api.akillionvoice.xyz/api/twilio/inbound
```

**Call Status:**
```
https://api.akillionvoice.xyz/api/twilio/status
```

### 3.2 Test Webhook Security
- [ ] Webhooks now validate Twilio signatures
- [ ] Only authentic Twilio requests will be processed
- [ ] Unauthorized requests will be rejected

---

## **Phase 4: Final Testing (5 minutes)**

### 4.1 Health Check
- [ ] Visit: https://akillionvoice.xyz/health
- [ ] Verify all services show as configured
- [ ] Check active_calls: 0, session_management: enabled

### 4.2 Test Call
- [ ] Call: (978) 643-2034
- [ ] Verify smart routing works
- [ ] Confirm SMS follow-up is sent
- [ ] Check call appears in admin dashboard

### 4.3 Security Verification
- [ ] Admin endpoints require API key
- [ ] Twilio webhooks validate signatures
- [ ] No credentials exposed in logs

---

## **🎉 Deployment Complete!**

**Your A Killion Voice system is now:**
- ✅ **Secure** - No hard-coded credentials, webhook validation, API authentication
- ✅ **Scalable** - Per-call state isolation, concurrent call support
- ✅ **Professional** - Smart routing, SMS follow-up, call analytics
- ✅ **Production-Ready** - Health monitoring, error handling, logging

**Phone:** (978) 643-2034  
**Website:** https://akillionvoice.xyz  
**API:** https://api.akillionvoice.xyz

---

## **🔧 Troubleshooting**

**If calls don't work:**
1. Check Twilio webhook URLs are correct
2. Verify environment variables in Render
3. Check health endpoint shows all services configured

**If SMS doesn't send:**
1. Verify TWILIO_AUTH_TOKEN is set
2. Check Twilio account has SMS enabled
3. Review logs in Render dashboard

**For support:** Check logs in Render dashboard → Your Service → Logs

