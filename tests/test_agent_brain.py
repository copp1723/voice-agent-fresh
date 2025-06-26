"""
Tests for AgentBrain - Core AI conversation processing
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from src.services.agent_brain import AgentBrain


class TestAgentBrain:
    """Test suite for AgentBrain class"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing"""
        with patch('src.services.agent_brain.openai.OpenAI') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def agent_brain_with_mock(self, mock_openai_client):
        """Create AgentBrain instance with mocked OpenAI client"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            brain = AgentBrain()
            return brain
    
    @pytest.fixture
    def agent_brain_no_api_key(self):
        """Create AgentBrain instance without API key"""
        with patch.dict(os.environ, {}, clear=True):
            brain = AgentBrain()
            return brain
    
    # ===== Initialization Tests =====
    
    def test_init_with_api_key(self, mock_openai_client):
        """Test AgentBrain initialization with API key"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            brain = AgentBrain()
            assert brain.openai_client is not None
            mock_openai_client.assert_called_once_with(
                api_key='test-key',
                base_url="https://openrouter.ai/api/v1"
            )
            assert brain.default_model == "openai/gpt-4o-mini"
            assert brain.max_tokens == 150
            assert brain.temperature == 0.7
    
    def test_init_without_api_key(self, agent_brain_no_api_key):
        """Test AgentBrain initialization without API key"""
        assert agent_brain_no_api_key.openai_client is None
    
    # ===== Voice Optimization Tests =====
    
    def test_optimize_for_voice_markdown_removal(self):
        """Test markdown formatting removal"""
        brain = AgentBrain()
        
        test_cases = [
            ("Hello **world**", "Hello world"),
            ("This is *important*", "This is important"),
            ("Use `code` here", "Use code here"),
            ("_Underlined_ text", "Underlined text"),
            ("**Bold** and *italic*", "Bold and italic"),
        ]
        
        for input_text, expected in test_cases:
            assert brain._optimize_for_voice(input_text) == expected
    
    def test_optimize_for_voice_symbol_replacement(self):
        """Test symbol to word conversion"""
        brain = AgentBrain()
        
        test_cases = [
            ("Cost is $100", "Cost is 100 dollars"),
            ("50% discount", "50 percent discount"),
            ("Email me @ test@example.com", "Email me at test at example.com"),
            ("Item #123", "Item number 123"),
            ("A & B", "A and B"),
            ("2 + 2 = 4", "2 plus 2 = 4"),
        ]
        
        for input_text, expected in test_cases:
            assert brain._optimize_for_voice(input_text) == expected
    
    def test_optimize_for_voice_acronym_pronunciation(self):
        """Test acronym pronunciation improvement"""
        brain = AgentBrain()
        
        test_cases = [
            ("Check the API", "Check the A P I"),
            ("Visit our URL", "Visit our U R L"),
            ("Read the FAQ", "Read the F A Q"),
            ("Contact the CEO", "Contact the C E O"),
        ]
        
        for input_text, expected in test_cases:
            assert brain._optimize_for_voice(input_text) == expected
    
    def test_optimize_for_voice_length_truncation(self):
        """Test response length truncation for voice"""
        brain = AgentBrain()
        
        # Create a long response with multiple sentences
        long_text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
        result = brain._optimize_for_voice(long_text * 10)  # Make it very long
        
        # Should be truncated to approximately 2 sentences
        assert len(result) <= 300
        assert result.endswith('.')
    
    def test_optimize_for_voice_ellipsis_handling(self):
        """Test ellipsis replacement for natural speech"""
        brain = AgentBrain()
        
        assert brain._optimize_for_voice("Wait... let me check") == "Wait. let me check"
        assert brain._optimize_for_voice("Well... I think...") == "Well. I think. "
    
    # ===== Process Conversation Tests =====
    
    def test_process_conversation_basic_success(self, agent_brain_with_mock):
        """Test basic successful conversation processing"""
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello! How can I help you today?"))]
        agent_brain_with_mock.openai_client.chat.completions.create.return_value = mock_response
        
        result = agent_brain_with_mock.process_conversation(
            user_input="Hello",
            conversation_history=[]
        )
        
        assert result == "Hello! How can I help you today?"
        agent_brain_with_mock.openai_client.chat.completions.create.assert_called_once()
    
    def test_process_conversation_with_history(self, agent_brain_with_mock):
        """Test conversation processing with history"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Your account balance is $500."))]
        agent_brain_with_mock.openai_client.chat.completions.create.return_value = mock_response
        
        conversation_history = [
            "I need help with my account",
            "I'd be happy to help you with your account. What specific information do you need?",
            "What's my balance?"
        ]
        
        result = agent_brain_with_mock.process_conversation(
            user_input="What's my balance?",
            conversation_history=conversation_history[:-1]  # Exclude the last user message
        )
        
        assert "500 dollars" in result  # Should be voice-optimized
        
        # Verify the messages were constructed correctly
        call_args = agent_brain_with_mock.openai_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        
        # Should have system message + history + current input
        assert len(messages) >= 4
        assert messages[0]['role'] == 'system'
        assert 'concise and conversational' in messages[0]['content']
    
    def test_process_conversation_with_custom_system_prompt(self, agent_brain_with_mock):
        """Test conversation with custom agent instructions"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="I understand you need technical support."))]
        agent_brain_with_mock.openai_client.chat.completions.create.return_value = mock_response
        
        # Set custom agent instructions
        agent_brain_with_mock.set_agent_instructions("You are a technical support specialist. Focus on IT issues.")
        
        result = agent_brain_with_mock.process_conversation(
            user_input="My computer won't start",
            conversation_history=[]
        )
        
        # Verify custom prompt was used
        call_args = agent_brain_with_mock.openai_client.chat.completions.create.call_args
        system_message = call_args[1]['messages'][0]['content']
        assert "technical support specialist" in system_message
    
    def test_process_conversation_api_error(self, agent_brain_with_mock):
        """Test error handling when API fails"""
        agent_brain_with_mock.openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = agent_brain_with_mock.process_conversation(
            user_input="Hello",
            conversation_history=[]
        )
        
        assert "I'm sorry, I had trouble processing that" in result
    
    def test_process_conversation_no_client(self, agent_brain_no_api_key):
        """Test conversation processing without OpenAI client"""
        result = agent_brain_no_api_key.process_conversation(
            user_input="Hello",
            conversation_history=[]
        )
        
        assert "I'm having trouble connecting to my AI service" in result
    
    def test_process_conversation_history_limit(self, agent_brain_with_mock):
        """Test that conversation history is limited to last 20 messages"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        agent_brain_with_mock.openai_client.chat.completions.create.return_value = mock_response
        
        # Create a long conversation history
        long_history = [f"Message {i}" for i in range(50)]
        
        agent_brain_with_mock.process_conversation(
            user_input="New message",
            conversation_history=long_history
        )
        
        call_args = agent_brain_with_mock.openai_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        
        # Should have system + last 20 history messages + current input
        # But we need to account for the alternating user/assistant pattern
        assert len(messages) <= 22  # system + 20 history + 1 current
    
    # ===== Conversation Summary Tests =====
    
    def test_generate_conversation_summary_empty(self):
        """Test summary generation with empty history"""
        brain = AgentBrain()
        summary = brain.generate_conversation_summary([])
        assert summary == "We discussed your inquiry and provided assistance."
    
    def test_generate_conversation_summary_single_message(self):
        """Test summary with single user message"""
        brain = AgentBrain()
        history = ["I need help with billing"]
        summary = brain.generate_conversation_summary(history)
        assert "We discussed: I need help with billing" in summary
    
    def test_generate_conversation_summary_multiple_messages(self):
        """Test summary with multiple messages"""
        brain = AgentBrain()
        history = [
            "I need help with billing",
            "I can help with that",
            "My bill seems too high",
            "Let me check that for you"
        ]
        summary = brain.generate_conversation_summary(history)
        assert "questions about" in summary
    
    def test_generate_conversation_summary_long_conversation(self):
        """Test summary with long conversation"""
        brain = AgentBrain()
        history = [f"Message {i}" for i in range(10)]
        summary = brain.generate_conversation_summary(history)
        assert "detailed conversation" in summary
    
    # ===== Extract Topics Tests =====
    
    def test_extract_topics(self):
        """Test topic extraction from conversation"""
        brain = AgentBrain()
        
        conversation = [
            "I have a billing issue",
            "I can help with billing",
            "Also need technical support",
            "Let me assist with that"
        ]
        
        topics = brain._extract_topics(conversation)
        assert "billing" in topics
        assert "technical" in topics
        assert "support" in topics
        assert len(topics) <= 3
    
    def test_extract_topics_no_keywords(self):
        """Test topic extraction with no matching keywords"""
        brain = AgentBrain()
        
        conversation = ["Hello", "Hi there", "How are you?", "I'm fine"]
        topics = brain._extract_topics(conversation)
        assert len(topics) == 0
    
    # ===== Conversation Metrics Tests =====
    
    def test_get_conversation_metrics(self):
        """Test conversation metrics calculation"""
        brain = AgentBrain()
        
        history = [
            "Hello",  # User
            "Hi, how can I help?",  # Assistant
            "I need assistance",  # User
            "I'd be happy to help you"  # Assistant
        ]
        
        metrics = brain.get_conversation_metrics(history)
        
        assert metrics["total_turns"] == 4
        assert metrics["user_messages"] == 2
        assert metrics["assistant_messages"] == 2
        assert metrics["avg_user_message_length"] > 0
        assert metrics["avg_assistant_message_length"] > 0
    
    def test_get_conversation_metrics_empty(self):
        """Test metrics with empty conversation"""
        brain = AgentBrain()
        metrics = brain.get_conversation_metrics([])
        
        assert metrics["total_turns"] == 0
        assert metrics["user_messages"] == 0
        assert metrics["assistant_messages"] == 0
        assert metrics["avg_user_message_length"] == 0
        assert metrics["avg_assistant_message_length"] == 0
    
    # ===== Generate Summary Tests =====
    
    def test_generate_summary_with_openai(self, agent_brain_with_mock):
        """Test full summary generation with OpenAI"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Customer needed help with billing. Issue was resolved."))]
        agent_brain_with_mock.openai_client.chat.completions.create.return_value = mock_response
        
        history = ["I need help with billing", "I can help with that"]
        summary_data = agent_brain_with_mock.generate_summary(history)
        
        assert summary_data['summary'] == "Customer needed help with billing. Issue was resolved."
        assert 'billing' in summary_data['key_topics']
        assert summary_data['turn_count'] == 2
        assert summary_data['sentiment'] == 'positive'
        assert summary_data['resolution_status'] == 'completed'
    
    def test_generate_summary_without_openai(self, agent_brain_no_api_key):
        """Test summary generation fallback without OpenAI"""
        history = ["I need help", "Sure, I can help"]
        summary_data = agent_brain_no_api_key.generate_summary(history)
        
        assert "2 exchanges" in summary_data['summary']
        assert summary_data['turn_count'] == 2
    
    def test_generate_summary_error_handling(self, agent_brain_with_mock):
        """Test summary generation error handling"""
        agent_brain_with_mock.openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        history = ["Test message"]
        summary_data = agent_brain_with_mock.generate_summary(history)
        
        assert "1 exchanges" in summary_data['summary']
        assert summary_data['resolution_status'] == 'completed'


# ===== Parameterized Tests =====

@pytest.mark.parametrize("input_text,expected_output", [
    ("", ""),
    ("Simple text", "Simple text"),
    ("**Bold** *italic* _underline_", "Bold italic underline"),
    ("$100 @ 50%", "100 dollars at 50 percent"),
    ("Contact CEO about API & URL", "Contact C E O about A P I and U R L"),
])
def test_optimize_for_voice_parametrized(input_text, expected_output):
    """Parameterized test for voice optimization"""
    brain = AgentBrain()
    assert brain._optimize_for_voice(input_text) == expected_output


@pytest.mark.parametrize("conversation_length,expected_status", [
    ([], "incomplete"),
    (["Hello"], "completed"),
    (["Hello", "Hi", "Goodbye", "Thanks"], "completed"),
])
def test_generate_summary_status_parametrized(conversation_length, expected_status):
    """Parameterized test for summary status"""
    brain = AgentBrain()
    summary_data = brain.generate_summary(conversation_length)
    assert summary_data['resolution_status'] == expected_status