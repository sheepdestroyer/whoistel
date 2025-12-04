import pytest
import os
import subprocess

def get_project_root():
    """Returns the root directory of the project."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Ensures the database is generated before tests run.
    """
    root_dir = get_project_root()
    update_script_path = os.path.join(root_dir, "updatearcep.sh")
    db_path = os.path.join(root_dir, "whoistel.sqlite3")

    if not os.path.exists(db_path):
        print("\nDatabase not found. Running updatearcep.sh to generate it...")
        # Check if we can run it (permissions)
        subprocess.run(["chmod", "+x", update_script_path], check=True, cwd=root_dir)
        try:
            subprocess.run(
                ["./updatearcep.sh"], # Executing directly since we chmodded it
                capture_output=True, text=True, check=True, cwd=root_dir
            )
        except subprocess.CalledProcessError as e:
            # Print stderr for debugging
            print(f"Update Script Output: {e.stdout}")
            print(f"Update Script Error: {e.stderr}")
            pytest.fail(f"Database generation failed: {e.stderr}")
