import pytest
from webapp import create_app

@pytest.fixture
def client():
    """Configures the app for testing and returns a test client."""
    app = create_app({'TESTING': True, 'WTF_CSRF_ENABLED': False, 'SECRET_KEY': 'test-key'})
    with app.test_client() as client:
        yield client

def test_security_headers(client):
    """
    Test that the application sets the expected security headers on responses.
    """
    response = client.get('/')
    assert response.status_code == 200

    headers = response.headers

    # CSP: Strict default, only allow own origin
    assert 'Content-Security-Policy' in headers, "Missing Content-Security-Policy header"
    assert "default-src 'self'" in headers['Content-Security-Policy']

    # X-Content-Type-Options: Prevent MIME sniffing
    assert 'X-Content-Type-Options' in headers, "Missing X-Content-Type-Options header"
    assert headers['X-Content-Type-Options'] == 'nosniff'

    # X-Frame-Options: Prevent clickjacking
    assert 'X-Frame-Options' in headers, "Missing X-Frame-Options header"
    assert headers['X-Frame-Options'] == 'SAMEORIGIN'

    # Referrer-Policy: Control referrer information
    assert 'Referrer-Policy' in headers, "Missing Referrer-Policy header"
    assert headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
