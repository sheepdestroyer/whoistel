## 2024-05-22 - Strict CSP Implementation
**Vulnerability:** Lack of Content-Security-Policy allowed potential XSS attacks.
**Learning:** Enforcing `default-src 'self'` provides strong protection but requires all resources (scripts, styles, images) to be served locally. This was validated against the template files which contain no inline scripts or styles.
**Prevention:** Always verify template assets before applying strict CSP. Future frontend changes must respect this constraint or update the policy intentionally.
