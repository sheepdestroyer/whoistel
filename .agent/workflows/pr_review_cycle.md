---
description: Official workflow for managing PR Review Cycles with AI bots (Gemini, CodeRabbit, Sourcery).
---

1.  **Preparation & Verification**
    *   Ensure all local changes are committed.
    *   **CRITICAL**: Run tests locally (`pytest`) and capture output in `tests/artifacts/`.
    *   **CRITICAL**: `git push` changes to the remote branch. *Never trigger a review on unpushed code.*

2.  **Trigger Reviews**
    *   Use the helper script to trigger reviews:
    ```bash
    python3 agent-tools/pr_helper.py trigger {PR_NUMBER}
    # Or manually:
    # gh pr comment {PR_NUMBER} --body="/gemini review"
    # gh pr comment {PR_NUMBER} --body="@coderabbitai review"
    # gh pr comment {PR_NUMBER} --body="@sourcery-ai review"
    ```

3.  **Monitor & Poll**
    *   Wait at least **3 minutes** before the first check.
    *   Use the helper script to monitor for feedback:
    ```bash
    python3 agent-tools/pr_helper.py monitor {PR_NUMBER} --since {TIMESTAMP} --output "agent-tools/agent-workspace/feedback.json"
    ```
    *   // turbo
    *   Alternatively, use `gh` CLI to check status manually if the script fails.

4.  **Analyze Feedback**
    *   Review the JSON output or GitHub comments.
    *   **Filter**: Ignore outdated comments or comments on lines you've already fixed.
    *   **Actionable?**: If bots say "LGTM" or "Ready to Merge" with zero actionable issues, proceed to Step 6.
    *   **Issues?**: If issues are found, proceed to Step 5.

5.  **Implement Fixes (The Loop)**
    *   Apply fixes to the code.
    *   Verify locally (Step 1).
    *   Push changes.
    *   **GO TO STEP 2**. (Repeat the cycle).

6.  **Finalize**
    *   Ensure all bots explicitly approve.
    *   Confirm no new regressions.
    *   Notify user of "Ready to Merge" status.
