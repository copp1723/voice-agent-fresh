"""
Integration example for Knowledge Management API Routes

This file shows how to integrate the knowledge management routes into your Flask application.
"""

# Add this to your main application file (e.g., src/main.py) where blueprints are registered:

# 1. Import the blueprints
from server.routes.knowledge_management import knowledge_bp, domains_bp

# 2. In your create_app() function, after other blueprint registrations:
def integrate_knowledge_routes(app):
    """
    Register knowledge management blueprints with the Flask application
    
    Args:
        app: Flask application instance
    """
    # Register knowledge management blueprint
    app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
    
    # Register domains management blueprint
    app.register_blueprint(domains_bp, url_prefix='/api/domains')
    
    print("✅ Knowledge Management routes registered:")
    print("   - /api/knowledge/* - Knowledge CRUD operations")
    print("   - /api/domains/* - Domain management")


# Example of complete integration in your create_app function:
"""
def create_app(config_name=None):
    app = Flask(__name__)
    
    # ... your existing configuration ...
    
    # Initialize database
    init_database(app)
    
    # Register existing blueprints
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(voice_bp, url_prefix='/')
    # ... other blueprints ...
    
    # Add knowledge management routes
    from server.routes.knowledge_management import knowledge_bp, domains_bp
    app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
    app.register_blueprint(domains_bp, url_prefix='/api/domains')
    
    return app
"""

# API Endpoints Available After Integration:
"""
Knowledge CRUD:
- POST   /api/knowledge                    - Add knowledge entry
- GET    /api/knowledge                    - List knowledge (with filtering)
- GET    /api/knowledge/<id>               - Get specific knowledge
- PUT    /api/knowledge/<id>               - Update knowledge
- DELETE /api/knowledge/<id>               - Deactivate knowledge

Bulk Operations:
- POST   /api/knowledge/import             - Import from CSV/JSON
- POST   /api/knowledge/generate-embeddings - Regenerate embeddings
- GET    /api/knowledge/export-template/<format> - Get import template

Domain Management:
- GET    /api/domains                      - List all domains
- POST   /api/domains                      - Create new domain

Query Parameters for GET /api/knowledge:
- domain: Filter by domain name
- active: Filter active/inactive (default: true)
- type: Filter by knowledge type
- search: Semantic search within domain
- limit: Number of results (default: 100)
- offset: Pagination offset (default: 0)
"""

# Example Usage with curl:
"""
# Create a domain
curl -X POST http://localhost:5000/api/domains \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "customer_support",
    "description": "Customer support knowledge base",
    "initial_knowledge": [{
      "content": "Our support hours are 9 AM to 5 PM EST",
      "title": "Support Hours",
      "knowledge_type": "fact"
    }]
  }'

# Add knowledge
curl -X POST http://localhost:5000/api/knowledge \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "domain_name": "customer_support",
    "content": "To reset your password, click on the forgot password link on the login page",
    "knowledge_type": "faq",
    "title": "Password Reset Process",
    "tags": ["password", "account", "security"]
  }'

# Search knowledge
curl -X GET "http://localhost:5000/api/knowledge?domain=customer_support&search=password" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Import knowledge from CSV
curl -X POST http://localhost:5000/api/knowledge/import \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@knowledge.csv" \
  -F "domain_name=customer_support"
"""

# Integration with Agent System:
"""
The knowledge base integrates with agents through the get_context_for_conversation method.
When processing conversations, inject relevant knowledge like this:

from server.services.knowledge_base import KnowledgeBase

# In your conversation processing logic:
def process_agent_message(agent_id, message):
    db = next(get_db())
    kb = KnowledgeBase(db)
    
    # Get relevant knowledge for the conversation
    knowledge_context = kb.get_context_for_conversation(
        agent_id=agent_id,
        conversation_text=message,
        max_tokens=1000
    )
    
    # Add to agent's prompt
    if knowledge_context:
        enhanced_prompt = f"{agent.system_prompt}\\n\\nRelevant Information:\\n{knowledge_context}"
    
    # Continue with LLM call using enhanced prompt
"""

if __name__ == "__main__":
    print(__doc__)