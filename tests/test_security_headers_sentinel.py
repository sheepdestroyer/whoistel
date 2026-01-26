
import pytest
import webapp

@pytest.fixture
def client():
    app = webapp.create_app({'TESTING': True, 'SECRET_KEY': 'dev'})
    with app.test_client() as client:
        yield client

def test_security_headers_presence(client):
    """
    Sentinel 🛡️ Verification:
    Ensures that critical security headers are present on all responses.
    """
    response = client.get('/')
    assert response.status_code == 200

    headers = response.headers

    # Anti-MIME-Sniffing
    assert 'X-Content-Type-Options' in headers
    assert headers['X-Content-Type-Options'] == 'nosniff'

    # Anti-Clickjacking
    assert 'X-Frame-Options' in headers
    assert headers['X-Frame-Options'] == 'SAMEORIGIN'

    # CSP (Relaxed for compatibility as per Sentinel Journal)
    assert 'Content-Security-Policy' in headers
    expected_csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    assert headers['Content-Security-Policy'] == expected_csp

    # Referrer Policy
    assert 'Referrer-Policy' in headers
    assert headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
