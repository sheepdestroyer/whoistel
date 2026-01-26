## 2025-02-12 - Missing Security Headers in Flask App
**Vulnerability:** The Flask application was missing standard security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`).
**Learning:** Even though memory suggested these were implemented, they were absent from the actual code. Always verify implementation against the codebase, not just documentation or memory.
**Prevention:** Use an `after_request` hook or a library like `Flask-Talisman` (if dependencies allow) to enforce these headers globally. Added a manual `after_request` hook to fix this without new dependencies.
