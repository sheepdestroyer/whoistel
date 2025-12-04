# TODO for whoistel Project

This file tracks tasks for the `whoistel` project.

## Completed
*   [x] **Refactor Data Ingestion (`generatedb.py`)**:
    *   [x] Switched to `pandas` for robust CSV handling (fixing encoding issues).
    *   [x] Implemented schema for `PlagesNumerosGeographiques` (Geo) and `PlagesNumeros` (Mobile/Special).
    *   [x] Imported Operators and Communes.
*   [x] **Refactor CLI (`whoistel.py`)**:
    *   [x] Cleaned up code, removed obsolete API calls.
    *   [x] Implemented "Longest Prefix Match" logic for accurate lookups.
    *   [x] Improved output format and error handling.
    *   [x] Added support for `+33` format.
*   [x] **Testing & Validation**:
    *   [x] Verified with `+33424288224` (Success: Found Operator and Region).
    *   [x] Verified with `+33740756315` (Handled: Correctly reports unknown due to missing data).
    *   [x] Updated `tests/test_whoistel.py` to match new behavior.
*   [x] **Documentation**:
    *   [x] Created `DATA_SOURCES.md`.
    *   [x] Researched availability of Subscriber (Reverse Directory) and Spam data sources.
*   [x] **Data Source Update**:
    *   [x] Replaced `galichon.com` with official "Communes de France - Base des codes postaux" (Enriched La Poste data) from `data.gouv.fr`.
    *   [x] Enriched `Communes` table with Latitude, Longitude, and Department Name.
    *   [x] Updated `whoistel.py` to display GPS coordinates if available.

## Known Issues / Future Work
*   **Missing Data:** The range `0740` (and potentially others) is missing from the ARCEP `MAJNUM.csv` file. This causes lookups for numbers like `+33740756315` to return "Unknown".
*   **Precise Location:** The mapping from Phone Prefix (EZABPQM) to specific ZNE/CodeInsee is missing in open data.
    *   `PlagesNumerosGeographiques` has `CodeInsee` set to '0'.
    *   Although the `Communes` table is now rich (with GPS), the link from phone number to commune is broken.
*   **ZNE Mapping:** Need to find a source mapping `EZABPQM` -> `ZNE` -> `Commune` to enable precise location lookups.

## Research Findings (Integration Blocked)
*   **Reverse Directory (Annuaire Inversé):** No Open Data source exists due to GDPR. Commercial APIs only.
*   **Spam Detection:** No free Open Data API exists. Requires commercial/community API keys.
*   **Business Reverse Lookup:** Sirene API (Open Data) does not support reliable reverse lookup by phone number.
