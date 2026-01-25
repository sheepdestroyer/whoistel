## 2025-02-18 - Missing Security Headers vs Memory
**Vulnerability:** Missing standard HTTP security headers (CSP, HSTS, X-Frame-Options) in Flask application despite memory suggesting their presence.
**Learning:** Security controls documented in memory/documentation may drift from implementation or be aspirational.
**Prevention:** Always verify the existence of security controls in the actual code (e.g., `after_request` hooks) and write regression tests (like `test_security_headers.py`) to enforce them.
