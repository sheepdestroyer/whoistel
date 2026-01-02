import pytest
import subprocess
import os
import sys

# Helper function to get the root directory of the project
def get_project_root():
    """Returns the root directory of the project."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Helper function to run whoistel.py main in-process
def run_whoistel_main(capsys, args_list, db_path=None):
    """Runs whoistel.main() with given args and optional DB patch."""
    from whoistel import main
    import whoistel
    from unittest.mock import patch
    
    # Patch sys.argv
    with patch('sys.argv', ['whoistel.py'] + args_list):
        # Patch DB_FILE if provided, otherwise use what's there (which is patched by conftest)
        # Note: conftest patches whoistel.DB_FILE for the session, 
        # but main() uses setup_db_connection which reads whoistel.DB_FILE.
        # So we just need to ensure standard flow works.
        try:
            main()
        except SystemExit as e:
            return e.code, capsys.readouterr()
        return 0, capsys.readouterr()

def test_geographic_number_lookup(capsys):
    """Tests lookup for a known geographic number."""
    # Use number from conftest setup ('01234...')
    number = "0123456789"
    ret, captured = run_whoistel_main(capsys, [number])

    assert ret == 0
    assert "Numéro : 0123456789" in captured.out
    assert "Type détecté : Geographique" in captured.out
    # conftest Operator is 'Operator One'
    assert "Operator One" in captured.out
    # conftest Region/City is 'Paris'
    assert "Paris" in captured.out

def test_non_geographic_test_number_lookup(capsys):
    """
    Tests lookup for a non-existent number.
    Fixture covers '09876...', so '07...' should be unknown.
    """
    number = "0740756315"
    ret, captured = run_whoistel_main(capsys, [number])

    assert "Numéro : 0740756315" in captured.out
    assert "Numéro inconnu dans la base ARCEP" in captured.out
    assert ret == 1

def test_valid_geo_number_lookup(capsys):
    """Tests lookup for another known valid number (same range)."""
    # Check another number in the '01234' range
    number = "0123400000"
    ret, captured = run_whoistel_main(capsys, [number])

    assert ret == 0
    assert "Numéro : 0123400000" in captured.out
    assert "Type détecté : Geographique" in captured.out
    assert "Operator One" in captured.out

def test_invalid_number_format_non_digit(capsys):
    """Tests handling of an invalidly formatted number."""
    number = "012345678A"
    ret, captured = run_whoistel_main(capsys, [number])

    assert ret == 1
    assert "invalide" in captured.err

def test_clean_phone_number():
    """Tests the phone number cleaning logic."""
    from whoistel import clean_phone_number
    # Formatted valid numbers
    assert clean_phone_number("01.02.03.04.05") == "0102030405"
    assert clean_phone_number("+33 1 02 03 04 05") == "0102030405"
    assert clean_phone_number("+33 (0) 6 12 34 56 78") == "0612345678"
    assert clean_phone_number("06-12-34-56-78") == "0612345678"
    assert clean_phone_number("06\t12 34\n56 78") == "0612345678"
    assert clean_phone_number("0033612345678") == "0612345678"
    
    # Falsy / missing inputs
    assert clean_phone_number("") == ""
    assert clean_phone_number(None) == ""

def test_is_valid_phone_format():
    """Tests the phone number validation helper."""
    from whoistel import is_valid_phone_format

    # Valid 10-digit strings
    assert is_valid_phone_format("0102030405") is True
    assert is_valid_phone_format("0612345678") is True

    # 9- and 11-digit strings should be rejected
    assert is_valid_phone_format("123456789") is False
    assert is_valid_phone_format("12345678901") is False

    # Empty / None inputs
    assert is_valid_phone_format("") is False
    assert is_valid_phone_format(None) is False

    # Non-digit characters should be rejected, even if upstream cleaning usually occurs
    assert is_valid_phone_format("0102AB0405") is False
    assert is_valid_phone_format("01 02 03 04 05") is False

def test_operator_info_validation():
    """Tests the email and URL validation logic in get_operator_info."""
    from whoistel import get_operator_info
    from unittest.mock import MagicMock

    # Mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Case 1: Valid email and URL
    # Return dict to simulate sqlite3.Row access by name
    mock_cursor.fetchone.return_value = {
        'NomOperateur': 'OpName', 
        'TypeOperateur': 'OpType', 
        'MailOperateur': 'contact@example.com', 
        'SiteOperateur': 'https://example.com'
    }
    result = get_operator_info(mock_conn, '1234')
    assert result['mail'] == 'contact@example.com'
    assert result['site'] == 'https://example.com'

    # Case 2: Invalid email
    mock_cursor.fetchone.return_value = {
        'NomOperateur': 'OpName', 
        'TypeOperateur': 'OpType', 
        'MailOperateur': 'invalid-email', 
        'SiteOperateur': 'https://example.com'
    }
    result = get_operator_info(mock_conn, '1234')
    assert result['mail'] is None
    assert result['site'] == 'https://example.com'

    # Case 3: Invalid URL (bad scheme)
    mock_cursor.fetchone.return_value = {
        'NomOperateur': 'OpName', 
        'TypeOperateur': 'OpType', 
        'MailOperateur': 'contact@example.com', 
        'SiteOperateur': 'ftp://example.com'
    }
    result = get_operator_info(mock_conn, '1234')
    assert result['mail'] == 'contact@example.com'
    assert result['site'] is None

    # Case 4: Invalid URL (no netloc)
    mock_cursor.fetchone.return_value = {
        'NomOperateur': 'OpName', 
        'TypeOperateur': 'OpType', 
        'MailOperateur': 'contact@example.com', 
        'SiteOperateur': 'http://'
    }
    result = get_operator_info(mock_conn, '1234')
    assert result['mail'] == 'contact@example.com'
    assert result['site'] is None

    # Case 5: No operator row found
    mock_cursor.fetchone.return_value = None
    result = get_operator_info(mock_conn, '9999')
    assert result is None
def test_get_full_info_known_and_unknown(db_connection):
    """Tests get_full_info using the DB fixture for known and unknown numbers."""
    from whoistel import get_full_info

    # Known geographic number (from conftest sample data: 01234...)
    known_number = "0123456789"
    known_result = get_full_info(db_connection, known_number)

    assert known_result["found"] is True
    assert known_result["type"] == "Geographique"
    assert known_result["operator"]["nom"] == "Operator One"
    assert known_result["location"]["commune"] == "Paris"

    # Unknown number
    unknown_number = "0799999999"
    unknown_result = get_full_info(db_connection, unknown_number)

    assert unknown_result["found"] is False
    assert "error" in unknown_result
    assert "inconnu" in unknown_result["error"]

def test_print_result_output(capsys):
    """Tests print_result presentation, including the 'Num\u00e9ro inconnu' branch."""
    from whoistel import print_result

    # Known number result dict
    known_result = {
        "found": True,
        "type": "Geographique",
        "operator": {"nom": "Operator One", "code": "OP1"},
        "location": {
            "region": "\u00cele-de-France",
            "commune": "Paris",
        },
        "number": "0123456789",
    }

    print_result(known_result)
    captured = capsys.readouterr()

    assert "0123456789" in captured.out
    assert "Geographique" in captured.out
    assert "Operator One" in captured.out
    assert "Paris" in captured.out
    assert "Num\u00e9ro inconnu" not in captured.out

    # Unknown number result dict
    unknown_result = {
        "found": False,
        "error": "Num\u00e9ro inconnu dans la base",
        "number": "0799999999",
    }

    print_result(unknown_result)
    captured = capsys.readouterr()

    assert "0799999999" in captured.out
    assert "Num\u00e9ro inconnu" in captured.out
    assert "Num\u00e9ro inconnu dans la base" in captured.out
