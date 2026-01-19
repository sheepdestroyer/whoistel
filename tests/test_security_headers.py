import pytest
from webapp import create_app
import history_manager
import os
import tempfile

@pytest.fixture
def app_instance(monkeypatch):
    """Fixture that creates a Flask app instance with a temporary history database."""
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setattr(history_manager, 'DB_FILE', db_path)

    app = create_app({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key'
    })

    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app_instance):
    with app_instance.test_client() as client:
        yield client

def test_security_headers_present(client):
    """Test that all required security headers are present in the response."""
    response = client.get('/')
    headers = response.headers

    # Check for CSP
    assert 'Content-Security-Policy' in headers, "Missing Content-Security-Policy header"
    assert "default-src 'self'" in headers['Content-Security-Policy']

    # Check for X-Content-Type-Options
    assert 'X-Content-Type-Options' in headers, "Missing X-Content-Type-Options header"
    assert headers['X-Content-Type-Options'] == 'nosniff'

    # Check for X-Frame-Options
    assert 'X-Frame-Options' in headers, "Missing X-Frame-Options header"
    assert headers['X-Frame-Options'] == 'SAMEORIGIN'

    # Check for Referrer-Policy
    assert 'Referrer-Policy' in headers, "Missing Referrer-Policy header"
    assert headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
