"""
Knowledge Base Service for managing domain-specific knowledge with semantic search capabilities.

This service handles:
- CRUD operations for knowledge entries
- Vector embeddings for semantic search
- Context injection during conversations
- Version management for knowledge updates
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import numpy as np
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sentence_transformers import SentenceTransformer

from server.models.enhanced_models import DomainKnowledge, AgentDomain, EnhancedAgentConfig

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence transformers."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Initialized embedding model '{model_name}' with dimension {self.embedding_dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array containing the embedding
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array with shape (n_texts, embedding_dim)
        """
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise


class KnowledgeBase:
    """
    Manages domain-specific knowledge for agents with semantic search capabilities.
    """
    
    def __init__(self, db: Session, embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize the knowledge base.
        
        Args:
            db: SQLAlchemy database session
            embedding_service: Optional embedding service instance
        """
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()
        
        # Check if pgvector extension is available
        self._check_pgvector()
    
    def _check_pgvector(self) -> bool:
        """Check if pgvector extension is available."""
        try:
            result = self.db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
            has_vector = result.scalar() is not None
            if not has_vector:
                logger.warning("pgvector extension not found. Semantic search will be limited.")
            return has_vector
        except Exception as e:
            logger.warning(f"Could not check for pgvector extension: {e}")
            return False
    
    def add_knowledge(self, domain: str, content: str, metadata: Optional[Dict] = None) -> DomainKnowledge:
        """
        Add or update a knowledge entry with its embedding.
        
        Args:
            domain: Domain name for the knowledge
            content: Knowledge content
            metadata: Optional metadata dictionary
            
        Returns:
            Created or updated DomainKnowledge instance
        """
        try:
            # Generate embedding
            embedding = self.embedding_service.embed_text(content)
            
            # Check if similar knowledge already exists
            existing = self._find_existing_knowledge(domain, content)
            
            if existing:
                # Update existing knowledge
                existing.content = content
                existing.metadata = metadata or {}
                existing.embedding_vector = embedding.tolist()
                existing.version += 1
                existing.updated_at = datetime.utcnow()
                
                self.db.commit()
                logger.info(f"Updated knowledge entry {existing.id} in domain '{domain}'")
                return existing
            else:
                # Create new knowledge entry
                knowledge = DomainKnowledge(
                    domain_name=domain,
                    content=content,
                    metadata=metadata or {},
                    embedding_vector=embedding.tolist(),
                    version=1,
                    active=True
                )
                
                self.db.add(knowledge)
                self.db.commit()
                self.db.refresh(knowledge)
                
                logger.info(f"Added new knowledge entry {knowledge.id} to domain '{domain}'")
                return knowledge
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add knowledge: {e}")
            raise
    
    def _find_existing_knowledge(self, domain: str, content: str) -> Optional[DomainKnowledge]:
        """Find existing knowledge entry with similar content."""
        # Simple check for exact matches or very similar content
        existing = self.db.query(DomainKnowledge).filter(
            and_(
                DomainKnowledge.domain_name == domain,
                DomainKnowledge.active == True
            )
        ).all()
        
        for entry in existing:
            # Check for exact match or high similarity
            if entry.content == content or self._calculate_similarity(entry.content, content) > 0.95:
                return entry
        
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using embeddings."""
        try:
            emb1 = self.embedding_service.embed_text(text1)
            emb2 = self.embedding_service.embed_text(text2)
            
            # Cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def search_relevant(self, query: str, domain: str, top_k: int = 5) -> List[Tuple[DomainKnowledge, float]]:
        """
        Search for relevant knowledge using semantic similarity.
        
        Args:
            query: Search query
            domain: Domain to search within
            top_k: Number of top results to return
            
        Returns:
            List of tuples containing (knowledge_entry, similarity_score)
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)
            
            # Check if we can use pgvector
            if hasattr(DomainKnowledge, 'embedding_vector') and self._check_pgvector():
                # Use pgvector for efficient similarity search
                results = self._search_with_pgvector(query_embedding, domain, top_k)
            else:
                # Fallback to in-memory search
                results = self._search_in_memory(query_embedding, domain, top_k)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []
    
    def _search_with_pgvector(self, query_embedding: np.ndarray, domain: str, top_k: int) -> List[Tuple[DomainKnowledge, float]]:
        """Search using pgvector extension for efficient similarity search."""
        try:
            # Convert embedding to PostgreSQL array format
            embedding_str = '[' + ','.join(map(str, query_embedding.tolist())) + ']'
            
            # Query using pgvector's <-> operator for cosine distance
            query = text("""
                SELECT id, content, metadata, 
                       1 - (embedding_vector <-> :embedding::vector) as similarity
                FROM domain_knowledge
                WHERE domain_name = :domain AND active = true
                ORDER BY embedding_vector <-> :embedding::vector
                LIMIT :limit
            """)
            
            results = self.db.execute(
                query,
                {
                    'embedding': embedding_str,
                    'domain': domain,
                    'limit': top_k
                }
            ).fetchall()
            
            # Convert results to DomainKnowledge objects with scores
            knowledge_results = []
            for row in results:
                knowledge = self.db.query(DomainKnowledge).filter_by(id=row[0]).first()
                if knowledge:
                    knowledge_results.append((knowledge, row[3]))
            
            return knowledge_results
            
        except Exception as e:
            logger.error(f"pgvector search failed, falling back to in-memory: {e}")
            return self._search_in_memory(query_embedding, domain, top_k)
    
    def _search_in_memory(self, query_embedding: np.ndarray, domain: str, top_k: int) -> List[Tuple[DomainKnowledge, float]]:
        """Fallback in-memory search when pgvector is not available."""
        # Get all active knowledge entries for the domain
        entries = self.db.query(DomainKnowledge).filter(
            and_(
                DomainKnowledge.domain_name == domain,
                DomainKnowledge.active == True
            )
        ).all()
        
        if not entries:
            return []
        
        # Calculate similarities
        similarities = []
        for entry in entries:
            if entry.embedding_vector:
                entry_embedding = np.array(entry.embedding_vector)
                # Cosine similarity
                similarity = np.dot(query_embedding, entry_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(entry_embedding)
                )
                similarities.append((entry, float(similarity)))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_context_for_conversation(self, agent_id: int, conversation_text: str, max_tokens: int = 1000) -> str:
        """
        Get relevant knowledge context for a conversation.
        
        Args:
            agent_id: ID of the agent
            conversation_text: Recent conversation text
            max_tokens: Maximum tokens to include in context
            
        Returns:
            Formatted context string to inject into the prompt
        """
        try:
            # Get agent's domains with their domain knowledge
            agent_domains = self.db.query(AgentDomain, DomainKnowledge).join(
                DomainKnowledge, AgentDomain.domain_id == DomainKnowledge.id
            ).filter(AgentDomain.agent_id == agent_id).all()
            
            if not agent_domains:
                return ""
            
            # Collect relevant knowledge from all agent's domains
            all_knowledge = []
            unique_domains = set()
            
            for agent_domain, domain_knowledge in agent_domains:
                domain_name = domain_knowledge.domain_name
                
                # Avoid searching the same domain multiple times
                if domain_name in unique_domains:
                    continue
                unique_domains.add(domain_name)
                
                # Search for relevant knowledge
                results = self.search_relevant(conversation_text, domain_name, top_k=3)
                
                for knowledge, score in results:
                    if score > 0.7:  # Relevance threshold
                        all_knowledge.append({
                            'domain': domain_name,
                            'content': knowledge.content,
                            'score': score * agent_domain.relevance_score,  # Apply agent-specific relevance
                            'metadata': knowledge.metadata
                        })
            
            # Sort by relevance score
            all_knowledge.sort(key=lambda x: x['score'], reverse=True)
            
            # Format context
            context_parts = []
            current_length = 0
            
            for item in all_knowledge:
                # Estimate token count (rough approximation)
                item_text = f"[{item['domain']}] {item['content']}"
                item_length = len(item_text.split())
                
                if current_length + item_length > max_tokens:
                    break
                
                context_parts.append(item_text)
                current_length += item_length
            
            if not context_parts:
                return ""
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return ""
    
    def update_knowledge(self, knowledge_id: int, content: Optional[str] = None, 
                        metadata: Optional[Dict] = None, active: Optional[bool] = None) -> Optional[DomainKnowledge]:
        """
        Update an existing knowledge entry.
        
        Args:
            knowledge_id: ID of the knowledge entry
            content: New content (if provided)
            metadata: New metadata (if provided)
            active: New active status (if provided)
            
        Returns:
            Updated knowledge entry or None if not found
        """
        try:
            knowledge = self.db.query(DomainKnowledge).filter_by(id=knowledge_id).first()
            
            if not knowledge:
                return None
            
            if content is not None:
                knowledge.content = content
                # Update embedding
                embedding = self.embedding_service.embed_text(content)
                knowledge.embedding_vector = embedding.tolist()
            
            if metadata is not None:
                knowledge.metadata = metadata
            
            if active is not None:
                knowledge.active = active
            
            knowledge.version += 1
            knowledge.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(knowledge)
            
            logger.info(f"Updated knowledge entry {knowledge_id}")
            return knowledge
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update knowledge: {e}")
            raise
    
    def delete_knowledge(self, knowledge_id: int) -> bool:
        """
        Soft delete a knowledge entry by marking it as inactive.
        
        Args:
            knowledge_id: ID of the knowledge entry
            
        Returns:
            True if deleted, False if not found
        """
        try:
            knowledge = self.db.query(DomainKnowledge).filter_by(id=knowledge_id).first()
            
            if not knowledge:
                return False
            
            knowledge.active = False
            knowledge.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Deactivated knowledge entry {knowledge_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete knowledge: {e}")
            raise
    
    def list_knowledge_by_domain(self, domain: str, active_only: bool = True) -> List[DomainKnowledge]:
        """
        List all knowledge entries for a domain.
        
        Args:
            domain: Domain name
            active_only: Whether to include only active entries
            
        Returns:
            List of knowledge entries
        """
        try:
            query = self.db.query(DomainKnowledge).filter_by(domain_name=domain)
            
            if active_only:
                query = query.filter_by(active=True)
            
            return query.order_by(DomainKnowledge.created_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Failed to list knowledge: {e}")
            return []
    
    def bulk_import_knowledge(self, domain: str, entries: List[Dict[str, any]]) -> Tuple[int, int]:
        """
        Bulk import knowledge entries.
        
        Args:
            domain: Domain name
            entries: List of dictionaries with 'content' and optional 'metadata' keys
            
        Returns:
            Tuple of (successful_imports, failed_imports)
        """
        successful = 0
        failed = 0
        
        for entry in entries:
            try:
                content = entry.get('content', '').strip()
                if not content:
                    failed += 1
                    continue
                
                metadata = entry.get('metadata', {})
                self.add_knowledge(domain, content, metadata)
                successful += 1
                
            except Exception as e:
                logger.error(f"Failed to import entry: {e}")
                failed += 1
        
        logger.info(f"Bulk import completed: {successful} successful, {failed} failed")
        return successful, failed
    
    def regenerate_embeddings(self, domain: Optional[str] = None) -> int:
        """
        Regenerate embeddings for all knowledge entries.
        
        Args:
            domain: Optional domain filter
            
        Returns:
            Number of embeddings regenerated
        """
        try:
            query = self.db.query(DomainKnowledge).filter_by(active=True)
            
            if domain:
                query = query.filter_by(domain_name=domain)
            
            entries = query.all()
            count = 0
            
            for entry in entries:
                try:
                    embedding = self.embedding_service.embed_text(entry.content)
                    entry.embedding_vector = embedding.tolist()
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to regenerate embedding for entry {entry.id}: {e}")
            
            self.db.commit()
            logger.info(f"Regenerated {count} embeddings")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to regenerate embeddings: {e}")
            raise