# Voice Agent Quick Start Guide

## Overview
This enhanced voice agent system now supports:
- ✅ **Phone call reception** via Twilio
- ✅ **Flexible agent customization** with templates
- ✅ **Variable conversation goals** (scheduling, qualification, support)
- ✅ **Variable instructions** (do's and don'ts)
- ✅ **Domain expertise** configuration
- ✅ **Low-latency Chatterbox TTS** with emotion support

## Getting Started

### 1. Database Setup
Run the migration to create enhanced agent tables:
```bash
cd server
psql -U your_user -d your_database -f migrations/add_enhanced_agent_tables.sql
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
npm install  # For frontend
```

### 3. Configure Environment
Add to your `.env`:
```bash
# Chatterbox TTS
CHATTERBOX_MODEL_PATH=/path/to/chatterbox/models
VOICE_CACHE_SIZE=50

# Redis (for caching)
REDIS_URL=redis://localhost:6379
```

### 4. Initialize Chatterbox
```python
from services.enhanced_chatterbox_service import chatterbox_service

# Initialize on startup
await chatterbox_service.initialize()
```

## Creating Custom Agents

### Option 1: Using API
```python
import requests

# Create appointment scheduler
agent_data = {
    "name": "Dr. Smith's Scheduler",
    "template_id": 1,  # Appointment Scheduler template
    "goals": [
        {"id": 1, "priority": 10, "required": True}  # Schedule Appointment
    ],
    "instructions": {
        "dos": [
            {"text": "Be warm and friendly", "category": "greeting"},
            {"text": "Offer morning and afternoon slots", "category": "scheduling"}
        ],
        "donts": [
            {"text": "Don't discuss medical advice", "category": "boundaries"},
            {"text": "Don't book outside office hours", "category": "scheduling"}
        ]
    },
    "domains": [1],  # Medical appointments domain
    "voice": {
        "provider": "chatterbox",
        "base_emotion": "friendly",
        "emotion_range": {
            "friendly": 0.7,
            "professional": 0.3
        }
    }
}

response = requests.post(
    "http://localhost:5000/api/agents",
    json=agent_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Option 2: Direct Database
```python
from services.agent_builder import AgentBuilder
from database import get_db

db = next(get_db())
builder = AgentBuilder()

# Create agent
agent = builder.create_agent(
    db=db,
    name="Sales Qualifier Pro",
    template_id=2,  # Lead Qualifier template
    customizations={
        "greeting_message": "Hi! I'm Sarah from SalesCo. I understand you're interested in our solutions?",
        "personality_traits": ["professional", "enthusiastic", "consultative"],
        "conversation_style": "balanced",
        "max_turns": 40
    }
)

# Add custom goal criteria
from models.enhanced_models import AgentGoal
goal = AgentGoal(
    agent_id=agent.id,
    goal_id=2,  # Qualify Lead goal
    priority=10,
    required=True,
    custom_criteria={
        "minimum_budget": 10000,
        "decision_timeframe": "3_months"
    }
)
db.add(goal)
db.commit()

# Compile system prompt
builder.compile_system_prompt(db, agent.id)
```

## Testing Your Agent

### 1. Test Conversation
```python
response = requests.post(
    f"http://localhost:5000/api/agents/{agent_id}/test",
    json={"input": "I need to schedule an appointment"},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### 2. Test Voice
```python
from services.enhanced_chatterbox_service import chatterbox_service

# Test different emotions
test_results = await chatterbox_service.test_voice(
    agent_id="dr_smith_scheduler",
    test_phrases=[
        "Hello! How can I help you today?",
        "I have appointments available tomorrow at 10 AM or 2 PM.",
        "Perfect! I've scheduled your appointment."
    ]
)
```

## Goal Tracking in Action

During a call, the system automatically:
1. Tracks data collection progress
2. Suggests next questions
3. Validates completion criteria
4. Triggers webhooks on goal completion

Example conversation flow:
```
Caller: "I need to schedule an appointment"
Agent: "I'd be happy to help! What service are you looking for?"
[Goal Manager: Tracking 'service_type' field]

Caller: "A dental cleaning"
Agent: "Great! What date works best for you?"
[Goal Manager: Collected 'service_type', now tracking 'date']

Caller: "Next Tuesday"
Agent: "What time would you prefer?"
[Goal Manager: Collected 'date', now tracking 'time']

Caller: "Morning if possible"
Agent: "I have 9 AM or 10:30 AM available. Which works better?"
[Goal Manager: Prompting for specific time]

Caller: "9 AM is perfect"
[Goal Manager: GOAL COMPLETED - All required fields collected]
```

## Voice Profile Creation

### Upload Voice Samples
```python
# Create custom voice from samples
result = await chatterbox_service.create_voice_profile(
    agent_id="custom_agent",
    voice_samples=[
        "/path/to/sample1.wav",
        "/path/to/sample2.wav",
        "/path/to/sample3.wav"
    ]
)
```

## Performance Monitoring

### Check System Status
```python
# API endpoint
GET /api/agents/{agent_id}/metrics

# Direct service call
stats = chatterbox_service.get_performance_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
print(f"Voice profiles loaded: {stats['voice_profiles']}")
```

## Common Use Cases

### 1. Appointment Scheduling
- Goal: Collect date, time, and service type
- Instructions: Be accommodating, offer multiple options
- Domain: Business-specific services and availability

### 2. Lead Qualification
- Goal: Identify budget, timeline, decision-maker
- Instructions: Ask open-ended questions, don't be pushy
- Domain: Product features, pricing tiers, competitors

### 3. Customer Support
- Goal: Resolve issue or escalate appropriately
- Instructions: Show empathy, gather details systematically
- Domain: Common issues, troubleshooting steps, policies

## Troubleshooting

### Chatterbox Model Loading Issues
1. Verify model files exist in `CHATTERBOX_MODEL_PATH`
2. Check file permissions
3. Ensure sufficient memory (4GB+ recommended)
4. View logs: `tail -f logs/chatterbox.log`

### Voice Quality Issues
1. Ensure voice samples are high quality (16kHz+, low noise)
2. Use at least 3-5 samples for voice cloning
3. Test different emotion settings
4. Adjust prosody settings in voice profile

### Goal Tracking Not Working
1. Verify goals are assigned to agent
2. Check success criteria configuration
3. Review conversation logs for data extraction
4. Ensure required fields match expected patterns

## Next Steps

1. **Create Domain Knowledge** (pending implementation)
   - Add FAQ responses
   - Import product/service information
   - Configure context-aware responses

2. **Build UI** (pending implementation)
   - Visual agent builder
   - Real-time conversation monitoring
   - Performance dashboards

3. **Production Deployment**
   - Set up Redis for caching
   - Configure GPU server for Chatterbox
   - Enable webhook endpoints
   - Set up monitoring (Datadog/New Relic)

## API Reference

See `/server/routes/agent_management.py` for full API documentation:
- `POST /api/agents` - Create agent
- `GET /api/agents/{id}` - Get agent details  
- `PUT /api/agents/{id}` - Update agent
- `POST /api/agents/{id}/goals` - Add goal
- `POST /api/agents/{id}/instructions` - Add instruction
- `POST /api/agents/{id}/test` - Test agent

## Support

For issues or questions:
1. Check logs in `/logs` directory
2. Review error messages in API responses
3. Consult the implementation plan for detailed architecture
4. Open an issue with reproduction steps