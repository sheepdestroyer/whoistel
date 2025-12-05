import sqlite3
import logging
from contextlib import closing
from functools import wraps

def with_db_connection(func):
    """Decorator to manage DB connection if not provided."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = kwargs.get('conn')
        if conn:
            return func(*args, **kwargs)
        else:
            with closing(get_db_connection()) as new_conn:
                kwargs['conn'] = new_conn
                return func(*args, **kwargs)
    return wrapper

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

@with_db_connection
def add_report(phone_number, report_date, is_spam, comment, conn=None):
    c = conn.cursor()
    c.execute('''
        INSERT INTO reports (phone_number, report_date, is_spam, comment)
        VALUES (?, ?, ?, ?)
    ''', (phone_number, report_date, 1 if is_spam else 0, comment))
    conn.commit()

@with_db_connection
def get_spam_count(phone_number, conn=None):
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM reports
        WHERE phone_number = ? AND is_spam = 1
    ''', (phone_number,))
    count = c.fetchone()[0]
    return count

@with_db_connection
def get_recent_reports(limit=50, conn=None):
    c = conn.cursor()
    c.execute('''
        SELECT * FROM reports
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    return [dict(row) for row in rows]
