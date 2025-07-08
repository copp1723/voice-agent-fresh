"""
Integration tests for customer management endpoints
"""
import pytest
import json
from src.models.customer import Customer, Tag, db
from src.models.call import Call, SMSLog
from src.models.user import User
from src.services.auth import AuthService

class TestCustomerIntegration:
    
    @pytest.fixture
    def auth_headers(self, app):
        """Create authenticated headers for requests"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            
            tokens = AuthService.generate_tokens(user.id)
            
            return {
                'Authorization': f'Bearer {tokens["access_token"]}',
                'Content-Type': 'application/json'
            }
    
    def test_create_customer(self, client, auth_headers):
        """Test creating a new customer"""
        customer_data = {
            'phoneNumber': '+1234567890',
            'name': 'John Doe',
            'email': 'john@example.com',
            'notes': 'VIP customer',
            'tags': ['VIP', 'Premium']
        }
        
        response = client.post(
            '/api/customers',
            data=json.dumps(customer_data),
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['phoneNumber'] == '+1234567890'
        assert data['name'] == 'John Doe'
        assert data['email'] == 'john@example.com'
        assert data['notes'] == 'VIP customer'
        assert 'VIP' in data['tags']
        assert 'Premium' in data['tags']
    
    def test_get_customers(self, client, auth_headers):
        """Test getting customer list"""
        # Create some customers
        with client.application.app_context():
            for i in range(5):
                customer = Customer(
                    phone_number=f'+123456789{i}',
                    name=f'Customer {i}'
                )
                db.session.add(customer)
            db.session.commit()
        
        response = client.get('/api/customers', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'customers' in data
        assert 'total' in data
        assert 'page' in data
        assert 'pageSize' in data
        assert 'totalPages' in data
        
        assert data['total'] >= 5
        assert len(data['customers']) >= 5
    
    def test_get_customers_with_search(self, client, auth_headers):
        """Test searching customers"""
        # Create customers
        with client.application.app_context():
            customer1 = Customer(
                phone_number='+1234567890',
                name='John Smith',
                email='john@example.com'
            )
            customer2 = Customer(
                phone_number='+0987654321',
                name='Jane Doe',
                email='jane@example.com'
            )
            db.session.add_all([customer1, customer2])
            db.session.commit()
        
        # Search by name
        response = client.get(
            '/api/customers?search=John',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert any(c['name'] == 'John Smith' for c in data['customers'])
        
        # Search by phone
        response = client.get(
            '/api/customers?search=0987',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert any(c['phoneNumber'] == '+0987654321' for c in data['customers'])
    
    def test_get_customers_with_tag_filter(self, client, auth_headers):
        """Test filtering customers by tags"""
        # Create customers with tags
        with client.application.app_context():
            tag_vip = Tag(name='VIP')
            tag_support = Tag(name='Support')
            db.session.add_all([tag_vip, tag_support])
            
            customer1 = Customer(phone_number='+1111111111')
            customer1.tags.append(tag_vip)
            
            customer2 = Customer(phone_number='+2222222222')
            customer2.tags.append(tag_support)
            
            customer3 = Customer(phone_number='+3333333333')
            customer3.tags.extend([tag_vip, tag_support])
            
            db.session.add_all([customer1, customer2, customer3])
            db.session.commit()
        
        # Filter by VIP tag
        response = client.get(
            '/api/customers?tags=VIP',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 2  # customer1 and customer3
    
    def test_get_customer_detail(self, client, auth_headers):
        """Test getting customer details"""
        # Create customer with related data
        with client.application.app_context():
            customer = Customer(
                phone_number='+1234567890',
                name='Test Customer'
            )
            db.session.add(customer)
            db.session.commit()
            
            # Add some calls
            call = Call(
                call_sid='CA123',
                from_number=customer.phone_number,
                to_number='+0987654321',
                customer_id=customer.id,
                status='completed'
            )
            db.session.add(call)
            db.session.commit()
            
            customer_id = customer.id
        
        response = client.get(
            f'/api/customers/{customer_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['phoneNumber'] == '+1234567890'
        assert data['name'] == 'Test Customer'
        assert 'stats' in data  # Should include stats when getting detail
    
    def test_update_customer(self, client, auth_headers):
        """Test updating customer information"""
        # Create customer
        with client.application.app_context():
            customer = Customer(
                phone_number='+1234567890',
                name='Old Name'
            )
            db.session.add(customer)
            db.session.commit()
            customer_id = customer.id
        
        update_data = {
            'name': 'New Name',
            'email': 'newemail@example.com',
            'notes': 'Updated notes',
            'tags': ['Updated', 'Customer']
        }
        
        response = client.put(
            f'/api/customers/{customer_id}',
            data=json.dumps(update_data),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['name'] == 'New Name'
        assert data['email'] == 'newemail@example.com'
        assert data['notes'] == 'Updated notes'
        assert 'Updated' in data['tags']
        assert 'Customer' in data['tags']
    
    def test_delete_customer(self, client, auth_headers):
        """Test deleting a customer"""
        # Create customer
        with client.application.app_context():
            customer = Customer(phone_number='+1234567890')
            db.session.add(customer)
            db.session.commit()
            customer_id = customer.id
        
        response = client.delete(
            f'/api/customers/{customer_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify customer is deleted
        with client.application.app_context():
            deleted_customer = Customer.query.get(customer_id)
            assert deleted_customer is None
    
    def test_get_customer_calls(self, client, auth_headers):
        """Test getting customer call history"""
        # Create customer with calls
        with client.application.app_context():
            customer = Customer(phone_number='+1234567890')
            db.session.add(customer)
            db.session.commit()
            
            # Create multiple calls
            for i in range(5):
                call = Call(
                    call_sid=f'CA{i:03d}',
                    from_number=customer.phone_number,
                    to_number='+0987654321',
                    customer_id=customer.id,
                    status='completed'
                )
                db.session.add(call)
            db.session.commit()
            
            customer_id = customer.id
        
        response = client.get(
            f'/api/customers/{customer_id}/calls',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'calls' in data
        assert 'total' in data
        assert data['total'] == 5
        assert len(data['calls']) == 5
    
    def test_get_customer_sms(self, client, auth_headers):
        """Test getting customer SMS history"""
        # Create customer with SMS logs
        with client.application.app_context():
            customer = Customer(phone_number='+1234567890')
            db.session.add(customer)
            
            # Create call first (required for SMS)
            call = Call(
                call_sid='CA123',
                from_number=customer.phone_number,
                to_number='+0987654321',
                customer_id=customer.id
            )
            db.session.add(call)
            db.session.commit()
            
            # Create SMS logs
            for i in range(3):
                sms = SMSLog(
                    call_id=call.id,
                    sms_sid=f'SM{i:03d}',
                    to_number=customer.phone_number,
                    message_body=f'Message {i}',
                    customer_id=customer.id
                )
                db.session.add(sms)
            db.session.commit()
            
            customer_id = customer.id
        
        response = client.get(
            f'/api/customers/{customer_id}/sms',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'customerId' in data
        assert 'phoneNumber' in data
        assert 'messages' in data
        assert 'total' in data
        assert data['total'] == 3
        assert len(data['messages']) == 3
    
    def test_get_tags(self, client, auth_headers):
        """Test getting all available tags"""
        # Create some tags
        with client.application.app_context():
            tags = [
                Tag(name='VIP', color='#FF0000'),
                Tag(name='Support', color='#00FF00'),
                Tag(name='Premium', color='#0000FF')
            ]
            db.session.add_all(tags)
            db.session.commit()
        
        response = client.get('/api/customers/tags', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert len(data) >= 3
        tag_names = [tag['name'] for tag in data]
        assert 'VIP' in tag_names
        assert 'Support' in tag_names
        assert 'Premium' in tag_names
    
    def test_create_customer_duplicate_phone(self, client, auth_headers):
        """Test creating customer with duplicate phone number"""
        # Create first customer
        customer_data = {
            'phoneNumber': '+1234567890',
            'name': 'First Customer'
        }
        
        response = client.post(
            '/api/customers',
            data=json.dumps(customer_data),
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Try to create second customer with same phone
        customer_data['name'] = 'Second Customer'
        
        response = client.post(
            '/api/customers',
            data=json.dumps(customer_data),
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'already exists' in data['error']