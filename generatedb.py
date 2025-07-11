#!/usr/bin/env python3
#-*- encoding: Utf-8 -*-
import sqlite3
# import xlrd # No longer needed
import csv
import os
import logging

# Define a custom TRACE logging level (lower than DEBUG)
TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

class TraceLogger(logging.Logger):
    """Custom logger to add a TRACE level."""
    def trace(self, message, *args, **kws):
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            # stacklevel=2 ensures the caller of trace() is logged as the source
            self._log(TRACE_LEVEL_NUM, message, args, stacklevel=2, **kws)

# Set the custom logger class BEFORE any loggers are instantiated or basicConfig is called.
logging.setLoggerClass(TraceLogger)

# Configure logging
# Set default level to INFO. DEBUG messages will be suppressed unless explicitly enabled.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Instantiate the module-level logger
# All subsequent logging calls in this file should use this 'logger' instance.
logger = logging.getLogger(__name__)

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# -----------------------------------------------------------

logger.info('Création de la base de données...')

if os.path.exists('whoistel.sqlite3'):
	logger.debug('Ancienne base de données whoistel.sqlite3 trouvée, suppression...')
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
	CodeInsee INTEGER,
	NomCommune TEXT,
	CodePostal INTEGER,
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

# -----------------------------------------------------------
# Processing Operateurs from identifiants_ce.csv
logger.info('Lecture du fichier CSV des identifiants opérateurs...')
ops = []
try:
    with open('arcep/identifiants_ce.csv', 'r', encoding='cp1252', newline='') as csvfile: # ANSI often means cp1252 in FR context
        reader = csv.DictReader(csvfile, delimiter=';')
        logger.debug(f"Fieldnames in identifiants_ce.csv: {reader.fieldnames}") # Keep as DEBUG
        for i, row in enumerate(reader):
            logger.trace(f"Processing row {i} from identifiants_ce.csv: {row}") # Change to TRACE
            ops.append((
                row['CODE_OPERATEUR'].strip(),
                row['IDENTITE_OPERATEUR'].strip(),
                '', # TypeOperateur - not available
                '', # MailOperateur - not available
                ''  # SiteOperateur - not available
            ))
except FileNotFoundError:
    logger.error("ERREUR: Fichier arcep/identifiants_ce.csv non trouvé. Exécutez updatearcep.sh.")
except Exception as e:
    logger.error(f"Erreur lors du traitement de identifiants_ce.csv: {e}", exc_info=True)

if ops:
    logger.debug(f"Inserting {len(ops)} operators into Operateurs table.")
    c.executemany("INSERT INTO Operateurs(CodeOperateur, NomOperateur, TypeOperateur, MailOperateur, SiteOperateur) VALUES (?, ?, ?, ?, ?);", ops)
del ops

# -----------------------------------------------------------
# Processing MAJNUM.csv for PlagesNumerosGeographiques and PlagesNumeros
logger.info('Lecture du fichier CSV des ressources en numérotation (MAJNUM)...')
plages_geo = []
plages_non_geo = []

