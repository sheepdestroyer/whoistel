## 2026-02-01 - Missing Security Headers vs Memory
**Vulnerability:** Application lacked standard security headers in `webapp.py`.
**Learning:** Memory stated these were implemented via an `after_request` hook, but the code was missing this hook. Documentation/memory can drift from code reality.
**Prevention:** Always verify security controls in the codebase, even if documented as present.
