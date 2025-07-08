#!/usr/bin/env python3
"""
Test script for vector database functionality with semantic search
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.services.knowledge_base import KnowledgeBase, EmbeddingService
from server.models.enhanced_models import DomainKnowledge
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """Set up database connection"""
    # Use SQLite for testing (you can change this to PostgreSQL)
    database_url = os.getenv('DATABASE_URL', 'sqlite:///test_vector.db')
    
    # If using PostgreSQL with pgvector:
    # database_url = 'postgresql://user:password@localhost/dbname'
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()


def demonstrate_vector_search():
    """Demonstrate vector database and semantic search functionality"""
    
    # Initialize database session
    db = setup_database()
    
    # Initialize embedding service and knowledge base
    embedding_service = EmbeddingService()
    kb = KnowledgeBase(db, embedding_service)
    
    print("\n=== Vector Database Demo ===\n")
    
    # Step 1: Add sample knowledge entries
    print("1. Adding knowledge entries...")
    
    sample_knowledge = [
        {
            "domain": "billing",
            "content": "Customers can cancel their subscription at any time through the account portal. Refunds are processed within 5-7 business days.",
            "metadata": {"category": "refunds", "tags": ["cancellation", "refund"]}
        },
        {
            "domain": "billing", 
            "content": "Our pricing plans include Basic ($9/month), Professional ($29/month), and Enterprise (custom pricing). All plans include 24/7 support.",
            "metadata": {"category": "pricing", "tags": ["plans", "pricing"]}
        },
        {
            "domain": "support",
            "content": "To reset your password, click on 'Forgot Password' on the login page. You'll receive a reset link via email within 5 minutes.",
            "metadata": {"category": "account", "tags": ["password", "reset"]}
        },
        {
            "domain": "support",
            "content": "If you're experiencing connection issues, try clearing your browser cache and cookies. Make sure you're using a supported browser.",
            "metadata": {"category": "troubleshooting", "tags": ["connection", "browser"]}
        },
        {
            "domain": "sales",
            "content": "New customers get a 30-day free trial with full access to all features. No credit card required to start your trial.",
            "metadata": {"category": "trial", "tags": ["free trial", "new customer"]}
        }
    ]
    
    for entry in sample_knowledge:
        knowledge = kb.add_knowledge(
            domain=entry["domain"],
            content=entry["content"],
            metadata=entry["metadata"]
        )
        print(f"   ✓ Added: {entry['domain']} - {entry['content'][:50]}...")
    
    print("\n2. Testing semantic search...")
    
    # Test queries
    test_queries = [
        ("billing", "How do I get my money back?"),
        ("billing", "What are the different subscription options?"),
        ("support", "I forgot my login credentials"),
        ("support", "The website isn't loading properly"),
        ("sales", "Can I try before buying?")
    ]
    
    for domain, query in test_queries:
        print(f"\n   Query: '{query}' in domain '{domain}'")
        results = kb.search_relevant(query, domain, top_k=3)
        
        for i, (knowledge, score) in enumerate(results):
            print(f"   Result {i+1} (similarity: {score:.3f}):")
            print(f"      {knowledge.content[:100]}...")
    
    print("\n3. Testing cross-domain context retrieval...")
    
    # Simulate a conversation context
    conversation_text = "I want to cancel my account and get a refund. Also having trouble logging in."
    
    # For this demo, we'll search across all domains
    all_results = []
    for domain in ["billing", "support", "sales"]:
        results = kb.search_relevant(conversation_text, domain, top_k=2)
        all_results.extend([(domain, k, s) for k, s in results])
    
    # Sort by relevance
    all_results.sort(key=lambda x: x[2], reverse=True)
    
    print(f"\n   Context for: '{conversation_text}'")
    for domain, knowledge, score in all_results[:5]:
        if score > 0.7:
            print(f"   [{domain}] (score: {score:.3f}): {knowledge.content[:80]}...")
    
    print("\n4. Testing embedding regeneration...")
    
    # Regenerate embeddings (useful if you change the embedding model)
    count = kb.regenerate_embeddings()
    print(f"   ✓ Regenerated {count} embeddings")
    
    print("\n=== Demo Complete ===\n")
    
    # Clean up
    db.close()


def demonstrate_pgvector_setup():
    """Show how to set up PostgreSQL with pgvector"""
    
    print("\n=== PostgreSQL with pgvector Setup ===\n")
    print("To use PostgreSQL with pgvector:")
    print("1. Install PostgreSQL and pgvector extension")
    print("2. Create database and enable extension:")
    print("   CREATE DATABASE voice_agent;")
    print("   \\c voice_agent;")
    print("   CREATE EXTENSION vector;")
    print("3. Run the migration:")
    print("   psql -d voice_agent -f server/migrations/add_pgvector_support.sql")
    print("4. Set DATABASE_URL environment variable:")
    print("   export DATABASE_URL='postgresql://username:password@localhost/voice_agent'")
    print("\nThe system will automatically use pgvector for efficient similarity search!")


if __name__ == "__main__":
    demonstrate_vector_search()
    demonstrate_pgvector_setup()