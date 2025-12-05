import pytest
import os
import tempfile
import sqlite3
from webapp import app
import history_manager
import whoistel
from unittest.mock import patch

@pytest.fixture
def client():
    # Create a temporary database for history
    db_fd, db_path = tempfile.mkstemp()
    history_manager.DB_FILE = db_path
    history_manager.init_history_db()

    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-key'

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_index(client):
    rv = client.get('/')
    assert b'Rechercher un num' in rv.data

def test_check_number_redirect(client):
    rv = client.post('/check', data={'number': '0123456789'})
    assert rv.status_code == 302
    assert '/view/0123456789' in rv.location

def test_view_number_unknown(client):
    # Tests checking a number that likely doesn't exist or is generic
    rv = client.get('/view/0123456789')
    assert b'0123456789' in rv.data
    # Check if spam count is 0
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

def test_database_connection_error(client):
    with patch('whoistel.setup_db_connection') as mock_db:
        mock_db.side_effect = whoistel.DatabaseError("Connection failed")
        rv = client.get('/view/0123456789')
        assert rv.status_code == 500
        assert b'Database error occurred' in rv.data

def test_report_comment_truncation(client):
    """Tests that the comment field is truncated to 1024 characters."""
    long_comment = "a" * 2000
    with patch('history_manager.add_report') as mock_add_report:
        client.post('/report', data={
            'number': '0123456789',
            'comment': long_comment
        })
        # Check that add_report was called with a truncated comment
        args, _ = mock_add_report.call_args
        # args: (number, date, is_spam, comment)
        assert len(args[3]) == 1024
        assert args[3] == "a" * 1024

def test_csrf_protection(client):
    """Tests that CSRF protection is active."""
    # Note: The client fixture disables CSRF by default (WTF_CSRF_ENABLED=False).
    # We need to enable it for this specific test.
    app.config['WTF_CSRF_ENABLED'] = True
    
    # Try to post without a CSRF token
    rv = client.post('/report', data={
        'number': '0123456789',
        'is_spam': 'on'
    })
    
    # Should return 400 Bad Request (CSRF token missing)
    assert rv.status_code == 400
    
    # Reset config
    app.config['WTF_CSRF_ENABLED'] = False

