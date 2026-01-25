import os
import tempfile

import pytest

import history_manager
from webapp import create_app


@pytest.fixture
def app_instance(monkeypatch):
    """Fixture that creates a Flask app instance with a temporary history database."""
    # Create a temporary database for history
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setattr(history_manager, "DB_FILE", db_path)

    app = create_app(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test-key"}
    )

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
    response = client.get("/")
    assert response.status_code == 200

    headers = response.headers

    # Content-Security-Policy
    assert "Content-Security-Policy" in headers
    csp = headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    # We check for the directives we plan to add
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp

    # X-Content-Type-Options
    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"

    # X-Frame-Options
    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "DENY"

    # Referrer-Policy
    assert "Referrer-Policy" in headers
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
