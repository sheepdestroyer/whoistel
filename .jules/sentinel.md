## 2026-01-22 - Missing Security Headers & CSP Constraints
**Vulnerability:** The Flask application lacked standard security headers (CSP, HSTS, X-Frame-Options, etc.), despite documentation/memory suggesting otherwise.
**Learning:** Legacy frontend templates rely heavily on inline scripts and styles, forcing the Content Security Policy (CSP) to permit `unsafe-inline`.
**Prevention:** Future frontend refactoring should move inline styles/scripts to separate files to allow tightening the CSP. Automated tests (like the one added) are essential to verify presence of headers that are assumed to exist.
