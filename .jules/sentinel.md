## 2024-05-22 - [HIGH] Missing Security Headers
**Vulnerability:** The Flask application lacked standard security headers (CSP, X-Frame-Options, etc.), leaving it vulnerable to clickjacking and other attacks.
**Learning:** Flask apps require explicit configuration for security headers, typically via `after_request` hooks or extensions like Flask-Talisman. Memory indicated they were present but code review proved otherwise.
**Prevention:** Verify security configurations in code rather than relying on documentation/memory. Use automated tests to assert header presence.
