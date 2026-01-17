## 2026-01-17 - [Critical Missing Security Headers]
**Vulnerability:** The web application lacked standard security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy), making it vulnerable to XSS, Clickjacking, and MIME sniffing attacks.
**Learning:** Even simple Flask apps need explicit configuration for security headers; they are not default. Discrepancy between documentation/memory and code should always trigger a verification.
**Prevention:** Use an `after_request` hook or a library like `Talisman` to enforce headers globally.
