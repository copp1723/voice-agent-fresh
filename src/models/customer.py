"""
Customer Model - Store customer information and interaction history
"""
from datetime import datetime
from . import db

# Many-to-many relationship table for customer tags
customer_tags = db.Table('customer_tags',
    db.Column('customer_id', db.Integer, db.ForeignKey('customer.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Customer(db.Model):
    """Customer model for storing customer information"""
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    calls = db.relationship('Call', backref='customer', lazy='dynamic')
    sms_logs = db.relationship('SMSLog', backref='customer', lazy='dynamic')
    tags = db.relationship('Tag', secondary=customer_tags, lazy='subquery',
                          backref=db.backref('customers', lazy=True))
    
    # Customer metrics
    total_calls = db.Column(db.Integer, default=0)
    total_sms = db.Column(db.Integer, default=0)
    last_contact = db.Column(db.DateTime)
    preferred_agent = db.Column(db.String(50))
    
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
            'tags': [tag.name for tag in self.tags],
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'lastContact': self.last_contact.isoformat() if self.last_contact else None,
            'preferredAgent': self.preferred_agent
        }
        
        if include_stats:
            data['stats'] = {
                'totalCalls': self.total_calls,
                'totalSMS': self.total_sms,
                'recentCalls': self.calls.limit(5).all() if self.calls else []
            }
        
        return data
    
    def update_stats(self):
        """Update customer statistics"""
        self.total_calls = self.calls.count()
        self.total_sms = self.sms_logs.count()
        
        # Get last contact from calls or SMS
        last_call = self.calls.order_by(db.desc('start_time')).first()
        last_sms = self.sms_logs.order_by(db.desc('created_at')).first()
        
        if last_call and last_sms:
            self.last_contact = max(last_call.start_time, last_sms.created_at)
        elif last_call:
            self.last_contact = last_call.start_time
        elif last_sms:
            self.last_contact = last_sms.created_at
        
        # Update preferred agent based on most frequent agent
        agent_counts = db.session.query(
            Call.agent_type, db.func.count(Call.id)
        ).filter(
            Call.customer_id == self.id
        ).group_by(Call.agent_type).all()
        
        if agent_counts:
            self.preferred_agent = max(agent_counts, key=lambda x: x[1])[0]

class Tag(db.Model):
    """Tag model for categorizing customers"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#3B82F6')  # Hex color code
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }