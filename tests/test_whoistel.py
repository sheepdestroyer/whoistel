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
    assert "Région Île-de-France" in result.stdout

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
    assert "Région Sud-Est" in result.stdout

def test_invalid_number_format_non_digit():
    """Tests handling of an invalidly formatted number."""
    number = "012345678A"
    result = run_whoistel_script(number)

    assert result.returncode == 1
    assert "Erreur: Le numéro doit contenir uniquement des chiffres" in result.stderr
