"""
Unit tests for customer management
"""
import pytest
from datetime import datetime
from src.models.customer import Customer, Tag, db
from src.models.call import Call, SMSLog

class TestCustomerModel:
    
    def test_create_customer(self, app, db):
        """Test creating a new customer"""
        with app.app_context():
            customer = Customer(
                phone_number='+1234567890',
                name='John Doe',
                email='john@example.com',
                notes='VIP customer'
            )
            db.session.add(customer)
            db.session.commit()
            
            # Verify customer was created
            saved_customer = Customer.query.filter_by(phone_number='+1234567890').first()
            assert saved_customer is not None
            assert saved_customer.name == 'John Doe'
            assert saved_customer.email == 'john@example.com'
            assert saved_customer.notes == 'VIP customer'
    
    def test_customer_to_dict(self, app, db):
        """Test customer to_dict method"""
        with app.app_context():
            customer = Customer(
                phone_number='+1234567890',
                name='Jane Doe',
                email='jane@example.com'
            )
            db.session.add(customer)
            db.session.commit()
            
            # Test basic to_dict
            customer_dict = customer.to_dict()
            assert customer_dict['phoneNumber'] == '+1234567890'
            assert customer_dict['name'] == 'Jane Doe'
            assert customer_dict['email'] == 'jane@example.com'
            assert 'stats' not in customer_dict
            
            # Test with stats
            customer_dict_with_stats = customer.to_dict(include_stats=True)
            assert 'stats' in customer_dict_with_stats
            assert customer_dict_with_stats['stats']['totalCalls'] == 0
            assert customer_dict_with_stats['stats']['totalSMS'] == 0
    
    def test_customer_tags(self, app, db):
        """Test customer tag relationships"""
        with app.app_context():
            # Create tags
            tag1 = Tag(name='VIP', color='#FF0000')
            tag2 = Tag(name='Support', color='#00FF00')
            db.session.add_all([tag1, tag2])
            
            # Create customer with tags
            customer = Customer(phone_number='+1234567890')
            customer.tags.append(tag1)
            customer.tags.append(tag2)
            db.session.add(customer)
            db.session.commit()
            
            # Verify tags
            saved_customer = Customer.query.filter_by(phone_number='+1234567890').first()
            assert len(saved_customer.tags) == 2
            tag_names = [tag.name for tag in saved_customer.tags]
            assert 'VIP' in tag_names
            assert 'Support' in tag_names
    
    def test_update_customer_stats(self, app, db):
        """Test updating customer statistics"""
        with app.app_context():
            # Create customer
            customer = Customer(phone_number='+1234567890')
            db.session.add(customer)
            db.session.commit()
            
            # Create some calls for the customer
            call1 = Call(
                call_sid='CA123',
                from_number='+1234567890',
                to_number='+0987654321',
                customer_id=customer.id,
                agent_type='billing',
                status='completed',
                start_time=datetime.utcnow()
            )
            call2 = Call(
                call_sid='CA456',
                from_number='+1234567890',
                to_number='+0987654321',
                customer_id=customer.id,
                agent_type='support',
                status='completed',
                start_time=datetime.utcnow()
            )
            db.session.add_all([call1, call2])
            
            # Create SMS log
            sms = SMSLog(
                call_id=call1.id,
                sms_sid='SM123',
                to_number='+1234567890',
                message_body='Thanks for calling',
                customer_id=customer.id
            )
            db.session.add(sms)
            db.session.commit()
            
            # Update stats
            customer.update_stats()
            db.session.commit()
            
            # Verify stats
            assert customer.total_calls == 2
            assert customer.total_sms == 1
            assert customer.last_contact is not None
            assert customer.preferred_agent in ['billing', 'support']
    
    def test_customer_unique_phone(self, app, db):
        """Test that phone numbers must be unique"""
        with app.app_context():
            # Create first customer
            customer1 = Customer(phone_number='+1234567890')
            db.session.add(customer1)
            db.session.commit()
            
            # Try to create second customer with same phone
            customer2 = Customer(phone_number='+1234567890')
            db.session.add(customer2)
            
            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()

class TestTagModel:
    
    def test_create_tag(self, app, db):
        """Test creating a tag"""
        with app.app_context():
            tag = Tag(name='Premium', color='#FFD700')
            db.session.add(tag)
            db.session.commit()
            
            saved_tag = Tag.query.filter_by(name='Premium').first()
            assert saved_tag is not None
            assert saved_tag.color == '#FFD700'
    
    def test_tag_to_dict(self, app, db):
        """Test tag to_dict method"""
        with app.app_context():
            tag = Tag(name='Urgent', color='#FF0000')
            db.session.add(tag)
            db.session.commit()
            
            tag_dict = tag.to_dict()
            assert tag_dict['name'] == 'Urgent'
            assert tag_dict['color'] == '#FF0000'
            assert 'id' in tag_dict
            assert 'createdAt' in tag_dict
    
    def test_tag_unique_name(self, app, db):
        """Test that tag names must be unique"""
        with app.app_context():
            # Create first tag
            tag1 = Tag(name='Important')
            db.session.add(tag1)
            db.session.commit()
            
            # Try to create second tag with same name
            tag2 = Tag(name='Important')
            db.session.add(tag2)
            
            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()
    
    def test_tag_default_color(self, app, db):
        """Test tag default color"""
        with app.app_context():
            tag = Tag(name='Default')
            db.session.add(tag)
            db.session.commit()
            
            assert tag.color == '#3B82F6'  # Default blue color