import pytest
import os
from src.main import create_app # Import the factory
from src.models import db # Import the centralized db instance

@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    # Create an app instance using the factory, configured for testing
    test_app = create_app(config_name='testing')

    # Set additional test-specific configurations if not handled by create_app('testing')
    # For example, API_KEY if it's still read from app.config in some places
    # (though os.environ is better for middleware that reads directly from env)
    test_app.config['API_KEY'] = "test-api-key-123" # Ensure it's on app.config if needed
    os.environ['API_KEY'] = 'test-api-key-123' # For middleware reading from os.environ

    # The create_app function already calls db.init_app(test_app)
    # and db.create_all() within an app context.
    # If create_app doesn't handle db.create_all() for the testing config,
    # or if we want to ensure a clean slate for each session:
    with test_app.app_context():
        db.drop_all()  # Ensure clean state if tables existed
        db.create_all()  # Create tables for the :memory: DB

    yield test_app

    # Teardown: Clean up the database (especially if not in-memory or for clarity)
    with test_app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
