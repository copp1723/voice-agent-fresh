"""
Tests for Knowledge Base Integration with Agent System
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

# Test imports
from server.services.agent_builder import AgentBuilder
from server.services.knowledge_base import KnowledgeBase
from server.models.enhanced_models import (
    EnhancedAgentConfig, AgentDomain, DomainKnowledge
)


class TestAgentBuilderKnowledgeIntegration:
    """Test agent builder knowledge domain integration"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def agent_builder(self):
        """Create agent builder instance"""
        return AgentBuilder()
    
    def test_compile_prompt_with_domains(self, agent_builder, mock_db):
        """Test that compile_system_prompt includes knowledge domains"""
        # Mock agent
        agent = Mock(spec=EnhancedAgentConfig)
        agent.id = 1
        agent.personality_traits = ['helpful', 'professional']
        agent.conversation_style = 'balanced'
        agent.max_conversation_turns = 50
        agent.response_time_ms = 1000
        agent.template = None
        
        # Mock agent domains query
        domain_knowledge = Mock(spec=DomainKnowledge)
        domain_knowledge.id = 1
        domain_knowledge.domain_name = "customer_support"
        domain_knowledge.active = True
        
        agent_domain = Mock(spec=AgentDomain)
        agent_domain.relevance_score = 0.9
        
        mock_db.query.return_value.filter_by.side_effect = [
            # First call for agent query
            Mock(first=Mock(return_value=agent)),
            # Second call for goals
            Mock(order_by=Mock(return_value=Mock(all=Mock(return_value=[])))),
            # Third call for instructions
            Mock(order_by=Mock(return_value=Mock(all=Mock(return_value=[]))))
        ]
        
        # Mock domains query with join
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [
            (agent_domain, domain_knowledge)
        ]
        
        # Compile prompt
        prompt = agent_builder.compile_system_prompt(mock_db, 1)
        
        # Verify knowledge base section is included
        assert "## Knowledge Base Access:" in prompt
        assert "You have access to information about:" in prompt
        assert "- customer_support" in prompt
        assert "Use this knowledge to provide accurate, detailed responses." in prompt
    
    def test_get_agent_domains(self, agent_builder, mock_db):
        """Test _get_agent_domains method"""
        # Mock domain knowledge entries
        dk1 = Mock(spec=DomainKnowledge)
        dk1.id = 1
        dk1.domain_name = "technical_support"
        dk1.active = True
        
        dk2 = Mock(spec=DomainKnowledge)
        dk2.id = 2
        dk2.domain_name = "billing"
        dk2.active = True
        
        # Mock agent domains
        ad1 = Mock(spec=AgentDomain)
        ad1.relevance_score = 0.95
        
        ad2 = Mock(spec=AgentDomain)
        ad2.relevance_score = 0.85
        
        # Mock query result
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [
            (ad1, dk1),
            (ad2, dk2)
        ]
        
        # Get domains
        domains = agent_builder._get_agent_domains(mock_db, 1)
        
        # Verify results
        assert len(domains) == 2
        assert domains[0]['name'] == 'technical_support'
        assert domains[0]['relevance_score'] == 0.95
        assert domains[1]['name'] == 'billing'
        assert domains[1]['relevance_score'] == 0.85


class TestConversationKnowledgeInjection:
    """Test knowledge injection during conversation processing"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def knowledge_base(self, mock_db):
        """Create knowledge base instance"""
        return KnowledgeBase(mock_db)
    
    def test_agent_brain_knowledge_injection(self):
        """Test that agent brain properly injects knowledge context"""
        # This test verifies the integration in agent_brain.py
        from src.services.agent_brain import AgentBrain
        
        brain = AgentBrain()
        
        # Mock the OpenAI client
        brain.openai_client = MagicMock()
        brain.openai_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        )
        
        # Mock database session
        mock_db = MagicMock(spec=Session)
        
        # Mock knowledge base
        with patch('src.services.agent_brain.KnowledgeBase') as mock_kb_class:
            mock_kb = mock_kb_class.return_value
            mock_kb.get_context_for_conversation.return_value = "Domain knowledge: Customer refund policy is 30 days."
            
            # Process conversation with knowledge injection
            response = brain.process_conversation(
                user_input="What's your refund policy?",
                conversation_history=[],
                agent_id=1,
                db_session=mock_db
            )
            
            # Verify knowledge base was called
            mock_kb.get_context_for_conversation.assert_called_once_with(
                agent_id=1,
                conversation_text="What's your refund policy?",
                max_tokens=300
            )
            
            # Verify OpenAI was called with knowledge context
            call_args = brain.openai_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            
            # Find the knowledge context message
            knowledge_messages = [m for m in messages if 'Relevant Information' in m.get('content', '')]
            assert len(knowledge_messages) == 1
            assert "Customer refund policy is 30 days" in knowledge_messages[0]['content']
    
    def test_enhanced_agent_brain_knowledge_injection(self):
        """Test that enhanced agent brain properly injects knowledge context"""
        from src.services.enhanced_agent_brain import EnhancedAgentBrain
        
        brain = EnhancedAgentBrain()
        
        # Mock the OpenAI client
        brain.openai_client = MagicMock()
        brain.openai_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        )
        
        # Mock database session
        mock_db = MagicMock(spec=Session)
        
        # Mock agent config
        agent_config = {
            'id': 1,
            'name': 'Support Agent',
            'system_prompt': 'You are a helpful support agent.'
        }
        
        # Mock knowledge base
        with patch('src.services.enhanced_agent_brain.KnowledgeBase') as mock_kb_class:
            mock_kb = mock_kb_class.return_value
            mock_kb.get_context_for_conversation.return_value = "FAQ: We offer 24/7 support via phone and email."
            
            # Process conversation
            response, metadata = brain.process_conversation(
                user_input="How can I contact support?",
                call_sid="test_call_123",
                agent_config=agent_config,
                conversation_history=[],
                db_session=mock_db
            )
            
            # Verify knowledge base was called
            mock_kb.get_context_for_conversation.assert_called_once_with(
                agent_id=1,
                conversation_text="How can I contact support?",
                max_tokens=500
            )
            
            # Verify metadata indicates knowledge was injected
            assert metadata['knowledge_injected'] is True
            
            # Verify OpenAI was called with knowledge context
            call_args = brain.openai_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            
            # Find the knowledge context message
            knowledge_messages = [m for m in messages if 'Knowledge Base' in m.get('content', '')]
            assert len(knowledge_messages) == 1
            assert "24/7 support via phone and email" in knowledge_messages[0]['content']


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    def test_agent_creation_with_knowledge_domains(self):
        """Test creating an agent and assigning knowledge domains"""
        # This would be an integration test with a real database
        # For now, we'll outline the expected flow
        
        # 1. Create domain knowledge entries
        # 2. Create an agent
        # 3. Link agent to domains
        # 4. Compile agent prompt (should include domains)
        # 5. Process a conversation (should inject relevant knowledge)
        # 6. Verify response uses knowledge context
        
        pass  # Implement with test database
    
    def test_knowledge_relevance_scoring(self):
        """Test that more relevant knowledge is prioritized"""
        # This would test the relevance scoring in search_relevant
        # and how it affects what knowledge gets injected
        
        pass  # Implement with test database


if __name__ == "__main__":
    pytest.main([__file__])