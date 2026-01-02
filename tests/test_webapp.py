import pytest
import os
import tempfile
from webapp import create_app, MAX_COMMENT_LENGTH
import history_manager
import whoistel
from unittest.mock import patch
from datetime import datetime

@pytest.fixture
def app_instance(monkeypatch):
    """Fixture that creates a Flask app instance with a temporary history database."""
    # Create a temporary database for history
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setattr(history_manager, 'DB_FILE', db_path)
    # No need to call init_history_db here, create_app does it within app_context

    app = create_app({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key'
    })

    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app_instance):
    """Fixture that provides a test client for the app."""
    with app_instance.test_client() as client:
        yield client

@pytest.fixture
def client_with_csrf(app_instance):
    """Fixture that enables CSRF protection for specific tests."""
    app_instance.config['WTF_CSRF_ENABLED'] = True
    with app_instance.test_client() as client:
        yield client
    app_instance.config['WTF_CSRF_ENABLED'] = False

def test_index(client):
    rv = client.get('/')
    assert b'Rechercher un num' in rv.data

def test_check_number_redirect(client):
    rv = client.post('/check', data={'number': '0123456789'})
    assert rv.status_code == 302
    assert '/view/0123456789' in rv.location

def test_check_number_missing_number_validation_error(client):
    rv = client.post('/check', data={'number': ''}, follow_redirects=True)
    # Should flash that a number is required and redirect back to the index
    assert b'Veuillez saisir un num' in rv.data
    assert b'Rechercher un num' in rv.data

def test_check_number_invalid_number_validation_error(client):
    rv = client.post('/check', data={'number': 'abcd'}, follow_redirects=True)
    # Should flash an invalid-characters error and redirect back to the index
    assert b'est invalide' in rv.data
    assert b'Rechercher un num' in rv.data

def test_view_number_unknown(client):
    # Tests checking a number that likely doesn't exist or is generic
    rv = client.get('/view/0123456789')
    assert b'0123456789' in rv.data
    # Check if spam count is 0 - using the literal bytes from the template
    assert b'signal\xc3\xa9 comme spam <strong>0</strong> fois' in rv.data

def test_report_flow(client):
    # 1. Report a number as spam
    rv = client.post('/report', data={
        'number': '0987654321',
        'date': '2023-01-01',
        'is_spam': 'on',
        'comment': 'Test Spam'
    }, follow_redirects=True)

    assert rv.status_code == 200
    # Should see the updated count in the result page (since it redirects to view)
    assert b'signal\xc3\xa9 comme spam <strong>1</strong> fois' in rv.data

    # 2. Check History
    rv = client.get('/history')
    assert b'0987654321' in rv.data
    assert b'Test Spam' in rv.data
    assert b'OUI' in rv.data

def test_report_non_spam_flow(client):
    # 1. Report a number as non-spam (is_spam unchecked)
    rv = client.post('/report', data={
        'number': '0123987654',
        'date': '2023-02-01',
        'comment': 'Test Non-Spam'
    }, follow_redirects=True)

    assert rv.status_code == 200
    # Since it's a non-spam report, the spam count for this number should remain 0
    assert b'signal\xc3\xa9 comme spam <strong>0</strong> fois' in rv.data

    # 2. Check History: the report should appear as NON (not spam)
    rv = client.get('/history')
    assert b'0123987654' in rv.data
    assert b'Test Non-Spam' in rv.data
    assert b'NON' in rv.data

def test_report_invalid_date_format_shows_error_and_redirects_to_view(client):
    rv = client.post('/report', data={
        'number': '0987654321',
        'date': '2023-13-40',
        'is_spam': 'on',
        'comment': 'Test Invalid Date'
    }, follow_redirects=False)
    assert rv.status_code == 302
    assert '/view/0987654321' in rv.location

    # Follow the redirect to ensure the flashed error message is rendered
    rv = client.get(rv.location)
    assert b'est invalide' in rv.data

def test_check_known_missing_number(client):
    # The number mentioned in AGENTS.md that is missing from ARCEP data
    # +33740756315 -> 0740756315
    rv = client.get('/view/0740756315')
    assert b'Num\xc3\xa9ro inconnu dans la base ARCEP' in rv.data

