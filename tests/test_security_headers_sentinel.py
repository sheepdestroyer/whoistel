import pytest
import tempfile
import os
from webapp import create_app
import history_manager

@pytest.fixture
def app_instance(monkeypatch):
    """Fixture that creates a Flask app instance with a temporary history database."""
    # Create a temporary database for history to avoid filesystem issues
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setattr(history_manager, 'DB_FILE', db_path)

    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-key'
    })

    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app_instance):
    """Fixture that provides a test client for the app."""
    with app_instance.test_client() as client:
        yield client

def test_security_headers(client):
    """Test that security headers are present in the response."""
    response = client.get('/')
    assert response.status_code == 200

    headers = response.headers

    # Check Content-Security-Policy
    # Allowing unsafe-inline for now as per legacy requirements
    assert 'Content-Security-Policy' in headers
    assert "default-src 'self'" in headers['Content-Security-Policy']
    assert "script-src 'self' 'unsafe-inline'" in headers['Content-Security-Policy']
    assert "style-src 'self' 'unsafe-inline'" in headers['Content-Security-Policy']

    # Check X-Content-Type-Options
    assert headers.get('X-Content-Type-Options') == 'nosniff'

    # Check X-Frame-Options
    assert headers.get('X-Frame-Options') == 'SAMEORIGIN'

    # Check Referrer-Policy
    assert headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
