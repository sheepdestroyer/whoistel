# whoistel: Whois for French Telephone Numbers

`whoistel` is a command-line tool to look up information about French telephone numbers. This project has been updated from its original 2013 Python 2 version to Python 3 and uses current data sources.

## Features

*   Fetches information from locally-built databases derived from official ARCEP and INSEE data.
*   Provides operator and (for geographic numbers) location information.
*   Identifies number types (geographic, mobile, special, etc.).
*   Includes basic information on surcharges for certain numbers (note: this information might be less current than number assignments).

## Data Sources

The program primarily uses the following information sources, converted to an SQLite database (`whoistel.sqlite3`) by the included scripts:

*   **ARCEP Data:**
    *   **Via data.gouv.fr (CSV):**
        *   `majournums.csv`: Contains number ranges (including `EZABPQM`), their allocation type (geographic, mobile, etc.), and operator mnemonics. This is the primary source for number-to-operator mapping.
        *   `identifiants_ce.csv`: Provides details about operators (e.g., full name for a given operator mnemonic).
    *   **Via arcep.fr (XLS, converted to CSV):**
        *   `liste-zne.xls`: Provides mappings between communes and ZNE (Zone de Numérotation Elémentaire). Specifically, the "Correspondance Communes-ZNE" sheet is used.
        *   `correspondance-zab-departements.xls`: Provides mappings between ZAB (Zone d'Appel de Base) prefixes and departments.
*   **INSEE Data:**
    *   `insee.csv` (originally from `insee.zip` from galichon.com): Links INSEE codes (city codes) to city names, postal codes, and departments. Used for geographic number localization.

The Annu.com and OVH Telecom API integrations from the original version have been removed as they are defunct or no longer suitable.

## Database Schema Highlights

The `generatedb.py` script creates several tables, including:
*   `PlagesNumeros`: Stores number ranges and associated operator/type information from `majournums.csv`.
*   `Operateurs`: Stores operator details from `identifiants_ce.csv`.
*   `Communes`: Stores city/postal code/department information from `insee.csv`.
*   `CommunesZNE`: Stores mappings between ZNEs and commune INSEE codes, derived from `liste-zne.xls`. `CodeINSEECommune` is stored as TEXT to accommodate alphanumeric Corsican codes.
*   `ZABDepartement`: Stores mappings between ZAB prefixes and department numbers, derived from `correspondance-zab-departements.xls`.

## Setup and Usage

### Prerequisites

*   Python 3
*   Python libraries: `pandas`, `openpyxl`, `xlrd`
*   Standard Unix utilities (`bash`, `wget`, `unzip`) for fetching data.
*   `pytest` for running tests (optional, for development).

### 1. Get the Code

Clone the repository or download the source files.

### 2. Install Dependencies (if not already present)
```bash
pip install pandas openpyxl xlrd
```

### 3. Prepare Data and Database

Before the first use, and periodically to update the data, make the `updatearcep.sh` script executable and then run it from the project's root directory:

```bash
chmod +x updatearcep.sh
./updatearcep.sh
```

This script will:
1.  Download the latest CSV data files from ARCEP (via data.gouv.fr) into the `arcep/` subdirectory.
2.  Download the `liste-zne.xls` and `correspondance-zab-departements.xls` files from arcep.fr into the `arcep/` subdirectory.
3.  Run the `xls_to_csv_converter.py` script (using `python3`) to convert the downloaded XLS files into multiple CSV files (one per sheet) within the `arcep/` directory. For example, `liste-zne.xls` will produce `arcep/liste-zne_Correspondance_Communes_ZNE.csv` among others.
4.  Run `generatedb.py` to process all relevant CSV files (both directly downloaded and converted) and create/update the `whoistel.sqlite3` database in the project root.

### 4. Run `whoistel.py`

Once the database is generated, you can query a number:

```bash
python3 whoistel.py <numéro_de_téléphone_français>
```

**Examples:**

```bash
python3 whoistel.py 0123456789
python3 whoistel.py +33612345678
python3 whoistel.py 0800000000
```

The script will output information about the number, including its type, the operator, and geographic details if applicable.

For the specific test number `+33740756315`, the script currently reports it as "Numéro inconnu dans la base ARCEP" due to data availability for its specific range and operator in the `majournums.csv` file.

### Command-line Arguments

*   `numero_tel`: (Positional) The French telephone number to look up.
*   `--no-annu`: (Obsolete and ignored)
*   `--no-ovh`: (Obsolete and ignored)

## Development & Testing

To run the tests, ensure `pytest` is installed (`pip install pytest`). Then, from the project root:

```bash
pytest
```
The tests include checks for geographic numbers, the specific test number `+33740756315` (expecting "Numéro inconnu" with current data), and invalid number formats. The test suite will attempt to run `updatearcep.sh` if the database is not found.

## Original TODOs (Status Update)

Many items from the original 2013 TODO list have been impacted by the migration to Python 3 and the change in data sources:

*   Use [this database](http://www.arcep.fr/fileadmin/reprise/dossiers/numero/liste-zne.xls) to show all cities composing a ZNE: *The `liste-zne.xls` source is obsolete. ZNE to commune mapping is currently omitted and would require finding a new, compatible data source.*
*   Maybe add a backend for a [website](http://www.annuaire-inverse-france.com/) allowing to access the data of the [G'NUM database](http://www.arcep.fr/index.php?id=8765): *Out of scope for the current CLI focus.*
*   Create a database about the surcharge of four-digits numbers: *Basic surcharge information for some number types is present in `whoistel.py` but relies on hardcoded logic from ~2013 and may be outdated. A structured, up-to-date data source for this would be needed.*
*   Choose a language for the script and the README between French, English, or Frenglish: *Currently mixed; primarily French in script output, English/French in documentation.*
*   Find a INSEE database that contains the name of cities with normal case: *The current `insee.csv` is used as-is.*
*   Build packages for various distributions: *Out of scope for current efforts.*

## Current Project Status & Known Issues

*   The project is functional in Python 3.
*   Data fetching and database generation are operational with current ARCEP CSV sources.
*   **Operator Lookup for some 07xxxx numbers:** The primary test number `+33740756315` is not found in the database. This is due to the data in `majournums.csv` not providing a direct `EZABPQM` prefix match that `generatedb.py` can currently use to associate this specific number with an operator. The general lookup mechanism works for numbers where such data exists.
*   **CodeInsee for Geographic Numbers:** Mapping for `CodeInsee` in the `PlagesNumerosGeographiques` table (used for localizing geographic numbers) currently uses a placeholder value of `0`. This is because the primary data source (`majournums.csv`) does not directly link geographic number ranges to ZNE chef-lieu INSEE codes, and the structure of other ARCEP files (like `liste-zne_Liste_des_ZNE.csv`) does not offer a straightforward mapping that has been implemented. The `CommunesZNE` table *does* link commune INSEE codes to ZNEs, but this is not yet used by `whoistel.py` for number lookup.
*   **ZNE to Commune Mapping:** While `generatedb.py` now populates a `CommunesZNE` table from `liste-zne.xls` (mapping ZNE numbers to commune INSEE codes), this information is not yet actively used by `whoistel.py` to, for example, list all communes within a ZNE for a given geographic number.
*   **Surtax Information:** Information on surcharges in `whoistel.py` is based on old logic and may not be accurate.
*   **Data Initialization:** The `arcep/` directory (containing downloaded and converted data) and `whoistel.sqlite3` (the database) are in `.gitignore`. The `updatearcep.sh` script is responsible for creating these if they are missing.

This version provides a functional CLI tool based on the latest available ARCEP data structure, with new tables for ZNE and ZAB information.
