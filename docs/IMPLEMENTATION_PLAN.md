# Voice Agent Customization Implementation Plan

## Overview
This plan transforms the existing voice agent system into a fully customizable platform supporting flexible agents with variable goals, instructions, and domain expertise while maintaining low-latency, empathetic voice interactions.

## Phase 1: Database Schema Enhancement (Week 1)

### 1.1 Enhanced Agent Configuration
```sql
-- New tables to add
CREATE TABLE agent_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_prompt TEXT,
    voice_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversation_goals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    success_criteria JSONB,
    required_data JSONB,
    completion_webhook TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_instructions (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agent_configs(id),
    instruction_type VARCHAR(50), -- 'do' or 'dont'
    instruction TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true
);

CREATE TABLE domain_knowledge (
    id SERIAL PRIMARY KEY,
    domain_name VARCHAR(255) NOT NULL,
    knowledge_type VARCHAR(50), -- 'fact', 'process', 'policy'
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_goals (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agent_configs(id),
    goal_id INTEGER REFERENCES conversation_goals(id),
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true
);

CREATE TABLE agent_domains (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agent_configs(id),
    domain_id INTEGER REFERENCES domain_knowledge(id)
);

-- Modify existing agent_configs table
ALTER TABLE agent_configs ADD COLUMN template_id INTEGER REFERENCES agent_templates(id);
ALTER TABLE agent_configs ADD COLUMN custom_settings JSONB;
```

### 1.2 Implementation Files
- `server/models/enhanced_models.py` - New SQLAlchemy models
- `server/migrations/` - Alembic migrations

## Phase 2: Agent Management API (Week 1-2)

### 2.1 RESTful API Endpoints
```python
# server/routes/agent_management.py

# Agent CRUD
POST   /api/agents                 # Create new agent
GET    /api/agents                 # List all agents
GET    /api/agents/{id}           # Get agent details
PUT    /api/agents/{id}           # Update agent
DELETE /api/agents/{id}           # Delete agent

# Templates
GET    /api/agents/templates      # List templates
POST   /api/agents/templates      # Create template

# Goals
POST   /api/agents/{id}/goals    # Assign goals
DELETE /api/agents/{id}/goals/{goal_id}

# Instructions
POST   /api/agents/{id}/instructions
PUT    /api/agents/{id}/instructions/{instruction_id}
DELETE /api/agents/{id}/instructions/{instruction_id}

# Domain Knowledge
POST   /api/domains               # Create domain
POST   /api/agents/{id}/domains  # Assign domain
```

### 2.2 Agent Builder Service
```python
# server/services/agent_builder.py
class AgentBuilder:
    def create_agent(self, template_id, customizations):
        """Create new agent from template with customizations"""
        
    def compile_system_prompt(self, agent_id):
        """Combine base prompt + instructions + domain knowledge"""
        
    def validate_agent_config(self, config):
        """Ensure agent has required components"""
```

## Phase 3: Goal & Instruction System (Week 2)

### 3.1 Goal Management
```python
# server/services/goal_manager.py
class GoalManager:
    def __init__(self):
        self.active_goals = {}
    
    def start_conversation(self, call_id, agent_id):
        """Initialize goals for conversation"""
        
    def track_progress(self, call_id, conversation_data):
        """Monitor goal completion"""
        
    def check_completion(self, call_id):
        """Evaluate if goals are met"""
        
    def get_next_action(self, call_id):
        """Suggest next conversation step"""
```

### 3.2 Dynamic Instruction Engine
```python
# server/services/instruction_engine.py
class InstructionEngine:
    def get_active_instructions(self, agent_id, context):
        """Get relevant instructions for current context"""
        
    def format_for_prompt(self, instructions):
        """Format instructions for LLM prompt"""
        
    def validate_response(self, response, instructions):
        """Check if response follows instructions"""
```

## Phase 4: Fix Chatterbox TTS Integration (Week 2-3)

### 4.1 Chatterbox Service Enhancement
```python
# server/services/chatterbox_service.py
class EnhancedChatterboxService:
    def __init__(self):
        self.model_cache = {}
        self.voice_profiles = {}
        
    def preload_models(self):
        """Preload models on startup to reduce latency"""
        
    def create_voice_profile(self, agent_id, voice_samples):
        """Create custom voice for agent"""
        
    def synthesize_with_emotion(self, text, emotion, agent_id):
        """Generate speech with specific emotion"""
        
    def optimize_for_twilio(self, audio):
        """Optimize audio for phone quality"""
```

### 4.2 Voice Profile Management
```python
# server/services/voice_manager.py
class VoiceProfileManager:
    def clone_voice(self, audio_samples, agent_id):
        """Create voice clone from samples"""
        
    def adjust_prosody(self, agent_id, settings):
        """Fine-tune voice characteristics"""
        
    def test_voice(self, agent_id, test_phrases):
        """Generate test samples for review"""
```

## Phase 5: Domain Knowledge System (Week 3)

### 5.1 Knowledge Base Integration
```python
# server/services/knowledge_base.py
class KnowledgeBase:
    def __init__(self):
        self.vector_store = None  # For semantic search
        
    def add_knowledge(self, domain, content, metadata):
        """Add knowledge to database"""
        
    def search_relevant(self, query, domain):
        """Find relevant knowledge for query"""
        
    def inject_context(self, prompt, relevant_knowledge):
        """Add knowledge to conversation context"""
```

