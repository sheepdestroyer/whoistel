#!/usr/bin/env python3
#-*- encoding: Utf-8 -*-
import sqlite3
# import xlrd # No longer needed
import csv
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# -----------------------------------------------------------

print('Création de la base de données...')

if os.path.exists('whoistel.sqlite3'):
	os.remove('whoistel.sqlite3')

sqlite_conn = sqlite3.connect('whoistel.sqlite3') # Renamed to avoid conflict with module
c = sqlite_conn.cursor()

c.execute('''
CREATE TABLE PlagesNumerosGeographiques(
	PlageTel INTEGER, /* Corresponds to EZABPQM for geo numbers, e.g., 12345 for 012345xxxx */
	CodeOperateur TEXT,
	CodeInsee INTEGER /* This will be an issue as MAJNUM.csv doesn't have it directly - Placeholder 0 */
);
''')

c.execute('''
CREATE TABLE PlagesNumeros(
	PlageTel TEXT, /* Can be various lengths, e.g., 06, 081, 0800 */
	CodeOperateur TEXT
);
''')

c.execute('''
CREATE TABLE Operateurs(
	CodeOperateur TEXT,
	NomOperateur TEXT,
	TypeOperateur TEXT, /* Not in identifiants_ce.csv */
	MailOperateur TEXT, /* Not in identifiants_ce.csv */
	SiteOperateur TEXT /* Not in identifiants_ce.csv */
);
''')

c.execute('''
CREATE TABLE Communes(
	CodeInsee TEXT, /* Changed to TEXT for Corsican INSEE codes like 2A001 */
	NomCommune TEXT,
	CodePostal INTEGER, /* Assuming CodePostal is always numeric, can be TEXT if not */
	NomDepartement TEXT
);
''')

# CommunesZNE might not be possible to populate from new data sources without more info
# c.execute('''
# CREATE TABLE CommunesZNE(
# 	CodeZNE INTEGER,
# 	CodeInsee INTEGER
# );
# ''')

c.execute('''
CREATE TABLE CommunesZNE(
	CodeZNE INTEGER,
	CodeINSEECommune TEXT /* Changed to TEXT for Corsican INSEE codes like 2A001 */
);
''')

c.execute('''
CREATE TABLE ZABDepartement(
    ZABPrefix TEXT,
    NumerosDepartement TEXT
);
''')

# -----------------------------------------------------------
# Processing Operateurs from identifiants_ce.csv
print('Lecture du fichier CSV des identifiants opérateurs...')
ops = []
try:
    with open('arcep/identifiants_ce.csv', 'r', encoding='cp1252', newline='') as csvfile: # ANSI often means cp1252 in FR context
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            ops.append((
                row['CODE_OPERATEUR'].strip(),
                row['IDENTITE_OPERATEUR'].strip(),
                '', # TypeOperateur - not available
                '', # MailOperateur - not available
                ''  # SiteOperateur - not available
            ))
except FileNotFoundError:
    print("ERREUR: Fichier arcep/identifiants_ce.csv non trouvé. Exécutez updatearcep.sh.")
except Exception as e:
    print(f"Erreur lors du traitement de identifiants_ce.csv: {e}")

if ops:
    c.executemany("INSERT INTO Operateurs(CodeOperateur, NomOperateur, TypeOperateur, MailOperateur, SiteOperateur) VALUES (?, ?, ?, ?, ?);", ops)
del ops

# -----------------------------------------------------------
# Processing MAJNUM.csv for PlagesNumerosGeographiques and PlagesNumeros
print('Lecture du fichier CSV des ressources en numérotation (MAJNUM)...')
plages_geo = []
plages_non_geo = []

