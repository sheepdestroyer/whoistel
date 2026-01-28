import pytest
import tempfile
import os
from webapp import create_app
import history_manager

@pytest.fixture
def app_instance(monkeypatch):
    """Fixture that creates a Flask app instance with a temporary history database."""
    # Create a temporary database for history to avoid file locking issues
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setattr(history_manager, 'DB_FILE', db_path)

    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-key-security'
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

    # CSP
    assert 'Content-Security-Policy' in headers
    expected_csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    assert headers['Content-Security-Policy'] == expected_csp

    # X-Content-Type-Options
    assert 'X-Content-Type-Options' in headers
    assert headers['X-Content-Type-Options'] == 'nosniff'

    # X-Frame-Options
    assert 'X-Frame-Options' in headers
    assert headers['X-Frame-Options'] == 'SAMEORIGIN'

    # Referrer-Policy
    assert 'Referrer-Policy' in headers
    assert headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
