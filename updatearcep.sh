#!/bin/sh
set -x

# Ensure Python dependencies are installed, unless skipped by environment variable
if [ "$SKIP_PIP_INSTALL_IN_CONTAINER" != "true" ]; then
    echo "Checking and installing Python dependencies from requirements.txt..."
    if command -v pip3 &> /dev/null
    then
        pip3 install -r requirements.txt
    elif command -v pip &> /dev/null
    then
        echo "pip3 not found, trying pip..."
        pip install -r requirements.txt
    else
        echo "Error: Neither pip3 nor pip found. Please install pip."
        echo "If running locally, please install dependencies manually (e.g., pip install -r requirements.txt) or ensure pip is available."
        exit 1
    fi
    echo "Dependency check complete."
else
    echo "Skipping pip install in updatearcep.sh as SKIP_PIP_INSTALL_IN_CONTAINER is true."
fi
echo

cd "$(dirname "$0")"
mkdir -p arcep
cd arcep

# ARCEP ZNE and ZAB data (XLS files to be converted)
echo "Downloading ARCEP ZNE list..."
wget -N -O liste-zne.xls http://www.arcep.fr/fileadmin/reprise/dossiers/numero/liste-zne.xls
echo "Downloading ARCEP ZAB-Departements correspondence..."
wget -N -O correspondance-zab-departements.xls http://www.arcep.fr/fileadmin/reprise/dossiers/numero/correspondance-zab-departements.xls

# Convert & Remove downloaded XLS files to CSV
echo "Converting XLS files to CSV..."
python3 ../xls_to_csv_converter.py liste-zne.xls liste-zne
python3 ../xls_to_csv_converter.py correspondance-zab-departements.xls correspondance-zab-departements
rm -f liste-zne.xls correspondance-zab-departements.xls

# New ARCEP data from data.gouv.fr (CSV files)
echo "Downloading ARCEP numbering resources (majournums.csv)..."
wget -N -O majournums.csv https://www.data.gouv.fr/fr/datasets/r/90e8bdd0-0f5c-47ac-bd39-5f46463eb806
echo "Downloading ARCEP operator identifiers (identifiants_ce.csv)..."
wget -N -O identifiants_ce.csv https://www.data.gouv.fr/fr/datasets/r/b0f62183-cd0c-498d-8153-aa1594e5e8d9

# INSEE data (unchanged)
echo "Downloading INSEE data..."
wget -N http://www.galichon.com/codesgeo/data/insee.zip

echo "Unzipping INSEE data..."
unzip -o insee.zip
rm -f insee.zip

# Old ARCEP data (commented out as they are superseded or handled differently)
# wget -N http://www.arcep.fr/fileadmin/reprise/dossiers/numero/ZABPQ-ZNE.xls
# wget -N http://www.arcep.fr/fileadmin/wopnum.xls
# wget -N http://www.arcep.fr/fileadmin/operateurs/liste-operateurs-declares.xls

cd ..
echo
echo "Running generatedb.py to build database..."
./generatedb.py
echo "Data update and database generation complete."
