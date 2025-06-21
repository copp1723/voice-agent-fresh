"""
SMS Follow-up Service - Professional SMS messaging after calls
"""
import os
import logging
from typing import Dict, Any, Optional
from twilio.rest import Client
from src.models.call import SMSLog, AgentConfig, db

logger = logging.getLogger(__name__)

class SMSService:
    """
    Professional SMS follow-up service for A Killion Voice
    """
    
    def __init__(self):
        self.twilio_client = None
        self.from_number = None
        self._initialize_twilio()
    
    def _initialize_twilio(self):
        """
        Initialize Twilio client for SMS
        """
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.from_number = os.getenv('TWILIO_PHONE_NUMBER', '+19786432034')
            
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
                logger.info("SMS service initialized successfully")
            else:
                logger.warning("Twilio credentials not found - SMS service in test mode")
        except Exception as e:
            logger.error(f"Failed to initialize SMS service: {e}")
    
    def send_call_follow_up(
        self, 
        call_id: int,
        to_number: str, 
        agent_type: str, 
        conversation_summary: str,
        call_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send professional SMS follow-up after call completion
        
        Args:
            call_id: Database call ID
            to_number: Customer phone number
            agent_type: Type of agent that handled the call
            conversation_summary: Summary of conversation
            call_duration: Call duration in seconds
            
        Returns:
            SMS sending result
        """
        try:
            # Get agent configuration for SMS template
            agent_config = AgentConfig.query.filter_by(agent_type=agent_type).first()
            
            # Generate SMS message
            message_body = self._generate_sms_message(
                agent_type, 
                agent_config, 
                conversation_summary, 
                call_duration
            )
            
            # Send SMS
            result = self._send_sms(to_number, message_body)
            
            # Log SMS in database
            if result['success']:
                sms_log = SMSLog(
                    call_id=call_id,
                    sms_sid=result.get('sms_sid'),
                    to_number=to_number,
                    message_body=message_body,
                    status='sent',
                    template_type=agent_type,
                    agent_type=agent_type
                )
                db.session.add(sms_log)
                db.session.commit()
                
                logger.info(f"SMS follow-up sent to {to_number} for call {call_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending SMS follow-up: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_sms_message(
        self, 
        agent_type: str, 
        agent_config: Optional[AgentConfig], 
        summary: str, 
        duration: Optional[int]
    ) -> str:
        """
        Generate personalized SMS message based on agent type and conversation
        
        Args:
            agent_type: Agent type
            agent_config: Agent configuration
            summary: Conversation summary
            duration: Call duration
            
        Returns:
            SMS message text
        """
        # Use agent-specific template if available
        if agent_config and agent_config.sms_template:
            template = agent_config.sms_template
            
            # Replace placeholders
            message = template.format(
                summary=summary,
                company_name="A Killion Voice",
                duration=f"{duration//60}:{duration%60:02d}" if duration else "a few minutes"
            )
        else:
            # Default templates by agent type
            templates = {
                'billing': f"Thanks for calling A Killion Voice about your billing inquiry. {summary} If you need further assistance with your account, please reply or call us back at (978) 643-2034.",
                
                'support': f"Thanks for calling A Killion Voice technical support. {summary} We've provided troubleshooting steps to help resolve your issue. Reply if you need more assistance!",
                
                'sales': f"Thanks for your interest in A Killion Voice services! {summary} I'll follow up with more information about our solutions. Questions? Just reply or call (978) 643-2034!",
                
                'scheduling': f"Thanks for scheduling with A Killion Voice! {summary} We'll send appointment confirmations and reminders. Reply to make changes or call (978) 643-2034.",
                
                'general': f"Thanks for calling A Killion Voice! {summary} We're here to help whenever you need us. Reply to this message or call (978) 643-2034 for assistance."
            }
            
            message = templates.get(agent_type, templates['general'])
        
        # Ensure message is within SMS limits (160 characters for single SMS)
        if len(message) > 160:
            # Truncate summary if message is too long
            max_summary_length = 160 - len(message) + len(summary) - 10  # Leave buffer
            if max_summary_length > 20:
                truncated_summary = summary[:max_summary_length] + "..."
                message = message.replace(summary, truncated_summary)
            else:
                # Use shorter default message
                message = f"Thanks for calling A Killion Voice! We discussed your inquiry and provided assistance. Reply or call (978) 643-2034 for more help."
        
        return message
    
    def _send_sms(self, to_number: str, message_body: str) -> Dict[str, Any]:
        """
        Send SMS using Twilio
        
        Args:
            to_number: Recipient phone number
            message_body: SMS message text
            
        Returns:
            Sending result
        """
        # Test mode - don't send real SMS
        if not self.twilio_client:
            logger.info(f"TEST MODE - Would send SMS to {to_number}: {message_body}")
            return {
                'success': True,
                'sms_sid': f'test_sms_{to_number}',
                'status': 'test_mode'
            }
        
        try:
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_number
            )
            
            return {
                'success': True,
                'sms_sid': message.sid,
                'status': message.status
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_sms_status(self, sms_sid: str) -> Dict[str, Any]:
        """
        Get SMS delivery status
        
        Args:
            sms_sid: Twilio SMS SID
            
        Returns:
            SMS status information
        """
        if not self.twilio_client:
            return {'status': 'test_mode'}
        
        try:
            message = self.twilio_client.messages(sms_sid).fetch()
            return {
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent,
                'date_updated': message.date_updated
            }
        except Exception as e:
            logger.error(f"Error getting SMS status: {e}")
            return {'error': str(e)}
    
    def handle_sms_reply(self, from_number: str, message_body: str) -> Dict[str, Any]:
        """
        Handle incoming SMS replies
        
        Args:
            from_number: Sender phone number
            message_body: Reply message text
            
        Returns:
            Response information
        """
        logger.info(f"SMS reply from {from_number}: {message_body}")
        
        # Simple auto-response for now
        auto_response = "Thanks for your message! For immediate assistance, please call us at (978) 643-2034. We're here to help!"
        
        return self._send_sms(from_number, auto_response)

# Global SMS service instance
sms_service = SMSService()