### 5.2 Context Management
```python
# server/services/context_manager.py
class ContextManager:
    def build_context(self, agent_id, conversation_history):
        """Build comprehensive context for LLM"""
        
    def get_domain_context(self, agent_id, topic):
        """Retrieve domain-specific context"""
        
    def update_context(self, call_id, new_info):
        """Update conversation context dynamically"""
```

## Phase 6: Performance Optimization (Week 3-4)

### 6.1 Latency Monitoring
```python
# server/services/performance_monitor.py
class PerformanceMonitor:
    def track_latency(self, operation, duration):
        """Track operation latencies"""
        
    def get_metrics(self):
        """Get performance metrics"""
        
    def identify_bottlenecks(self):
        """Find slow operations"""
```

### 6.2 Caching Strategy
- Implement Redis for:
  - Compiled prompts
  - Voice profiles
  - Domain knowledge
  - Active conversations

## Phase 7: Agent Customization UI (Week 4)

### 7.1 React Components
```typescript
// client/src/components/AgentBuilder/
- AgentForm.tsx          // Main form
- GoalSelector.tsx       // Goal assignment
- InstructionEditor.tsx  // Do's and don'ts
- DomainPicker.tsx      // Domain selection
- VoiceConfigurator.tsx // Voice settings
- TestConsole.tsx       // Test agent
```

### 7.2 API Integration
```typescript
// client/src/services/agentService.ts
export class AgentService {
    createAgent(config: AgentConfig): Promise<Agent>
    updateAgent(id: string, updates: Partial<AgentConfig>): Promise<Agent>
    testAgent(id: string, scenario: TestScenario): Promise<TestResult>
}
```

## Implementation Timeline

### Week 1: Foundation
- [ ] Database schema updates
- [ ] Basic agent CRUD API
- [ ] Migration scripts

### Week 2: Core Systems
- [ ] Goal management system
- [ ] Instruction engine
- [ ] Start Chatterbox fixes

### Week 3: Advanced Features
- [ ] Complete Chatterbox integration
- [ ] Domain knowledge system
- [ ] Performance monitoring

### Week 4: UI & Polish
- [ ] Agent builder UI
- [ ] Testing interface
- [ ] Documentation

## Testing Strategy

### 1. Unit Tests
```python
# tests/test_agent_builder.py
def test_agent_creation()
def test_prompt_compilation()
def test_goal_tracking()
```

### 2. Integration Tests
```python
# tests/test_call_flow.py
def test_full_conversation_flow()
def test_goal_completion()
def test_voice_generation()
```

### 3. Performance Tests
```python
# tests/test_performance.py
def test_latency_requirements()
def test_concurrent_calls()
```

## Configuration Examples

### 1. Appointment Scheduling Agent
```json
{
  "name": "Appointment Scheduler",
  "template_id": 1,
  "goals": [
    {
      "name": "schedule_appointment",
      "success_criteria": {
        "has_date": true,
        "has_time": true,
        "has_service": true
      }
    }
  ],
  "instructions": {
    "dos": [
      "Be friendly and accommodating",
      "Offer multiple time slots",
      "Confirm details before ending"
    ],
    "donts": [
      "Don't pressure for immediate booking",
      "Don't discuss pricing"
    ]
  },
  "domain": "medical_appointments",
  "voice": {
    "emotion_default": "friendly",
    "speed": 1.0,
    "pitch": 0
  }
}
```

### 2. Lead Qualification Agent
```json
{
  "name": "Sales Qualifier",
  "template_id": 2,
  "goals": [
    {
      "name": "qualify_lead",
      "success_criteria": {
        "budget_identified": true,
        "timeline_identified": true,
        "decision_maker": true
      }
    }
  ],
  "instructions": {
    "dos": [
      "Ask open-ended questions",
      "Listen actively",
      "Take detailed notes"
    ],
    "donts": [
      "Don't be pushy",
      "Don't make promises"
    ]
  },
  "domain": "b2b_software_sales",
  "voice": {
    "emotion_default": "professional",
    "speed": 0.95,
    "pitch": -1
  }
}
```

## Deployment Considerations

### 1. Environment Variables
```bash
# .env additions
CHATTERBOX_MODEL_PATH=/models/chatterbox
REDIS_URL=redis://localhost:6379
VECTOR_DB_URL=postgresql://...
MAX_CONCURRENT_CALLS=100
VOICE_CACHE_SIZE=50
```

### 2. Infrastructure
- Redis for caching
- PostgreSQL with pgvector for knowledge base
- GPU server for Chatterbox TTS
- CDN for voice profile storage

### 3. Monitoring
- Datadog/New Relic for APM
- Custom dashboard for agent performance
- Call quality metrics

## Success Metrics

1. **Latency**: < 500ms response time
2. **Goal Completion**: > 80% success rate
3. **Voice Quality**: > 4.5/5 user rating
4. **Customization Time**: < 10 minutes to create new agent
5. **Concurrent Capacity**: 100+ simultaneous calls

## Next Steps

1. Review and approve plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Weekly progress reviews
5. Continuous testing and optimization