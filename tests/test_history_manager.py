import pytest
import sqlite3
import history_manager
import os
from contextlib import closing

# Use a separate test DB file for history manager tests to adhere to isolation
TEST_HISTORY_DB = 'test_history_manager.sqlite3'

@pytest.fixture
def history_db_connection(tmp_path):
    """Provides a connection to a temporary history database."""
    db_path = tmp_path / TEST_HISTORY_DB
    
    # Initialize schema
    conn = sqlite3.connect(db_path)
    if hasattr(history_manager, "init_history_db"):
        # We need to monkeypatch DB_FILE or pass conn if possible.
        # history_manager.init_history_db uses get_db_connection() which uses DB_FILE.
        # But our history_manager functions accept a 'conn' argument.
        # Let's create the schema manually or assume init_history_db can be bypassed 
        # if we provide the connection with schema.
        
        # Actually simplest is to run the init logic on this conn directly.
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                report_date DATE,
                is_spam INTEGER DEFAULT 0,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_reports_phone_number_spam ON reports (phone_number, is_spam);
        ''')
        conn.commit()

    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

def test_history_manager_add_report_and_get_spam_count_with_conn(history_db_connection):
    """Directly test add_report + get_spam_count using an explicit SQLite connection."""
    conn = history_db_connection
    number = "0123456789"
    date = "2023-03-01"

    # Initially, count should be 0
    initial_count = history_manager.get_spam_count(number, conn=conn)
    assert initial_count == 0

    # Add a spam report
    history_manager.add_report(
        phone_number=number, # Changed from number to phone_number to match func sig
        report_date=date, # Changed from date to report_date
        is_spam=True,
        comment="First spam",
        conn=conn,
    )

    # Add a non-spam report (should not change spam count)
    history_manager.add_report(
        phone_number=number,
        report_date=date,
        is_spam=False,
        comment="Legit call",
        conn=conn,
    )

    # Spam count should now be 1
    spam_count = history_manager.get_spam_count(number, conn=conn)
    assert spam_count == 1

def test_history_manager_get_recent_reports_with_conn(history_db_connection):
    """Directly test get_recent_reports using an explicit SQLite connection."""
    conn = history_db_connection

    number_1 = "0987654321"
    number_2 = "0123987654"

    # Insert multiple reports
    history_manager.add_report(
        phone_number=number_1,
        report_date="2023-01-01",
        is_spam=True,
        comment="Spam 1",
        conn=conn,
    )
    history_manager.add_report(
        phone_number=number_2,
        report_date="2023-01-02",
        is_spam=False,
        comment="Not spam",
        conn=conn,
    )
    history_manager.add_report(
        phone_number=number_1,
        report_date="2023-01-03",
        is_spam=True,
        comment="Spam 2",
        conn=conn,
    )

    # Fetch recent reports and check ordering/contents
    recent = history_manager.get_recent_reports(limit=10, conn=conn)

    # We expect 3 entries total
    assert len(recent) == 3

    # reports are row objects
    numbers = [r["phone_number"] for r in recent]
    comments = [r["comment"] for r in recent]

    # Should contain both numbers
    assert number_1 in numbers
    assert number_2 in numbers

    # Should contain our comments
    assert "Spam 1" in comments
    assert "Spam 2" in comments
    assert "Not spam" in comments

    # get_recent_reports should be ordered by created_at DESC (default) or id DESC?
    # history_manager.get_recent_reports likely orders by ID DESC or created_at DESC.
    # The last inserted (Spam 2) should be first.
    latest = recent[0]
    assert latest["comment"] == "Spam 2"
    assert latest["phone_number"] == number_1
