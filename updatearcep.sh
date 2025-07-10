#!/bin/sh

cd "$(dirname "$0")"
mkdir -p arcep
cd arcep

# wget -N http://www.arcep.fr/fileadmin/reprise/dossiers/numero/ZABPQ-ZNE.xls # Old
# wget -N http://www.arcep.fr/fileadmin/wopnum.xls # Old
# wget -N http://www.arcep.fr/fileadmin/operateurs/liste-operateurs-declares.xls # Old
# wget -N http://www.arcep.fr/fileadmin/reprise/dossiers/numero/liste-zne.xls # Old

# New ARCEP data from data.gouv.fr
# Ressources en numérotation téléphonique (main file, contains number ranges and operators)
wget -N -O majournums.csv https://www.data.gouv.fr/fr/datasets/r/90e8bdd0-0f5c-47ac-bd39-5f46463eb806
# Identifiants de communications électroniques (operator details)
wget -N -O identifiants_ce.csv https://www.data.gouv.fr/fr/datasets/r/b0f62183-cd0c-498d-8153-aa1594e5e8d9

# INSEE data (unchanged)
wget -N http://www.galichon.com/codesgeo/data/insee.zip

unzip -o insee.zip
rm -f insee.zip
# Ensure new CSVs are not accidentally deleted if they were previously part of a zip (they are not)

cd ..
echo
./generatedb.py
