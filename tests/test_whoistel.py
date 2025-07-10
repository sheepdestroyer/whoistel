import pytest
import subprocess
import os
import sqlite3

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

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Ensures the database is generated before tests run.
    This fixture will run once per module.
    """
    root_dir = get_project_root()
    update_script_path = os.path.join(root_dir, "updatearcep.sh")
    db_path = os.path.join(root_dir, "whoistel.sqlite3")

    # To avoid re-downloading/re-generating db for every test run if not necessary,
    # we can check if the db exists. A more robust check might involve checking its age.
    if not os.path.exists(db_path):
        print("\nDatabase not found. Running updatearcep.sh to generate it...")
        try:
            # Ensure updatearcep.sh is executable
            subprocess.run(["chmod", "+x", update_script_path], check=True, cwd=root_dir)
            # Run updatearcep.sh, which should also call generatedb.py
            process = subprocess.run(
                ["bash", update_script_path],
                capture_output=True, text=True, check=True, cwd=root_dir
            )
            print("updatearcep.sh output:")
            print(process.stdout)
            if process.stderr:
                print("updatearcep.sh errors:")
                print(process.stderr)
        except FileNotFoundError:
            pytest.skip("updatearcep.sh not found, cannot generate database.")
        except subprocess.CalledProcessError as e:
            print(f"Error running updatearcep.sh: {e}")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            pytest.fail("Database generation via updatearcep.sh failed.")

    if not os.path.exists(db_path):
         pytest.fail("Database whoistel.sqlite3 could not be generated.")


# --- Test Cases ---

def test_geographic_number_lookup():
    """
    Tests lookup for a known geographic number.
    This is a placeholder, a real geographic number and expected operator/location
    would be needed. For now, we check if it runs and identifies type.
    Example: Using a number for Orange in Paris (actual operator may vary based on DB).
    """
    number = "0140000000" # Example, may need adjustment
    result = run_whoistel_script(number)

    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    assert "Type : EZABPQMCDU (Numéro géographique ou mobile/VoIP)" in result.stdout
    # Add more specific assertions here once expected output is known
    # e.g. assert "Opérateur : ORANGE" in result.stdout
    # e.g. assert "Commune : PARIS" in result.stdout (if INSEE mapping is fixed)


def test_non_geographic_test_number_lookup():
    """
    Tests lookup for the specific non-geographic number +33740756315.
    """
    number = "+33740756315"
    result = run_whoistel_script(number)

    # It identifies the type, then prints error and exits with 1 as it's not found
    assert "Type : EZABPQMCDU (Numéro géographique ou mobile/VoIP)" in result.stdout
    assert "[Erreur] Numéro inconnu dans la base ARCEP." in result.stdout
    assert result.returncode == 1, f"Script should exit with 1 for unknown number. Stderr: {result.stderr}"


def test_invalid_number_format_too_short():
    """
    Tests handling of an invalidly formatted number (too short).
    """
    number = "0123"
    result = run_whoistel_script(number)

    # The script exits with 1 for errors, and prints error message to stdout
    assert result.returncode == 1, "Script should fail for invalid number."
    assert "Type de numéro non formellement identifié" in result.stdout or \
           "Numéro non reconnu ou format invalide pour recherche ARCEP" in result.stdout


def test_invalid_number_format_non_digit():
    """
    Tests handling of an invalidly formatted number (contains letters).
    """
    number = "012345678A"
    result = run_whoistel_script(number)

    assert result.returncode == 1, "Script should fail for non-digit number."
    assert "contient des caractères non numériques après nettoyage" in result.stdout

# More tests can be added:
# - Other types of special numbers (118xxx, 3xxx)
# - Numbers with different formatting (+33 (0)..., 0033...)
# - Edge cases for prefix lookups if known problematic ones exist

# Placeholder for checking the test number's operator directly from DB if needed
# def get_operator_from_db(cleaned_number_prefix):
#     root_dir = get_project_root()
#     db_path = os.path.join(root_dir, "whoistel.sqlite3")
#     if not os.path.exists(db_path):
#         return None
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#     cursor.execute("SELECT CodeOperateur FROM PlagesNumeros WHERE PlageTel=?", (cleaned_number_prefix,))
#     result = cursor.fetchone()
#     conn.close()
#     if result:
#         # This would then need another lookup in Operateurs table
#         return result[0]
#     return None

# To run tests:
# 1. Make sure `updatearcep.sh` has been run at least once to generate the database.
#    The fixture attempts this but might fail in some environments if not setup.
# 2. Install pytest: `pip install pytest`
# 3. Run pytest from the project root: `pytest`
#
# Note: The geographic number test currently uses a placeholder number and operator.
# This will need to be updated with a real example from the generated database.
# The non-geographic test for +33740756315 also needs its expected operator confirmed.
# For now, it primarily checks that *an* operator is found.
