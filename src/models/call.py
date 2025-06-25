"""
Optimized Call Database Models - Clean, focused schema for voice agent
"""
from . import db # Use the db instance from models/__init__.py
from datetime import datetime
import json

class Call(db.Model):
    """
    Call tracking model - optimized for voice agent workflow
    """
    __tablename__ = 'calls'
    
    id = db.Column(db.Integer, primary_key=True)
    call_sid = db.Column(db.String(100), unique=True, nullable=False, index=True)
    from_number = db.Column(db.String(20), nullable=False)
    to_number = db.Column(db.String(20), nullable=False)
    
    # Call timing
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer, default=0)  # seconds
    
    # Agent routing
    agent_type = db.Column(db.String(50), default='general', nullable=False)
    routing_confidence = db.Column(db.Float, default=0.0)
    routing_keywords = db.Column(db.Text)  # JSON array
    
    # Call status
    status = db.Column(db.String(20), default='active')  # active, completed, failed
    direction = db.Column(db.String(10), default='inbound')  # inbound, outbound
    
    # Conversation metrics
    message_count = db.Column(db.Integer, default=0)
    summary = db.Column(db.Text)
    
    # SMS follow-up
    sms_sent = db.Column(db.Boolean, default=False)
    sms_sid = db.Column(db.String(100))
    
    # Relationships
    messages = db.relationship('Message', backref='call', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_sid': self.call_sid,
            'from_number': self.from_number,
            'to_number': self.to_number,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'agent_type': self.agent_type,
            'routing_confidence': self.routing_confidence,
            'status': self.status,
            'direction': self.direction,
            'message_count': self.message_count,
            'summary': self.summary,
            'sms_sent': self.sms_sent
        }
    
    def get_routing_keywords(self):
        """Get routing keywords as list"""
        if self.routing_keywords:
            try:
                return json.loads(self.routing_keywords)
            except:
                return []
        return []
    
    def set_routing_keywords(self, keywords):
        """Set routing keywords from list"""
        self.routing_keywords = json.dumps(keywords) if keywords else None

class Message(db.Model):
    """
    Conversation messages within calls
    """
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('calls.id'), nullable=False)
    
    # Message data
    role = db.Column(db.String(20), nullable=False)  # user, assistant
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Audio metadata
    audio_url = db.Column(db.String(500))  # Twilio recording URL
    confidence = db.Column(db.Float)  # Transcription confidence
    processing_time = db.Column(db.Float)  # Response generation time
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'audio_url': self.audio_url,
            'confidence': self.confidence,
            'processing_time': self.processing_time
        }

class AgentConfig(db.Model):
    """
    Agent configuration and behavior settings
    """
    __tablename__ = 'agent_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_type = db.Column(db.String(50), unique=True, nullable=False)
    
    # Agent behavior
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    system_prompt = db.Column(db.Text, nullable=False)
    
    # Conversation settings
    max_turns = db.Column(db.Integer, default=20)
    timeout_seconds = db.Column(db.Integer, default=30)
    
    # Voice settings
    voice_provider = db.Column(db.String(50), default='openai')
    voice_model = db.Column(db.String(100), default='alloy')
    
    # Routing
    keywords = db.Column(db.Text)  # JSON array
    priority = db.Column(db.Integer, default=1)
    
    # SMS template
    sms_template = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'max_turns': self.max_turns,
            'timeout_seconds': self.timeout_seconds,
            'voice_provider': self.voice_provider,
            'voice_model': self.voice_model,
            'keywords': self.get_keywords(),
            'priority': self.priority,
            'sms_template': self.sms_template,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_keywords(self):
        """Get keywords as list"""
        if self.keywords:
            try:
                return json.loads(self.keywords)
            except:
                return []
        return []
    
    def set_keywords(self, keywords):
        """Set keywords from list"""
        self.keywords = json.dumps(keywords) if keywords else None

class SMSLog(db.Model):
    """
    SMS follow-up tracking
    """
    __tablename__ = 'sms_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('calls.id'), nullable=False)
    
    # SMS data
    sms_sid = db.Column(db.String(100), unique=True, nullable=False)
    to_number = db.Column(db.String(20), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    
    # Status tracking
    status = db.Column(db.String(20), default='sent')  # sent, delivered, failed
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = db.Column(db.DateTime)
    
    # Template info
    template_type = db.Column(db.String(50))
    agent_type = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'sms_sid': self.sms_sid,
            'to_number': self.to_number,
            'message_body': self.message_body,
            'status': self.status,
            'sent_at': self.sent_at.isoformat(),
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'template_type': self.template_type,
            'agent_type': self.agent_type
        }