try:
    with open('arcep/majournums.csv', 'r', encoding='cp1252', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        logging.debug(f"Fieldnames in majournums.csv: {reader.fieldnames}") # Keep as DEBUG
        for i, row in enumerate(reader):
            logger.trace(f"Processing row {i} from majournums.csv: {row}") # Change to TRACE
            ezabpqm = row['EZABPQM'].strip() # e.g. "01056", "0603", "0800"
            # The second fieldname can vary ('Mnémo', 'Mnémo ', etc.)
            # Let's find it more robustly or assume it's the one after 'EZABPQM'
            # Based on current file, it's fieldnames[1] which is 'Mnémo'
            operateur_key = reader.fieldnames[1]
            operateur = row[operateur_key].strip()
            logger.debug(f"EZABPQM: {ezabpqm}, Operateur Key: {operateur_key}, Operateur: {operateur}")

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
            operateur_key = reader.fieldnames[1]
            operateur = row[operateur_key].strip()
            logger.debug(f"EZABPQM: {ezabpqm}, Operateur Key: {operateur_key}, Operateur: {operateur}")

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
                        logger.debug(f"Geo number, Tranche_Debut: {tranche_debut_str}, extracted PlageTel: {plage_tel_int}")
                    except ValueError:
                        logger.warning(f"Erreur de conversion pour PlageTel geo (Tranche_Debut): {tranche_debut_str} pour EZABPQM {ezabpqm}")
                        continue
                else:
                    logger.warning(f"Format Tranche_Debut inattendu pour geo: {tranche_debut_str} pour EZABPQM {ezabpqm}. Tentative de fallback.")
                    # Fallback: try to use EZABPQM itself if it's numeric and 5 digits after stripping 0
                    if ezabpqm.startswith('0') and len(ezabpqm) == 5 and ezabpqm[1:].isdigit(): # e.g. 01234
                        plage_tel_int = int(ezabpqm[1:]) * 10 # Heuristic: 12340
                        logger.debug(f"  Fallback using EZABPQM (5-digit type 0ZXXX): {ezabpqm} -> {plage_tel_int}")
                    elif ezabpqm.startswith('0') and len(ezabpqm) == 6 and ezabpqm[1:].isdigit(): # e.g. 012345
                         plage_tel_int = int(ezabpqm[1:])
                         logger.debug(f"  Fallback using EZABPQM (6-digit type 0ZXXXX): {ezabpqm} -> {plage_tel_int}")
                    else:
                        logger.warning(f"  -> Tentative de fallback avec EZABPQM {ezabpqm} échouée pour geo. Assignation à non-geo.")
                        plages_non_geo.append((ezabpqm, operateur)) # Add to non-geo if unsure
                        continue

                # CODE_INSEE IS MISSING. Placeholder 0.
                # This functionality is degraded. A separate file or different column in MAJNUM might be needed.
                plages_geo.append((plage_tel_int, operateur, 0))
                logger.debug(f"Added to plages_geo: PlageTel={plage_tel_int}, Operateur={operateur}, CodeInsee=0")
            else:
                # Non-geographic numbers (06, 07, 08, 09, special numbers)
                # PlageTel is TEXT here. EZABPQM is directly the prefix.
                plages_non_geo.append((ezabpqm, operateur))
                logger.debug(f"Added to plages_non_geo: EZABPQM={ezabpqm}, Operateur={operateur}")

except FileNotFoundError:
    logging.error("ERREUR: Fichier arcep/majournums.csv non trouvé. Exécutez updatearcep.sh.")
except Exception as e:
    logging.error(f"Erreur lors du traitement de majournums.csv: {e}", exc_info=True)


if plages_geo:
    logging.debug(f"Inserting {len(plages_geo)} records into PlagesNumerosGeographiques.")
    c.executemany("INSERT INTO PlagesNumerosGeographiques (PlageTel, CodeOperateur, CodeInsee) VALUES (?, ?, ?);", plages_geo)
del plages_geo

if plages_non_geo:
    logging.debug(f"Inserting {len(plages_non_geo)} records into PlagesNumeros.")
    c.executemany("INSERT INTO PlagesNumeros (PlageTel, CodeOperateur) VALUES (?, ?);", plages_non_geo)
del plages_non_geo

# -----------------------------------------------------------
# CommunesZNE data processing - commented out as liste-zne.xls replacement is unknown
# logging.info('Lecture du fichier CSV des zones géographiques...')
# ... (original code for liste-zne.xls was here) ...
# -----------------------------------------------------------

logging.info('Lecture du fichier CSV des codes communes (INSEE)...')
insee_data = [] # Renamed to avoid conflict
try:
    with open('arcep/insee.csv', 'r', encoding='cp1252', newline='') as file_insee:
        csv_insee = csv.DictReader(file_insee, delimiter=';')
        logging.debug(f"Fieldnames in insee.csv: {csv_insee.fieldnames}") # Keep as DEBUG
        for i, row in enumerate(csv_insee):
            logging.getLogger(__name__).trace(f"Processing row {i} from insee.csv: {row}") # Change to TRACE
            if not row['Codepos'] or not row['INSEE'] or not row['Commune'] or not row['Departement']: # Skip if essential fields are empty
                logging.warning(f"Ligne incomplète dans insee.csv: {row}, sautée.")
                continue
            try:
                insee_data.append((
                    int(row['INSEE'].strip()),
                    row['Commune'].strip(),
                    int(row['Codepos'].strip()),
                    row['Departement'].strip()
                ))
            except ValueError:
                logging.warning(f"Skipping row due to ValueError in INSEE data: {row}")
                continue
except FileNotFoundError:
    logging.error("ERREUR: Fichier arcep/insee.csv non trouvé. Assurez-vous que updatearcep.sh a bien fonctionné et décompressé insee.zip.")
except Exception as e:
    logging.error(f"Erreur lors du traitement de insee.csv: {e}", exc_info=True)

if insee_data:
    logging.debug(f"Inserting {len(insee_data)} records into Communes.")
    c.executemany("INSERT INTO Communes(CodeInsee, NomCommune, CodePostal, NomDepartement) VALUES (?, ?, ?, ?);", insee_data)
del insee_data

# -----------------------------------------------------------

logging.info('Sauvegarde de la base de données...')
sqlite_conn.commit()
sqlite_conn.close()

logging.info('Terminé.')
