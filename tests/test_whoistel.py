import pytest
import subprocess
import os
import sys

# Helper function to get the root directory of the project
def get_project_root():
    """Returns the root directory of the project."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Helper function to run whoistel.py script
def run_whoistel_script(number):
    """Runs the whoistel.py script with the given number and returns the output."""
    root_dir = get_project_root()
    script_path = os.path.join(root_dir, "whoistel.py")
    db_path = os.path.join(root_dir, "whoistel.sqlite3")

    if not os.path.exists(db_path):
        pytest.skip("whoistel.sqlite3 not found, skipping integration tests")

    process = subprocess.run(
        ["python3", script_path, number],
        capture_output=True,
        text=True,
        cwd=root_dir  # Ensure script runs from project root
    )
    return process

def test_geographic_number_lookup():
    """Tests lookup for a known geographic number."""
    number = "0140000000"
    result = run_whoistel_script(number)

    assert result.returncode == 0
    assert "Numéro : 0140000000" in result.stdout
    assert "Type détecté : Geographique" in result.stdout
    assert "Opérateur" in result.stdout
    assert "Orange" in result.stdout
    assert "Région : Île-de-France" in result.stdout

def test_non_geographic_test_number_lookup():
    """
    Tests lookup for the specific non-geographic number +33740756315.
    Known to be missing from ARCEP data, so expects Unknown result.
    """
    number = "+33740756315"
    result = run_whoistel_script(number)

    assert "Numéro : 0740756315" in result.stdout
    assert "Numéro inconnu dans la base ARCEP" in result.stdout
    assert result.returncode == 1

def test_valid_geo_number_lookup():
    """Tests lookup for the requested test number +33424288224."""
    number = "+33424288224"
    result = run_whoistel_script(number)

    assert result.returncode == 0
    assert "Numéro : 0424288224" in result.stdout
    assert "Type détecté : Geographique" in result.stdout
    assert "Kav El International" in result.stdout
    assert "Région : Sud-Est" in result.stdout

def test_invalid_number_format_non_digit():
    """Tests handling of an invalidly formatted number."""
    number = "012345678A"
    result = run_whoistel_script(number)

    assert result.returncode == 1
    assert "uniquement des chiffres après nettoyage" in result.stderr

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
