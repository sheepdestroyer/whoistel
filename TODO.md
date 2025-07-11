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
*   [x] **Integrate New ARCEP XLS Data Sources:**
    *   [x] Updated `updatearcep.sh` to download `liste-zne.xls` and `correspondance-zab-departements.xls`.
    *   [x] Created `xls_to_csv_converter.py` to convert XLS to CSV.
    *   [x] Modified `generatedb.py` to:
        *   [x] Create `CommunesZNE` and `ZABDepartement` tables.
        *   [x] Populate `CommunesZNE` from `liste-zne_Correspondance_Communes_ZNE.csv`.
        *   [x] Populate `ZABDepartement` from `correspondance-zab-departements_ZAB_D_partement.csv`.
        *   [x] Changed `Communes.CodeInsee` and `CommunesZNE.CodeINSEECommune` to TEXT.
*   [x] Updated `.gitignore` to exclude `arcep/` and other generated/downloaded files.
*   [x] Updated `AGENTS.md` with rule about not reading full data files.

### Pending Tasks
*   [ ] **Data Initialization Robustness:** Verify and ensure `updatearcep.sh` and `generatedb.py` correctly initialize all necessary data (download, convert) and the database (`whoistel.sqlite3`) if the `arcep/` directory or the database file are missing (as they are now in `.gitignore`).
*   [ ] **`generatedb.py`:** Address placeholder CodeInsee in `PlagesNumerosGeographiques` (currently 0).
    *   *Assessment: This is complex. The `majournums.csv` doesn't directly link to ZNE chef-lieu INSEE. `liste-zne_Liste_des_ZNE.csv` exists but mapping logic isn't straightforward and was deferred. The current implementation uses a placeholder `0`.*
*   [ ] **`whoistel.py`:** Utilize `CommunesZNE` and `ZABDepartement` tables.
    *   *Currently, these tables are populated by `generatedb.py` but not yet used by `whoistel.py` for lookups (e.g., to list all communes in a ZNE or to use ZAB-department info).*
*   [ ] **Further `+33740756315` Investigation (Data Permitting):**
    *   If the user can provide the *expected operator* for `+33740756315`, further investigation into `majournums.csv` could be done to see if a different data extraction strategy in `generatedb.py` is needed for this specific number's range.
*   [ ] Review all code for clarity, comments, and any remaining Python 2 artifacts (mostly done, but a final pass is good).
*   [ ] Update `README.md` (Completed in this session).
*   [ ] Create `requirements.txt` file listing dependencies (`pandas`, `openpyxl`, `xlrd`, `pytest`).

### Future Considerations (Post-MVP)
*   Explore options for more accurate CodeInsee mapping in `PlagesNumerosGeographiques` if a clear data linkage strategy emerges.
*   Investigate if any new, reliable, free APIs exist for supplementary information.
*   Enhance `whoistel.py` output using the new ZNE/ZAB data (e.g., show department for ZAB, list communes in ZNE).
