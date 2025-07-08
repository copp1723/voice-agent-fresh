"""
Enhanced Agent Brain with Vector Search Integration
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import openai
from sqlalchemy.orm import Session
from server.services.vector_search_service import VectorSearchService
from server.models.enhanced_models import EnhancedAgentConfig

logger = logging.getLogger(__name__)


class EnhancedAgentBrain:
    """
    Enhanced AI processing engine with semantic search capabilities
    """
    
    def __init__(self, db: Session):
        """
        Initialize enhanced agent brain
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.vector_search = VectorSearchService(db)
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            self.openai_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.openai_client = None
            logger.warning("OpenRouter API key not found - AgentBrain will not function")
        
        # Configuration
        self.default_model = "openai/gpt-4o-mini"
        self.max_tokens = 200
        self.temperature = 0.7
        self.context_token_limit = 1000
        self.relevance_threshold = 0.75
    
    def process_message(self, agent_id: int, user_message: str, 
                       conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Process user message with enhanced context from vector search
        
        Args:
            agent_id: ID of the agent
            user_message: User's message
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Get agent configuration
            agent = self.db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
            if not agent:
                return {
                    'response': "I'm sorry, I'm not properly configured right now.",
                    'error': f"Agent {agent_id} not found"
                }
            
            # Get relevant context from vector search
            context = self._get_enhanced_context(agent_id, user_message, conversation_history)
            
            # Build enhanced system prompt
            system_prompt = self._build_enhanced_prompt(agent, context)
            
            # Generate response
            response = self._generate_response(system_prompt, user_message, conversation_history)
            
            return {
                'response': response,
                'context_used': len(context) > 0,
                'context_sources': [c['domain'] for c in context],
                'agent_id': agent_id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'response': "I'm sorry, I encountered an error processing your request.",
                'error': str(e)
            }
    
    def _get_enhanced_context(self, agent_id: int, user_message: str, 
                            conversation_history: List[Dict] = None) -> List[Dict]:
        """
        Get enhanced context using vector search
        
        Args:
            agent_id: ID of the agent
            user_message: Current user message
            conversation_history: Previous conversation
            
        Returns:
            List of relevant context entries
        """
        # Combine current message with recent conversation for context
        search_text = user_message
        
        if conversation_history:
            # Include last 3 messages for context
            recent_messages = conversation_history[-3:]
            conversation_text = " ".join([
                msg.get('content', '') for msg in recent_messages
                if msg.get('role') in ['user', 'assistant']
            ])
            search_text = f"{conversation_text} {user_message}"
        
        # Search for relevant knowledge
        search_results = self.vector_search.search_agent_knowledge(
            agent_id=agent_id,
            query=search_text,
            top_k=5
        )
        
        # Filter by relevance threshold
        relevant_context = [
            result for result in search_results 
            if result['score'] >= self.relevance_threshold
        ]
        
        return relevant_context
    
    def _build_enhanced_prompt(self, agent: EnhancedAgentConfig, 
                             context: List[Dict]) -> str:
        """
        Build enhanced system prompt with context
        
        Args:
            agent: Agent configuration
            context: Relevant context from vector search
            
        Returns:
            Enhanced system prompt
        """
        base_prompt = agent.system_prompt or "You are a helpful customer service agent."
        
        # Add personality traits if available
        if agent.personality_traits:
            traits = ", ".join(agent.personality_traits)
            base_prompt += f"\n\nPersonality: Be {traits} in your responses."
        
        # Add conversation style
        if agent.conversation_style:
            base_prompt += f"\n\nConversation style: {agent.conversation_style}"
        
        # Add relevant context
        if context:
            context_parts = []
            current_tokens = 0
            
            for ctx in context:
                # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
                ctx_tokens = len(ctx['content']) // 4
                if current_tokens + ctx_tokens > self.context_token_limit:
                    break
                
                context_parts.append(f"[{ctx['domain']}] {ctx['content']}")
                current_tokens += ctx_tokens
            
            if context_parts:
                context_text = "\n".join(context_parts)
                base_prompt += f"\n\nRelevant Information:\n{context_text}"
                base_prompt += "\n\nUse this information to help answer questions accurately."
        
        return base_prompt
    
    def _generate_response(self, system_prompt: str, user_message: str, 
                         conversation_history: List[Dict] = None) -> str:
        """
        Generate response using OpenAI API
        
        Args:
            system_prompt: Enhanced system prompt
            user_message: User's message
            conversation_history: Previous conversation
            
        Returns:
            Generated response
        """
        if not self.openai_client:
            return "I'm sorry, I'm not properly configured to respond right now."
        
        try:
            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 5 messages to keep context reasonable)
            if conversation_history:
                recent_history = conversation_history[-5:]
                for msg in recent_history:
                    if msg.get('role') in ['user', 'assistant']:
                        messages.append({
                            "role": msg['role'],
                            "content": msg['content']
                        })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, I couldn't process your request right now."
    
    def search_knowledge(self, query: str, domain: str = None, 
                        agent_id: int = None) -> List[Dict]:
        """
        Search knowledge base directly
        
        Args:
            query: Search query
            domain: Optional domain filter
            agent_id: Optional agent filter
            
        Returns:
            List of search results
        """
        if agent_id:
            return self.vector_search.search_agent_knowledge(agent_id, query)
        elif domain:
            return self.vector_search.search_by_domain(domain, query)
        else:
            return self.vector_search.multi_domain_search(query)
    
    def add_knowledge(self, domain: str, content: str, 
                     metadata: Dict = None) -> Optional[int]:
        """
        Add knowledge to the knowledge base
        
        Args:
            domain: Domain for the knowledge
            content: Knowledge content
            metadata: Optional metadata
            
        Returns:
            ID of created knowledge entry
        """
        return self.vector_search.add_knowledge_entry(domain, content, metadata)
    
    def get_agent_domains(self, agent_id: int) -> List[str]:
        """
        Get domains associated with an agent
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of domain names
        """
        try:
            agent = self.db.query(EnhancedAgentConfig).filter_by(id=agent_id).first()
            if not agent:
                return []
            
            return [ad.domain.domain_name for ad in agent.domains if ad.domain]
            
        except Exception as e:
            logger.error(f"Error getting agent domains: {e}")
            return []
    
    def get_conversation_summary(self, agent_id: int, 
                               conversation_history: List[Dict]) -> str:
        """
        Generate a summary of the conversation with relevant context
        
        Args:
            agent_id: ID of the agent
            conversation_history: Full conversation history
            
        Returns:
            Conversation summary
        """
        if not conversation_history:
            return "No conversation history available."
        
        # Extract key messages
        user_messages = [
            msg['content'] for msg in conversation_history 
            if msg.get('role') == 'user'
        ]
        
        # Get context for the overall conversation
        conversation_text = " ".join(user_messages)
        context = self._get_enhanced_context(agent_id, conversation_text)
        
        # Build summary prompt
        summary_prompt = f"""
        Summarize this conversation, highlighting key points and any relevant context.
        
        Conversation:
        {conversation_text}
        
        Context information:
        {'; '.join([ctx['content'][:100] for ctx in context[:3]])}
        
        Provide a concise summary focusing on the customer's needs and any actions taken.
        """
        
        return self._generate_response(summary_prompt, "", [])


# Example usage in routes
def create_enhanced_agent_processor(db: Session) -> EnhancedAgentBrain:
    """
    Factory function to create enhanced agent brain
    
    Args:
        db: Database session
        
    Returns:
        Enhanced agent brain instance
    """
    return EnhancedAgentBrain(db)


# Integration with existing voice processing
def process_voice_message_enhanced(db: Session, agent_id: int, 
                                 user_message: str, call_session: Dict) -> Dict:
    """
    Process voice message with enhanced context
    
    Args:
        db: Database session
        agent_id: ID of the agent
        user_message: Transcribed user message
        call_session: Current call session data
        
    Returns:
        Processing result with enhanced response
    """
    # Initialize enhanced brain
    brain = EnhancedAgentBrain(db)
    
    # Get conversation history from call session
    conversation_history = call_session.get('messages', [])
    
    # Process message with enhanced context
    result = brain.process_message(agent_id, user_message, conversation_history)
    
    # Update call session with new message
    if 'messages' not in call_session:
        call_session['messages'] = []
    
    call_session['messages'].extend([
        {'role': 'user', 'content': user_message},
        {'role': 'assistant', 'content': result['response']}
    ])
    
    return result