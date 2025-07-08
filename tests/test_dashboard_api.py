"""
Integration tests for dashboard API endpoints
"""
import pytest
import json
from datetime import datetime, timedelta
from src.models.call import Call, AgentConfig, SMSLog, db
from src.models.user import User
from src.models.customer import Customer
from src.services.auth import AuthService

class TestDashboardAPI:
    
    @pytest.fixture
    def auth_headers(self, app):
        """Create authenticated headers for requests"""
        with app.app_context():
            # Create test user
            user = User(username='testuser', email='test@example.com', role='admin')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            
            # Generate token
            tokens = AuthService.generate_tokens(user.id)
            
            return {
                'Authorization': f'Bearer {tokens["access_token"]}',
                'Content-Type': 'application/json'
            }
    
    @pytest.fixture
    def sample_data(self, app):
        """Create sample data for testing"""
        with app.app_context():
            # Create agent configs
            agents = [
                AgentConfig(
                    agent_type='billing',
                    name='Billing Agent',
                    description='Handles billing inquiries',
                    system_prompt='You are a billing specialist'
                ),
                AgentConfig(
                    agent_type='support',
                    name='Support Agent',
                    description='Technical support',
                    system_prompt='You are a tech support specialist'
                )
            ]
            db.session.add_all(agents)
            
            # Create customers
            customers = []
            for i in range(5):
                customer = Customer(
                    phone_number=f'+123456789{i}',
                    name=f'Customer {i}'
                )
                customers.append(customer)
            db.session.add_all(customers)
            db.session.commit()
            
            # Create calls
            calls = []
            for i in range(10):
                call = Call(
                    call_sid=f'CA{i:03d}',
                    from_number=customers[i % 5].phone_number,
                    to_number='+0987654321',
                    customer_id=customers[i % 5].id,
                    agent_type=agents[i % 2].agent_type,
                    status='completed' if i < 8 else 'failed',
                    duration=180 + (i * 30),
                    start_time=datetime.utcnow() - timedelta(days=i),
                    end_time=datetime.utcnow() - timedelta(days=i) + timedelta(minutes=3)
                )
                calls.append(call)
            db.session.add_all(calls)
            
            # Create SMS logs
            sms_logs = []
            for i in range(5):
                sms = SMSLog(
                    call_id=calls[i].id,
                    sms_sid=f'SM{i:03d}',
                    to_number=calls[i].from_number,
                    message_body='Thanks for calling!',
                    customer_id=customers[i].id,
                    status='sent' if i < 4 else 'failed',
                    agent_type=calls[i].agent_type
                )
                sms_logs.append(sms)
            db.session.add_all(sms_logs)
            
            db.session.commit()
            
            return {
                'agents': agents,
                'customers': customers,
                'calls': calls,
                'sms_logs': sms_logs
            }
    
    def test_get_dashboard_metrics(self, client, auth_headers, sample_data):
        """Test getting dashboard metrics"""
        response = client.get(
            '/api/dashboard/metrics?days=7',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check summary metrics
        assert 'totalCalls' in data
        assert data['totalCalls'] >= 7  # Last 7 days
        assert 'activeCalls' in data
        assert 'averageCallDuration' in data
        assert 'callSuccessRate' in data
        assert 'totalSMS' in data
        assert 'smsSuccessRate' in data
        
        # Check distributions
        assert 'callStatuses' in data
        assert 'agentDistribution' in data
        assert 'callVolumeData' in data
        
        # Check period info
        assert 'period' in data
        assert data['period']['days'] == 7
    
    def test_get_agent_metrics(self, client, auth_headers, sample_data):
        """Test getting agent-specific metrics"""
        response = client.get(
            '/api/dashboard/agent-metrics?days=30',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'agents' in data
        assert len(data['agents']) >= 2  # billing and support
        
        # Check agent metrics structure
        for agent in data['agents']:
            assert 'agentType' in agent
            assert 'name' in agent
            assert 'status' in agent
            assert 'totalCalls' in agent
            assert 'completedCalls' in agent
            assert 'averageDuration' in agent
            assert 'successRate' in agent
            assert 'activeCalls' in agent
    
    def test_get_call_distribution(self, client, auth_headers, sample_data):
        """Test getting call distribution data"""
        response = client.get(
            '/api/dashboard/call-distribution?days=7',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check distribution types
        assert 'byAgent' in data
        assert 'byHour' in data
        assert 'byDayOfWeek' in data
        
        # Check agent distribution
        assert len(data['byAgent']) > 0
        for item in data['byAgent']:
            assert 'agent' in item
            assert 'calls' in item
            assert 'avgDuration' in item
        
        # Check period info
        assert 'period' in data
        assert data['period']['days'] == 7
    
    def test_health_check(self, client):
        """Test health check endpoint (no auth required)"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'status' in data
        assert 'timestamp' in data
        assert 'services' in data
        assert 'stats' in data
        
        # Check services status
        services = data['services']
        assert 'database' in services
        assert 'websocket' in services
        assert 'twilio' in services
        assert 'openrouter' in services
    
    def test_dashboard_metrics_unauthorized(self, client):
        """Test dashboard metrics without authentication"""
        response = client.get('/api/dashboard/metrics')
        assert response.status_code == 401
    
    def test_dashboard_metrics_with_filters(self, client, auth_headers, sample_data):
        """Test dashboard metrics with custom date range"""
        response = client.get(
            '/api/dashboard/metrics?days=30',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should include all sample data (10 calls)
        assert data['totalCalls'] == 10
        assert data['period']['days'] == 30
    
    def test_agent_metrics_empty_data(self, client, auth_headers):
        """Test agent metrics with no data"""
        # Clear all calls
        with client.application.app_context():
            Call.query.delete()
            db.session.commit()
        
        response = client.get(
            '/api/dashboard/agent-metrics',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should still return agent list, just with zero stats
        assert 'agents' in data
        for agent in data['agents']:
            assert agent['totalCalls'] == 0
            assert agent['completedCalls'] == 0