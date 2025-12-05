import sqlite3
import logging
from contextlib import closing

DB_FILE = 'history.sqlite3'
logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_history_db():
    logger.info(f"Initializing history database schema in {DB_FILE}...")

    with closing(get_db_connection()) as conn:
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
        conn.commit()

def add_report(phone_number, report_date, is_spam, comment):
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO reports (phone_number, report_date, is_spam, comment)
            VALUES (?, ?, ?, ?)
        ''', (phone_number, report_date, 1 if is_spam else 0, comment))
        conn.commit()

def get_spam_count(phone_number):
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT COUNT(*) FROM reports
            WHERE phone_number = ? AND is_spam = 1
        ''', (phone_number,))
        count = c.fetchone()[0]
        return count

def get_recent_reports(limit=50):
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT * FROM reports
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        rows = c.fetchall()
        # Convert rows to dicts
        return [dict(row) for row in rows]
