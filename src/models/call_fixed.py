"""
Fixed Call Database Models - Resolves circular import issues
"""
from .database import db, BaseModel, JSONMixin, create_safe_foreign_key, create_safe_relationship, register_model
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class Call(BaseModel, JSONMixin):
    """
    Call tracking model - optimized for voice agent workflow
    Fixed to avoid circular import issues
    """
    __tablename__ = 'calls'
    
    # Override id from BaseModel to add our own created_at/updated_at handling
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
    
    # Safe foreign key relationships - using table names to avoid circular imports
    customer_id = create_safe_foreign_key('customer', nullable=True)
    
    # Relationships - using string references to avoid import order issues
    messages = create_safe_relationship('Message', back_ref='call', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'call_sid': self.call_sid,
            'from_number': self.from_number,
            'to_number': self.to_number,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'agent_type': self.agent_type,
            'routing_confidence': self.routing_confidence,
            'status': self.status,
            'direction': self.direction,
            'message_count': self.message_count,
            'summary': self.summary,
            'sms_sent': self.sms_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_routing_keywords(self):
        """Get routing keywords as list"""
        return self.get_json_field('routing_keywords', [])
    
    def set_routing_keywords(self, keywords):
        """Set routing keywords from list"""
        self.set_json_field('routing_keywords', keywords)
    
    def get_customer(self):
        """Get associated customer (lazy loading to avoid circular imports)"""
        if self.customer_id:
            # Import only when needed
            from .customer import Customer
            return Customer.query.get(self.customer_id)
        return None
    
    def get_messages_list(self):
        """Get messages as a list (avoiding dynamic query issues)"""
        return list(self.messages.all())


class Message(BaseModel):
    """
    Conversation messages within calls
    Fixed to avoid circular import issues
    """
    __tablename__ = 'messages'
    
    # Safe foreign key to calls table
    call_id = create_safe_foreign_key('calls', nullable=False)
    
    # Message data
    role = db.Column(db.String(20), nullable=False)  # user, assistant
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Audio metadata
    audio_url = db.Column(db.String(500))  # Twilio recording URL
    confidence = db.Column(db.Float)  # Transcription confidence
    processing_time = db.Column(db.Float)  # Response generation time
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'call_id': self.call_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'audio_url': self.audio_url,
            'confidence': self.confidence,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_call(self):
        """Get associated call (lazy loading)"""
        if self.call_id:
            return Call.query.get(self.call_id)
        return None


class AgentConfig(BaseModel, JSONMixin):
    """
    Agent configuration and behavior settings
    Self-contained to avoid circular imports
    """
    __tablename__ = 'agent_configs'
    
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
    
    def to_dict(self):
        """Convert to dictionary"""
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_keywords(self):
        """Get keywords as list"""
        return self.get_json_field('keywords', [])
    
    def set_keywords(self, keywords):
        """Set keywords from list"""
        self.set_json_field('keywords', keywords)


class SMSLog(BaseModel):
    """
    SMS follow-up tracking
    Fixed to avoid circular import issues
    """
    __tablename__ = 'sms_logs'
    
    # Safe foreign key relationships
    call_id = create_safe_foreign_key('calls', nullable=False)
    customer_id = create_safe_foreign_key('customer', nullable=True)
    
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
        """Convert to dictionary"""
        return {
            'id': self.id,
            'call_id': self.call_id,
            'customer_id': self.customer_id,
            'sms_sid': self.sms_sid,
            'to_number': self.to_number,
            'message_body': self.message_body,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'template_type': self.template_type,
            'agent_type': self.agent_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_call(self):
        """Get associated call (lazy loading)"""
        if self.call_id:
            return Call.query.get(self.call_id)
        return None
    
    def get_customer(self):
        """Get associated customer (lazy loading)"""
        if self.customer_id:
            from .customer import Customer
            return Customer.query.get(self.customer_id)
        return None


# Register models in the registry
register_model('Call', Call)
register_model('Message', Message)
register_model('AgentConfig', AgentConfig)
register_model('SMSLog', SMSLog)

# Export models
__all__ = ['Call', 'Message', 'AgentConfig', 'SMSLog']
