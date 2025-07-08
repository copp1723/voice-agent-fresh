"""
Unit tests for WebSocket event handlers
"""
import pytest
from unittest.mock import patch, MagicMock
from src.services.websocket_events import (
    emit_call_started,
    emit_call_updated,
    emit_call_ended,
    emit_transcription_update,
    emit_agent_status_changed,
    emit_metrics_update,
    emit_sms_sent,
    emit_sms_failed,
    WSEventType
)

class TestWebSocketEvents:
    
    @patch('src.services.websocket_events.socketio')
    def test_emit_call_started(self, mock_socketio):
        """Test emitting call started event"""
        call_data = {
            'callSid': 'CA123456',
            'from': '+1234567890',
            'to': '+0987654321',
            'startTime': '2024-01-01T12:00:00'
        }
        
        emit_call_started(call_data)
        
        mock_socketio.emit.assert_called_once_with(
            WSEventType.CALL_STARTED,
            call_data,
            namespace='/'
        )
    
    @patch('src.services.websocket_events.socketio')
    def test_emit_call_updated(self, mock_socketio):
        """Test emitting call updated event"""
        call_sid = 'CA123456'
        update_data = {
            'agentType': 'billing',
            'status': 'routed'
        }
        
        emit_call_updated(call_sid, update_data)
        
        expected_data = {'callSid': call_sid, **update_data}
        
        # Should emit to general namespace and call-specific room
        assert mock_socketio.emit.call_count == 2
        
        # Check general broadcast
        mock_socketio.emit.assert_any_call(
            WSEventType.CALL_UPDATED,
            expected_data,
            namespace='/'
        )
        
        # Check room-specific broadcast
        mock_socketio.emit.assert_any_call(
            WSEventType.CALL_UPDATED,
            expected_data,
            room=f'call_{call_sid}',
            namespace='/'
        )
    
    @patch('src.services.websocket_events.socketio')
    def test_emit_call_ended(self, mock_socketio):
        """Test emitting call ended event"""
        call_sid = 'CA123456'
        end_data = {
            'status': 'completed',
            'endTime': '2024-01-01T12:30:00',
            'duration': 1800
        }
        
        emit_call_ended(call_sid, end_data)
        
        expected_data = {'callSid': call_sid, **end_data}
        
        # Should emit to general namespace and call-specific room
        assert mock_socketio.emit.call_count == 2
        
        # Check both emit calls
        mock_socketio.emit.assert_any_call(
            WSEventType.CALL_ENDED,
            expected_data,
            namespace='/'
        )
        mock_socketio.emit.assert_any_call(
            WSEventType.CALL_ENDED,
            expected_data,
            room=f'call_{call_sid}',
            namespace='/'
        )
    
    @patch('src.services.websocket_events.socketio')
    def test_emit_transcription_update(self, mock_socketio):
        """Test emitting transcription update event"""
        call_sid = 'CA123456'
        transcription_data = {
            'speaker': 'customer',
            'text': 'I need help with my billing',
            'timestamp': '2024-01-01T12:05:00'
        }
        
        emit_transcription_update(call_sid, transcription_data)
        
        expected_data = {'callSid': call_sid, **transcription_data}
        
        # Should only emit to call-specific room
        mock_socketio.emit.assert_called_once_with(
            WSEventType.TRANSCRIPTION_UPDATE,
            expected_data,
            room=f'call_{call_sid}',
            namespace='/'
        )
    
    @patch('src.services.websocket_events.socketio')
    def test_emit_agent_status_changed(self, mock_socketio):
        """Test emitting agent status change event"""
        agent_type = 'billing'
        status_data = {
            'status': 'busy',
            'activeCalls': 3
        }
        
        emit_agent_status_changed(agent_type, status_data)
        
        expected_data = {'agentType': agent_type, **status_data}
        
        mock_socketio.emit.assert_called_once_with(
            WSEventType.AGENT_STATUS_CHANGED,
            expected_data,
            namespace='/'
        )
    
    @patch('src.services.websocket_events.socketio')
    def test_emit_metrics_update(self, mock_socketio):
        """Test emitting metrics update event"""
        metrics_data = {
            'totalCalls': 150,
            'activeCalls': 5,
            'averageCallDuration': 245.5,
            'callSuccessRate': 92.5
        }
        
        emit_metrics_update(metrics_data)
        
        mock_socketio.emit.assert_called_once_with(
            WSEventType.METRICS_UPDATE,
            metrics_data,
            namespace='/'
        )
    
    @patch('src.services.websocket_events.socketio')
    def test_emit_sms_sent(self, mock_socketio):
        """Test emitting SMS sent event"""
        sms_data = {
            'to': '+1234567890',
            'callSid': 'CA123456',
            'message': 'Thanks for calling!'
        }
        
        emit_sms_sent(sms_data)
        
        mock_socketio.emit.assert_called_once_with(
            WSEventType.SMS_SENT,
            sms_data,
            namespace='/'
        )
    
    @patch('src.services.websocket_events.socketio')
    def test_emit_sms_failed(self, mock_socketio):
        """Test emitting SMS failed event"""
        sms_data = {
            'to': '+1234567890',
            'callSid': 'CA123456',
            'error': 'Invalid phone number'
        }
        
        emit_sms_failed(sms_data)
        
        mock_socketio.emit.assert_called_once_with(
            WSEventType.SMS_FAILED,
            sms_data,
            namespace='/'
        )
    
    @patch('src.services.websocket_events.socketio')
    @patch('src.services.websocket_events.join_room')
    def test_handle_join(self, mock_join_room, mock_socketio):
        """Test handling join room event"""
        from src.services.websocket_events import handle_join
        
        data = {'room': 'call_CA123456'}
        handle_join(data)
        
        mock_join_room.assert_called_once_with('call_CA123456')
    
    @patch('src.services.websocket_events.socketio')
    @patch('src.services.websocket_events.leave_room')
    def test_handle_leave(self, mock_leave_room, mock_socketio):
        """Test handling leave room event"""
        from src.services.websocket_events import handle_leave
        
        data = {'room': 'call_CA123456'}
        handle_leave(data)
        
        mock_leave_room.assert_called_once_with('call_CA123456')