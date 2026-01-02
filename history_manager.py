"""
Management of the SQLite-based history database for storing and 
retrieving community spam reports.
"""
import sqlite3
import logging
import os
from contextlib import closing
from functools import wraps
import whoistel

def with_db_connection(func):
    """Decorator to manage DB connection if not provided."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'conn' in kwargs and kwargs.get('conn') is not None:
            return func(*args, **kwargs)
            
        with closing(get_db_connection()) as new_conn:
            new_kwargs = kwargs.copy()
            new_kwargs['conn'] = new_conn
            return func(*args, **new_kwargs)
    return wrapper

DB_FILE = os.environ.get('HISTORY_DB_FILE', 'data/history.sqlite3')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes and returns a connection to the SQLite history database."""
    try:
        db_dir = os.path.dirname(DB_FILE)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        msg = f"Erreur lors de la connexion à la base de données d'historique: {e}"
        logger.exception(msg)
        raise whoistel.DatabaseError(msg) from e
    else:
        return conn

def init_history_db():
    """Initializes the history database schema and indexes."""
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
        # Add a composite index for faster spam count lookups
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_reports_phone_number_spam ON reports (phone_number, is_spam);
        ''')
        conn.commit()

@with_db_connection
def add_report(phone_number, report_date, is_spam, comment, *, conn=None):
    """
    Adds a new spam report to the history database.
    
    Args:
        phone_number (str): The cleaned 10-digit phone number.
        report_date (str): Optional date of incident (AAAA-MM-JJ).
        is_spam (bool): Whether the report marks the number as spam.
        comment (str): Optional description.
        conn (sqlite3.Connection): Optional existing connection.
    """
    c = conn.cursor()
    c.execute('''
        INSERT INTO reports (phone_number, report_date, is_spam, comment)
        VALUES (?, ?, ?, ?)
    ''', (phone_number, report_date, 1 if is_spam else 0, comment))
    conn.commit()

@with_db_connection
def get_spam_count(phone_number, *, conn=None):
    """Returns the total number of spam reports for a given phone number."""
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM reports
        WHERE phone_number = ? AND is_spam = 1
    ''', (phone_number,))
    return c.fetchone()[0]

DEFAULT_RECENT_REPORTS_LIMIT = 50

@with_db_connection
def get_recent_reports(limit=DEFAULT_RECENT_REPORTS_LIMIT, *, conn=None):
    """
    Retrieves the most recent reports.
    """
    c = conn.cursor()
    c.execute('''
        SELECT * FROM reports
        ORDER BY created_at DESC, id DESC
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    return [dict(row) for row in rows]
