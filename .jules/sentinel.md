## 2025-02-13 - Missing Security Headers vs Memory Contradiction
**Vulnerability:** The application was missing standard security headers (CSP, X-Frame-Options, etc.) despite internal documentation/memory stating they were enforced.
**Learning:** Documentation and memory can drift from the actual codebase state. "Trust but verify" applies to internal knowledge bases as much as user input.
**Prevention:** Always verify the existence of security controls in the code (e.g., via `grep` or reading files) before assuming they are present, regardless of what documentation says. Implement tests that fail if these controls are missing (Regression Testing).
