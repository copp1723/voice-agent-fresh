"""
Unified AI Agent Brain - Enhanced features with legacy compatibility
"""
import os
import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import deque
import openai
from sqlalchemy.orm import Session

# Try to import knowledge base if available
try:
    from server.services.knowledge_base import KnowledgeBase
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_BASE_AVAILABLE = False
    logger.warning("Knowledge base service not available - running without knowledge integration")

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

class UnifiedAgentBrain:
    """
    Unified AI processing engine with enhanced features and legacy compatibility
    """
    
    def __init__(
        self,
        llm_client=None,
        knowledge_provider=None,
        analysis_provider=None,
        conversation_model: str = None,
        analysis_model: str = None,
        max_tokens: int = 120,
        temperature: float = 0.8,
        interruption_detector=None,
    ):
        """
        Dependency injection constructor with fallback to legacy initialization
        All dependencies can be provided by the caller or fallback to environment/defaults
        """
        # Use injected dependencies or initialize from environment (legacy compatibility)
        self.llm_client = llm_client or self._init_legacy_llm_client()
        self.knowledge_provider = knowledge_provider or self._init_legacy_knowledge_provider()
        self.analysis_provider = analysis_provider or self._init_legacy_analysis_provider()
        
        # Model configuration
        self.conversation_model = conversation_model or os.getenv('CONVERSATION_MODEL', 'anthropic/claude-3-sonnet')
        self.analysis_model = analysis_model or os.getenv('ANALYSIS_MODEL', 'openai/gpt-4o-mini')
        self.default_model = "openai/gpt-4o-mini"  # Legacy compatibility
        
        # Conversation settings
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Enhanced features
        self.conversation_states = {}  # Track state per call
        self.interruption_threshold = 0.5  # seconds
        self.last_response_time = {}
        self.interruption_detector = interruption_detector or self._default_interruption_detector
        
        # Legacy compatibility
        self.current_system_prompt = None
        
        # Alias for legacy compatibility
        self.openai_client = self.llm_client
    
    def _init_legacy_llm_client(self):
        """Legacy initialization for LLM client"""
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            return openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            logger.warning("OpenRouter API key not found - UnifiedAgentBrain will not function")
            return None
    
    def _init_legacy_knowledge_provider(self):
        """Legacy initialization for knowledge provider"""
        if KNOWLEDGE_BASE_AVAILABLE:
            # Return a wrapper that creates KnowledgeBase instances with db_session
            class LegacyKnowledgeProvider:
                def get_context_for_conversation(self, agent_id, conversation_text, max_tokens, db_session=None):
                    if db_session:
                        kb = KnowledgeBase(db_session)
                        return kb.get_context_for_conversation(agent_id, conversation_text, max_tokens)
                    return None
            return LegacyKnowledgeProvider()
        return None
    
    def _init_legacy_analysis_provider(self):
        """Legacy initialization for analysis provider"""
        class LegacyAnalysisProvider:
            def __init__(self, llm_client, analysis_model):
                self.llm_client = llm_client
                self.analysis_model = analysis_model
            
            def analyze(self, user_input, state):
                return self._analyze_input_legacy(user_input, state)
            
            def _analyze_input_legacy(self, user_input, state):
                """Legacy analysis using the LLM client"""
                try:
                    if not self.llm_client:
                        return self._basic_analysis(user_input)
                    
                    analysis_prompt = f"""Analyze this phone conversation input:
Input: "{user_input}"

Extract:
1. Intent (e.g., question, complaint, request, confirmation)
2. Sentiment (positive/neutral/negative)
3. Key entities (names, dates, amounts, etc.)
4. Topic category
5. Urgency level (low/medium/high)

Response format: JSON only"""

                    response = self.llm_client.chat.completions.create(
                        model=self.analysis_model,
                        messages=[{"role": "user", "content": analysis_prompt}],
                        max_tokens=150,
                        temperature=0.3,
                        timeout=3
                    )
                    
                    try:
                        analysis = json.loads(response.choices[0].message.content)
                        return analysis
                    except:
                        return self._basic_analysis(user_input)
                        
                except Exception as e:
                    logger.error(f"Analysis failed: {e}")
                    return self._basic_analysis(user_input)
            
            def _basic_analysis(self, user_input):
                """Basic fallback analysis"""
                lower_input = user_input.lower()
                
                if any(word in lower_input for word in ['angry', 'frustrated', 'upset', 'terrible']):
                    sentiment = 'negative'
                elif any(word in lower_input for word in ['great', 'perfect', 'excellent', 'thank']):
                    sentiment = 'positive'
                else:
                    sentiment = 'neutral'
                    
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
        
        return LegacyAnalysisProvider(self.llm_client, self.analysis_model)
    
    def _default_interruption_detector(self, call_sid: str, user_input: str) -> bool:
        """Default logic for detecting interruption (can be replaced via DI)"""
        if call_sid not in self.last_response_time:
            return False
        time_since_response = time.time() - self.last_response_time[call_sid]
        is_short = len(user_input.split()) < 3
        is_quick = time_since_response < self.interruption_threshold
        return is_short and is_quick
        
    def set_agent_instructions(self, system_prompt: str):
        """
        Legacy compatibility - Set specialized instructions for current conversation
        """
        self.current_system_prompt = system_prompt
        logger.info("Updated agent instructions for specialized behavior")
    
    def process_conversation(
        self, 
        user_input: str, 
        conversation_history: List[str], 
        agent_id: Optional[int] = None, 
        db_session: Optional[Session] = None
    ) -> str:
        """
        Legacy compatible interface with enhanced processing
        """
        # Create a simple call_sid for state tracking
        call_sid = f"legacy_{hash(str(conversation_history))}"
        
        # Build agent config from legacy data
        agent_config = {
            'id': agent_id,
            'system_prompt': self.current_system_prompt or self._get_default_prompt()
        }
        
        # Use enhanced processing
        ai_response, metadata = self.process_conversation_enhanced(
            user_input=user_input,
            call_sid=call_sid,
            agent_config=agent_config,
            conversation_history=conversation_history,
            db_session=db_session
        )
        
        return ai_response
    
    def process_conversation_enhanced(
        self, 
        user_input: str, 
        call_sid: str,
        agent_config: Dict[str, Any],
        conversation_history: List[str],
        db_session: Optional[Session] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Enhanced conversation processing with full state tracking
        """
        try:
            if not self.openai_client:
                return "I'm having trouble connecting right now. Please try again.", {"error": "No client"}
            
            # Get or create conversation state
            state = self.get_conversation_state(call_sid)
            if not state:
                state = self.create_conversation_state(call_sid)
            
            # Detect interruption (using injected detector)
            is_interruption = self.interruption_detector(call_sid, user_input)
            
            # Analyze user input via injected analysis provider
            analysis = self.analysis_provider.analyze(user_input, state)
            
            # Get knowledge context via injected provider
            knowledge_context = None
            if self.knowledge_provider and db_session and agent_config.get('id'):
                try:
                    knowledge_context = self.knowledge_provider.get_context_for_conversation(
                        agent_id=agent_config['id'],
                        conversation_text=user_input,
                        max_tokens=500,
                        db_session=db_session,
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
    
    def create_conversation_state(self, call_sid: str) -> ConversationState:
        """Create a new conversation state for a call"""
        state = ConversationState(call_sid)
        self.conversation_states[call_sid] = state
        return state
        
    def get_conversation_state(self, call_sid: str) -> Optional[ConversationState]:
        """Get conversation state for a call"""
        return self.conversation_states.get(call_sid)
    
    # Legacy methods now delegate to injected providers
    def _detect_interruption(self, call_sid: str, user_input: str) -> bool:
        """Legacy method - now delegates to injected interruption detector"""
        return self.interruption_detector(call_sid, user_input)
    
    def _analyze_input(self, user_input: str, state: ConversationState) -> Dict[str, Any]:
        """Legacy method - now delegates to injected analysis provider"""
        return self.analysis_provider.analyze(user_input, state)
    
    def _basic_analysis(self, user_input: str) -> Dict[str, Any]:
        """Legacy method - now delegates to injected analysis provider"""
        # Create a dummy state for basic analysis
        dummy_state = ConversationState("legacy_basic")
        return self.analysis_provider.analyze(user_input, dummy_state)
    
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
    
    def _optimize_for_voice(self, text: str, state: Optional[ConversationState] = None) -> str:
        """Optimize text for natural speech with enhanced context"""
        
        # Remove any markdown or formatting
        text = text.replace('*', '').replace('_', '').replace('#', '')
        text = text.replace("**", "").replace("`", "")
        
        # Replace symbols with words
        text = text.replace("&", "and")
        text = text.replace("@", "at") 
        text = text.replace("#", "number")
        text = text.replace("$", "dollars")
        text = text.replace("%", "percent")
        text = text.replace("+", "plus")
        
        # Improve pronunciation of common terms
        text = text.replace("API", "A P I")
        text = text.replace("URL", "U R L")
        text = text.replace("FAQ", "F A Q")
        text = text.replace("CEO", "C E O")
        
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
        
        # Enhanced context-aware optimization
        if state and state.conversation_phase == 'discovery' and '?' in text:
            # Add slight pause before questions
            text = text.replace('?', '?...')
        
        # Ensure natural speech flow
        text = text.replace("...", ". ")
        
        # Keep responses concise for voice
        if len(text) > 300:
            sentences = text.split('. ')
            text = '. '.join(sentences[:2]) + '.'
        
        # Ensure it ends properly
        if not text.endswith(('.', '!', '?')):
            text += '.'
            
        return text.strip()
    
    # Legacy compatibility methods
    def generate_conversation_summary(self, conversation_history: List[str]) -> str:
        """Legacy method - Generate a summary of the conversation for SMS follow-up"""
        try:
            if not conversation_history:
                return "We discussed your inquiry and provided assistance."
            
            # Get user messages (every other message starting from 0)
            user_messages = [conversation_history[i] for i in range(0, len(conversation_history), 2)]
            
            if len(user_messages) == 1:
                return f"We discussed: {user_messages[0][:50]}..."
            elif len(user_messages) <= 3:
                topics = ", ".join(user_messages[:2])
                return f"We discussed your questions about {topics}."
            else:
                return "We had a detailed conversation about your inquiry and provided solutions."
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "We discussed your inquiry and provided assistance."
    
    def generate_summary(self, conversation_history: List[str]) -> Dict[str, Any]:
        """Legacy method - Generate conversation summary with metadata"""
        try:
            if not conversation_history:
                return {
                    'summary': 'No conversation recorded',
                    'key_topics': [],
                    'sentiment': 'neutral',
                    'resolution_status': 'incomplete'
                }
            
            # Create summary prompt
            conversation_text = '\n'.join([
                f"{'User' if i % 2 == 0 else 'Assistant'}: {turn}"
                for i, turn in enumerate(conversation_history)
            ])
            
            summary_prompt = f"""
Please summarize this customer service conversation:

{conversation_text}

Provide a brief summary focusing on:
- Main issue or request
- Key points discussed
- Resolution or next steps

Keep it concise and professional.
"""
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": summary_prompt}],
                    max_tokens=150,
                    temperature=0.3
                )
                summary = response.choices[0].message.content.strip()
            else:
                # Fallback summary
                summary = f"Customer conversation with {len(conversation_history)} exchanges. Main topic: {conversation_history[0][:50]}..."
            
            return {
                'summary': summary,
                'key_topics': self._extract_topics(conversation_history),
                'sentiment': 'positive',  # Could be enhanced with sentiment analysis
                'resolution_status': 'completed',
                'turn_count': len(conversation_history)
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                'summary': f"Conversation completed with {len(conversation_history)} exchanges",
                'key_topics': [],
                'sentiment': 'neutral',
                'resolution_status': 'completed'
            }
    
    def _extract_topics(self, conversation_history: List[str]) -> List[str]:
        """Extract key topics from conversation"""
        topics = []
        keywords = ['billing', 'support', 'technical', 'account', 'payment', 'service', 'help']
        
        conversation_text = ' '.join(conversation_history).lower()
        for keyword in keywords:
            if keyword in conversation_text:
                topics.append(keyword)
        
        return topics[:3]  # Return top 3 topics
    
    def _get_default_prompt(self) -> str:
        """Get default system prompt"""
        return os.getenv(
            'DEFAULT_INSTRUCTIONS',
            "You are a helpful customer service representative. Be friendly, professional, and concise in your responses."
        )
    
    def get_conversation_metrics(self, conversation_history: List[str]) -> Dict[str, Any]:
        """Get metrics about the conversation"""
        user_messages = [conversation_history[i] for i in range(0, len(conversation_history), 2)]
        assistant_messages = [conversation_history[i] for i in range(1, len(conversation_history), 2)]
        
        return {
            "total_turns": len(conversation_history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "avg_user_message_length": sum(len(msg) for msg in user_messages) / len(user_messages) if user_messages else 0,
            "avg_assistant_message_length": sum(len(msg) for msg in assistant_messages) / len(assistant_messages) if assistant_messages else 0
        }

# Factory function for creating instances with proper dependency injection
def create_unified_agent_brain(
    llm_client=None,
    knowledge_provider=None,
    analysis_provider=None,
    conversation_model: str = None,
    analysis_model: str = None,
    max_tokens: int = 120,
    temperature: float = 0.8,
    interruption_detector=None,
):
    """Factory function for dependency injection"""
    return UnifiedAgentBrain(
        llm_client=llm_client,
        knowledge_provider=knowledge_provider,
        analysis_provider=analysis_provider,
        conversation_model=conversation_model,
        analysis_model=analysis_model,
        max_tokens=max_tokens,
        temperature=temperature,
        interruption_detector=interruption_detector,
    )

# Global unified agent brain instance with legacy compatibility
agent_brain = UnifiedAgentBrain()