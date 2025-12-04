# whoistel: Whois for French Telephone Numbers

`whoistel` is a command-line tool to look up information about French telephone numbers. This project has been updated from its original 2013 Python 2 version to Python 3 and uses current data sources.

## Features

*   Fetches information from locally-built databases derived from official ARCEP and INSEE data.
*   Provides operator and (for geographic numbers) location information.
*   Identifies number types (geographic, mobile, special, etc.).
*   Includes basic information on surcharges for certain numbers (note: this information might be less current than number assignments).

## Data Sources

The program primarily uses the following information sources, converted to an SQLite database (`whoistel.sqlite3`) by the included scripts:

*   **ARCEP Data (via data.gouv.fr):**
    *   `majournums.csv`: Contains number ranges (including `EZABPQM`), their allocation type (geographic, mobile, etc.), and operator mnemonics. This is the primary source for number-to-operator mapping.
    *   `identifiants_ce.csv`: Provides details about operators (e.g., full name for a given operator mnemonic).
*   **INSEE Data:**
    *   `insee.csv` (originally from `insee.zip` from galichon.com): Links INSEE codes (city codes) to city names, postal codes, and departments. Used for geographic number localization.

The Annu.com and OVH Telecom API integrations from the original version have been removed as they are defunct or no longer suitable.

## Setup and Usage

### Prerequisites

*   Python 3
*   Standard Unix utilities (`bash`, `wget`, `unzip`) for fetching data.
*   Python package installer `pip` or `pip3`.
*   Dependencies listed in `requirements.txt` (includes `pandas` for data processing and `pytest` for tests). These are installed automatically by `updatearcep.sh` or can be installed manually.

### 1. Get the Code

Clone the repository or download the source files.

### 2. Prepare Data and Database

Before the first use, and periodically to update the data, make the `updatearcep.sh` script executable and then run it from the project's root directory:

```bash
chmod +x updatearcep.sh
./updatearcep.sh
```

This script will:
1.  Attempt to install necessary Python dependencies from `requirements.txt` (e.g., `pandas`) if not run in an environment where this step is skipped (like during a Docker build where `SKIP_PIP_INSTALL_IN_CONTAINER=true` is set). For local/manual execution, ensure dependencies are installed.
2.  Download the latest CSV data files from ARCEP (via data.gouv.fr) and the INSEE data into the `arcep/` subdirectory.
3.  Run `generatedb.py` to process these CSV files and create/update the `whoistel.sqlite3` database in the project root.

**Important for local/manual use of `updatearcep.sh`**:
Ensure Python dependencies are installed before running, or allow the script to install them. You can install them manually via:
```bash
pip3 install -r requirements.txt
# or
# pip install -r requirements.txt
```

### 3. Run `whoistel.py`

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

## Web Application

The project includes a simple Web UI using Flask.

### Running Locally

To start the web application in development mode:

```bash
python3 webapp.py
```

The application will be available at `http://127.0.0.1:5000`.

### Production Deployment

**Warning:** Do not use `python3 webapp.py` (which uses `app.run()`) in a production environment. It is not designed for security or performance under load.

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 webapp:app
```

## Development & Testing

To run the tests, ensure `pytest` is installed. If you ran `./updatearcep.sh`, `pytest` (listed in `requirements.txt`) should already be installed. Otherwise, you can install it as part of all dependencies:
```bash
pip3 install -r requirements.txt
```
Or specifically:
```bash
pip3 install pytest
```
Then, from the project root:

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
*   **CodeInsee and ZNE Mapping:** Mapping for CodeInsee for geographic numbers (beyond a placeholder) and ZNE to commune mapping are currently not implemented due to complexities with the new data formats and lack of direct mappings in the primary CSVs. These are considered future enhancements if critical.
*   **Surtax Information:** Information on surcharges in `whoistel.py` is based on old logic and may not be accurate.

This version provides a functional CLI tool based on the latest available ARCEP data structure.
