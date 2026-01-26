import pytest
from webapp import create_app

@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test'})
    with app.test_client() as client:
        yield client

def test_security_headers(client):
    response = client.get('/')
    headers = response.headers

    assert headers.get('Content-Security-Policy') == "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    assert headers.get('X-Content-Type-Options') == 'nosniff'
    assert headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'

def test_cookie_security(client):
    # To test cookie security, we need to inspect the app config or response cookies
    # Since we can't easily inspect response cookies attributes with simple test_client without setting one,
    # let's check the app config defaults which Flask uses.
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test'})

    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
