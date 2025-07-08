"""
Enhanced AI Agent Brain - Improved conversation processing for natural phone calls
"""
import os
import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import openai
from collections import deque
from sqlalchemy.orm import Session

# Try to import knowledge base if available
try:
    from server.services.knowledge_base import KnowledgeBase
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError:
    logger.warning("Knowledge base service not available - running without knowledge integration")
    KNOWLEDGE_BASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class ConversationState:
    """Tracks conversation state and context"""
    
    def __init__(self, call_sid: str):
        self.call_sid = call_sid
        self.started_at = datetime.utcnow()
        self.turn_count = 0
        self.context = {}  # Key facts mentioned
        self.intents = []  # Detected intents
        self.entities = {}  # Extracted entities
        self.sentiment_history = deque(maxlen=5)  # Recent sentiment
        self.clarification_needed = False
        self.topic_stack = []  # Topics being discussed
        self.interruption_context = None
        self.conversation_phase = "greeting"  # greeting, discovery, resolution, closing
        
    def update(self, user_input: str, ai_response: str, analysis: Dict):
        """Update conversation state with new turn"""
        self.turn_count += 1
        
        # Update from analysis
        if 'intent' in analysis:
            self.intents.append(analysis['intent'])
        if 'entities' in analysis:
            self.entities.update(analysis['entities'])
        if 'sentiment' in analysis:
            self.sentiment_history.append(analysis['sentiment'])
        if 'topic' in analysis:
            self._update_topic(analysis['topic'])
        if 'phase' in analysis:
            self.conversation_phase = analysis['phase']
            
    def _update_topic(self, new_topic: str):
        """Manage topic stack for context switching"""
        if self.topic_stack and self.topic_stack[-1] != new_topic:
            # Topic switch detected
            self.topic_stack.append(new_topic)
        elif not self.topic_stack:
            self.topic_stack.append(new_topic)
            
    def get_recent_sentiment(self) -> str:
        """Get overall recent sentiment"""
        if not self.sentiment_history:
            return "neutral"
        
        sentiment_scores = {"positive": 1, "neutral": 0, "negative": -1}
        avg_score = sum(sentiment_scores.get(s, 0) for s in self.sentiment_history) / len(self.sentiment_history)
        
        if avg_score > 0.3:
            return "positive"
        elif avg_score < -0.3:
            return "negative"
        return "neutral"

