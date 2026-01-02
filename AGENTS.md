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
    *   **Never attempt to read data files directly (like `.csv` or `.xls`) within the main application logic and your tests.** These data files are large, converted if necessary and used during the database generation phase (`generatedb.py`), but not directly by `whoistel.py`. Only inspect them using `head` or `tail`.
5.  **Python Version:** The project targets Python 3. Ensure all code is Python 3 compatible.
6.  **Dependency Management:** If new dependencies are added, ensure they are documented (e.g., in a `requirements.txt` if appropriate).
7.  **Committing Code:**
    *   Use clear and descriptive commit messages.
    *   Ensure all tests pass before submitting.
    *   Ensure the script runs successfully with the primary test number.
8.  **Error Handling:** Implement robust error handling, especially for API calls and data parsing.
9.  **User Interaction:** The primary interface is command-line. Ensure output is clear and informative. Successful results should go to `stdout`, while logs, errors, and diagnostic information should go to `stderr`.
10. **Containerization**:
    *   Assist with the creation and debugging of the production-ready `Containerfile`.
    *   Provide instructions for building and running the container locally if requested.
    *   Note: Direct execution of `docker` or `podman` commands by the agent may be subject to environment limitations.

### Specific Known Issues (and areas to focus on if not yet resolved)
*   Operator lookup for non-geographic mobile numbers (e.g., 07xxxx) needs to be reliable. This may involve adjustments in `generatedb.py` regarding how `PlagesNumeros` is populated from `majournums.csv` (particularly the `EZABPQM` field) or how `whoistel.py` performs its search.
*   Ensure 10-digit number validation is correctly implemented in `whoistel.py` before attempting ARCEP lookups.
*   Address any encoding issues when reading data files (e.g., the 'Mnémo' vs 'Mn\\xe9mo' issue in `generatedb.py`).

By following these guidelines, we aim to create a robust and reliable version of the `whoistel` tool.


# GitHub PR Review Cycle
A PR Review Cycle triggers, fetches and addresses Code Reviews on GitHub's PR until there is nothing left to fix and the PR is Ready to Merge.

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
To successfully iterate with AI reviewers (Gemini, CodeRabbit, Sourcery) using the CLI:

### 1. Request Review
Trigger the bot to review your latest changes.
```bash
gh pr comment {PR_NUMBER} --body "/gemini review"
# Optional: Trigger CodeRabbit if needed
gh pr comment {PR_NUMBER} --body "@coderabbitai review"
```

### 2. Wait & Monitor (Non-Stop)
The Review Loop must **NOT** be interrupted unless:
1.  **Rate Limit**: We are explicitly in a rate-limited state (e.g., 429 error) and the recovery window has not expired.
2.  **Success**: The reviewer explicitly states "Ready to Merge" or "LGTM" with *no* actionable feedback.

**Action**:
-   **Poll**: Run the polling script immediately after requesting a review.
-   **Increments**: Wait in at least 2-minute increments.
-   **Do not stop** doing nothing. If you are not fixing, you are waiting. If you are not waiting, you are pushing.

### 3. Fetch Comments (Cleanly)
Use a **temporary directory** to avoid polluting the workspace.
```bash
WORK_DIR=$(mktemp -d)
gh pr view {PR_NUMBER} --json reviews --json comments > "$WORK_DIR/status.json"
```

### 4. Analyze & Filter (Agent Responsibility)
The Agent must parse the JSON to find comments created **after** the last push/fix cycle.
*   **Semantic Analysis**: Do not rely on scripts to tell you if it's "Ready". Read the comment body.
    *   Does it say "LGTM" but list 3 "Nitpicks"? -> **Fixes Needed**.
    *   Does it say "Changes Requested"? -> **Fixes Needed**.
    *   Does it say "No actionable comments"? -> **Ready**.
*   **Filter**: Ignore "outdated" or resolved comments if your logic handles them.

### 5. Implement & Verify
*   Address the specific feedback.
*   Run tests (`pytest`) to verify fixes.
*   **Cleanup**: Remove the temporary directory.

### 6. Push & Repeat
```bash
git add .
git commit -m "Address Cycle X comments"
git push
```
Return to Step 1.

## Post-Mortem: Repeated Review Request Failure (Cycle 26)

**Issue**: The agent failed to fetch new Code Review comments and instead repeatedly posted review requests ("gemini review"), triggering the daily quota limit.

### Cycle 7: Robustness & Cleanup
**Improvements:**
- **Container Persistence**: `history.sqlite3` is now correctly persisted in the `/app/data` volume using `HISTORY_DB_FILE`.
- **Review Cycle Robustness**: The review loop now handles timeouts and API rate limits gracefully, with scripts designed to be non-destructive.
- **Cleanliness**: Temporary files (`*_dump.json`, `*status*.json`) are explicitly ignored or cleaned up.
- **Testing**: Added CSRF protection tests for `/check` and refactored `history_manager` for clarity.

**Workflow Update:**
When running a review cycle:
1.  **Request**: Trigger reviews (`/gemini review`, `@coderabbitai review`).
2.  **Poll**: Use `agent-tools/poll_reviews.py` with a reasonable timeout.
3.  **Analyze**: Use `analyze_reviews.py` (or Agent's internal logic) to parse feedback.
4.  **Fix**: Implement changes.
5.  **Verify**: Run tests and check clean repo state.
6.  **Repeat**: Until "Ready to Merge".

**Root Cause**:
1.  **Improper Monitoring**: The agent relied on a polling script (`monitor_c26.py`) that likely wasn't capturing or outputting the review state correctly, or the agent failed to interpret the specific output conditions (e.g., distinguishing between a pending review and a lack of new reviews).
2.  **Blind Retries**: Instead of verifying the *absence* of a review definitively (by checking the raw comments list manually via `gh pr view --json comments`), the agent assumed the request hadn't triggered and re-sent the command `/gemini review`.
3.  **Lack of Backoff**: There was no exponential backoff or sufficient wait time between retry attempts.

**Corrective Actions**:
1.  **Exhaustive State Check**: Before requesting a new review, explicitly fetch and count existing comments and reviews. Only request a new review if:
    *   One hasn't been requested in the last X minutes.
    *   No new comments have appeared since the last request.
2.  **Use Raw Tools**: Do not rely solely on custom monitoring scripts which can mask errors. Use extensive `gh` CLI commands directly to verify state.
3.  **Respect Quotas**: Be mindful of the cost of each interaction and avoid tight loops of API calls.

**Resolution**: The agent manually fetched all comments, identified the missing feedback, and proceeded to address it without further superfluous review requests.
