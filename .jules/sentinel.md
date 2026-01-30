## 2026-01-30 - Missing Security Headers
**Vulnerability:** The Flask application was missing critical security headers (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`), exposing users to XSS, clickjacking, and MIME sniffing attacks.
**Learning:** Flask does not include these headers by default. An `after_request` hook is the standard way to add them globally.
**Prevention:** Always verify security headers in new Flask applications. Added a regression test `tests/test_security_headers.py`.
