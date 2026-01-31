## 2026-01-31 - Flask Security Headers
**Vulnerability:** Missing standard HTTP security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
**Learning:** Flask web applications require explicit configuration for security headers. While `flask-talisman` is robust, a simple `after_request` hook is sufficient for basic protection without new dependencies.
**Prevention:** Implement an `after_request` hook in the application factory to enforce these headers globally and verify with a dedicated test.
