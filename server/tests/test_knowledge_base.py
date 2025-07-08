"""
Tests for the Knowledge Base Service
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from server.services.knowledge_base import KnowledgeBase, EmbeddingService
from server.models.enhanced_models import DomainKnowledge, AgentDomain


class TestEmbeddingService:
    """Test the EmbeddingService class"""
    
    @patch('server.services.knowledge_base.SentenceTransformer')
    def test_init(self, mock_transformer):
        """Test embedding service initialization"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        
        mock_transformer.assert_called_once_with('all-MiniLM-L6-v2')
        assert service.embedding_dimension == 384
    
    @patch('server.services.knowledge_base.SentenceTransformer')
    def test_embed_text(self, mock_transformer):
        """Test single text embedding"""
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        result = service.embed_text("test text")
        
        mock_model.encode.assert_called_once_with("test text", convert_to_numpy=True)
        np.testing.assert_array_equal(result, mock_embedding)
    
    @patch('server.services.knowledge_base.SentenceTransformer')
    def test_embed_texts(self, mock_transformer):
        """Test multiple text embeddings"""
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        texts = ["text1", "text2"]
        result = service.embed_texts(texts)
        
        mock_model.encode.assert_called_once_with(texts, convert_to_numpy=True)
        np.testing.assert_array_equal(result, mock_embeddings)


