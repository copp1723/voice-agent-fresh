"""
Tests for Knowledge Management API endpoints
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from io import BytesIO

# Import the blueprints
from server.routes.knowledge_management import knowledge_bp, domains_bp


@pytest.fixture
def app():
    """Create a test Flask application"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(domains_bp)
    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def mock_auth():
    """Mock the authentication decorator"""
    with patch('server.routes.knowledge_management.require_auth', lambda f: f) as mock:
        yield mock


@pytest.fixture
def mock_db():
    """Mock database session"""
    with patch('server.routes.knowledge_management.get_db') as mock:
        db_session = MagicMock()
        mock.return_value = iter([db_session])
        yield db_session


@pytest.fixture
def mock_kb():
    """Mock KnowledgeBase"""
    with patch('server.routes.knowledge_management.KnowledgeBase') as mock:
        yield mock


class TestKnowledgeEndpoints:
    """Test knowledge CRUD endpoints"""
    
    def test_add_knowledge_success(self, client, mock_auth, mock_db, mock_kb):
        """Test successful knowledge creation"""
        # Mock knowledge base response
        mock_knowledge = Mock()
        mock_knowledge.id = 1
        mock_knowledge.domain_name = "test_domain"
        mock_knowledge.content = "Test content"
        mock_knowledge.metadata = {"knowledge_type": "fact", "title": "Test"}
        mock_knowledge.version = 1
        mock_knowledge.active = True
        mock_knowledge.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_knowledge.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        
        mock_kb_instance = mock_kb.return_value
        mock_kb_instance.add_knowledge.return_value = mock_knowledge
        
        # Make request
        response = client.post('/api/knowledge', 
            json={
                'domain_name': 'test_domain',
                'content': 'Test content',
                'knowledge_type': 'fact',
                'title': 'Test'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['knowledge_id'] == 1
        assert 'knowledge' in data
    
    def test_add_knowledge_missing_fields(self, client, mock_auth, mock_db):
        """Test knowledge creation with missing required fields"""
        response = client.post('/api/knowledge', 
            json={'content': 'Test content'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Domain name is required' in data['error']
    
    def test_list_knowledge(self, client, mock_auth, mock_db):
        """Test listing knowledge entries"""
        # Mock database query
        mock_item = Mock()
        mock_item.id = 1
        mock_item.domain_name = "test_domain"
        mock_item.title = "Test Title"
        mock_item.knowledge_type = "fact"
        mock_item.content = "Test content"
        mock_item.metadata = {"title": "Test Title", "knowledge_type": "fact"}
        mock_item.version = 1
        mock_item.active = True
        mock_item.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_item.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = [mock_item]
        
        # Make request
        response = client.get('/api/knowledge?domain=test_domain')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'knowledge_items' in data
        assert len(data['knowledge_items']) == 1
        assert data['total'] == 1
    
    def test_get_knowledge_by_id(self, client, mock_auth, mock_db):
        """Test getting specific knowledge entry"""
        # Mock knowledge entry
        mock_knowledge = Mock()
        mock_knowledge.id = 1
        mock_knowledge.domain_name = "test_domain"
        mock_knowledge.title = "Test Title"
        mock_knowledge.knowledge_type = "fact"
        mock_knowledge.content = "Test content"
        mock_knowledge.metadata = {"title": "Test Title", "knowledge_type": "fact"}
        mock_knowledge.version = 1
        mock_knowledge.active = True
        mock_knowledge.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_knowledge.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_knowledge
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        # Make request
        response = client.get('/api/knowledge/1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 1
        assert data['domain_name'] == 'test_domain'
    
    def test_update_knowledge(self, client, mock_auth, mock_db, mock_kb):
        """Test updating knowledge entry"""
        # Mock existing knowledge
        mock_knowledge = Mock()
        mock_knowledge.id = 1
        mock_knowledge.metadata = {"title": "Old Title"}
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_knowledge
        
        # Mock update response
        updated_knowledge = Mock()
        updated_knowledge.id = 1
        updated_knowledge.domain_name = "test_domain"
        updated_knowledge.metadata = {"title": "New Title", "knowledge_type": "fact"}
        updated_knowledge.content = "Updated content"
        updated_knowledge.version = 2
        updated_knowledge.active = True
        updated_knowledge.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        
        mock_kb_instance = mock_kb.return_value
        mock_kb_instance.update_knowledge.return_value = updated_knowledge
        
        # Make request
        response = client.put('/api/knowledge/1',
            json={'content': 'Updated content', 'title': 'New Title'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['knowledge']['version'] == 2
    
    def test_delete_knowledge(self, client, mock_auth, mock_db, mock_kb):
        """Test deleting knowledge entry"""
        mock_kb_instance = mock_kb.return_value
        mock_kb_instance.delete_knowledge.return_value = True
        
        response = client.delete('/api/knowledge/1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_import_knowledge_csv(self, client, mock_auth, mock_db, mock_kb):
        """Test importing knowledge from CSV"""
        # Create CSV data
        csv_data = b"""title,content,type,tags,source
Test FAQ,This is a test FAQ,faq,test,manual
Test Policy,This is a test policy,policy,test,manual"""
        
        mock_kb_instance = mock_kb.return_value
        mock_kb_instance.bulk_import_knowledge.return_value = (2, 0)
        
        # Make request with file upload
        data = {
            'file': (BytesIO(csv_data), 'test.csv'),
            'domain_name': 'test_domain'
        }
        
        response = client.post('/api/knowledge/import',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True
        assert result['successful'] == 2
        assert result['failed'] == 0
    
    def test_generate_embeddings(self, client, mock_auth, mock_db, mock_kb):
        """Test regenerating embeddings"""
        mock_kb_instance = mock_kb.return_value
        mock_kb_instance.regenerate_embeddings.return_value = 10
        
        response = client.post('/api/knowledge/generate-embeddings',
            json={'domain': 'test_domain'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 10


class TestDomainEndpoints:
    """Test domain management endpoints"""
    
    def test_list_domains(self, client, mock_auth, mock_db):
        """Test listing all domains"""
        # Mock domain query
        mock_db.query.return_value.filter.return_value.all.return_value = [
            ('domain1',), ('domain2',)
        ]
        
        # Mock count queries
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.join.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        
        response = client.get('/api/domains')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'domains' in data
        assert len(data['domains']) == 2
        assert data['total'] == 2
    
    def test_create_domain(self, client, mock_auth, mock_db, mock_kb):
        """Test creating a new domain"""
        # Mock existing check
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        
        # Mock knowledge base
        mock_kb_instance = mock_kb.return_value
        
        response = client.post('/api/domains',
            json={
                'name': 'new_domain',
                'description': 'Test domain',
                'initial_knowledge': [
                    {
                        'content': 'Initial knowledge',
                        'title': 'Overview',
                        'knowledge_type': 'fact'
                    }
                ]
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['domain']['name'] == 'new_domain'
    
    def test_create_domain_already_exists(self, client, mock_auth, mock_db):
        """Test creating domain that already exists"""
        # Mock existing domain
        mock_db.query.return_value.filter_by.return_value.first.return_value = Mock()
        
        response = client.post('/api/domains',
            json={'name': 'existing_domain'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'already exists' in data['error']
    
    def test_export_template_csv(self, client, mock_auth):
        """Test exporting CSV template"""
        response = client.get('/api/knowledge/export-template/csv')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert b'title,content,type,tags,source' in response.data
    
    def test_export_template_json(self, client, mock_auth):
        """Test exporting JSON template"""
        response = client.get('/api/knowledge/export-template/json')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert 'entries' in data
        assert len(data['entries']) > 0


if __name__ == "__main__":
    pytest.main([__file__])