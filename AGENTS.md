## Agent Instructions for whoistel Project

This document provides guidelines and instructions for AI agents working on the `whoistel` project.

### Core Task
The primary goal is to have a working command-line tool (`whoistel.py`) that can check and provide information on French phone numbers.

### Development Process & Rules
1.  **Maintain `TODO.md`:** A `TODO.md` file must be kept in the root directory. All planned work, work in progress, and completed tasks related to the current set of objectives must be tracked in this file. Update it as tasks are identified, started, and completed.
2.  **Code Review & Updates:**
    *   Perform a full code review if requested or if starting a significant new piece of work.
    *   Ensure APIs and data sources are current. If an API is defunct, find an alternative or remove the functionality if an alternative isn't readily available.
    *   The primary data sources are from `data.gouv.fr` for ARCEP data.
3.  **Testing:**
    *   The phone number `+33740756315` must be used as a test case.
    *   The script must be runnable with this number by explicitly passing it as the main phone number argument (e.g., `python3 whoistel.py +33740756315`).
    *   Use `pytest -v` for validation. Write tests to cover core functionality, especially number lookups.
    *   Run the script with the test number before submitting changes.
4.  **Data Handling:**
    *   **Never attempt to read data files directly (like `.csv` or `.xls` ) within the main application logic and your tests** These data files are large, converted if nececessary and used during the database generation phase (`generatedb.py`), but not directly by `whoistel.py`. Only inspect them using `head` or `tail`.
5.  **Python Version:** The project targets Python 3. Ensure all code is Python 3 compatible.
6.  **Dependency Management:** If new dependencies are added, ensure they are documented (e.g., in a `requirements.txt` if appropriate).
7.  **Committing Code:**
    *   Use clear and descriptive commit messages.
    *   Ensure all tests pass before submitting.
    *   Ensure the script runs successfully with the primary test number.
8.  **Error Handling:** Implement robust error handling, especially for API calls and data parsing.
9.  **User Interaction:** The primary interface is command-line. Ensure output is clear and informative. Successful results should go to `stdout`, while logs, errors, and diagnostic information should go to `stderr`.
10. **Containerization**:
    *   Assist with the creation and debugging of the production ready `Containerfile`.
    *   Provide instructions for building and running the container locally if requested.
    *   Note: Direct execution of `docker` or `podman` commands by the agent may be subject to environment limitations.

### Specific Known Issues (and areas to focus on if not yet resolved)
*   Operator lookup for non-geographic mobile numbers (e.g., 07xxxx) needs to be reliable. This may involve adjustments in `generatedb.py` regarding how `PlagesNumeros` is populated from `majournums.csv` (particularly the `EZABPQM` field) or how `whoistel.py` performs its search.
*   Ensure 10-digit number validation is correctly implemented in `whoistel.py` before attempting ARCEP lookups.
*   Address any encoding issues when reading data files (e.g., the 'Mnémo' vs 'Mn\\xe9mo' issue in `generatedb.py`).

By following these guidelines, we aim to create a robust and reliable version of the `whoistel` tool.


# GitHub PR Review Cycle
A PR Review Cycle triggers, fetches and address Code Reviews on GitHub's PR until there is nothing left to fix and the PR is Ready to Merge.

## Learned Lessons: Fetching Comments
In order to initiate or restart a successful Code Review Cycle, here is what we learned:

1.  **Endpoint Distinction**:
    *   `gh pr view {N} --json comments`: Fetches **Issue Comments** (top-level discussion). It does **NOT** fetch inline code review comments (specific to lines of code).
    *   `gh api repos/{owner}/{repo}/pulls/{N}/comments`: Fetches **Review Comments** (inline feedback). This is the correct endpoint for code review feedback.

2.  **Pagination is Critical**:
    *   The GitHub API paginates results (default ~30 items).
    *   **Failure Mode**: Without pagination, we only retrieved the first page of comments (often the oldest ones). New feedback was missed because it fell on subsequent pages.
    *   **Solution**: Always use the `--paginate` flag with `gh api` to retrieve all comments.

## The Correct Review Cycle Workflow
To successfully iterate with Gemini Code Assist (or any reviewer) using the CLI:

### 1. Request Review
Trigger the bot to review your latest changes.
```bash
gh pr comment {PR_NUMBER} --body "/gemini review"
```

### 2. Wait
Allow time for the review to process (typically 3-5 minutes).

### 3. Fetch Comments (Correctly)
Use the API endpoint with pagination to ensure you get *everything*.
```bash
gh api repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}/comments --paginate > comments.json
```

### 4. Analyze & Filter
Parse the JSON to find comments created **after** your last push/fix cycle.
*   Filter by `created_at` timestamp.
*   Ignore "outdated" or resolved comments if your logic handles them.

### 5. Implement & Verify
*   Address the specific feedback (unless the review says that there is nothing left to fix and that the PR is ready to merge)
*   Run tests (`pytest`) to verify fixes.

### 6. Push & Repeat
```bash
git add .
git commit -m "Address Cycle X comments"
git push
```
Return to Step 1.
