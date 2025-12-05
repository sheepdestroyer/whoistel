# GitHub CLI Review Cycle & Troubleshooting

## Learned Lessons: Fetching Comments
During the implementation of the `whoistel` web UI, we encountered issues reliably fetching code review comments using the `gh` CLI. Here is what we learned:

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
*   Address the specific feedback.
*   Run tests (`pytest`) to verify fixes.

### 6. Push & Repeat
```bash
git add .
git commit -m "Address Cycle X comments"
git push
```
Return to Step 1.
