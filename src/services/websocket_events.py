"""
WebSocket Event Handlers for Real-time Updates
"""
import logging

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


# Utility functions to emit events, using injected emitter
def emit_call_started(call_data, emitter):
    """Emit call started event"""
    emitter.emit(WSEventType.CALL_STARTED, call_data, namespace='/')
    logger.info(f"Emitted call started: {call_data.get('callSid')}")

def emit_call_updated(call_sid, update_data, emitter):
    """Emit call update event"""
    data = {'callSid': call_sid, **update_data}
    emitter.emit(WSEventType.CALL_UPDATED, data, namespace='/')
    # Also emit to call-specific room
    emitter.emit(WSEventType.CALL_UPDATED, data, room=f'call_{call_sid}', namespace='/')
    logger.info(f"Emitted call update: {call_sid}")

def emit_call_ended(call_sid, end_data, emitter):
    """Emit call ended event"""
    data = {'callSid': call_sid, **end_data}
    emitter.emit(WSEventType.CALL_ENDED, data, namespace='/')
    emitter.emit(WSEventType.CALL_ENDED, data, room=f'call_{call_sid}', namespace='/')
    logger.info(f"Emitted call ended: {call_sid}")

def emit_transcription_update(call_sid, transcription_data, emitter):
    """Emit transcription update event"""
    data = {'callSid': call_sid, **transcription_data}
    emitter.emit(WSEventType.TRANSCRIPTION_UPDATE, data, room=f'call_{call_sid}', namespace='/')
    logger.info(f"Emitted transcription update: {call_sid}")

def emit_agent_status_changed(agent_type, status_data, emitter):
    """Emit agent status change event"""
    data = {'agentType': agent_type, **status_data}
    emitter.emit(WSEventType.AGENT_STATUS_CHANGED, data, namespace='/')
    logger.info(f"Emitted agent status change: {agent_type}")

def emit_metrics_update(metrics_data, emitter):
    """Emit metrics update event"""
    emitter.emit(WSEventType.METRICS_UPDATE, metrics_data, namespace='/')
    logger.info("Emitted metrics update")

def emit_sms_sent(sms_data, emitter):
    """Emit SMS sent event"""
    emitter.emit(WSEventType.SMS_SENT, sms_data, namespace='/')
    logger.info(f"Emitted SMS sent: {sms_data.get('to')}")

def emit_sms_failed(sms_data, emitter):
    """Emit SMS failed event"""
    emitter.emit(WSEventType.SMS_FAILED, sms_data, namespace='/')
    logger.error(f"Emitted SMS failed: {sms_data.get('to')}")


# Event handler registration with injected emitter object
def init_ws_events(emitter):
    """
    Register WebSocket event handlers with the given emitter (socketio or mock).
    Call this at app startup.
    """
    from flask_socketio import emit as flask_emit, join_room as flask_join_room, leave_room as flask_leave_room

    @emitter.on('connect')
    def handle_connect(auth):
        """Handle client connection"""
        try:
            # Validate authentication
            api_key = auth.get('apiKey') if auth else None
            token = auth.get('token') if auth else None

            # For now, just check API key
            # TODO: Implement JWT validation when auth system is ready (pluginize authentication)
            if api_key or token:
                logger.info(f"WebSocket client connected")
                flask_emit(WSEventType.CONNECTION_STATUS, {'connected': True})
            else:
                logger.warning("WebSocket connection rejected - no authentication")
                return False
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            return False

    @emitter.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info("WebSocket client disconnected")

    @emitter.on('join')
    def handle_join(data):
        """Handle joining a room (e.g., for call-specific updates)"""
        room = data.get('room')
        if room:
            flask_join_room(room)
            logger.info(f"Client joined room: {room}")

    @emitter.on('leave')
    def handle_leave(data):
        """Handle leaving a room"""
        room = data.get('room')
        if room:
            flask_leave_room(room)
            logger.info(f"Client left room: {room}")

    # TODO: Pluginize authentication and emitting to MCP/event bus


# Example: Dummy/mock emitter for testing
class DummyEmitter:
    def __init__(self):
        self.events = {}
        self.emitted = []
    def on(self, event):
        def decorator(fn):
            self.events[event] = fn
            return fn
        return decorator
    def emit(self, event, data, room=None, namespace=None):
        self.emitted.append({'event': event, 'data': data, 'room': room, 'namespace': namespace})
        print(f"[DummyEmitter] emit: {event} data: {data} room: {room} ns: {namespace}")


# Sample initialization (for test or app startup)
# from src.main import socketio
# init_ws_events(socketio)
#
# For tests:
# dummy = DummyEmitter()
# init_ws_events(dummy)