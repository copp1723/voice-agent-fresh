"""
Voice Routes - Handle Twilio webhooks and voice interactions with security
"""
import os
import logging
from flask import Blueprint, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from src.middleware.security import validate_twilio_request, require_api_key
from src.services.call_session import session_manager
from src.services.sms_service import sms_service
from src.models.call import Call, Message, db
from datetime import datetime

logger = logging.getLogger(__name__)

voice_bp = Blueprint('voice', __name__)

# Remove global instances - now using per-call sessions

@voice_bp.route('/api/twilio/inbound', methods=['POST'])
@validate_twilio_request
def handle_inbound_call():
    """
    Handle incoming Twilio call webhook - Production endpoint with session isolation
    """
    try:
        # Get call data from Twilio
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        
        logger.info(f"Incoming call: {call_sid} from {from_number} to {to_number}")
        
        # Create isolated call session
        session = session_manager.create_session(call_sid, from_number)
        
        # Create TwiML response
        response = VoiceResponse()
        response.say("Hello! Thank you for calling A Killion Voice. I'm here to help you today. Please tell me how I can assist you.")
        response.record(
            action=f'/api/twilio/process/{call_sid}',
            method='POST',
            max_length=30,
            finish_on_key='#',
            timeout=10
        )
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, we're experiencing technical difficulties. Please try calling back later.")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}

@voice_bp.route('/api/twilio/process/<call_sid>', methods=['POST'])
@validate_twilio_request
def process_voice_input(call_sid):
    """
    Process voice input from caller - Production endpoint with session isolation
    """
    try:
        # Get transcription from Twilio
        transcription = request.form.get('TranscriptionText', '').strip()
        recording_url = request.form.get('RecordingUrl', '')
        
        if not transcription:
            # No transcription - ask to repeat
            response = VoiceResponse()
            response.say("I didn't catch that. Could you please repeat?")
            response.record(
                action=f'/api/twilio/process/{call_sid}',
                method='POST',
                max_length=30,
                finish_on_key='#',
                timeout=10
            )
            return str(response), 200, {'Content-Type': 'text/xml'}
        
        logger.info(f"Processing voice input for {call_sid}: {transcription}")
        
        # Get call session
        session = session_manager.get_session(call_sid)
        if not session:
            # Session not found - end gracefully
            response = VoiceResponse()
            response.say("I'm sorry, there was an issue with your call. Please call back.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}
        
        # First message - route the call
        if session.turn_count == 0:
            session.route_call(transcription)
            logger.info(f"Routed call {call_sid} to {session.agent_type} agent")
        
        # Process conversation turn with isolated state
        ai_response = session.process_conversation_turn(transcription)
        
        # Create TwiML response
        response = VoiceResponse()
        response.say(ai_response)
        
        # Check if we should continue or end the call
        if session.turn_count >= session.max_turns:
            response.say("Thank you for calling A Killion Voice. Have a great day!")
            response.hangup()
        else:
            # Continue conversation
            response.record(
                action=f'/api/twilio/process/{call_sid}',
                method='POST',
                max_length=30,
                finish_on_key='#'
            )
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error processing voice input for {call_sid}: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, I had trouble processing that. Could you please try again?")
        response.record(
            action=f'/api/twilio/process/{call_sid}',
            method='POST',
            max_length=30,
            finish_on_key='#'
        )
        
        return str(response), 200, {'Content-Type': 'text/xml'}

@voice_bp.route('/api/twilio/status', methods=['POST'])
@validate_twilio_request
def call_status_callback():
    """
    Handle call status updates from Twilio - Production endpoint with session management
    """
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        
        logger.info(f"Call status update: {call_sid} - {call_status}")
        
        if call_status in ['completed', 'busy', 'failed', 'no-answer']:
            # End the call session and trigger SMS follow-up
            session_result = session_manager.end_session(call_sid, call_status)
            
            if session_result and call_status == 'completed':
                # Send SMS follow-up
                try:
                    sms_service.send_call_summary_sms(
                        to_number=session_result['phone_number'],
                        agent_type=session_result['agent_type'],
                        summary=session_result['summary']['summary'],
                        call_sid=call_sid
                    )
                    logger.info(f"SMS follow-up sent for call {call_sid}")
                except Exception as e:
                    logger.error(f"Error sending SMS follow-up for {call_sid}: {e}")
        
        return '', 200
        
    except Exception as e:
        logger.error(f"Error handling call status: {e}")
        return '', 500

@voice_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for A Killion Voice with session management
    """
    active_sessions = session_manager.get_active_sessions()
    return jsonify({
        "status": "healthy",
        "service": "A Killion Voice Agent",
        "domain": "akillionvoice.xyz",
        "phone": "(978) 643-2034",
        "active_calls": len(active_sessions),
        "webhook_url": "https://api.akillionvoice.xyz/api/twilio/inbound",
        "openrouter_configured": bool(os.getenv('OPENROUTER_API_KEY')),
        "twilio_configured": bool(os.getenv('TWILIO_ACCOUNT_SID')),
        "sms_enabled": bool(os.getenv('TWILIO_AUTH_TOKEN')),
        "session_management": "enabled"
    }), 200

@voice_bp.route('/api/calls', methods=['GET'])
@require_api_key
def get_calls():
    """
    Get call history
    """
    try:
        calls = Call.query.order_by(Call.start_time.desc()).limit(50).all()
        return jsonify([call.to_dict() for call in calls]), 200
    except Exception as e:
        logger.error(f"Error getting calls: {e}")
        return jsonify({"error": "Failed to get calls"}), 500

@voice_bp.route('/api/agents', methods=['GET'])
@require_api_key
def get_agents():
    """
    Get agent configurations
    """
    try:
        agents = call_router.get_all_agents()
        return jsonify(agents), 200
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        return jsonify({"error": "Failed to get agents"}), 500

