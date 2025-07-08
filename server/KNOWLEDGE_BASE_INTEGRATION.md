# Knowledge Base Integration Documentation

## Overview
This document describes how the Knowledge Base system has been integrated with the voice agent conversation processing system. The integration allows agents to access domain-specific knowledge during conversations, providing more accurate and contextual responses.

## Integration Points

### 1. Conversation Processing Integration

#### Enhanced Agent Brain (`src/services/enhanced_agent_brain.py`)
The enhanced agent brain now accepts an optional database session and automatically injects relevant knowledge context:

```python
def process_conversation(
    self, 
    user_input: str, 
    call_sid: str,
    agent_config: Dict[str, Any],
    conversation_history: List[str],
    db_session: Optional[Session] = None  # New parameter
) -> Tuple[str, Dict[str, Any]]:
```

**Key Features:**
- Automatically queries knowledge base when database session is provided
- Injects relevant knowledge as system context before generating response
- Tracks knowledge injection status in response metadata
- Configurable max tokens for knowledge context (default: 500)

#### Basic Agent Brain (`src/services/agent_brain.py`)
The basic agent brain also supports knowledge injection with a simpler interface:

```python
def process_conversation(
    self, 
    user_input: str, 
    conversation_history: List[str], 
    agent_id: Optional[int] = None,     # New parameter
    db_session: Optional[Session] = None # New parameter
) -> str:
```

### 2. Agent Builder Integration

#### System Prompt Compilation (`server/services/agent_builder.py`)
The agent builder now includes knowledge domain references in the compiled system prompt:

```python
def compile_system_prompt(self, db: Session, agent_id: int) -> str:
    # ... existing code ...
    
    # Add domain knowledge context
    domains = self._get_agent_domains(db, agent_id)
    if domains:
        prompt_parts.append("\n## Knowledge Base Access:")
        prompt_parts.append("You have access to information about:")
        for domain in domains:
            prompt_parts.append(f"- {domain['name']}")
        prompt_parts.append("Use this knowledge to provide accurate, detailed responses.")
```

This ensures agents are aware of their available knowledge domains and are instructed to use them.

## Usage Examples

### 1. Processing a Conversation with Knowledge

```python
from src.services.enhanced_agent_brain import EnhancedAgentBrain
from src.models.database import get_db

# Initialize brain
brain = EnhancedAgentBrain()

# Get database session
db = next(get_db())

# Agent configuration
agent_config = {
    'id': 1,
    'name': 'Customer Support Agent',
    'system_prompt': 'You are a helpful customer support agent.'
}

# Process conversation with knowledge injection
response, metadata = brain.process_conversation(
    user_input="What's your return policy?",
    call_sid="call_123",
    agent_config=agent_config,
    conversation_history=["Hello", "Hi, how can I help you?"],
    db_session=db  # Pass database session to enable knowledge injection
)

# Check if knowledge was injected
if metadata['knowledge_injected']:
    print("Knowledge context was used for this response")
```

### 2. Creating an Agent with Knowledge Domains

```python
from server.services.agent_builder import AgentBuilder
from server.models.enhanced_models import AgentDomain

builder = AgentBuilder()

# Create agent
agent = builder.create_agent(
    db=db,
    name="Support Agent",
    template_id=1,
    customizations={'personality_traits': ['helpful', 'knowledgeable']}
)

# Link to knowledge domain
agent_domain = AgentDomain(
    agent_id=agent.id,
    domain_id=knowledge_domain.id,  # ID of existing domain knowledge
    relevance_score=0.95
)
db.add(agent_domain)
db.commit()

# Compile prompt (will include domain references)
prompt = builder.compile_system_prompt(db, agent.id)
```

### 3. Integration in Call Processing Flow

```python
# Example integration in a call processor or WebSocket handler
class CallProcessor:
    def __init__(self):
        self.brain = EnhancedAgentBrain()
    
    def handle_message(self, call_id: str, message: str, agent_id: int):
        # Get database session
        db = next(get_db())
        
        try:
            # Get agent configuration
            agent = db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
            
            agent_config = {
                'id': agent.id,
                'name': agent.name,
                'system_prompt': agent.system_prompt
            }
            
            # Process with knowledge injection
            response, metadata = self.brain.process_conversation(
                user_input=message,
                call_sid=call_id,
                agent_config=agent_config,
                conversation_history=self.get_history(call_id),
                db_session=db  # Enable knowledge injection
            )
            
            return response
            
        finally:
            db.close()
```

## Configuration

### Knowledge Context Limits
- Enhanced Agent Brain: 500 tokens max (configurable)
- Basic Agent Brain: 300 tokens max (configurable)

### Performance Considerations
- Knowledge queries add ~100-200ms latency
- Use connection pooling for database sessions
- Consider caching frequently accessed knowledge

### Fallback Behavior
- If knowledge base is unavailable, conversation continues without it
- Errors are logged but don't interrupt conversation flow
- Metadata indicates whether knowledge was successfully injected

## Database Schema Requirements

The integration expects the following relationships:
- `enhanced_agent_configs` → `agent_domains` → `domain_knowledge`
- Active domain knowledge entries with embeddings
- Proper relevance scoring in `agent_domains` table

## Testing

Run integration tests:
```bash
pytest server/tests/test_knowledge_integration.py
```

Key test scenarios:
1. Agent prompt compilation with domains
2. Knowledge context injection during conversation
3. Fallback when knowledge base unavailable
4. Multiple domain handling
5. Relevance-based knowledge selection

## Migration Guide

To add knowledge integration to existing agents:

1. **Install dependencies:**
   ```bash
   pip install -r requirements-ml.txt
   ```

2. **Run database migrations:**
   ```bash
   psql -d your_database -f server/migrations/add_pgvector_support.sql
   ```

3. **Update agent configurations:**
   - Link agents to relevant knowledge domains
   - Recompile agent prompts to include domain references

4. **Update conversation handlers:**
   - Pass database session to `process_conversation`
   - For enhanced brain: Include agent ID in config
   - For basic brain: Pass agent_id parameter

## Troubleshooting

### Knowledge not being injected
- Verify agent has linked domains: Check `agent_domains` table
- Ensure domain knowledge is active: `active = true` in `domain_knowledge`
- Check embeddings exist: `embedding_vector` should not be null
- Review logs for errors during knowledge retrieval

### Performance issues
- Index domain_name in `domain_knowledge` table
- Use pgvector indexes for embedding searches
- Limit knowledge context tokens appropriately
- Consider async knowledge retrieval for better response times

### Import errors
- Ensure proper Python path configuration
- Install all required dependencies
- Check for circular imports between src/ and server/ modules