def test_view_number_redirect_dirty(client):
    # /view/01.02... should redirect to /view/0102...
    rv = client.get('/view/01.02.03.04.05')
    assert rv.status_code == 302
    assert '/view/0102030405' in rv.location

def test_report_empty_date(client):
    rv = client.post('/report', data={
        'number': '0987654321',
        'date': '',
        'is_spam': 'on',
        'comment': 'Test Empty Date'
    }, follow_redirects=True)
    assert rv.status_code == 200
    rv = client.get('/history')
    assert b'Test Empty Date' in rv.data

def test_view_invalid_number_format_returns_400(client):
    # A completely non-numeric number should be rejected and return 400
    rv = client.get('/view/abcd')
    assert rv.status_code == 400

def test_report_validation_error_requires_at_least_one_field(client):
    rv = client.post('/report', data={
        'number': '0123456789',
        'is_spam': '',
        'comment': '',
        'date': '',
    }, follow_redirects=True)

    # Should redirect back to the view page for that number
    assert b'0123456789' in rv.data
    # Should flash an error about needing at least spam/comment/date
    assert b'cocher la case spam' in rv.data

def test_database_connection_error(client):
    with patch('whoistel.setup_db_connection') as mock_db:
        mock_db.side_effect = whoistel.DatabaseError("Connection failed")
        rv = client.get('/view/0123456789')
        assert rv.status_code == 500
        assert b'Database error occurred' in rv.data

def test_report_comment_truncation(client):
    """Tests that the comment field is truncated to 1024 characters."""
    long_comment = "a" * (MAX_COMMENT_LENGTH + 1000) # Ensure it's longer than MAX_COMMENT_LENGTH
    with patch('history_manager.add_report') as mock_add_report:
        client.post('/report', data={
            'number': '0123456789',
            'date': '2023-01-01',
            'comment': long_comment
        })
        
        args, _ = mock_add_report.call_args
        # Check comment was truncated
        assert len(args[3]) == MAX_COMMENT_LENGTH
        assert args[3] == "a" * MAX_COMMENT_LENGTH


def test_csrf_protection(client_with_csrf):
    """Tests that CSRF protection is active."""
    # The fixture client_with_csrf enables CSRF.
    
    # Try to post without a CSRF token to /report
    rv = client_with_csrf.post('/report', data={
        'number': '0123456789',
        'is_spam': 'on'
    })
    # Should return 400 Bad Request (CSRF token missing)
    assert rv.status_code == 400

    # Try to post without a CSRF token to /check
    rv = client_with_csrf.post('/check', data={
        'number': '0123456789'
    })
    # Should return 400 Bad Request (CSRF token missing)
    assert rv.status_code == 400


def test_format_datetime_filter(app_instance):
    """Test the format_datetime utility function directly."""
    # Filters are registered on the app, but we can't easily call them outside context
    # unless we use the function directly. In our case, it's defined inside create_app.
    # To test it, we can use app.jinja_env.filters['format_datetime']
    
    f = app_instance.jinja_env.filters['format_datetime']
    
    # Test with datetime object
    dt = datetime(2023, 1, 1, 12, 34, 56)
    assert f(dt) == "01/01/2023 12:34"
    
    # Test with valid strings
    assert f("2023-01-01 12:34:56") == "01/01/2023 12:34"
    assert f("2023-01-01") == "01/01/2023 00:00"
    
    # Test with None or empty
    assert f(None) == ""
    assert f("") == ""
    
    # Test with invalid string
    assert f("invalid-date") == ""

def test_report_html_comment_escaped_in_history(client):
    """Ensure submitted HTML comments are escaped in the history view."""
    # 1. Report a number with an HTML comment
    html_comment = '<script>alert(1)</script>'
    rv = client.post(
        '/report',
        data={
            'number': '0678901234',
            'date': '2023-03-01',
            'is_spam': 'on',
            'comment': html_comment,
        },
        follow_redirects=True,
    )

    assert rv.status_code == 200

    # 2. Check History: raw HTML must not appear, escaped HTML must appear
    rv = client.get('/history')
    assert b'0678901234' in rv.data
    # Ensure raw HTML is not rendered
    assert b'<script>alert(1)</script>' not in rv.data
    # Ensure the comment is HTML-escaped in the rendered page
    # Jinja2 auto-escaping converts < to &lt;, > to &gt;
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in rv.data
