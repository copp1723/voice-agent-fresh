"""
AI Agent Brain - Core conversation processing with OpenRouter
"""
import os
import logging
from typing import Dict, Any, List, Optional
import openai

logger = logging.getLogger(__name__)

class AgentBrain:
    """
    Core AI processing engine for voice conversations
    """
    
    def __init__(self):
        # Get API key with fallback
        api_key = os.getenv('OPENROUTER_API_KEY')
        
        if api_key:
            self.openai_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.openai_client = None
            logger.warning("OpenRouter API key not found - AgentBrain will not function")
        self.default_model = "openai/gpt-4o-mini"
        self.current_system_prompt = None
        self.max_tokens = 150  # Keep responses concise for voice
        self.temperature = 0.7
    
    def set_agent_instructions(self, system_prompt: str):
        """
        Set specialized instructions for current conversation
        
        Args:
            system_prompt: Agent-specific system prompt
        """
        self.current_system_prompt = system_prompt
        logger.info("Updated agent instructions for specialized behavior")
    
    def process_conversation(self, user_input: str, conversation_history: List[str]) -> str:
        """
        Process user input and generate AI response optimized for voice
        
        Args:
            user_input: User's spoken input
            conversation_history: Previous conversation turns
            
        Returns:
            AI response text optimized for speech
        """
        try:
            if not self.openai_client:
                return "I'm sorry, I'm having trouble connecting to my AI service. Please try again later."
            
            # Build conversation messages
            messages = []
            
            # Add system prompt
            system_prompt = self.current_system_prompt or self._get_default_prompt()
            messages.append({
                "role": "system",
                "content": f"{system_prompt}\n\nImportant: Keep responses concise and conversational since this is a voice conversation. Use simple language, avoid technical jargon, and speak naturally as if talking to someone on the phone. Responses should be 1-2 sentences maximum unless specifically asked for details."
            })
            
            # Add conversation history (alternating user/assistant)
            for i, msg in enumerate(conversation_history[-20:]):  # Last 20 messages
                role = "user" if i % 2 == 0 else "assistant"
                messages.append({"role": role, "content": msg})
            
            # Add current user input
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=30
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Optimize for voice synthesis
            ai_response = self._optimize_for_voice(ai_response)
            
            logger.info(f"Generated voice-optimized response: {ai_response[:100]}...")
            return ai_response
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return "I'm sorry, I had trouble processing that. Could you please repeat your question?"
    
    def _optimize_for_voice(self, text: str) -> str:
        """
        Optimize text for better voice synthesis
        
        Args:
            text: Original AI response
            
        Returns:
            Voice-optimized text
        """
        # Remove markdown formatting
        optimized = text.replace("**", "").replace("*", "")
        optimized = optimized.replace("_", "").replace("`", "")
        
        # Replace symbols with words
        optimized = optimized.replace("&", "and")
        optimized = optimized.replace("@", "at") 
        optimized = optimized.replace("#", "number")
        optimized = optimized.replace("$", "dollars")
        optimized = optimized.replace("%", "percent")
        optimized = optimized.replace("+", "plus")
        
        # Improve pronunciation of common terms
        optimized = optimized.replace("API", "A P I")
        optimized = optimized.replace("URL", "U R L")
        optimized = optimized.replace("FAQ", "F A Q")
        optimized = optimized.replace("CEO", "C E O")
        
        # Ensure natural speech flow
        optimized = optimized.replace("...", ". ")
        
        # Keep responses concise for voice
        if len(optimized) > 300:
            sentences = optimized.split('. ')
            optimized = '. '.join(sentences[:2]) + '.'
        
        return optimized
    
    def generate_conversation_summary(self, conversation_history: List[str]) -> str:
        """
        Generate a summary of the conversation for SMS follow-up
        
        Args:
            conversation_history: Complete conversation history
            
        Returns:
            Summary text
        """
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
        """
        Generate conversation summary
        
        Args:
            conversation_history: List of conversation turns
            
        Returns:
            Dictionary with summary and metadata
        """
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
        """
        Determine if conversation should end based on AI response
        
        Args:
            ai_response: Latest AI response
            conversation_history: Conversation history
            
        Returns:
            True if conversation should end
        """
        # Check for conversation end indicators in AI response
        end_phrases = [
            "goodbye", "thank you for calling", "have a great day",
            "is there anything else", "that completes", "we're all set",
            "have a wonderful day", "thanks for calling"
        ]
        
        ai_response_lower = ai_response.lower()
        
        # Check if AI indicated end of conversation
        if any(phrase in ai_response_lower for phrase in end_phrases):
            return True
        
        # Check conversation length
        max_turns = int(os.getenv('MAX_CONVERSATION_TURNS', 20))
        if len(conversation_history) >= max_turns:
            return True
        
        return False
    
    def _get_default_prompt(self) -> str:
        """
        Get default system prompt
        
        Returns:
            Default system prompt
        """
        return os.getenv(
            'DEFAULT_INSTRUCTIONS',
            "You are a helpful customer service representative. Be friendly, professional, and concise in your responses."
        )
    
    def get_conversation_metrics(self, conversation_history: List[str]) -> Dict[str, Any]:
        """
        Get metrics about the conversation
        
        Args:
            conversation_history: Conversation history
            
        Returns:
            Conversation metrics
        """
        user_messages = [conversation_history[i] for i in range(0, len(conversation_history), 2)]
        assistant_messages = [conversation_history[i] for i in range(1, len(conversation_history), 2)]
        
        return {
            "total_turns": len(conversation_history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "avg_user_message_length": sum(len(msg) for msg in user_messages) / len(user_messages) if user_messages else 0,
            "avg_assistant_message_length": sum(len(msg) for msg in assistant_messages) / len(assistant_messages) if assistant_messages else 0
        }

