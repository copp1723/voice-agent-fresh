"""
WebSocket Event Handlers for Real-time Updates
"""
import logging
from flask_socketio import emit, join_room, leave_room
from src.main import socketio

logger = logging.getLogger(__name__)

# Event types matching frontend
class WSEventType:
    CALL_STARTED = 'call:started'
    CALL_UPDATED = 'call:updated'
    CALL_ENDED = 'call:ended'
    AGENT_STATUS_CHANGED = 'agent:status_changed'
    TRANSCRIPTION_UPDATE = 'transcription:update'
    METRICS_UPDATE = 'metrics:update'
    SMS_SENT = 'sms:sent'
    SMS_FAILED = 'sms:failed'
    CONNECTION_STATUS = 'connection:status'

@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection"""
    try:
        # Validate authentication
        api_key = auth.get('apiKey') if auth else None
        token = auth.get('token') if auth else None
        
        # For now, just check API key
        # TODO: Implement JWT validation when auth system is ready
        if api_key or token:
            logger.info(f"WebSocket client connected")
            emit(WSEventType.CONNECTION_STATUS, {'connected': True})
        else:
            logger.warning("WebSocket connection rejected - no authentication")
            return False
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("WebSocket client disconnected")

@socketio.on('join')
def handle_join(data):
    """Handle joining a room (e.g., for call-specific updates)"""
    room = data.get('room')
    if room:
        join_room(room)
        logger.info(f"Client joined room: {room}")

@socketio.on('leave')
def handle_leave(data):
    """Handle leaving a room"""
    room = data.get('room')
    if room:
        leave_room(room)
        logger.info(f"Client left room: {room}")

# Utility functions to emit events
def emit_call_started(call_data):
    """Emit call started event"""
    socketio.emit(WSEventType.CALL_STARTED, call_data, namespace='/')
    logger.info(f"Emitted call started: {call_data.get('callSid')}")

def emit_call_updated(call_sid, update_data):
    """Emit call update event"""
    data = {'callSid': call_sid, **update_data}
    socketio.emit(WSEventType.CALL_UPDATED, data, namespace='/')
    # Also emit to call-specific room
    socketio.emit(WSEventType.CALL_UPDATED, data, room=f'call_{call_sid}', namespace='/')
    logger.info(f"Emitted call update: {call_sid}")

def emit_call_ended(call_sid, end_data):
    """Emit call ended event"""
    data = {'callSid': call_sid, **end_data}
    socketio.emit(WSEventType.CALL_ENDED, data, namespace='/')
    socketio.emit(WSEventType.CALL_ENDED, data, room=f'call_{call_sid}', namespace='/')
    logger.info(f"Emitted call ended: {call_sid}")

def emit_transcription_update(call_sid, transcription_data):
    """Emit transcription update event"""
    data = {'callSid': call_sid, **transcription_data}
    socketio.emit(WSEventType.TRANSCRIPTION_UPDATE, data, room=f'call_{call_sid}', namespace='/')
    logger.info(f"Emitted transcription update: {call_sid}")

def emit_agent_status_changed(agent_type, status_data):
    """Emit agent status change event"""
    data = {'agentType': agent_type, **status_data}
    socketio.emit(WSEventType.AGENT_STATUS_CHANGED, data, namespace='/')
    logger.info(f"Emitted agent status change: {agent_type}")

def emit_metrics_update(metrics_data):
    """Emit metrics update event"""
    socketio.emit(WSEventType.METRICS_UPDATE, metrics_data, namespace='/')
    logger.info("Emitted metrics update")

def emit_sms_sent(sms_data):
    """Emit SMS sent event"""
    socketio.emit(WSEventType.SMS_SENT, sms_data, namespace='/')
    logger.info(f"Emitted SMS sent: {sms_data.get('to')}")

def emit_sms_failed(sms_data):
    """Emit SMS failed event"""
    socketio.emit(WSEventType.SMS_FAILED, sms_data, namespace='/')
    logger.error(f"Emitted SMS failed: {sms_data.get('to')}")