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
    return app_instance.test_client()


def test_security_headers_present(client):
    """Test that security headers are present in the response."""
    response = client.get("/")
    headers = response.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # CSP: Allow self and inline scripts/styles
    csp = headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "'unsafe-inline'" in csp
