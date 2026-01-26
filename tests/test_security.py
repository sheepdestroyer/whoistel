import pytest
import os
import tempfile
from webapp import create_app
import history_manager

@pytest.fixture
def client(monkeypatch):
    # Create a temporary database for history to avoid locking/IO issues
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setattr(history_manager, 'DB_FILE', db_path)

    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-key'})
    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_security_headers(client):
    """Test that all required security headers are present in the response."""
    response = client.get('/')
    headers = response.headers

    # Content-Security-Policy
    assert 'Content-Security-Policy' in headers
    assert "default-src 'self'" in headers['Content-Security-Policy']

    # X-Content-Type-Options
    assert headers.get('X-Content-Type-Options') == 'nosniff'

    # X-Frame-Options
    assert headers.get('X-Frame-Options') in ['DENY', 'SAMEORIGIN']

    # Referrer-Policy
    assert headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'

    # Strict-Transport-Security (HSTS)
    assert 'Strict-Transport-Security' in headers
