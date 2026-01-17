import os
import tempfile
import pytest
from webapp import create_app

@pytest.fixture
def app_instance():
    """Fixture that creates a Flask app instance with a temporary history database."""
    db_fd, db_path = tempfile.mkstemp()
    os.environ['HISTORY_DB_FILE'] = db_path

    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'dev',
        'WTF_CSRF_ENABLED': False
    })

    yield app

    os.close(db_fd)
    os.unlink(db_path)

def test_security_headers_present(app_instance):
    """Test that standard security headers are present in responses."""
    client = app_instance.test_client()
    response = client.get('/')

    headers = response.headers

    expected = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }

    for key, value in expected.items():
        assert key in headers, f"Missing security header: {key}"
        assert headers[key] == value, f"Incorrect value for {key}. Expected '{value}', got '{headers[key]}'"
