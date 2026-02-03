## 2025-02-18 - Flask Security Headers
**Vulnerability:** The Flask application was missing standard security headers (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`), making it potentially vulnerable to XSS, clickjacking, and MIME sniffing attacks.
**Learning:** Flask does not enforce these headers by default. While extensions like `Flask-Talisman` exist, they add dependencies. A simple `after_request` hook is an effective, lightweight way to enforce these headers for simple applications.
**Prevention:** Always verify security headers are present. For Flask, use an `after_request` hook or a dedicated library to inject them into every response.
