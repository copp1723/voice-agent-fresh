"""
Voice Routes - Handle Twilio webhooks and voice interactions
"""
import os
import logging
from flask import Blueprint, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from src.services.call_router import call_router
from src.services.agent_brain import AgentBrain
from src.models.call import Call, Message, db
from datetime import datetime

logger = logging.getLogger(__name__)

voice_bp = Blueprint('voice', __name__)

# Global instances
agent_brain = AgentBrain()
active_calls = {}  # In-memory call tracking

@voice_bp.route('/api/twilio/inbound', methods=['POST'])
def handle_incoming_call():
    """
    Handle incoming Twilio call webhook - Production endpoint
    """
    try:
        # Get call data from Twilio
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        
        logger.info(f"Incoming call: {call_sid} from {from_number} to {to_number}")
        
        # Create call record
        call = Call(
            call_sid=call_sid,
            from_number=from_number,
            to_number=to_number,
            status='active',
            direction='inbound'
        )
        db.session.add(call)
        db.session.commit()
        
        # Initialize call tracking
        active_calls[call_sid] = {
            'call_id': call.id,
            'from_number': from_number,
            'conversation_history': [],
            'agent_type': 'general',  # Default until routing
            'start_time': datetime.utcnow()
        }
        
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
def process_voice_input(call_sid):
    """
    Process voice input from caller - Production endpoint
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
        
        # Get call info
        call_info = active_calls.get(call_sid)
        if not call_info:
            # Call not found - end gracefully
            response = VoiceResponse()
            response.say("I'm sorry, there was an issue with your call. Please call back.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}
        
        # First message - route the call
        if not call_info['conversation_history']:
            routing_decision = call_router.route_call(call_sid, transcription, call_info['from_number'])
            
            # Update call info with routing decision
            call_info.update({
                'agent_type': routing_decision['agent_type'],
                'system_prompt': routing_decision['system_prompt'],
                'confidence': routing_decision['confidence'],
                'matched_keywords': routing_decision['matched_keywords']
            })
            
            # Set agent instructions
            agent_brain.set_agent_instructions(routing_decision['system_prompt'])
            
            # Update database
            call = Call.query.filter_by(call_sid=call_sid).first()
            if call:
                call.agent_type = routing_decision['agent_type']
                call.routing_confidence = routing_decision['confidence']
                call.set_routing_keywords(routing_decision['matched_keywords'])
                db.session.commit()
            
            logger.info(f"Routed call {call_sid} to {routing_decision['agent_type']} agent")
        
        # Add user message to conversation
        call_info['conversation_history'].append(transcription)
        
        # Save user message to database
        user_message = Message(
            call_id=call_info['call_id'],
            role='user',
            content=transcription,
            audio_url=recording_url
        )
        db.session.add(user_message)
        
        # Generate AI response
        ai_response = agent_brain.process_conversation(
            transcription, 
            call_info['conversation_history']
        )
        
        # Add AI response to conversation
        call_info['conversation_history'].append(ai_response)
        
        # Save AI message to database
        ai_message = Message(
            call_id=call_info['call_id'],
            role='assistant',
            content=ai_response
        )
        db.session.add(ai_message)
        db.session.commit()
        
        # Create TwiML response
        response = VoiceResponse()
        response.say(ai_response)
        
        # Check if conversation should continue
        should_end = agent_brain.should_end_conversation(ai_response, call_info['conversation_history'])
        
        if should_end or len(call_info['conversation_history']) >= 20:
            # End conversation
            response.say("Thank you for calling A Killion Voice. Have a great day!")
            response.hangup()
            
            # Trigger call completion
            complete_call(call_sid)
        else:
            # Continue conversation
            response.record(
                action=f'/api/twilio/process/{call_sid}',
                method='POST',
                max_length=30,
                finish_on_key='#',
                timeout=10
            )
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error processing voice input: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, I had trouble understanding. Could you please repeat?")
        response.record(
            action=f'/api/twilio/process/{call_sid}',
            method='POST',
            max_length=30,
            finish_on_key='#'
        )
        return str(response), 200, {'Content-Type': 'text/xml'}

@voice_bp.route('/api/twilio/status', methods=['POST'])
def handle_call_status():
    """
    Handle call status updates from Twilio - Production endpoint
    """
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        
        logger.info(f"Call status update: {call_sid} - {call_status}")
        
        if call_status in ['completed', 'busy', 'failed', 'no-answer']:
            complete_call(call_sid)
        
        return '', 200
        
    except Exception as e:
        logger.error(f"Error handling call status: {e}")
        return '', 500

def complete_call(call_sid: str):
    """
    Complete call and trigger SMS follow-up
    """
    try:
        call_info = active_calls.get(call_sid)
        if not call_info:
            return
        
        # Calculate duration
        duration = (datetime.utcnow() - call_info['start_time']).total_seconds()
        
        # Update database
        call = Call.query.filter_by(call_sid=call_sid).first()
        if call:
            call.status = 'completed'
            call.end_time = datetime.utcnow()
            call.duration = int(duration)
            call.message_count = len(call_info['conversation_history'])
            
            # Generate summary
            summary = agent_brain.generate_conversation_summary(call_info['conversation_history'])
            call.summary = summary
            
            db.session.commit()
            
            # Send SMS follow-up
            from src.services.sms_service import sms_service
            
            sms_result = sms_service.send_call_follow_up(
                call_id=call.id,
                to_number=call_info['from_number'],
                agent_type=call_info.get('agent_type', 'general'),
                conversation_summary=summary,
                call_duration=int(duration)
            )
            
            if sms_result['success']:
                call.sms_sent = True
                call.sms_sid = sms_result.get('sms_sid')
                db.session.commit()
                logger.info(f"SMS follow-up sent for call {call_sid}")
            else:
                logger.error(f"Failed to send SMS follow-up: {sms_result.get('error')}")
        
        # Clean up active call
        del active_calls[call_sid]
        
        logger.info(f"Call {call_sid} completed after {duration:.1f} seconds")
        
    except Exception as e:
        logger.error(f"Error completing call: {e}")

@voice_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for A Killion Voice
    """
    return jsonify({
        "status": "healthy",
        "service": "A Killion Voice Agent",
        "domain": "akillionvoice.xyz",
        "phone": "(978) 643-2034",
        "active_calls": len(active_calls),
        "webhook_url": "https://api.akillionvoice.xyz/api/twilio/inbound",
        "openrouter_configured": bool(os.getenv('OPENROUTER_API_KEY')),
        "twilio_configured": bool(os.getenv('TWILIO_ACCOUNT_SID')),
        "sms_enabled": bool(os.getenv('TWILIO_AUTH_TOKEN'))
    }), 200

@voice_bp.route('/api/calls', methods=['GET'])
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

