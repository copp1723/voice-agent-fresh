"""
Vector Search Service - High-level interface for semantic search functionality
"""

import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from server.services.knowledge_base import KnowledgeBase, EmbeddingService
from server.models.enhanced_models import DomainKnowledge, EnhancedAgentConfig

logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    Service for performing vector-based semantic searches across domain knowledge
    """
    
    def __init__(self, db: Session):
        """
        Initialize the vector search service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.embedding_service = EmbeddingService()
        self.knowledge_base = KnowledgeBase(db, self.embedding_service)
    
    def search_agent_knowledge(self, agent_id: int, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search relevant knowledge for a specific agent
        
        Args:
            agent_id: ID of the agent
            query: Search query text
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries containing search results
        """
        try:
            # Get agent configuration
            agent = self.db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
            if not agent:
                logger.error(f"Agent {agent_id} not found")
                return []
            
            # Get all domains associated with the agent
            agent_domains = [ad.domain.domain_name for ad in agent.domains if ad.domain]
            
            # Search across all agent's domains
            all_results = []
            for domain in set(agent_domains):
                results = self.knowledge_base.search_relevant(query, domain, top_k)
                for knowledge, score in results:
                    all_results.append({
                        'domain': domain,
                        'content': knowledge.content,
                        'metadata': knowledge.metadata,
                        'score': score,
                        'knowledge_id': knowledge.id
                    })
            
            # Sort by score and return top results
            all_results.sort(key=lambda x: x['score'], reverse=True)
            return all_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching agent knowledge: {e}")
            return []
    
    def search_by_domain(self, domain: str, query: str, top_k: int = 5, 
                        score_threshold: float = 0.7) -> List[Dict]:
        """
        Search within a specific domain
        
        Args:
            domain: Domain name to search in
            query: Search query text
            top_k: Number of top results to return
            score_threshold: Minimum similarity score to include
            
        Returns:
            List of dictionaries containing search results
        """
        try:
            results = self.knowledge_base.search_relevant(query, domain, top_k)
            
            # Filter by threshold and format results
            formatted_results = []
            for knowledge, score in results:
                if score >= score_threshold:
                    formatted_results.append({
                        'domain': domain,
                        'content': knowledge.content,
                        'metadata': knowledge.metadata,
                        'score': score,
                        'knowledge_id': knowledge.id,
                        'knowledge_type': knowledge.knowledge_type
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching domain {domain}: {e}")
            return []
    
    def multi_domain_search(self, query: str, domains: Optional[List[str]] = None, 
                           top_k: int = 10) -> List[Dict]:
        """
        Search across multiple domains
        
        Args:
            query: Search query text
            domains: List of domains to search (None = all domains)
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries containing search results
        """
        try:
            # Get all available domains if not specified
            if domains is None:
                domains_query = self.db.query(DomainKnowledge.domain_name).distinct()
                domains = [d[0] for d in domains_query.all()]
            
            # Search across all domains
            all_results = []
            for domain in domains:
                results = self.knowledge_base.search_relevant(query, domain, top_k=5)
                for knowledge, score in results:
                    all_results.append({
                        'domain': domain,
                        'content': knowledge.content,
                        'metadata': knowledge.metadata,
                        'score': score,
                        'knowledge_id': knowledge.id
                    })
            
            # Sort by score and return top results
            all_results.sort(key=lambda x: x['score'], reverse=True)
            return all_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in multi-domain search: {e}")
            return []
    
    def get_conversation_context(self, agent_id: int, conversation_text: str, 
                               max_tokens: int = 1000) -> str:
        """
        Get relevant context for a conversation
        
        Args:
            agent_id: ID of the agent
            conversation_text: Recent conversation text
            max_tokens: Maximum tokens to include in context
            
        Returns:
            Formatted context string
        """
        try:
            return self.knowledge_base.get_context_for_conversation(
                agent_id, conversation_text, max_tokens
            )
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return ""
    
    def add_knowledge_entry(self, domain: str, content: str, 
                           metadata: Optional[Dict] = None) -> Optional[int]:
        """
        Add a new knowledge entry
        
        Args:
            domain: Domain for the knowledge
            content: Knowledge content
            metadata: Optional metadata
            
        Returns:
            ID of created knowledge entry or None if failed
        """
        try:
            knowledge = self.knowledge_base.add_knowledge(domain, content, metadata)
            return knowledge.id if knowledge else None
        except Exception as e:
            logger.error(f"Error adding knowledge entry: {e}")
            return None
    
    def update_knowledge_entry(self, knowledge_id: int, content: Optional[str] = None,
                             metadata: Optional[Dict] = None) -> bool:
        """
        Update an existing knowledge entry
        
        Args:
            knowledge_id: ID of the knowledge entry
            content: New content (if provided)
            metadata: New metadata (if provided)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.knowledge_base.update_knowledge(knowledge_id, content, metadata)
            return result is not None
        except Exception as e:
            logger.error(f"Error updating knowledge entry: {e}")
            return False
    
    def bulk_import(self, domain: str, entries: List[Dict[str, any]]) -> Tuple[int, int]:
        """
        Bulk import knowledge entries
        
        Args:
            domain: Domain for all entries
            entries: List of entries to import
            
        Returns:
            Tuple of (successful_imports, failed_imports)
        """
        try:
            return self.knowledge_base.bulk_import_knowledge(domain, entries)
        except Exception as e:
            logger.error(f"Error in bulk import: {e}")
            return 0, len(entries)


# Example usage in existing routes
def enhance_agent_response(db: Session, agent_id: int, user_message: str) -> str:
    """
    Example of how to enhance agent responses with vector search
    
    Args:
        db: Database session
        agent_id: ID of the agent
        user_message: User's message
        
    Returns:
        Relevant context to inject into the agent's prompt
    """
    search_service = VectorSearchService(db)
    
    # Get relevant context
    context = search_service.get_conversation_context(agent_id, user_message)
    
    if context:
        return f"\n\nRelevant Information:\n{context}\n"
    return ""


# Integration example for the agent brain
def create_enhanced_prompt(base_prompt: str, user_message: str, 
                         search_results: List[Dict]) -> str:
    """
    Create an enhanced prompt with search results
    
    Args:
        base_prompt: Base system prompt
        user_message: User's message
        search_results: Results from vector search
        
    Returns:
        Enhanced prompt with context
    """
    if not search_results:
        return base_prompt
    
    context_parts = []
    for result in search_results[:3]:  # Top 3 results
        if result['score'] > 0.75:  # High relevance only
            context_parts.append(f"[{result['domain']}] {result['content']}")
    
    if context_parts:
        context = "\n".join(context_parts)
        return f"{base_prompt}\n\nRelevant Knowledge:\n{context}"
    
    return base_prompt