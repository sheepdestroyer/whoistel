## 2025-02-14 - Missing Security Headers in Flask
**Vulnerability:** The Flask application was missing critical security headers (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`), leaving it vulnerable to XSS, clickjacking, and MIME sniffing.
**Learning:** Flask does not include these security headers by default. Developers must explicitly add them or use extensions like `Flask-Talisman` (though we used a manual hook here for simplicity/control).
**Prevention:** Always verify security headers in new Flask applications. Use `@app.after_request` or a dedicated library to enforce them globally. Test for their presence in integration tests.
