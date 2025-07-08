"""
Call Session Management - Per-call state isolation for concurrent calls
"""
import os
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from src.services.agent_brain_unified import agent_brain
from src.services.call_router import call_router
from src.models.call import Call, Message, db
from src.models.customer import Customer

logger = logging.getLogger(__name__)

class CallSession:
    """
    Isolated session for each call to prevent cross-call interference
    """

    def __init__(
        self,
        call_sid: str,
        phone_number: str,
        agent_brain,
        call_router,
        twilio_phone_number: str,
        db_session=None,
        customer_finder: Optional[Callable[[str], Any]] = None,
    ):
        self.call_sid = call_sid
        self.phone_number = phone_number
        self.created_at = datetime.utcnow()

        # Injected dependencies
        self.agent_brain = agent_brain
        self.call_router = call_router
        self.db_session = db_session if db_session is not None else db.session
        self.customer_finder = customer_finder if customer_finder is not None else self.default_customer_finder
        self.twilio_phone_number = twilio_phone_number

        # Call-specific state
        self.conversation_history = []
        self.agent_config = None
        self.agent_type = 'general'
        self.routing_confidence = 0.0
        self.matched_keywords = []
        self.turn_count = 0
        self.max_turns = 20

        # Call tracking
        self.call_record = None
        self.is_active = True

        logger.info(f"Created isolated call session for {call_sid}")

    def default_customer_finder(self, phone_number: str):
        """
        Default customer finder/creator function
        """
        customer = Customer.query.filter_by(phone_number=phone_number).first()
        if not customer:
            customer = Customer(phone_number=phone_number)
            self.db_session.add(customer)
            self.db_session.commit()
        return customer

    def route_call(self, initial_input: str) -> Dict[str, Any]:
        """
        Route the call to appropriate agent with isolated state
        """
        try:
            # Use injected call router to determine agent
            routing_decision = self.call_router.route_call(
                self.call_sid,
                initial_input,
                self.phone_number
            )

            # Store routing information in this session
            self.agent_type = routing_decision['agent_type']
            self.routing_confidence = routing_decision['confidence']
            self.matched_keywords = routing_decision['matched_keywords']
            self.max_turns = routing_decision.get('max_turns', 20)

            # Configure the agent brain for this specific call
            self.agent_brain.set_agent_instructions(routing_decision['system_prompt'])

            # Find or create customer via injected customer_finder
            customer = self.customer_finder(self.phone_number)

            # Create call record in database
            self.call_record = Call(
                call_sid=self.call_sid,
                from_number=self.phone_number,
                to_number=self.twilio_phone_number,
                agent_type=self.agent_type,
                routing_confidence=self.routing_confidence,
                routing_keywords=','.join(self.matched_keywords),
                status='active',
                customer_id=customer.id
            )
            self.db_session.add(self.call_record)
            self.db_session.commit()

            # Update customer stats
            customer.update_stats()
            self.db_session.commit()

            # TODO: Plugin hook for metrics and routing analytics

            logger.info(f"Call {self.call_sid} routed to {self.agent_type} agent (confidence: {self.routing_confidence:.2f})")

            return routing_decision

        except Exception as e:
            logger.error(f"Error routing call {self.call_sid}: {e}")
            # Fallback to general agent
            self.agent_type = 'general'
            self.agent_brain.set_agent_instructions(
                "You are a helpful customer service representative for A Killion Voice. Be friendly, professional, and concise."
            )
            return {
                'agent_type': 'general',
                'confidence': 0.1,
                'system_prompt': self.agent_brain.current_system_prompt
            }

    def process_conversation_turn(self, user_input: str) -> str:
        """
        Process a conversation turn with isolated state
        """
        try:
            # Check turn limits
            if self.turn_count >= self.max_turns:
                return "Thank you for calling A Killion Voice. I need to end this call now, but please feel free to call back if you need more assistance."

            # Add user input to conversation history
            self.conversation_history.append(user_input)

            # Generate AI response using this call's agent brain
            ai_response = self.agent_brain.process_conversation(
                user_input,
                self.conversation_history
            )

            # Add AI response to conversation history
            self.conversation_history.append(ai_response)

            # Save conversation turn to database
            user_message = Message(
                call_id=self.call_record.id if self.call_record else None,
                role='user',
                content=user_input
            )

            assistant_message = Message(
                call_id=self.call_record.id if self.call_record else None,
                role='assistant',
                content=ai_response
            )

            self.db_session.add(user_message)
            self.db_session.add(assistant_message)
            self.db_session.commit()

            # TODO: Plugin hook for conversation logging and analytics

            self.turn_count += 1

            logger.info(f"Processed turn {self.turn_count} for call {self.call_sid}")

            return ai_response

        except Exception as e:
            logger.error(f"Error processing conversation for {self.call_sid}: {e}")
            return "I'm sorry, I had trouble processing that. Could you please repeat your question?"

    def end_call(self, call_status: str = 'completed') -> Dict[str, Any]:
        """
        End the call session and generate summary
        """
        try:
            self.is_active = False

            # Generate conversation summary
            summary = self.agent_brain.generate_summary(self.conversation_history)

            # Update call record
            if self.call_record:
                self.call_record.status = call_status
                self.call_record.duration = (datetime.utcnow() - self.created_at).total_seconds()
                self.call_record.turn_count = self.turn_count
                self.call_record.summary = summary.get('summary', 'Call completed')
                self.db_session.commit()

            # TODO: Plugin hook for call summary storage and post-call processing

            logger.info(f"Call session {self.call_sid} ended with status: {call_status}")

            return {
                'call_sid': self.call_sid,
                'agent_type': self.agent_type,
                'turn_count': self.turn_count,
                'summary': summary,
                'phone_number': self.phone_number
            }

        except Exception as e:
            logger.error(f"Error ending call {self.call_sid}: {e}")
            return {
                'call_sid': self.call_sid,
                'agent_type': self.agent_type,
                'summary': {'summary': 'Call ended with errors'}
            }

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get current session information
        """
        return {
            'call_sid': self.call_sid,
            'phone_number': self.phone_number,
            'agent_type': self.agent_type,
            'turn_count': self.turn_count,
            'max_turns': self.max_turns,
            'is_active': self.is_active,
            'routing_confidence': self.routing_confidence,
            'matched_keywords': self.matched_keywords,
            'conversation_length': len(self.conversation_history)
        }

class CallSessionManager:
    """
    Thread-safe manager for call sessions
    """

    def __init__(self, session_factory: Optional[Callable[..., CallSession]] = None):
        self.sessions: Dict[str, CallSession] = {}
        self.lock = threading.RLock()
        self.session_factory = session_factory
        logger.info("CallSessionManager initialized")

    def create_session(self, call_sid: str, phone_number: str) -> CallSession:
        """
        Create a new call session
        """
        with self.lock:
            if call_sid in self.sessions:
                logger.warning(f"Session {call_sid} already exists, returning existing")
                return self.sessions[call_sid]

            if self.session_factory is None:
                raise ValueError("No CallSession factory provided to CallSessionManager")

            session = self.session_factory(call_sid, phone_number)
            self.sessions[call_sid] = session

            logger.info(f"Created new session for call {call_sid}")
            return session

    def get_session(self, call_sid: str) -> Optional[CallSession]:
        """
        Get an existing call session
        """
        with self.lock:
            return self.sessions.get(call_sid)

    def end_session(self, call_sid: str, call_status: str = 'completed') -> Optional[Dict[str, Any]]:
        """
        End and remove a call session
        """
        with self.lock:
            session = self.sessions.get(call_sid)
            if session:
                result = session.end_call(call_status)
                del self.sessions[call_sid]
                logger.info(f"Ended and removed session {call_sid}")
                return result
            else:
                logger.warning(f"Attempted to end non-existent session {call_sid}")
                return None

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get information about all active sessions
        """
        with self.lock:
            return [session.get_session_info() for session in self.sessions.values() if session.is_active]

    def cleanup_inactive_sessions(self):
        """
        Remove inactive sessions (cleanup utility)
        """
        with self.lock:
            inactive_sids = [sid for sid, session in self.sessions.items() if not session.is_active]
            for sid in inactive_sids:
                del self.sessions[sid]

            if inactive_sids:
                logger.info(f"Cleaned up {len(inactive_sids)} inactive sessions")

def create_call_session_factory():
    """
    Factory function that creates CallSession instances with unified dependencies
    """
    def session_factory(call_sid: str, phone_number: str):
        return CallSession(
            call_sid=call_sid,
            phone_number=phone_number,
            agent_brain=agent_brain,  # Use unified agent brain
            call_router=call_router,
            twilio_phone_number=os.getenv('TWILIO_PHONE_NUMBER', '+19786432034'),
            db_session=db.session
        )
    return session_factory

# Global session manager instance with unified dependencies
session_manager = CallSessionManager(session_factory=create_call_session_factory())
