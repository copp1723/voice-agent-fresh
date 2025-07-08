# Vector Database and Semantic Search Guide

This guide explains how to set up and use the vector database functionality for semantic search in the voice agent system.

## Overview

The vector database system provides semantic search capabilities using sentence transformers and vector embeddings. This allows agents to find relevant knowledge even when queries don't match exact keywords.

## Features

- **Semantic Search**: Find relevant content based on meaning, not just keywords
- **Multi-Domain Support**: Search across different knowledge domains
- **PostgreSQL + pgvector**: Efficient vector similarity search for production
- **SQLite Fallback**: In-memory search for development and testing
- **Context Injection**: Automatically enhance agent responses with relevant knowledge

## Setup

### 1. Install Dependencies

```bash
pip install sentence-transformers psycopg2-binary
```

### 2. Database Setup

#### Option A: PostgreSQL with pgvector (Recommended for Production)

1. Install PostgreSQL and pgvector extension
2. Create database and enable extension:
   ```sql
   CREATE DATABASE voice_agent;
   \c voice_agent;
   CREATE EXTENSION vector;
   ```
3. Run the migration:
   ```bash
   psql -d voice_agent -f server/migrations/add_pgvector_support.sql
   ```
4. Set environment variable:
   ```bash
   export DATABASE_URL='postgresql://username:password@localhost/voice_agent'
   ```

#### Option B: SQLite (Development/Testing)

The system will automatically use SQLite if no DATABASE_URL is set. Vector search will use in-memory similarity calculations.

### 3. Initialize Knowledge Base

```python
from sqlalchemy.orm import Session
from server.services.knowledge_base import KnowledgeBase

# Initialize
db = Session()  # Your database session
kb = KnowledgeBase(db)

# Add knowledge
kb.add_knowledge(
    domain="billing",
    content="Customers can cancel subscriptions through the account portal",
    metadata={"category": "cancellation", "tags": ["refund", "cancel"]}
)
```

## Usage Examples

### Basic Search

```python
from server.services.vector_search_service import VectorSearchService

# Initialize service
search_service = VectorSearchService(db)

# Search within a domain
results = search_service.search_by_domain(
    domain="billing",
    query="How do I get my money back?",
    top_k=5
)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Content: {result['content']}")
```

### Agent-Specific Search

```python
# Search knowledge specific to an agent
agent_results = search_service.search_agent_knowledge(
    agent_id=1,
    query="password reset help",
    top_k=3
)
```

### Multi-Domain Search

```python
# Search across multiple domains
results = search_service.multi_domain_search(
    query="I need help with my account",
    domains=["support", "billing", "sales"],
    top_k=10
)
```

### Context Enhancement

```python
# Get conversation context for an agent
context = search_service.get_conversation_context(
    agent_id=1,
    conversation_text="User is asking about refunds and having login issues",
    max_tokens=1000
)

# Enhanced prompt with context
enhanced_prompt = f"""
You are a customer service agent.

{context}

User: {user_message}
"""
```

## Integration with Agent Brain

### Enhance Agent Responses

```python
from server.services.vector_search_service import enhance_agent_response

# In your agent processing logic
def process_agent_message(agent_id, user_message):
    # Get relevant context
    context = enhance_agent_response(db, agent_id, user_message)
    
    # Create enhanced prompt
    system_prompt = agent.system_prompt + context
    
    # Generate response with LLM
    response = generate_llm_response(system_prompt, user_message)
    
    return response
```

### Automatic Context Injection

```python
def create_contextual_prompt(agent_id, user_message, base_prompt):
    search_service = VectorSearchService(db)
    
    # Get top 3 most relevant knowledge entries
    search_results = search_service.search_agent_knowledge(
        agent_id=agent_id,
        query=user_message,
        top_k=3
    )
    
    # Only include highly relevant results
    relevant_results = [r for r in search_results if r['score'] > 0.75]
    
    if relevant_results:
        context_parts = []
        for result in relevant_results:
            context_parts.append(f"[{result['domain']}] {result['content']}")
        
        context = "\n".join(context_parts)
        return f"{base_prompt}\n\nRelevant Information:\n{context}"
    
    return base_prompt
```

