#!/usr/bin/env python3
#-*- encoding: Utf-8 -*-
import sqlite3
import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_FILE = 'whoistel.sqlite3'

def setup_database():
    if os.path.exists(DB_FILE):
        logger.info(f"Removing old database {DB_FILE}...")
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Create Tables
    # PlagesNumerosGeographiques: Geo numbers (01-05). PlageTel is the prefix (e.g. "01056").
    # Changed PlageTel to TEXT for consistency and flexibility.
    c.execute('''
    CREATE TABLE PlagesNumerosGeographiques(
        PlageTel TEXT PRIMARY KEY,
        CodeOperateur TEXT,
        CodeInsee INTEGER
    );
    ''')

    # PlagesNumeros: Non-Geo numbers (06, 07, 08, 09, etc.). PlageTel is the prefix.
    c.execute('''
    CREATE TABLE PlagesNumeros(
        PlageTel TEXT PRIMARY KEY,
        CodeOperateur TEXT
    );
    ''')

    # Operateurs
    c.execute('''
    CREATE TABLE Operateurs(
        CodeOperateur TEXT PRIMARY KEY,
        NomOperateur TEXT,
        TypeOperateur TEXT,
        MailOperateur TEXT,
        SiteOperateur TEXT
    );
    ''')

    # Communes
    c.execute('''
    CREATE TABLE Communes(
        CodeInsee INTEGER PRIMARY KEY,
        NomCommune TEXT,
        CodePostal INTEGER,
        NomDepartement TEXT
    );
    ''')

    conn.commit()
    return conn

def import_operateurs(conn):
    logger.info('Importing Operators from arcep/identifiants_ce.csv...')
    try:
        # Columns: CODE_OPERATEUR;IDENTITE_OPERATEUR;...
        df = pd.read_csv('arcep/identifiants_ce.csv', sep=';', encoding='cp1252', dtype=str)

        # Select and rename columns
        # We only have Code and Name basically.
        data = df[['CODE_OPERATEUR', 'IDENTITE_OPERATEUR']].copy()
        data.columns = ['CodeOperateur', 'NomOperateur']
        data['TypeOperateur'] = ''
        data['MailOperateur'] = ''
        data['SiteOperateur'] = ''

        # Clean data
        data['CodeOperateur'] = data['CodeOperateur'].str.strip()
        data['NomOperateur'] = data['NomOperateur'].str.strip()

        # Drop duplicates
        data.drop_duplicates(subset=['CodeOperateur'], inplace=True)

        data.to_sql('Operateurs', conn, if_exists='append', index=False)
        logger.info(f"Imported {len(data)} operators.")

    except Exception as e:
        logger.error(f"Error importing operators: {e}")

def import_numeros(conn):
    logger.info('Importing Numbering Resources from arcep/majournums.csv...')
    try:
        # Columns: EZABPQM;Tranche_Debut;Tranche_Fin;Mnémo;Territoire;Date_Attribution
        df = pd.read_csv('arcep/majournums.csv', sep=';', encoding='cp1252', dtype=str)

        # Rename columns for clarity
        df.rename(columns={'EZABPQM': 'PlageTel', 'Mnémo': 'CodeOperateur'}, inplace=True)

        # Filter for Metropole? (User wants +33, usually implies Metropole but Overseas is also +262 etc. +33 is Metropole)
        # However, checking +33 numbers implies we mostly care about Metropole.
        # But we can keep all. "Territoire" column.
        # Let's keep all for now, or filter 'Métropole' if we only want +33.
        # +33 is France. DOM have their own codes (+262, +590...).
        # Arcep file contains all.
        # Ideally we should filter by Territoire = Métropole for +33.

        df_metro = df[df['Territoire'] == 'Métropole'].copy()
        logger.info(f"Filtered {len(df_metro)} entries for Métropole.")

        # Separate Geo and Non-Geo
        # Geo: Starts with 01, 02, 03, 04, 05.
        mask_geo = df_metro['PlageTel'].str.match(r'^0[1-5]')
        df_geo = df_metro[mask_geo].copy()
        df_non_geo = df_metro[~mask_geo].copy()

        # Prepare Geo Table
        # PlageTel, CodeOperateur, CodeInsee (0 placeholder)
        df_geo = df_geo[['PlageTel', 'CodeOperateur']]
        df_geo['CodeInsee'] = 0

        # Drop duplicates
        df_geo.drop_duplicates(subset=['PlageTel'], inplace=True)

        df_geo.to_sql('PlagesNumerosGeographiques', conn, if_exists='append', index=False)
        logger.info(f"Imported {len(df_geo)} geographic number ranges.")

        # Prepare Non-Geo Table
        # PlageTel, CodeOperateur
        df_non_geo = df_non_geo[['PlageTel', 'CodeOperateur']]

        # Drop duplicates
        df_non_geo.drop_duplicates(subset=['PlageTel'], inplace=True)

        df_non_geo.to_sql('PlagesNumeros', conn, if_exists='append', index=False)
        logger.info(f"Imported {len(df_non_geo)} non-geographic number ranges.")

    except Exception as e:
        logger.error(f"Error importing numbers: {e}")

def import_communes(conn):
    logger.info('Importing Communes from arcep/insee.csv...')
    try:
        # Columns: Commune;Codepos;Departement;INSEE
        # The file is headerless? No, header is present: Commune;Codepos;Departement;INSEE
        # Check delimiter.
        df = pd.read_csv('arcep/insee.csv', sep=';', encoding='cp1252', dtype=str)

        # Select and rename
        # We need CodeInsee, NomCommune, CodePostal, NomDepartement
        data = df[['INSEE', 'Commune', 'Codepos', 'Departement']].copy()
        data.columns = ['CodeInsee', 'NomCommune', 'CodePostal', 'NomDepartement']

        # Clean
        data.dropna(subset=['CodeInsee'], inplace=True)
        data['CodeInsee'] = pd.to_numeric(data['CodeInsee'], errors='coerce')
        data.dropna(subset=['CodeInsee'], inplace=True)
        data['CodeInsee'] = data['CodeInsee'].astype(int)

        data['CodePostal'] = pd.to_numeric(data['CodePostal'], errors='coerce').fillna(0).astype(int)

        # Remove duplicates
        data.drop_duplicates(subset=['CodeInsee'], inplace=True)

        data.to_sql('Communes', conn, if_exists='append', index=False)
        logger.info(f"Imported {len(data)} communes.")

    except Exception as e:
        logger.error(f"Error importing communes: {e}")

if __name__ == "__main__":
    conn = setup_database()
    import_operateurs(conn)
    import_numeros(conn)
    import_communes(conn)
    conn.close()
    logger.info("Database generation complete.")
