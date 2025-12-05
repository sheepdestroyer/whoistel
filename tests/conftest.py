import pytest
import os
import subprocess
import tempfile
import sqlite3
import whoistel

# Set SECRET_KEY for testing before any app import happens
os.environ['SECRET_KEY'] = 'test-key-for-conftest'

def get_project_root():
    """Returns the root directory of the project."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Creates a temporary database with sample data for tests, 
    avoiding external network dependency.
    """
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    
    # Initialize DB schema and sample data
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Tables matching those in generatedb.py
    c.execute('''
    CREATE TABLE PlagesNumerosGeographiques(
        PlageTel TEXT PRIMARY KEY,
        CodeOperateur TEXT,
        CodeInsee TEXT
    );
    ''')
    
    c.execute('''
    CREATE TABLE PlagesNumeros(
        PlageTel TEXT PRIMARY KEY,
        CodeOperateur TEXT
    );
    ''')
    
    c.execute('''
    CREATE TABLE Operateurs(
        CodeOperateur TEXT PRIMARY KEY,
        NomOperateur TEXT,
        TypeOperateur TEXT,
        MailOperateur TEXT,
        SiteOperateur TEXT
    );
    ''')
    
    c.execute('''
    CREATE TABLE Communes(
        CodeInsee TEXT PRIMARY KEY,
        NomCommune TEXT,
        CodePostal TEXT,
        NomDepartement TEXT,
        Latitude REAL,
        Longitude REAL
    );
    ''')
    
    # Sample Data
    # Geo Range: 0123... -> Op 1, Insee 75056 (Paris)
    c.execute("INSERT INTO PlagesNumerosGeographiques VALUES (?, ?, ?)", 
              ('01234', 'OP1', '75056'))
    
    # Non-Geo Range: 0987... -> Op 2
    c.execute("INSERT INTO PlagesNumeros VALUES (?, ?)", 
              ('09876', 'OP2'))
              
    # Operator
    c.execute("INSERT INTO Operateurs VALUES (?, ?, ?, ?, ?)", 
              ('OP1', 'Operator One', 'L1', 'contact@op1.fr', 'http://op1.fr'))
    c.execute("INSERT INTO Operateurs VALUES (?, ?, ?, ?, ?)", 
              ('OP2', 'Operator Two', 'L1', '', ''))
              
    # Commune
    c.execute("INSERT INTO Communes VALUES (?, ?, ?, ?, ?, ?)", 
              ('75056', 'Paris', '75000', 'Paris', 48.8566, 2.3522))
              
    conn.commit()
    conn.close()
    
    # Patch whoistel.DB_FILE to use our temp DB
    original_db_file = whoistel.DB_FILE
    whoistel.DB_FILE = db_path
    
    yield
    
    # Teardown
    whoistel.DB_FILE = original_db_file
    os.unlink(db_path)
