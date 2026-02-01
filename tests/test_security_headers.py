import pytest
import os
import tempfile
from webapp import create_app
import history_manager

@pytest.fixture
def app_instance(monkeypatch):
    """Fixture that creates a Flask app instance with a temporary history database."""
    # Create a temporary database for history to avoid touching the real one
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
    """Fixture that provides a test client for the app."""
    with app_instance.test_client() as client:
        yield client

def test_security_headers_present(client):
    """Test that all required security headers are present in the response."""
    response = client.get('/')
    assert response.status_code == 200

    headers = response.headers

    # Check X-Content-Type-Options
    assert headers.get('X-Content-Type-Options') == 'nosniff', "X-Content-Type-Options header missing or incorrect"

    # Check X-Frame-Options
    assert headers.get('X-Frame-Options') == 'SAMEORIGIN', "X-Frame-Options header missing or incorrect"

    # Check Referrer-Policy
    assert headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin', "Referrer-Policy header missing or incorrect"

    # Check Content-Security-Policy
    csp = headers.get('Content-Security-Policy')
    assert csp is not None, "Content-Security-Policy header missing"
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'unsafe-inline'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "object-src 'none'" in csp
