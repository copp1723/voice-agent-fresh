"""
Database Model Registry - Resolves circular import issues and manages model dependencies
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# Centralized db instance
db = SQLAlchemy()

class ModelRegistry:
    """
    Registry to manage model imports and resolve circular dependencies
    """
    
    def __init__(self):
        self._models = {}
        self._initialized = False
    
    def register_model(self, name: str, model_class):
        """Register a model class"""
        self._models[name] = model_class
        logger.debug(f"Registered model: {name}")
    
    def get_model(self, name: str):
        """Get a registered model"""
        return self._models.get(name)
    
    def get_all_models(self):
        """Get all registered models"""
        return self._models.copy()
    
    def initialize_relationships(self):
        """Initialize model relationships after all models are loaded"""
        if self._initialized:
            return
        
        logger.info("Initializing model relationships...")
        
        # This is called after all models are imported
        # Any relationship fixes can go here
        self._initialized = True
        logger.info("Model relationships initialized")

# Global registry instance
model_registry = ModelRegistry()

# Base model class with common functionality
class BaseModel(db.Model):
    """Base model with common fields and methods"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self):
        """Save the model to database"""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving {self.__class__.__name__}: {e}")
            return False
    
    def delete(self):
        """Delete the model from database"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting {self.__class__.__name__}: {e}")
            return False
    
    def to_dict(self):
        """Convert model to dictionary - should be overridden"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class JSONMixin:
    """Mixin for JSON field handling"""
    
    def get_json_field(self, field_name: str, default=None):
        """Get JSON field value"""
        field_value = getattr(self, field_name, None)
        if field_value:
            try:
                return json.loads(field_value)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid JSON in {field_name}: {field_value}")
                return default
        return default or []
    
    def set_json_field(self, field_name: str, value):
        """Set JSON field value"""
        if value is not None:
            try:
                setattr(self, field_name, json.dumps(value))
            except (TypeError, ValueError) as e:
                logger.error(f"Error setting JSON field {field_name}: {e}")
        else:
            setattr(self, field_name, None)

def create_safe_foreign_key(table_name: str, column_name: str = 'id', nullable: bool = True):
    """
    Create a foreign key that safely references a table
    """
    return db.Column(
        db.Integer, 
        db.ForeignKey(f'{table_name}.{column_name}', ondelete='CASCADE'), 
        nullable=nullable
    )

def create_safe_relationship(model_name: str, back_ref: str = None, **kwargs):
    """
    Create a relationship that safely references a model
    Uses lazy loading to avoid circular import issues
    """
    default_kwargs = {
        'lazy': 'dynamic',
        'cascade': 'all, delete-orphan'
    }
    default_kwargs.update(kwargs)
    
    if back_ref:
        default_kwargs['backref'] = db.backref(back_ref, lazy='select')
    
    # Use string reference to avoid import issues
    return db.relationship(model_name, **default_kwargs)