try:
    with open('arcep/majournums.csv', 'r', encoding='cp1252', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            ezabpqm = row['EZABPQM'].strip() # e.g. "01056", "0603", "0800"
            operateur = row['Mnémo'].strip() # Use the correctly decoded key

            # Determine if it's geographic (starts with 01-05)
            is_geo = False
            if ezabpqm.startswith('0') and len(ezabpqm) > 1:
                if ezabpqm[1] in '12345':
                    is_geo = True

            if is_geo:
                # Geographic numbers
                # PlageTel for PlagesNumerosGeographiques was an INTEGER, derived from the first 5 digits of the number
                # e.g. for "01056xxxxx", PlageTel was 10560 (if EZABPQM was 010560) or 1056 (if EZABPQM was 01056)
                # The new MAJNUM.csv provides EZABPQM, Tranche_Debut, Tranche_Fin.
                # We'll use Tranche_Debut (first 5 digits, excluding leading 0) as PlageTel.
                # Example: Tranche_Debut "0105600000", PlageTel should be 10560.
                plage_tel_int = 0
                tranche_debut_str = row['Tranche_Debut'].strip() # e.g. "0105600000"
                if tranche_debut_str.startswith('0') and len(tranche_debut_str) >= 6 :
                    try:
                        plage_tel_int = int(tranche_debut_str[1:6]) # e.g. 10560
                    except ValueError:
                        print(f"Erreur de conversion pour PlageTel geo (Tranche_Debut): {tranche_debut_str} pour EZABPQM {ezabpqm}")
                        continue
                else:
                    print(f"Format Tranche_Debut inattendu pour geo: {tranche_debut_str} pour EZABPQM {ezabpqm}")
                    # Fallback: try to use EZABPQM itself if it's numeric and 5 digits after stripping 0
                    if ezabpqm.startswith('0') and len(ezabpqm) == 5 and ezabpqm[1:].isdigit(): # e.g. 01234
                        plage_tel_int = int(ezabpqm[1:]) * 10 # Heuristic: 12340
                    elif ezabpqm.startswith('0') and len(ezabpqm) == 6 and ezabpqm[1:].isdigit(): # e.g. 012345
                         plage_tel_int = int(ezabpqm[1:])
                    else:
                        print(f"  -> Tentative de fallback avec EZABPQM {ezabpqm} échouée pour geo.")
                        plages_non_geo.append((ezabpqm, operateur)) # Add to non-geo if unsure
                        continue

                # CODE_INSEE IS MISSING. Placeholder 0.
                # This functionality is degraded. A separate file or different column in MAJNUM might be needed.
                plages_geo.append((plage_tel_int, operateur, 0))
            else:
                # Non-geographic numbers (06, 07, 08, 09, special numbers)
                # PlageTel is TEXT here. EZABPQM is directly the prefix.
                plages_non_geo.append((ezabpqm, operateur))

except FileNotFoundError:
    print("ERREUR: Fichier arcep/majournums.csv non trouvé. Exécutez updatearcep.sh.")
except Exception as e:
    print(f"Erreur lors du traitement de majournums.csv: {e}")


if plages_geo:
    c.executemany("INSERT INTO PlagesNumerosGeographiques (PlageTel, CodeOperateur, CodeInsee) VALUES (?, ?, ?);", plages_geo)
del plages_geo

if plages_non_geo:
    c.executemany("INSERT INTO PlagesNumeros (PlageTel, CodeOperateur) VALUES (?, ?);", plages_non_geo)
del plages_non_geo

# -----------------------------------------------------------
# Processing CommunesZNE from liste-zne_Correspondance_Communes_ZNE.csv
print('Lecture du fichier CSV de correspondance Communes-ZNE...')
communes_zne_data = []
try:
    # Path: arcep/liste-zne_Correspondance_Communes_ZNE.csv
    # Headers: ZNE_NUM,ZNE_CHEF_LIEU,COMMUNE_INSEE,COMMUNE_NOM,ZNE_NBABO,ZNE_COM
    with open('arcep/liste-zne_Correspondance_Communes_ZNE.csv', 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                code_zne = int(row['ZNE_NUM'].strip())
                commune_insee = row['COMMUNE_INSEE'].strip() # Keep as TEXT
                communes_zne_data.append((code_zne, commune_insee))
            except ValueError: # Will now only catch issues with ZNE_NUM
                print(f"Skipping row due to ValueError (likely ZNE_NUM) in Communes-ZNE data: {row}")
                continue
            except KeyError as e:
                print(f"Skipping row due to KeyError '{e}' in Communes-ZNE data (check headers): {row}")
                continue
except FileNotFoundError:
    print("ERREUR: Fichier arcep/liste-zne_Correspondance_Communes_ZNE.csv non trouvé.")
except Exception as e:
    print(f"Erreur lors du traitement de liste-zne_Correspondance_Communes_ZNE.csv: {e}")

if communes_zne_data:
    c.executemany("INSERT INTO CommunesZNE (CodeZNE, CodeINSEECommune) VALUES (?, ?);", communes_zne_data)
del communes_zne_data

# -----------------------------------------------------------
# Processing ZABDepartement from arcep/correspondance-zab-departements_ZAB_D_partement.csv
print('Lecture du fichier CSV de correspondance ZAB-Départements...')
zab_departement_data = []
try:
    # Path: arcep/correspondance-zab-departements_ZAB_D_partement.csv
    # Headers: Régions ou groupes de départements,N° des départements,0ZAB
    with open('arcep/correspondance-zab-departements_ZAB_D_partement.csv', 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                zab_prefix = row['0ZAB'].strip()
                numeros_dept = row['N° des départements'].strip()
                if zab_prefix and numeros_dept: # Ensure essential data is present
                    zab_departement_data.append((zab_prefix, numeros_dept))
                else:
                    print(f"Skipping row due to missing ZABPrefix or NumerosDepartement in ZAB-Départements data: {row}")
            except KeyError as e:
                print(f"Skipping row due to KeyError '{e}' in ZAB-Départements data (check headers): {row}")
                continue
except FileNotFoundError:
    print("ERREUR: Fichier arcep/correspondance-zab-departements_ZAB_D_partement.csv non trouvé.")
except Exception as e:
    print(f"Erreur lors du traitement de correspondance-zab-departements_ZAB_D_partement.csv: {e}")

if zab_departement_data:
    c.executemany("INSERT INTO ZABDepartement (ZABPrefix, NumerosDepartement) VALUES (?, ?);", zab_departement_data)
del zab_departement_data

# -----------------------------------------------------------
# CodeInsee in PlagesNumerosGeographiques will remain 0 as the current majournums.csv
# does not provide a clear way to link to ZNE Chef-Lieu INSEE codes.
# The dict_zne_cheflieu_insee and related logic has been removed.
# The original MAJNUM.csv processing block correctly inserts 0 for CodeInsee.
# -----------------------------------------------------------

print('Lecture du fichier CSV des codes communes (INSEE)...')
insee_data = [] # Renamed to avoid conflict
try:
    with open('arcep/insee.csv', 'r', encoding='cp1252', newline='') as file_insee:
        csv_insee = csv.DictReader(file_insee, delimiter=';')
        for row in csv_insee:
            if not row['Codepos'] or not row['INSEE'] or not row['Commune'] or not row['Departement']: # Skip if essential fields are empty
                print(f"Ligne incomplète dans insee.csv: {row}, sautée.")
                continue
            try:
                # INSEE code is now TEXT, Codepos is INTEGER
                code_postal_val = None
                if row['Codepos'].strip(): # Check if Codepos is not empty
                    code_postal_val = int(row['Codepos'].strip())

                insee_data.append((
                    row['INSEE'].strip(), # Keep as TEXT
                    row['Commune'].strip(),
                    code_postal_val, # Use potentially None value
                    row['Departement'].strip()
                ))
            except ValueError: # Will now primarily catch issues with Codepos
                print(f"Skipping row due to ValueError (likely Codepos) in INSEE data: {row}")
                continue
except FileNotFoundError:
    print("ERREUR: Fichier arcep/insee.csv non trouvé. Assurez-vous que updatearcep.sh a bien fonctionné et décompressé insee.zip.")
except Exception as e:
    print(f"Erreur lors du traitement de insee.csv: {e}")

if insee_data:
    c.executemany("INSERT INTO Communes(CodeInsee, NomCommune, CodePostal, NomDepartement) VALUES (?, ?, ?, ?);", insee_data)
del insee_data

# -----------------------------------------------------------

print('Sauvegarde de la base de données...')
sqlite_conn.commit()
sqlite_conn.close()

print('Terminé.')
