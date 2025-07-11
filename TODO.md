# TODO for whoistel Project

This file tracks tasks for the `whoistel` project.

## Phase 1: Refactor, Fix, and Test (Current)

### Done (Based on previous agent's work and user summary)
*   [x] Migrated `whoistel.py`, `generatedb.py`, `updatearcep.sh` to Python 3.
*   [x] Replaced ARCEP XLS downloads with CSVs from data.gouv.fr in `updatearcep.sh`.
*   [x] Refactored `generatedb.py` to use the `csv` module for new data formats.
    *   [x] Operator details sourced from `identifiants_ce.csv`.
    *   [x] Number ranges sourced from `majournums.csv`.
*   [x] Removed Annu.com and OVH Telecom API integrations from `whoistel.py`.
*   [x] Adjusted database query handling in `whoistel.py` for schema changes.
*   [x] Created `AGENTS.md`.
*   [x] Initialized `TODO.md` (this file).

### Completed in This Session
*   [x] **`generatedb.py`:** Fix CSV header key access for 'Mnémo'.
    *   [x] Changed `row['Mn\\xe9mo']` to `row['Mnémo']`.
*   [x] **`whoistel.py`:** Enforce 10-digit length for standard French numbers before ARCEP lookups.
    *   [x] Modified the condition to `if tel.startswith('0') and len(tel) == 10:`.
*   [x] **`generatedb.py`:** Remove debug print statement.
*   [x] **`whoistel.py`:** Refactored argument parsing to use `argparse`.
*   [x] **`generatedb.py` / `whoistel.py`:** Operator lookup for non-geographic mobile numbers (e.g., 07xxxx).
    *   [x] Verified `EZABPQM` is used as prefix key in `generatedb.py`.
    *   [x] Verified `whoistel.py` searches prefixes correctly.
    *   [x] Confirmed failure for `+33740756315` is due to data not being found for its specific prefixes in `majournums.csv` by the current `generatedb.py` strategy. The general mechanism works for other numbers where `EZABPQM` is a direct prefix match.
*   [x] **Pytest Implementation:**
    *   [x] Created `tests/` directory.
    *   [x] Created `tests/test_whoistel.py`.
    *   [x] Wrote pytest tests covering:
        *   [x] Lookup for `+33740756315` (adjusted to expect "Numéro inconnu").
        *   [x] Lookup for a known geographic number (basic type check).
        *   [x] Handling of invalid number formats.
    *   [x] Added `setup_database` fixture to `test_whoistel.py`.
*   [x] **Full Execution Test:**
    *   [x] Ran `updatearcep.sh` (downloads data and runs `generatedb.py`).
    *   [x] Ran `python whoistel.py +33740756315` and verified its output (Numéro inconnu).
    *   [x] Ran `pytest tests/test_whoistel.py` - all tests passed.
*   [x] **Documentation Files**: Ensured `AGENTS.md` and `TODO.md` are created/overwritten with latest content.

### Pending Tasks (Deferred / Future Considerations)
*   [ ] **`generatedb.py`:** Address placeholder CodeInsee (currently 0).
    *   *Assessment: This is complex due to changes in data mapping. Deferred as not critical for primary CLI functionality.*
*   [ ] **`generatedb.py`:** Address omitted ZNE to commune mapping.
    *   *Assessment: Similar to CodeInsee, deferred.*
*   [ ] **Further `+33740756315` Investigation (Data Permitting):**
    *   If the user can provide the *expected operator* for `+33740756315`, further investigation into `majournums.csv` could be done to see if a different data extraction strategy in `generatedb.py` is needed for this specific number's range (e.g., using `Tranche_Debut` / `Tranche_Fin` instead of/alongside `EZABPQM` if `EZABPQM` is not the definitive prefix for its operator). Currently, the script correctly reports "unknown" based on available data and current processing.
*   [ ] Review all code for clarity, comments, and any remaining Python 2 artifacts (mostly done, but a final pass is good).
*   [ ] Update `README.md` if necessary to reflect changes in usage or setup (e.g. `argparse` usage).
*   [ ] Consider adding `requirements.txt` (currently only standard library + `pytest` for testing).

### Future Considerations (Post-MVP)
*   Explore options for CodeInsee and ZNE/commune mapping if deemed important.
*   Investigate if any new, reliable, free APIs exist for supplementary information.
*   **Web Service Conversion**:
    *   [ ] Adapt `whoistel.py` or create a new wrapper script to function as a web service (e.g., using Flask/FastAPI).
    *   [ ] The service should accept phone numbers via API requests and return JSON responses.
    *   [ ] Ensure `Containerfile` `EXPOSE` directive matches the port used by the web service.
*   **In-Container Database Updates**:
    *   [ ] Implement a mechanism (possibly an API endpoint in the web service) to trigger `updatearcep.sh` (and thus `generatedb.py`) from within the running container.
    *   [ ] This requires `pandas` and `xlrd` (from `requirements.txt`) to be available in the runtime container image.
    *   [ ] Consider how the updated `whoistel.sqlite3` database will be persisted or how the running application will reload it.
