
import pytest
import tempfile
import os
from webapp import create_app
import history_manager

@pytest.fixture
def client():
    # Mock history DB to avoid file locking issues or side effects
    fd, path = tempfile.mkstemp()
    os.close(fd)
    original_db = history_manager.DB_FILE
    history_manager.DB_FILE = path

    app = create_app({'TESTING': True, 'SECRET_KEY': 'dev', 'WTF_CSRF_ENABLED': False})

    with app.test_client() as client:
        yield client

    # Cleanup
    history_manager.DB_FILE = original_db
    if os.path.exists(path):
        os.unlink(path)

def test_security_headers_present(client):
    response = client.get('/')
    headers = response.headers

    # Check Content-Security-Policy
    csp = headers.get('Content-Security-Policy')
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'unsafe-inline'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp

    # Check X-Content-Type-Options
    assert headers.get('X-Content-Type-Options') == 'nosniff'

    # Check X-Frame-Options
    assert headers.get('X-Frame-Options') == 'SAMEORIGIN'

    # Check Referrer-Policy
    assert headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
