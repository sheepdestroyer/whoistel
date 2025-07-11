## Agent Instructions for whoistel Project

This document provides guidelines and instructions for AI agents working on the `whoistel` project.

### Core Task
The primary goal is to have a working command-line tool (`whoistel.py`) that can check and provide information on French phone numbers.

### Development Process & Rules
1.  **Maintain `TODO.md`:** A `TODO.md` file must be kept in the root directory. All planned work, work in progress, and completed tasks related to the current set of objectives must be tracked in this file. Update it as tasks are identified, started, and completed.
2.  **Code Review & Updates:**
    *   Perform a full code review if requested or if starting a significant new piece of work.
    *   Ensure APIs and data sources are current. If an API is defunct, find an alternative or remove the functionality if an alternative isn't readily available.
    *   The primary data sources are CSV files from `data.gouv.fr` for ARCEP data.
3.  **Testing:**
    *   The phone number `+33740756315` must be used as a test case.
    *   The script must be runnable with this number by explicitly passing it as the main phone number argument (e.g., `python3 whoistel.py +33740756315`).
    *   Use `pytest -v` for validation. Write tests to cover core functionality, especially number lookups.
    *   Run the script with the test number before submitting changes.
4.  **Data Handling:**
    *   **Never attempt to read `.csv` or `.xls` files directly within the main application logic and your tests** These data files are large, converted if nececessary and used during the database generation phase (`generatedb.py`), but not directly by `whoistel.py`. Only inspect them using `head` or `tail`.
5.  **Python Version:** The project targets Python 3. Ensure all code is Python 3 compatible.
6.  **Dependency Management:** If new dependencies are added, ensure they are documented (e.g., in a `requirements.txt` if appropriate).
7.  **Committing Code:**
    *   Use clear and descriptive commit messages.
    *   Ensure all tests pass before submitting.
    *   Ensure the script runs successfully with the primary test number.
8.  **Error Handling:** Implement robust error handling, especially for API calls and data parsing.
9.  **User Interaction:** The primary interface is command-line. Ensure output is clear and informative. Successful results should go to `stdout`, while logs, errors, and diagnostic information should go to `stderr`.
10. **Containerization**:
    *   Assist with the creation and debugging of the `Containerfile`.
    *   Provide instructions for building and running the container locally if requested.
    *   Note: Direct execution of `docker` or `podman` commands by the agent may be subject to environment limitations.

### Specific Known Issues (and areas to focus on if not yet resolved)
*   Operator lookup for non-geographic mobile numbers (e.g., 07xxxx) needs to be reliable. This may involve adjustments in `generatedb.py` regarding how `PlagesNumeros` is populated from `majournums.csv` (particularly the `EZABPQM` field) or how `whoistel.py` performs its search.
*   Ensure 10-digit number validation is correctly implemented in `whoistel.py` before attempting ARCEP lookups.
*   Address any encoding issues when reading CSV files (e.g., the 'Mnémo' vs 'Mn\\xe9mo' issue in `generatedb.py`).

By following these guidelines, we aim to create a robust and reliable version of the `whoistel` tool.