## Knowledge Management

### Adding Knowledge

```python
# Add single entry
knowledge_id = search_service.add_knowledge_entry(
    domain="support",
    content="To reset password, click 'Forgot Password' on login page",
    metadata={"category": "account", "difficulty": "easy"}
)

# Bulk import
entries = [
    {"content": "FAQ answer 1", "metadata": {"type": "faq"}},
    {"content": "FAQ answer 2", "metadata": {"type": "faq"}},
]
success, failed = search_service.bulk_import("support", entries)
```

### Updating Knowledge

```python
# Update existing entry
success = search_service.update_knowledge_entry(
    knowledge_id=123,
    content="Updated content here",
    metadata={"updated": True}
)
```

## Performance Optimization

### Using pgvector

For production deployments, use PostgreSQL with pgvector:

1. **Efficient similarity search**: Uses specialized vector indexes
2. **Scalable**: Handles large knowledge bases efficiently
3. **ACID compliance**: Transactional consistency

Example pgvector query:
```sql
SELECT content, metadata, 
       1 - (embedding <-> %s) as similarity
FROM domain_knowledge
WHERE domain_name = %s AND active = true
ORDER BY similarity DESC
LIMIT %s
```

### Embedding Model Selection

The default model `all-MiniLM-L6-v2` provides good balance of speed and accuracy:

- **Dimension**: 384
- **Speed**: Fast inference
- **Quality**: Good for most use cases

For better accuracy, consider:
- `all-mpnet-base-v2` (768 dimensions)
- `all-distilroberta-v1` (768 dimensions)

## Testing

Run the test script to verify functionality:

```bash
python scripts/test_vector_search.py
```

This will:
1. Create sample knowledge entries
2. Test semantic search functionality
3. Demonstrate context retrieval
4. Show embedding regeneration

## API Integration

### REST API Example

```python
@app.route('/api/search', methods=['POST'])
def search_knowledge():
    data = request.get_json()
    
    search_service = VectorSearchService(db)
    results = search_service.search_by_domain(
        domain=data['domain'],
        query=data['query'],
        top_k=data.get('top_k', 5)
    )
    
    return jsonify(results)
```

### WebSocket Integration

```python
@socketio.on('search_knowledge')
def handle_search(data):
    search_service = VectorSearchService(db)
    results = search_service.search_agent_knowledge(
        agent_id=data['agent_id'],
        query=data['query']
    )
    
    emit('search_results', results)
```

## Best Practices

1. **Relevance Threshold**: Use score thresholds (0.7-0.8) to filter low-relevance results
2. **Context Size**: Limit context to ~1000 tokens to avoid overwhelming the LLM
3. **Domain Organization**: Structure knowledge by domain for better search precision
4. **Regular Updates**: Regenerate embeddings when changing models or updating content
5. **Monitoring**: Track search performance and relevance scores

## Troubleshooting

### Common Issues

1. **pgvector not found**: Ensure PostgreSQL has pgvector extension installed
2. **Slow searches**: Check if vector indexes are created properly
3. **Poor results**: Verify embedding model is appropriate for your content
4. **Memory issues**: Consider using a smaller embedding model

### Performance Monitoring

```python
import time

def timed_search(search_service, query, domain):
    start = time.time()
    results = search_service.search_by_domain(domain, query)
    duration = time.time() - start
    
    print(f"Search took {duration:.3f}s, found {len(results)} results")
    return results
```

## Migration from Existing Systems

If you have existing knowledge in other formats:

1. **CSV Import**: Use pandas to read CSV and bulk import
2. **JSON Import**: Parse JSON files and extract content
3. **Database Migration**: Query existing tables and transform data

Example migration script:
```python
def migrate_existing_knowledge(old_db, new_kb):
    # Query existing knowledge
    old_entries = old_db.query("SELECT * FROM old_knowledge_table")
    
    # Transform and import
    for entry in old_entries:
        new_kb.add_knowledge(
            domain=entry['category'],
            content=entry['text'],
            metadata={'migrated': True, 'source': 'old_system'}
        )
```

This vector search system provides a powerful foundation for intelligent agent responses based on semantic understanding of your knowledge base.