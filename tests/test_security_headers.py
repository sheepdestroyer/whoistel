import pytest
from webapp import create_app

@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test'})
    with app.test_client() as client:
        yield client

def test_security_headers(client):
    response = client.get('/')
    assert response.status_code == 200
    headers = response.headers

    # Check for X-Content-Type-Options
    assert headers.get('X-Content-Type-Options') == 'nosniff'

    # Check for X-Frame-Options
    assert headers.get('X-Frame-Options') == 'SAMEORIGIN'

    # Check for Content-Security-Policy
    # Allowing unsafe-inline as per existing patterns/requirements mentioned in memory
    csp = headers.get('Content-Security-Policy')
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'unsafe-inline'" in csp

    # Check for Referrer-Policy
    assert headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