class TestKnowledgeBase:
    """Test the KnowledgeBase class"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock()
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock embedding service"""
        service = Mock()
        service.embed_text.return_value = np.array([0.1, 0.2, 0.3])
        service.embedding_dimension = 3
        return service
    
    @pytest.fixture
    def knowledge_base(self, mock_db, mock_embedding_service):
        """Create a KnowledgeBase instance with mocks"""
        with patch.object(KnowledgeBase, '_check_pgvector', return_value=False):
            kb = KnowledgeBase(mock_db, mock_embedding_service)
        return kb
    
    def test_add_knowledge_new(self, knowledge_base, mock_db, mock_embedding_service):
        """Test adding new knowledge"""
        # Mock the query to find no existing knowledge
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = knowledge_base.add_knowledge(
            domain="test_domain",
            content="Test content",
            metadata={"key": "value"}
        )
        
        # Verify embedding was generated
        mock_embedding_service.embed_text.assert_called_once_with("Test content")
        
        # Verify knowledge was added to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify the knowledge object was created correctly
        added_knowledge = mock_db.add.call_args[0][0]
        assert isinstance(added_knowledge, DomainKnowledge)
        assert added_knowledge.domain_name == "test_domain"
        assert added_knowledge.content == "Test content"
        assert added_knowledge.metadata == {"key": "value"}
        assert added_knowledge.embedding_vector == [0.1, 0.2, 0.3]
        assert added_knowledge.version == 1
        assert added_knowledge.active is True
    
    def test_add_knowledge_update_existing(self, knowledge_base, mock_db, mock_embedding_service):
        """Test updating existing knowledge"""
        # Create existing knowledge mock
        existing = Mock(spec=DomainKnowledge)
        existing.content = "Old content"
        existing.version = 1
        mock_db.query.return_value.filter.return_value.all.return_value = [existing]
        
        # Mock similarity calculation
        with patch.object(knowledge_base, '_calculate_similarity', return_value=1.0):
            result = knowledge_base.add_knowledge(
                domain="test_domain",
                content="Old content",
                metadata={"new": "metadata"}
            )
        
        # Verify existing knowledge was updated
        assert existing.content == "Old content"
        assert existing.metadata == {"new": "metadata"}
        assert existing.embedding_vector == [0.1, 0.2, 0.3]
        assert existing.version == 2
        mock_db.commit.assert_called_once()
    
    def test_search_relevant_in_memory(self, knowledge_base, mock_db, mock_embedding_service):
        """Test in-memory semantic search"""
        # Create mock knowledge entries
        entry1 = Mock(spec=DomainKnowledge)
        entry1.embedding_vector = [0.1, 0.2, 0.3]
        entry1.content = "Content 1"
        
        entry2 = Mock(spec=DomainKnowledge)
        entry2.embedding_vector = [0.4, 0.5, 0.6]
        entry2.content = "Content 2"
        
        mock_db.query.return_value.filter.return_value.all.return_value = [entry1, entry2]
        
        # Search
        results = knowledge_base.search_relevant("test query", "test_domain", top_k=2)
        
        # Verify results
        assert len(results) == 2
        assert results[0][0] in [entry1, entry2]
        assert isinstance(results[0][1], float)  # similarity score
    
    @patch('server.services.knowledge_base.text')
    def test_search_relevant_with_pgvector(self, mock_text, knowledge_base, mock_db, mock_embedding_service):
        """Test pgvector-based semantic search"""
        # Mock pgvector availability
        with patch.object(knowledge_base, '_check_pgvector', return_value=True):
            # Mock query results
            mock_row = Mock()
            mock_row.__getitem__ = lambda self, i: [1, "Content", {}, 0.9][i]
            mock_db.execute.return_value.fetchall.return_value = [mock_row]
            
            # Mock knowledge retrieval
            mock_knowledge = Mock(spec=DomainKnowledge)
            mock_db.query.return_value.filter_by.return_value.first.return_value = mock_knowledge
            
            # Search
            results = knowledge_base.search_relevant("test query", "test_domain", top_k=5)
            
            # Verify results
            assert len(results) == 1
            assert results[0][0] == mock_knowledge
            assert results[0][1] == 0.9
    
    def test_get_context_for_conversation(self, knowledge_base, mock_db, mock_embedding_service):
        """Test getting conversation context"""
        # Mock agent domain relationships
        agent_domain = Mock(spec=AgentDomain)
        agent_domain.relevance_score = 0.8
        
        domain_knowledge = Mock(spec=DomainKnowledge)
        domain_knowledge.domain_name = "test_domain"
        
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (agent_domain, domain_knowledge)
        ]
        
        # Mock search results
        with patch.object(knowledge_base, 'search_relevant') as mock_search:
            mock_search.return_value = [
                (Mock(content="Relevant info 1", metadata={}), 0.9),
                (Mock(content="Relevant info 2", metadata={}), 0.8),
            ]
            
            # Get context
            context = knowledge_base.get_context_for_conversation(
                agent_id=1,
                conversation_text="What is the process?",
                max_tokens=1000
            )
            
            # Verify context formatting
            assert "[test_domain]" in context
            assert "Relevant info 1" in context
            assert "Relevant info 2" in context
    
    def test_update_knowledge(self, knowledge_base, mock_db, mock_embedding_service):
        """Test updating knowledge entry"""
        # Mock existing knowledge
        knowledge = Mock(spec=DomainKnowledge)
        knowledge.version = 1
        mock_db.query.return_value.filter_by.return_value.first.return_value = knowledge
        
        # Update
        result = knowledge_base.update_knowledge(
            knowledge_id=1,
            content="Updated content",
            metadata={"updated": True},
            active=False
        )
        
        # Verify updates
        assert knowledge.content == "Updated content"
        assert knowledge.metadata == {"updated": True}
        assert knowledge.active is False
        assert knowledge.version == 2
        assert knowledge.embedding_vector == [0.1, 0.2, 0.3]
        mock_db.commit.assert_called_once()
    
    def test_delete_knowledge(self, knowledge_base, mock_db):
        """Test soft deleting knowledge"""
        # Mock existing knowledge
        knowledge = Mock(spec=DomainKnowledge)
        knowledge.active = True
        mock_db.query.return_value.filter_by.return_value.first.return_value = knowledge
        
        # Delete
        result = knowledge_base.delete_knowledge(1)
        
        # Verify soft delete
        assert result is True
        assert knowledge.active is False
        mock_db.commit.assert_called_once()
    
    def test_bulk_import_knowledge(self, knowledge_base, mock_db):
        """Test bulk importing knowledge entries"""
        entries = [
            {"content": "Content 1", "metadata": {"type": "faq"}},
            {"content": "Content 2", "metadata": {"type": "policy"}},
            {"content": ""},  # Invalid entry
        ]
        
        with patch.object(knowledge_base, 'add_knowledge') as mock_add:
            mock_add.side_effect = [None, None]  # Success for first two
            
            successful, failed = knowledge_base.bulk_import_knowledge("test_domain", entries)
            
            assert successful == 2
            assert failed == 1
            assert mock_add.call_count == 2
    
    def test_regenerate_embeddings(self, knowledge_base, mock_db, mock_embedding_service):
        """Test regenerating embeddings"""
        # Mock knowledge entries
        entry1 = Mock(spec=DomainKnowledge)
        entry1.id = 1
        entry1.content = "Content 1"
        
        entry2 = Mock(spec=DomainKnowledge)
        entry2.id = 2
        entry2.content = "Content 2"
        
        mock_db.query.return_value.filter_by.return_value.all.return_value = [entry1, entry2]
        
        # Regenerate
        count = knowledge_base.regenerate_embeddings("test_domain")
        
        # Verify
        assert count == 2
        assert entry1.embedding_vector == [0.1, 0.2, 0.3]
        assert entry2.embedding_vector == [0.1, 0.2, 0.3]
        mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])