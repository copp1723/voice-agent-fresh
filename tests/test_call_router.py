import pytest
from src.services.call_router import call_router
from src.models.call import AgentConfig, db

# Sample agent configurations for testing
SAMPLE_AGENTS_DATA = [
    {
        'agent_type': 'general', 'name': 'General', 'priority': 1,
        'keywords': ['hello', 'info', 'help'],
        'system_prompt': 'General prompt', 'sms_template': 'General SMS'
    },
    {
        'agent_type': 'billing', 'name': 'Billing', 'priority': 2,
        'keywords': ['invoice', 'payment', 'charge', 'refund'],
        'system_prompt': 'Billing prompt', 'sms_template': 'Billing SMS'
    },
    {
        'agent_type': 'support', 'name': 'Support', 'priority': 2,
        'keywords': ['broken', 'fix', 'technical issue', 'error'],
        'system_prompt': 'Support prompt', 'sms_template': 'Support SMS'
    },
    {
        'agent_type': 'sales', 'name': 'Sales', 'priority': 3, # Higher priority
        'keywords': ['buy', 'new product', 'pricing'],
        'system_prompt': 'Sales prompt', 'sms_template': 'Sales SMS'
    }
]

@pytest.fixture(scope="function", autouse=True)
def setup_agents_db(app):
    """Populates the database with agent configurations for each test function."""
    with app.app_context():
        # Clear existing AgentConfig data to ensure clean state for each test
        AgentConfig.query.delete()
        db.session.commit()

        for agent_data in SAMPLE_AGENTS_DATA:
            agent = AgentConfig(
                agent_type=agent_data['agent_type'],
                name=agent_data['name'],
                description=f"{agent_data['name']} Agent",
                system_prompt=agent_data['system_prompt'],
                sms_template=agent_data['sms_template'],
                priority=agent_data['priority']
            )
            agent.set_keywords(agent_data['keywords'])
            db.session.add(agent)
        db.session.commit()

        # Crucially, reload configurations into the global call_router instance
        call_router.load_agent_configs()

    yield # Test runs here

    # Teardown (optional, as in-memory DB is usually fresh, but good for clarity)
    # with app.app_context():
    #     AgentConfig.query.delete()
    #     db.session.commit()
    #     call_router.agent_configs = {} # Clear loaded configs


def test_route_to_general_default(app):
    """Test routing to general agent for ambiguous input."""
    with app.app_context():
        decision = call_router.route_call("call_sid_test_1", "I have a question.", "12345")
        assert decision['agent_type'] == 'general'
        assert decision['confidence'] == 0.1 # Default confidence for general

def test_route_to_billing_specific_keyword(app):
    """Test routing to billing agent with a specific keyword."""
    with app.app_context():
        decision = call_router.route_call("call_sid_test_2", "I have an issue with my invoice.", "12345")
        assert decision['agent_type'] == 'billing'
        assert decision['confidence'] > 0.1
        assert 'invoice' in decision['matched_keywords']

def test_route_to_support_multiple_keywords(app):
    """Test routing to support agent with multiple keywords."""
    with app.app_context():
        decision = call_router.route_call("call_sid_test_3", "My thing is broken and I see an error message.", "12345")
        assert decision['agent_type'] == 'support'
        assert decision['confidence'] > 0.1
        assert 'broken' in decision['matched_keywords']
        assert 'error' in decision['matched_keywords']

def test_route_to_sales_due_to_priority_and_keyword(app):
    """Test routing to sales agent, considering priority."""
    # "pricing" is a sales keyword.
    with app.app_context():
        decision = call_router.route_call("call_sid_test_4", "I want to know about pricing.", "12345")
        assert decision['agent_type'] == 'sales'
        assert decision['confidence'] > 0.1
        assert 'pricing' in decision['matched_keywords']

def test_route_to_general_if_no_keywords_match(app):
    """Test routing to general agent if no keywords match."""
    with app.app_context():
        decision = call_router.route_call("call_sid_test_5", "The sky is blue today.", "12345")
        assert decision['agent_type'] == 'general'

def test_analyze_intent_exact_match_bonus(app):
    """Test that an exact match of a keyword gets a higher score."""
    with app.app_context():
        # "payment" is a billing keyword
        analysis_specific = call_router.analyze_intent("I want to make a payment")
        analysis_exact = call_router.analyze_intent("payment")

        assert analysis_specific['agent_type'] == 'billing'
        assert analysis_exact['agent_type'] == 'billing'
        # Exact match should ideally have higher confidence if scoring reflects it.
        # The current scoring gives a fixed +50 bonus for exact phrase match.
        # A specific phrase containing a keyword will get score based on len(keyword)*priority + multi-keyword bonus
        # An exact single keyword match will get len(keyword)*priority + 50
        # This test will depend on the exact scoring logic and keyword lengths/priorities.
        # For "payment" (len 7, priority 2): score = 7*2 = 14. Exact match bonus +50 -> 64
        # For "I want to make a payment" (contains "payment"): score = 7*2 = 14.
        # So, analysis_exact should have a higher score.

        # We access the raw score from the analyze_intent logic for this assertion
        # This requires a bit of knowledge of the internal structure or a helper if this was common.
        # For simplicity, let's assume the confidence reflects this score difference.
        assert analysis_exact['confidence'] > analysis_specific['confidence']

def test_get_all_agents(app):
    """Test retrieving all agent configurations."""
    with app.app_context():
        agents = call_router.get_all_agents()
        assert len(agents) == len(SAMPLE_AGENTS_DATA)
        agent_types_retrieved = [agent['agent_type'] for agent in agents]
        for sample_agent in SAMPLE_AGENTS_DATA:
            assert sample_agent['agent_type'] in agent_types_retrieved

def test_get_agent_info(app):
    """Test retrieving a specific agent's configuration."""
    with app.app_context():
        billing_agent_info = call_router.get_agent_info('billing')
        assert billing_agent_info is not None
        assert billing_agent_info['name'] == 'Billing'
        assert 'invoice' in billing_agent_info['keywords']

        non_existent_agent_info = call_router.get_agent_info('nonexistent')
        assert non_existent_agent_info is None

# More tests could be added for update_agent_config, edge cases in scoring, etc.
