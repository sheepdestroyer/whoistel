## 2025-10-26 - [Flask Security Headers & CSP]
**Vulnerability:** Missing HTTP security headers (CSP, HSTS, X-Frame-Options, etc.) in Flask application.
**Learning:** Default Flask configurations do not include security headers. Adding a strict `default-src 'self'` CSP can break applications that rely on inline styles/scripts or external resources, which is common in simple Flask apps or default error pages.
**Prevention:** Use an `after_request` hook to inject headers. Start with a relaxed CSP (`script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'`) if existing templates use inline code, then tighten iteratively.
