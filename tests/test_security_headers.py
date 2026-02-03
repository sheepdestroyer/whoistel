import pytest

from webapp import create_app


@pytest.fixture
def client():
    # Provide a SECRET_KEY for testing
    app = create_app(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test_secret"}
    )
    with app.test_client() as client:
        yield client


def test_security_headers(client):
    """Test that security headers are present in the response."""
    response = client.get("/")
    headers = response.headers

    # Content-Security-Policy
    assert "Content-Security-Policy" in headers
    csp = headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp

    # X-Content-Type-Options
    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"

    # X-Frame-Options
    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "SAMEORIGIN"

    # Referrer-Policy
    assert "Referrer-Policy" in headers
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
