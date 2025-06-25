import json

def test_health_check(client):
    """Test the /health endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'A Killion Voice Agent'
    assert data['domain'] == 'akillionvoice.xyz' # Expected value from voice.py
    assert data['phone'] == '(978) 643-2034'   # Expected value from voice.py
    assert 'active_calls' in data # Check presence, value can vary
    assert data['webhook_url'] == 'https://api.akillionvoice.xyz/api/twilio/inbound' # Expected
    # For a test environment, OPENROUTER_API_KEY and TWILIO_ACCOUNT_SID might not be set.
    # The boolean conversion bool(os.getenv(...)) will result in False.
    # So, we should assert their expected state in a test environment (likely False).
    # This can be made more robust by setting test-specific env vars in conftest.py if needed.
    assert data['openrouter_configured'] is False # Assuming not set in test env
    assert data['twilio_configured'] is False   # Assuming not set in test env
    assert data['sms_enabled'] is False         # Assuming not set in test env
    assert data['session_management'] == "enabled"

def test_main_page_serves_index_html(client):
    """Test that the root path serves index.html."""
    response = client.get('/')
    assert response.status_code == 200
    # The title in src/static/index.html is "voice-agent-fresh"
    assert b"<title>voice-agent-fresh</title>" in response.data

def test_favicon_serves_correctly(client):
    """Test that /favicon.ico is served."""
    response = client.get('/favicon.ico')
    assert response.status_code == 200
    assert response.mimetype == 'image/vnd.microsoft.icon'

def test_get_calls_unauthorized(client):
    """Test GET /api/calls without API key returns 401."""
    # Temporarily remove API_KEY from environment for this test if it was set globally for the app
    # Or, more simply, rely on the client not sending it by default.
    # The conftest.py sets os.environ['API_KEY'], so the middleware will expect it.
    response = client.get('/api/calls')
    assert response.status_code == 401 # As per require_api_key decorator

def test_get_calls_authorized_header(client, app):
    """Test GET /api/calls with correct API key in header returns 200."""
    api_key = app.config.get('API_KEY')
    assert api_key is not None, "API_KEY should be set in app.config for this test"
    headers = {
        'X-API-Key': api_key
    }
    response = client.get('/api/calls', headers=headers)
    assert response.status_code == 200
    # We can also assert that the response is a list (empty or not)
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_get_calls_authorized_query_param(client, app):
    """Test GET /api/calls with correct API key in query param returns 200."""
    api_key = app.config.get('API_KEY')
    assert api_key is not None, "API_KEY should be set in app.config for this test"
    response = client.get(f'/api/calls?api_key={api_key}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_get_calls_invalid_key(client, app):
    """Test GET /api/calls with incorrect API key returns 401."""
    headers = {
        'X-API-Key': 'wrong-key'
    }
    response = client.get('/api/calls', headers=headers)
    assert response.status_code == 401

# The /api/agents endpoint is also protected by require_api_key
def test_get_agents_unauthorized(client):
    """Test GET /api/agents without API key returns 401."""
    response = client.get('/api/agents')
    assert response.status_code == 401

def test_get_agents_authorized(client, app):
    """Test GET /api/agents with correct API key returns 200."""
    api_key = app.config.get('API_KEY')
    headers = {
        'X-API-Key': api_key
    }
    response = client.get('/api/agents', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list) # Expecting a list of agent configurations
