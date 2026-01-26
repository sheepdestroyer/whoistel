## 2025-02-14 - Missing Security Headers in Flask App
**Vulnerability:** The Flask application lacked standard security headers (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`), leaving it vulnerable to XSS, clickjacking, and MIME sniffing attacks.
**Learning:** Even if `Flask-WTF` handles CSRF, other headers must be explicitly added. The `after_request` hook is a reliable place to enforce these globally.
**Prevention:** Always verify security headers using `curl -I` or a dedicated test case. Include an `after_request` hook in the application factory to enforce a secure default policy.