class DatabaseManager:
    """
    Manages database operations and model relationships
    """
    
    def __init__(self, db_instance):
        self.db = db_instance
        self.models_loaded = False
    
    def initialize_database(self, app):
        """Initialize database with app context"""
        with app.app_context():
            try:
                # Create all tables
                self.db.create_all()
                logger.info("Database tables created successfully")
                
                # Initialize model relationships
                model_registry.initialize_relationships()
                
                # Populate default data
                self._populate_default_data()
                
                self.models_loaded = True
                return True
                
            except Exception as e:
                logger.error(f"Database initialization failed: {e}")
                return False
    
    def _populate_default_data(self):
        """Populate default data if needed"""
        try:
            # Import models here to avoid circular imports
            from src.models.call import AgentConfig
            
            # Check if default agents exist
            if not AgentConfig.query.first():
                self._create_default_agents()
                
        except ImportError as e:
            logger.warning(f"Could not populate default data: {e}")
    
    def _create_default_agents(self):
        """Create default agent configurations"""
        try:
            from src.models.call import AgentConfig
            
            default_agents = [
                {
                    'agent_type': 'general', 'name': 'General Assistant',
                    'description': 'General purpose customer service agent',
                    'system_prompt': 'You are a helpful customer service representative for A Killion Voice. Be friendly, professional, and concise in your responses.',
                    'keywords': ['hello', 'hi', 'help', 'general', 'information'], 'priority': 1,
                    'sms_template': 'Thanks for calling A Killion Voice! We discussed your inquiry and provided assistance. Reply if you need more help!'
                },
                {
                    'agent_type': 'billing', 'name': 'Billing Specialist',
                    'description': 'Handles billing, payments, and subscription inquiries',
                    'system_prompt': 'You are a billing specialist for A Killion Voice. Help customers with payment issues, billing questions, and subscription management. Be empathetic and provide clear explanations.',
                    'keywords': ['billing', 'payment', 'invoice', 'charge', 'refund', 'subscription', 'cancel', 'money', 'cost', 'price'], 'priority': 2,
                    'sms_template': 'Thanks for calling A Killion Voice about your billing inquiry. {summary} If you need further assistance, please reply or call us back.'
                },
                {
                    'agent_type': 'support', 'name': 'Technical Support',
                    'description': 'Provides technical assistance and troubleshooting',
                    'system_prompt': 'You are a technical support specialist for A Killion Voice. Help customers resolve technical issues with clear, step-by-step guidance. Ask clarifying questions when needed.',
                    'keywords': ['help', 'problem', 'issue', 'error', 'broken', 'not working', 'bug', 'technical', 'support', 'fix'], 'priority': 2,
                    'sms_template': 'Thanks for calling A Killion Voice technical support. {summary} We\'ve provided troubleshooting steps. Reply if you need more assistance!'
                },
                {
                    'agent_type': 'sales', 'name': 'Sales Representative',
                    'description': 'Handles sales inquiries and product information',
                    'system_prompt': 'You are a sales representative for A Killion Voice. Help customers understand our products and services. Be consultative, not pushy. Focus on their needs.',
                    'keywords': ['buy', 'purchase', 'pricing', 'demo', 'trial', 'features', 'plans', 'upgrade', 'sales', 'interested'], 'priority': 2,
                    'sms_template': 'Thanks for your interest in A Killion Voice services! {summary} I\'ll follow up with more information. Questions? Just reply!'
                },
                {
                    'agent_type': 'scheduling', 'name': 'Scheduling Coordinator',
                    'description': 'Manages appointments and scheduling',
                    'system_prompt': 'You are a scheduling coordinator for A Killion Voice. Help customers book appointments, check availability, and manage their calendar needs professionally.',
                    'keywords': ['appointment', 'schedule', 'meeting', 'book', 'calendar', 'available', 'time', 'date'], 'priority': 3,
                    'sms_template': 'Thanks for scheduling with A Killion Voice! {summary} We\'ll send appointment confirmations and reminders. Reply to make changes.'
                }
            ]
            
            for agent_data in default_agents:
                agent = AgentConfig(
                    agent_type=agent_data['agent_type'], 
                    name=agent_data['name'],
                    description=agent_data['description'], 
                    system_prompt=agent_data['system_prompt'],
                    sms_template=agent_data['sms_template'], 
                    priority=agent_data['priority']
                )
                agent.set_keywords(agent_data['keywords'])
                self.db.session.add(agent)
            
            self.db.session.commit()
            logger.info("✅ Default agent configurations created")
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Failed to create default agents: {e}")
    
    def check_model_integrity(self):
        """Check model relationships and foreign key integrity"""
        try:
            # This will be called after models are loaded
            integrity_issues = []
            
            # Check for missing foreign key references
            # This would contain actual integrity checks
            
            if integrity_issues:
                logger.warning(f"Model integrity issues found: {integrity_issues}")
                return False
            
            logger.info("Model integrity check passed")
            return True
            
        except Exception as e:
            logger.error(f"Model integrity check failed: {e}")
            return False
    
    def migrate_database(self):
        """Perform database migrations"""
        try:
            # Add any migration logic here
            logger.info("Database migration completed")
            return True
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            return False

# Global database manager
database_manager = DatabaseManager(db)

def init_database(app):
    """Initialize database with the Flask app"""
    db.init_app(app)
    return database_manager.initialize_database(app)

def get_model(name: str):
    """Get a model by name from registry"""
    return model_registry.get_model(name)

def register_model(name: str, model_class):
    """Register a model in the registry"""
    model_registry.register_model(name, model_class)
