# LLM Optimization Guide for Voice Conversations

## Overview

This guide explains how to enhance your LLM-based voice agent for more natural, intelligent conversations.

## Key Improvements Implemented

### 1. **Conversation State Management**
- Tracks context across turns
- Remembers key facts mentioned
- Manages topic switches
- Handles interruptions gracefully

### 2. **Enhanced Models**
```bash
# In your .env file:

# Use better models for conversation quality
CONVERSATION_MODEL=anthropic/claude-3-sonnet  # Or gpt-4-turbo
ANALYSIS_MODEL=openai/gpt-4o-mini  # Fast for intent analysis
```

### 3. **Dynamic Response Generation**
- Adjusts temperature based on conversation phase
- Shorter responses for natural speech (120 tokens max)
- Phase-aware prompting (greeting → discovery → resolution → closing)

### 4. **Interruption Handling**
- Detects when users interrupt
- Acknowledges and pivots quickly
- Maintains conversation flow

### 5. **Sentiment-Aware Responses**
- Tracks sentiment over recent turns
- Adjusts tone accordingly
- Extra empathy for frustrated callers

## Quick Start

### 1. Update Your Environment
```bash
# .env file additions
CONVERSATION_MODEL=anthropic/claude-3-sonnet
ANALYSIS_MODEL=openai/gpt-4o-mini
USE_COQUI=true
OPTIMIZE_FOR_TWILIO=true
```

### 2. Install Dependencies
```bash
# For Coqui TTS
pip install -r requirements-ml.txt

# For better models (if using Anthropic)
pip install anthropic
```

### 3. Update Your Call Session
```python
# In src/services/call_session.py, replace:
from src.services.agent_brain import AgentBrain

# With:
from src.services.enhanced_agent_brain import enhanced_agent_brain
```

## Conversation Quality Tips

### 1. **Better Prompting**
```python
# Example agent configuration with enhanced prompting
agent_config = {
    "name": "Sarah",
    "role": "Customer Support Specialist",
    "system_prompt": """You are Sarah, a friendly customer support specialist.
    
PERSONALITY:
- Warm and empathetic
- Solution-focused
- Patient listener

CONVERSATION STYLE:
- Use the customer's name when you learn it
- Mirror their communication style
- Acknowledge emotions before solving problems
- Ask one question at a time

KNOWLEDGE:
- Product details: [Your product info]
- Common issues: [Common problems and solutions]
- Escalation: Transfer to supervisor for billing over $100"""
}
```

### 2. **Handle Common Scenarios**

#### Frustrated Customer
```python
# The system automatically detects negative sentiment and adjusts:
# - Lower temperature for consistency
# - More empathetic language
# - Acknowledgment before solutions
```

#### Interruptions
```python
# System detects and handles:
# - "Actually, wait..."
# - "No, that's not..."
# - Quick corrections
```

#### Multiple Topics
```python
# Topic stack management:
# - Tracks topic switches
# - Can return to previous topics
# - Maintains context for each
```

### 3. **Voice-Specific Optimizations**

#### Natural Speech Patterns
- Automatic contraction conversion (I will → I'll)
- Removes formal language
- Adds natural pauses
- Limits to 1-2 sentences

#### Phone Call Awareness
- No lists or bullet points
- No technical jargon
- Simple, clear language
- Confirmation phrases

## Testing Your Enhanced System

### 1. Test Coqui TTS
```bash
python scripts/test_coqui_tts.py
```

### 2. Test Conversation Flow
```python
# Create test scenarios:
test_conversations = [
    # Interruption test
    ("Actually wait, I meant my billing account", 0.3),  # 0.3s after AI speaks
    
    # Sentiment test
    ("This is ridiculous! I've been waiting for hours!", None),
    
    # Topic switch test
    ("That's fine, but what about my refund?", None),
]
```

### 3. Monitor Performance
```python
# Check metadata from responses:
response, metadata = enhanced_agent_brain.process_conversation(...)
print(f"Phase: {metadata['phase']}")
print(f"Sentiment: {metadata['sentiment']}")
print(f"Generation time: {metadata['generation_time']}")
```

## Production Checklist

- [ ] Install Coqui TTS dependencies
- [ ] Configure better LLM models
- [ ] Update call session to use enhanced brain
- [ ] Test with real phone calls
- [ ] Monitor conversation quality metrics
- [ ] Adjust prompts based on feedback

## Advanced Features

### 1. **Goal Tracking Integration**
```python
# Integrate with goal_manager.py for outcome tracking
from server.services.goal_manager import GoalManager

# Track conversation goals
goal_manager.track_conversation_goal(call_sid, "schedule_appointment")
```

### 2. **Knowledge Base Integration**
```python
# Use knowledge base for domain expertise
from server.services.knowledge_base import KnowledgeBase

# Inject relevant knowledge into prompts
context = knowledge_base.get_context_for_conversation(agent_id, user_query)
```

### 3. **Voice Profile Customization**
```python
# Create custom voice profiles
coqui_service.create_voice_profile(
    audio_path="path/to/voice_sample.wav",
    profile_name="friendly_support"
)
```

## Troubleshooting

### Issue: Responses Too Long
- Reduce `max_tokens` to 80-100
- Add explicit instruction: "Keep responses under 15 words"

### Issue: Too Formal
- Check temperature (should be 0.7-0.8)
- Ensure contraction conversion is working
- Add personality traits to prompt

### Issue: Slow Generation
- Use faster models for analysis
- Implement response caching
- Reduce conversation history to last 6-8 turns

### Issue: Doesn't Handle Interruptions
- Check interruption threshold timing
- Ensure WebSocket events are fast
- Test with realistic delays