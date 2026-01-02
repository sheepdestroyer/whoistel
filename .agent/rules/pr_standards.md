# PR Review Standards & Rules

## 1. The Loop Rule
A Review Cycle is a **LOOP**, not a check.
*   **Definition**: A cycle is `Push -> Trigger -> Poll -> Analyze -> Fix -> REPEAT`.
*   **Exit Condition**: You may ONLY exit the loop when the reviewer explicitly states "Ready to Merge" or "No issues found".
*   **Prohibition**: Never stop after fixing issues without re-verifying with the bot.

## 2. Push Before Trigger
**STRICT RULE**: You MUST `git push` your changes BEFORE triggering a review.
*   Triggering a review on unpushed code results in outdated feedback and wastes API rate limits.
*   Always verify `git status` is clean and `git log` shows your commit before running `gh pr comment`.

## 3. Artifact Hygiene
*   **Test Artifacts**: All test output files (e.g., `pytest_output.txt`, `coverage.xml`) MUST be placed in `tests/artifacts/`.
*   **Root Directory**: Do NOT write temporary files, logs, or debug dumps to the repository root.
*   **Agent Workspace**: Use `agent-tools/agent-workspace/` for operational logs (e.g., `feedback.json`).

## 4. Polling & Wait Times
*   **Initial Wait**: Wait **at least 3 minutes** after requesting a review to allow bots to process.
*   **Poll Interval**: Check for feedback every **2 minutes**.
*   **Timeout**: Set a reasonable timeout (e.g., 15-25 minutes) to avoid infinite loops, but do not give up early.

## 5. Tool Usage
*   **Primary Tool**: Use `agent-tools/pr_helper.py` for triggering and monitoring.
*   **Fallback**: Use `gh` CLI directly if the helper encounters issues.
*   **Path Safety**: Ensure all file paths passed to tools are validated to be within the project root.

## 6. Bot Etiquette
*   **Gemini Code Assist**: Use `/gemini review` for general code review.
*   **CodeRabbit**: Use `@coderabbitai review` for deep static analysis and logical bugs.
*   **Sourcery**: Use `@sourcery-ai review` for Pythonic refactoring suggestions.
*   **Respect**: Address all actionable feedback. If a bot suggests a fix that is wrong, explain why in a comment or ignore it if trivial, but prefer to address it if possible.

## 7. CLI Pagination
*   **Mandatory Flag**: When using `gh api` to fetch comments or reviews, YOU MUST ALWAYS use `--paginate`.
    *   *Reason*: Large PRs often exceed the default page size (30 items). Without `--paginate`, validation cycles may miss critical feedback or approval states.
