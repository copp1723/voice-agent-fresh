"""
Enhanced database models for flexible agent customization
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class AgentTemplate(Base):
    """Base templates for creating agents"""
    __tablename__ = 'agent_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    base_prompt = Column(Text, nullable=False)
    voice_config = Column(JSONB, default={})
    industry = Column(String(100))
    use_case = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agents = relationship("EnhancedAgentConfig", back_populates="template")

class ConversationGoal(Base):
    """Defines possible conversation goals"""
    __tablename__ = 'conversation_goals'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    goal_type = Column(String(50))  # 'schedule', 'qualify', 'support', 'survey', 'custom'
    success_criteria = Column(JSONB, nullable=False)  # {"required_fields": [], "conditions": []}
    required_data = Column(JSONB, default=[])  # List of data points to collect
    completion_webhook = Column(Text)  # URL to call on completion
    max_duration_seconds = Column(Integer, default=600)  # 10 minutes default
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent_goals = relationship("AgentGoal", back_populates="goal")

class AgentInstruction(Base):
    """Do's and Don'ts for agents"""
    __tablename__ = 'agent_instructions'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('enhanced_agent_configs.id'), nullable=False)
    instruction_type = Column(String(50), nullable=False)  # 'do' or 'dont'
    category = Column(String(100))  # 'greeting', 'objection_handling', 'closing', etc.
    instruction = Column(Text, nullable=False)
    priority = Column(Integer, default=0)  # Higher = more important
    active = Column(Boolean, default=True)
    context_trigger = Column(JSONB)  # Conditions when this instruction applies
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("EnhancedAgentConfig", back_populates="instructions")

class DomainKnowledge(Base):
    """Domain-specific knowledge base"""
    __tablename__ = 'domain_knowledge'
    
    id = Column(Integer, primary_key=True)
    domain_name = Column(String(255), nullable=False)
    knowledge_type = Column(String(50), nullable=False)  # 'fact', 'process', 'policy', 'faq'
    title = Column(String(255))
    content = Column(Text, nullable=False)
    metadata = Column(JSONB, default={})  # Tags, sources, validity period
    embedding_vector = Column(JSON)  # For semantic search
    version = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent_domains = relationship("AgentDomain", back_populates="domain")

class EnhancedAgentConfig(Base):
    """Enhanced agent configuration with full customization"""
    __tablename__ = 'enhanced_agent_configs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    template_id = Column(Integer, ForeignKey('agent_templates.id'))
    
    # Core configuration
    system_prompt = Column(Text)  # Compiled from template + customizations
    greeting_message = Column(Text)
    voice_id = Column(String(100))
    voice_settings = Column(JSONB, default={})  # Speed, pitch, emotion defaults
    
    # Behavioral settings
    personality_traits = Column(JSONB, default=[])  # ['empathetic', 'professional', 'casual']
    conversation_style = Column(String(50), default='balanced')  # 'formal', 'casual', 'balanced'
    max_conversation_turns = Column(Integer, default=50)
    response_time_ms = Column(Integer, default=1000)  # Target response time
    
    # Routing and priority
    keywords = Column(JSONB, default=[])  # For routing decisions
    priority = Column(Integer, default=0)
    routing_confidence_threshold = Column(Float, default=0.7)
    
    # Status
    active = Column(Boolean, default=True)
    test_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Custom settings
    custom_settings = Column(JSONB, default={})
    
    # Relationships
    template = relationship("AgentTemplate", back_populates="agents")
    instructions = relationship("AgentInstruction", back_populates="agent", cascade="all, delete-orphan")
    goals = relationship("AgentGoal", back_populates="agent", cascade="all, delete-orphan")
    domains = relationship("AgentDomain", back_populates="agent", cascade="all, delete-orphan")
    voice_profile = relationship("VoiceProfile", back_populates="agent", uselist=False)

class AgentGoal(Base):
    """Links agents to their conversation goals"""
    __tablename__ = 'agent_goals'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('enhanced_agent_configs.id'), nullable=False)
    goal_id = Column(Integer, ForeignKey('conversation_goals.id'), nullable=False)
    priority = Column(Integer, default=0)  # Order of importance
    required = Column(Boolean, default=False)  # Must complete vs. optional
    active = Column(Boolean, default=True)
    custom_criteria = Column(JSONB)  # Agent-specific overrides
    
    # Relationships
    agent = relationship("EnhancedAgentConfig", back_populates="goals")
    goal = relationship("ConversationGoal", back_populates="agent_goals")

class AgentDomain(Base):
    """Links agents to their domain knowledge"""
    __tablename__ = 'agent_domains'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('enhanced_agent_configs.id'), nullable=False)
    domain_id = Column(Integer, ForeignKey('domain_knowledge.id'), nullable=False)
    relevance_score = Column(Float, default=1.0)  # How relevant this knowledge is
    
    # Relationships
    agent = relationship("EnhancedAgentConfig", back_populates="domains")
    domain = relationship("DomainKnowledge", back_populates="agent_domains")

class VoiceProfile(Base):
    """Custom voice profiles for agents"""
    __tablename__ = 'voice_profiles'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('enhanced_agent_configs.id'), nullable=False, unique=True)
    voice_provider = Column(String(50), default='chatterbox')  # 'chatterbox', 'openai', 'elevenlabs'
    voice_model = Column(String(100))
    voice_clone_id = Column(String(255))  # ID of cloned voice if applicable
    
    # Voice characteristics
    base_emotion = Column(String(50), default='neutral')
    emotion_range = Column(JSONB, default={})  # Allowed emotions and thresholds
    prosody_settings = Column(JSONB, default={})  # Rate, pitch, volume defaults
    
    # Sample storage
    sample_audio_urls = Column(JSONB, default=[])
    training_status = Column(String(50), default='pending')  # 'pending', 'training', 'ready'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("EnhancedAgentConfig", back_populates="voice_profile")

class GoalProgress(Base):
    """Tracks goal completion during calls"""
    __tablename__ = 'goal_progress'
    
    id = Column(Integer, primary_key=True)
    call_id = Column(String(255), nullable=False)
    agent_id = Column(Integer, ForeignKey('enhanced_agent_configs.id'), nullable=False)
    goal_id = Column(Integer, ForeignKey('conversation_goals.id'), nullable=False)
    
    # Progress tracking
    status = Column(String(50), default='in_progress')  # 'in_progress', 'completed', 'failed'
    collected_data = Column(JSONB, default={})
    missing_data = Column(JSONB, default=[])
    completion_percentage = Column(Float, default=0.0)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Conversation context
    relevant_messages = Column(JSONB, default=[])  # Message IDs that contributed to goal
    
class PerformanceMetric(Base):
    """Tracks agent performance metrics"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('enhanced_agent_configs.id'), nullable=False)
    call_id = Column(String(255))
    metric_type = Column(String(50), nullable=False)  # 'latency', 'goal_completion', 'satisfaction'
    metric_value = Column(Float, nullable=False)
    metadata = Column(JSONB, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)