class EnhancedAgentBrain:
    """
    Enhanced AI processing engine for natural voice conversations
    """
    
    def __init__(self):
        # API Configuration
        api_key = os.getenv('OPENROUTER_API_KEY')
        
        if api_key:
            self.openai_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.openai_client = None
            logger.warning("OpenRouter API key not found - EnhancedAgentBrain will not function")
        
        # Model configuration for better quality
        self.conversation_model = os.getenv('CONVERSATION_MODEL', 'anthropic/claude-3-sonnet')  # Better for conversations
        self.analysis_model = os.getenv('ANALYSIS_MODEL', 'openai/gpt-4o-mini')  # Fast analysis
        
        # Conversation settings
        self.max_tokens = 120  # Shorter for natural speech
        self.temperature = 0.8  # More natural variation
        self.conversation_states = {}  # Track state per call
        
        # Interruption handling
        self.interruption_threshold = 0.5  # seconds
        self.last_response_time = {}
        
    def create_conversation_state(self, call_sid: str) -> ConversationState:
        """Create a new conversation state for a call"""
        state = ConversationState(call_sid)
        self.conversation_states[call_sid] = state
        return state
        
    def get_conversation_state(self, call_sid: str) -> Optional[ConversationState]:
        """Get conversation state for a call"""
        return self.conversation_states.get(call_sid)
    
    def process_conversation(
        self, 
        user_input: str, 
        call_sid: str,
        agent_config: Dict[str, Any],
        conversation_history: List[str],
        db_session: Optional[Session] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process user input with enhanced conversation awareness
        
        Returns:
            Tuple of (response_text, metadata)
        """
        try:
            if not self.openai_client:
                return "I'm having trouble connecting right now. Please try again.", {"error": "No client"}
            
            # Get or create conversation state
            state = self.get_conversation_state(call_sid)
            if not state:
                state = self.create_conversation_state(call_sid)
            
            # Detect interruption
            is_interruption = self._detect_interruption(call_sid, user_input)
            
            # Analyze user input
            analysis = self._analyze_input(user_input, state)
            
            # Get knowledge context if available
            knowledge_context = None
            if KNOWLEDGE_BASE_AVAILABLE and db_session and agent_config.get('id'):
                try:
                    kb = KnowledgeBase(db_session)
                    knowledge_context = kb.get_context_for_conversation(
                        agent_id=agent_config['id'],
                        conversation_text=user_input,
                        max_tokens=500
                    )
                    if knowledge_context:
                        logger.info(f"Injected knowledge context for agent {agent_config['id']}")
                except Exception as e:
                    logger.error(f"Failed to get knowledge context: {e}")
            
            # Build enhanced messages
            messages = self._build_conversation_messages(
                user_input, 
                agent_config, 
                conversation_history, 
                state, 
                analysis,
                is_interruption,
                knowledge_context
            )
            
            # Generate response with appropriate model
            start_time = time.time()
            response = self.openai_client.chat.completions.create(
                model=self.conversation_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self._get_dynamic_temperature(state),
                timeout=10  # Faster timeout for phone calls
            )
            
            ai_response = response.choices[0].message.content.strip()
            generation_time = time.time() - start_time
            
            # Post-process for natural speech
            ai_response = self._optimize_for_voice(ai_response, state)
            
            # Update conversation state
            state.update(user_input, ai_response, analysis)
            
            # Update last response time
            self.last_response_time[call_sid] = time.time()
            
            metadata = {
                'generation_time': generation_time,
                'model': self.conversation_model,
                'turn_count': state.turn_count,
                'phase': state.conversation_phase,
                'sentiment': state.get_recent_sentiment(),
                'interrupted': is_interruption,
                'analysis': analysis,
                'knowledge_injected': bool(knowledge_context)
            }
            
            logger.info(f"Enhanced response generated in {generation_time:.2f}s")
            return ai_response, metadata
            
        except Exception as e:
            logger.error(f"Error in enhanced processing: {e}")
            return "I apologize, could you repeat that please?", {"error": str(e)}
    
    def _detect_interruption(self, call_sid: str, user_input: str) -> bool:
        """Detect if user interrupted the AI"""
        if call_sid not in self.last_response_time:
            return False
            
        time_since_response = time.time() - self.last_response_time[call_sid]
        
        # Quick interjections indicate interruption
        is_short = len(user_input.split()) < 3
        is_quick = time_since_response < self.interruption_threshold
        
        return is_short and is_quick
    
    def _analyze_input(self, user_input: str, state: ConversationState) -> Dict[str, Any]:
        """Analyze user input for intent, entities, and sentiment"""
        try:
            # Quick analysis with fast model
            analysis_prompt = f"""Analyze this phone conversation input:
Input: "{user_input}"

Extract:
1. Intent (e.g., question, complaint, request, confirmation)
2. Sentiment (positive/neutral/negative)
3. Key entities (names, dates, amounts, etc.)
4. Topic category
5. Urgency level (low/medium/high)

Response format: JSON only"""

            response = self.openai_client.chat.completions.create(
                model=self.analysis_model,
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=150,
                temperature=0.3,
                timeout=3  # Quick timeout
            )
            
            try:
                analysis = json.loads(response.choices[0].message.content)
                return analysis
            except:
                # Fallback to basic analysis
                return self._basic_analysis(user_input)
                
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._basic_analysis(user_input)
    
    def _basic_analysis(self, user_input: str) -> Dict[str, Any]:
        """Basic fallback analysis"""
        lower_input = user_input.lower()
        
        # Basic sentiment
        if any(word in lower_input for word in ['angry', 'frustrated', 'upset', 'terrible']):
            sentiment = 'negative'
        elif any(word in lower_input for word in ['great', 'perfect', 'excellent', 'thank']):
            sentiment = 'positive'
        else:
            sentiment = 'neutral'
            
        # Basic intent
        if '?' in user_input:
            intent = 'question'
        elif any(word in lower_input for word in ['want', 'need', 'like', 'please']):
            intent = 'request'
        else:
            intent = 'statement'
            
        return {
            'intent': intent,
            'sentiment': sentiment,
            'entities': {},
            'topic': 'general',
            'urgency': 'medium'
        }
    
    def _build_conversation_messages(
        self, 
        user_input: str,
        agent_config: Dict[str, Any],
        conversation_history: List[str],
        state: ConversationState,
        analysis: Dict[str, Any],
        is_interruption: bool,
        knowledge_context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build messages with enhanced context"""
        
        messages = []
        
        # Enhanced system prompt
        system_prompt = self._build_enhanced_system_prompt(agent_config, state, analysis)
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation context if exists
        if state.context:
            context_prompt = f"Known context: {json.dumps(state.context)}"
            messages.append({"role": "system", "content": context_prompt})
        
        # Add knowledge base context if available
        if knowledge_context:
            messages.append({
                "role": "system", 
                "content": f"Relevant Information from Knowledge Base:\n{knowledge_context}\n\nUse this information to provide accurate, detailed responses."
            })
        
        # Handle interruption
        if is_interruption:
            messages.append({
                "role": "system", 
                "content": "The user interrupted you. Acknowledge briefly and address their concern immediately."
            })
        
        # Add conversation history with better formatting
        for i, msg in enumerate(conversation_history[-10:]):  # Last 10 turns
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": msg})
        
        # Add current input with analysis
        enhanced_input = user_input
        if analysis.get('urgency') == 'high':
            enhanced_input = f"[URGENT] {user_input}"
            
        messages.append({"role": "user", "content": enhanced_input})
        
        return messages
    
    def _build_enhanced_system_prompt(
        self, 
        agent_config: Dict[str, Any],
        state: ConversationState,
        analysis: Dict[str, Any]
    ) -> str:
        """Build enhanced system prompt based on conversation state"""
        
        base_prompt = agent_config.get('system_prompt', '')
        
        # Phase-specific instructions
        phase_prompts = {
            'greeting': "Be warm and welcoming. Quickly understand their need.",
            'discovery': "Ask clarifying questions. Show you're listening.",
            'resolution': "Provide clear solutions. Confirm understanding.",
            'closing': "Summarize next steps. End positively."
        }
        
        phase_instruction = phase_prompts.get(state.conversation_phase, '')
        
        # Sentiment-aware adjustments
        sentiment = state.get_recent_sentiment()
        sentiment_prompts = {
            'negative': "Be extra empathetic and patient. Acknowledge their frustration.",
            'positive': "Match their positive energy. Build on the momentum.",
            'neutral': "Be professional and helpful."
        }
        
        sentiment_instruction = sentiment_prompts.get(sentiment, '')
        
        # Build complete prompt
        enhanced_prompt = f"""{base_prompt}

CONVERSATION GUIDELINES:
- You're on a phone call. Keep responses under 2 sentences.
- {phase_instruction}
- {sentiment_instruction}
- Use natural speech patterns (contractions, simple words).
- Never use lists, bullet points, or formal language.
- If unsure, ask for clarification naturally.
- Current phase: {state.conversation_phase}
- Turn {state.turn_count} of the conversation"""

        return enhanced_prompt
    
    def _get_dynamic_temperature(self, state: ConversationState) -> float:
        """Adjust temperature based on conversation state"""
        
        # Lower temperature for critical phases
        if state.conversation_phase in ['resolution', 'closing']:
            return 0.6
        
        # Higher temperature for discovery/rapport building
        if state.conversation_phase in ['greeting', 'discovery']:
            return 0.8
            
        # Adjust for sentiment
        sentiment = state.get_recent_sentiment()
        if sentiment == 'negative':
            return 0.5  # More consistent when dealing with upset customers
            
        return self.temperature
    
    def _optimize_for_voice(self, text: str, state: ConversationState) -> str:
        """Optimize text for natural speech"""
        
        # Remove any markdown or formatting
        text = text.replace('*', '').replace('_', '').replace('#', '')
        
        # Ensure conversational tone
        replacements = {
            "I will": "I'll",
            "I am": "I'm",
            "You are": "You're",
            "It is": "It's",
            "That is": "That's",
            "We are": "We're",
            "They are": "They're",
            "Cannot": "Can't",
            "Do not": "Don't",
            "Would not": "Wouldn't",
            "Could not": "Couldn't"
        }
        
        for formal, casual in replacements.items():
            text = text.replace(formal, casual)
            text = text.replace(formal.lower(), casual.lower())
        
        # Add natural pauses
        if state.conversation_phase == 'discovery' and '?' in text:
            # Add slight pause before questions
            text = text.replace('?', '?...')
            
        # Ensure it ends properly
        if not text.endswith(('.', '!', '?')):
            text += '.'
            
        return text.strip()
    
    def handle_clarification(self, call_sid: str, original_input: str) -> str:
        """Generate clarification request"""
        state = self.get_conversation_state(call_sid)
        if not state:
            return "I'm sorry, could you repeat that?"
            
        # Context-aware clarification
        templates = [
            "I want to make sure I understand correctly. Are you asking about {topic}?",
            "Just to clarify, did you mean {interpretation}?",
            "I didn't quite catch that. Could you tell me more about {context}?"
        ]
        
        # Use appropriate template based on context
        if state.topic_stack:
            topic = state.topic_stack[-1]
            return f"I want to make sure I understand correctly. Are you asking about {topic}?"
        
        return "I'm sorry, I didn't quite catch that. Could you please repeat?"

# Global instance
enhanced_agent_brain = EnhancedAgentBrain()