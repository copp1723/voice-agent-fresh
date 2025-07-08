"""
Fixed Customer Model - Resolves circular import issues
"""
from .database import db, BaseModel, create_safe_foreign_key, create_safe_relationship, register_model
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Many-to-many relationship table for customer tags
# Using table reference to avoid import issues
customer_tags = db.Table('customer_tags',
    db.Column('customer_id', db.Integer, db.ForeignKey('customer.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Customer(BaseModel):
    """
    Customer model for storing customer information
    Fixed to avoid circular import issues
    """
    __tablename__ = 'customer'
    
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    notes = db.Column(db.Text)
    
    # Customer metrics
    total_calls = db.Column(db.Integer, default=0)
    total_sms = db.Column(db.Integer, default=0)
    last_contact = db.Column(db.DateTime)
    preferred_agent = db.Column(db.String(50))
    
    # Safe relationships using string references
    calls = create_safe_relationship('Call', back_ref='customer', lazy='dynamic', cascade='all, delete-orphan')
    sms_logs = create_safe_relationship('SMSLog', back_ref='customer', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=customer_tags, lazy='subquery',
                          backref=db.backref('customers', lazy=True))
    
    def __repr__(self):
        return f'<Customer {self.phone_number}>'
    
    def to_dict(self, include_stats=False):
        """Convert customer to dictionary"""
        data = {
            'id': self.id,
            'phoneNumber': self.phone_number,
            'name': self.name,
            'email': self.email,
            'notes': self.notes,
            'tags': [tag.name for tag in self.tags] if self.tags else [],
            'totalCalls': self.total_calls,
            'totalSMS': self.total_sms,
            'lastContact': self.last_contact.isoformat() if self.last_contact else None,
            'preferredAgent': self.preferred_agent,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_stats:
            data['stats'] = self.get_detailed_stats()
        
        return data
    
    def get_detailed_stats(self):
        """Get detailed customer statistics"""
        try:
            recent_calls = list(self.calls.order_by(db.desc('start_time')).limit(5))
            recent_sms = list(self.sms_logs.order_by(db.desc('sent_at')).limit(5))
            
            return {
                'totalCalls': self.total_calls,
                'totalSMS': self.total_sms,
                'recentCalls': [call.to_dict() for call in recent_calls],
                'recentSMS': [sms.to_dict() for sms in recent_sms]
            }
        except Exception as e:
            logger.error(f"Error getting customer stats: {e}")
            return {
                'totalCalls': self.total_calls,
                'totalSMS': self.total_sms,
                'recentCalls': [],
                'recentSMS': []
            }
    
    def update_stats(self):
        """Update customer statistics safely"""
        try:
            # Update call and SMS counts
            self.total_calls = self.calls.count()
            self.total_sms = self.sms_logs.count()
            
            # Get last contact from calls or SMS
            last_call = self.calls.order_by(db.desc('start_time')).first()
            last_sms = self.sms_logs.order_by(db.desc('sent_at')).first()
            
            contact_times = []
            if last_call and hasattr(last_call, 'start_time') and last_call.start_time:
                contact_times.append(last_call.start_time)
            if last_sms and hasattr(last_sms, 'sent_at') and last_sms.sent_at:
                contact_times.append(last_sms.sent_at)
            
            if contact_times:
                self.last_contact = max(contact_times)
            
            # Update preferred agent based on most frequent agent
            try:
                # Import Call model only when needed to avoid circular imports
                from .call_fixed import Call
                
                agent_counts = db.session.query(
                    Call.agent_type, db.func.count(Call.id)
                ).filter(
                    Call.customer_id == self.id
                ).group_by(Call.agent_type).all()
                
                if agent_counts:
                    self.preferred_agent = max(agent_counts, key=lambda x: x[1])[0]
                    
            except Exception as e:
                logger.warning(f"Could not update preferred agent: {e}")
            
            # Save changes
            self.save()
            
        except Exception as e:
            logger.error(f"Error updating customer stats: {e}")
    
    @classmethod
    def find_by_phone(cls, phone_number: str):
        """Find customer by phone number"""
        return cls.query.filter_by(phone_number=phone_number).first()
    
    @classmethod
    def get_or_create(cls, phone_number: str, **kwargs):
        """Get existing customer or create new one"""
        customer = cls.find_by_phone(phone_number)
        if not customer:
            customer = cls(phone_number=phone_number, **kwargs)
            customer.save()
        return customer


class Tag(BaseModel):
    """Tag model for categorizing customers"""
    __tablename__ = 'tag'
    
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#3B82F6')  # Hex color code
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_or_create(cls, name: str, color: str = None):
        """Get existing tag or create new one"""
        tag = cls.query.filter_by(name=name).first()
        if not tag:
            tag = cls(name=name, color=color or '#3B82F6')
            tag.save()
        return tag


# Register models in the registry
register_model('Customer', Customer)
register_model('Tag', Tag)

# Export models
__all__ = ['Customer', 'Tag', 'customer_tags']
