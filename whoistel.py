#!/usr/bin/env python3
#-*- encoding: Utf-8 -*-
"""
Core logic for cleaning phone numbers and looking up operator/location info
from the ARCEP database.
"""
import sqlite3
import argparse
import sys
import os
import logging
import re
from urllib.parse import urlparse
from email_validator import validate_email, EmailNotValidError
from contextlib import closing

class DatabaseError(Exception):
    """Custom exception raised for database-related errors."""
    pass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s') # Simplified format for CLI
logger = logging.getLogger(__name__)

DB_FILE = 'whoistel.sqlite3'

REGION_MAP = {
    '01': 'Île-de-France',
    '02': 'Nord-Ouest',
    '03': 'Nord-Est',
    '04': 'Sud-Est',
    '05': 'Sud-Ouest'
}

def clean_phone_number(raw_tel):
    """
    Cleans a raw phone number by removing separators and handling international prefixes.
    
    Args:
        raw_tel (str): Raw input phone number.
        
    Returns:
        str: Cleaned digits-only number or empty string.
    """
    if not raw_tel:
        return ""
    # Remove separators and parenthesis (including tabs, non-breaking spaces)
    tel = re.sub(r'[\s.\-()]', '', raw_tel)

    # Handle +33 (0) case which becomes +330... after removal
    if tel.startswith('+330'):
        tel = f"0{tel[4:]}"
    elif tel.startswith('+33'):
        tel = f"0{tel[3:]}"
    elif tel.startswith('0033'):
        tel = f"0{tel[4:]}"

    return tel

def is_valid_phone_format(tel):
    """
    Checks if a cleaned phone number is valid (digits only and exactly 10 digits).
    
    Args:
        tel (str): Cleaned phone number.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if not tel:
        return False
    return tel.isdigit() and len(tel) == 10

def setup_db_connection():
    """
    Establishes a connection to the SQLite database.
    Raises DatabaseError if DB file is missing or connection fails.
    """
    if not os.path.exists(DB_FILE):
        msg = f"Erreur: La base de données '{DB_FILE}' est absente. Veuillez exécuter le script 'updatearcep.sh' ou 'generatedb.py' pour la générer."
        logger.error(msg)
        raise DatabaseError(msg)
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        msg = f"Erreur lors de la connexion à la base de données: {e}"
        logger.exception(msg)
        raise DatabaseError(msg) from e
    else:
        return conn

def get_operator_info(conn, code_operateur):
    """
    Retrieves operator details (name, type, email, site) from the database by operator code.
    Validates email and URL fields to prevent malformed data.
    """
    if not code_operateur:
        return None

    cursor = conn.cursor()
    cursor.execute("SELECT NomOperateur, TypeOperateur, MailOperateur, SiteOperateur FROM Operateurs WHERE CodeOperateur=?", (code_operateur,))
    row = cursor.fetchone()
    if row:
        mail = row['MailOperateur']
        site = row['SiteOperateur']

        # Validate and sanitize email/URL to prevent display of malformed data
        if mail:
            try:
                validate_email(mail, check_deliverability=False)
            except EmailNotValidError:
                mail = None

        if site:
            parsed = urlparse(site)
            if not parsed.scheme or not parsed.netloc or parsed.scheme not in ['http', 'https']:
                site = None

        return {
            'code': code_operateur,
            'nom': row['NomOperateur'],
            'type': row['TypeOperateur'],
            'mail': mail,
            'site': site
        }
    return None

def get_commune_info(conn, code_insee):
    """
    Retrieves commune name from the database based on INSEE code.
    """
    if not code_insee or str(code_insee) == '0':
        return None

    cursor = conn.cursor()
    cursor.execute("SELECT NomCommune, CodePostal, NomDepartement, Latitude, Longitude FROM Communes WHERE CodeInsee=?", (code_insee,))
    row = cursor.fetchone()
    if row:
        return {
            'code_insee': code_insee,
            'commune': row['NomCommune'],
            'code_postal': row['CodePostal'],
            'departement': row['NomDepartement'],
            'latitude': row['Latitude'],
            'longitude': row['Longitude']
        }
    return None

def search_number(conn, tel):
    """
    Search for a phone number range in the database.
    
    Args:
        conn (sqlite3.Connection): Database connection.
        tel (str): Cleaned 10-digit phone number.
        
    Returns:
        dict | None: A dictionary containing 'prefix', 'code_operateur', 'code_insee', and 'type', or None if no match.
    """
    cursor = conn.cursor()

    # 1. Determine if Geo or Non-Geo
    is_geo = tel.startswith('0') and len(tel) >= 2 and tel[1] in '12345'

    table = 'PlagesNumerosGeographiques' if is_geo else 'PlagesNumeros'

    # 2. Longest Prefix Match
    # Prefixes in DB can be 2 to 7 digits (or more).
    # We check prefixes from length 7 down to 2.
    best_match = None

    for length in range(min(len(tel), 9), 1, -1):
        prefix = tel[:length]
        # logging.debug(f"Checking prefix: {prefix} in {table}")

        if is_geo:
            cursor.execute(f"SELECT CodeOperateur, CodeInsee FROM {table} WHERE PlageTel=?", (prefix,))
            row = cursor.fetchone()
            if row:
                best_match = {
                    'prefix': prefix,
                    'code_operateur': row['CodeOperateur'],
                    'code_insee': row['CodeInsee'],
                    'type': 'Geographique'
                }
                break
        else:
            cursor.execute(f"SELECT CodeOperateur FROM {table} WHERE PlageTel=?", (prefix,))
            row = cursor.fetchone()
            if row:
                best_match = {
                    'prefix': prefix,
                    'code_operateur': row['CodeOperateur'],
                    'code_insee': None,
                    'type': 'Non-Geographique'
                }
                break

    return best_match

def get_full_info(conn, tel):
    """
    Combines search results with operator and location details into a dictionary.
    """
    info = search_number(conn, tel)
    result = {
        'number': tel,
        'found': False,
        'type': None,
        'prefix': None,
        'operator': None,
        'location': None,
        'error': None
    }

    if not info:
        result['error'] = "Numéro inconnu dans la base ARCEP (pas d'opérateur assigné trouvé)."
        return result

    result['found'] = True
    result['type'] = info['type']
    result['prefix'] = info['prefix']
    result['code_operateur'] = info['code_operateur']

    # Operator Info
    op_info = get_operator_info(conn, info['code_operateur'])
    if op_info:
        result['operator'] = op_info
    else:
        result['operator'] = {'code': info['code_operateur'], 'nom': 'Inconnu', 'type': 'N/A', 'site': None, 'mail': None}

    # Location Info
    if info['code_insee'] and info['code_insee'] != '0':
        result['location'] = get_commune_info(conn, info['code_insee'])
    
    # Always try to add region for Geographique numbers
    if info['type'] == 'Geographique':
        region_code = tel[:2]
        if region_code in REGION_MAP:
            if not result['location']:
                result['location'] = {}
            result['location']['region'] = REGION_MAP[region_code]

    return result

def print_result(result):
    """
    Prints the formatted search result to stdout.
    
    Args:
        result (dict): Full info dictionary from get_full_info.
        
    Returns:
        bool: True if result found and printed, False otherwise.
    """
    print(f"Numéro : {result['number']}")

    if not result['found']:
        print(f"Résultat : {result.get('error', 'Inconnu')}")
        print("Note : Certains numéros récents ou portés peuvent ne pas figurer dans le fichier public Open Data.")
        return False

    print(f"Type détecté : {result.get('type')}")
    print(f"Préfixe identifié : {result.get('prefix')}")

    # Operator Info
    op_info = result.get('operator')
    if isinstance(op_info, dict) and op_info.get('nom') != 'Inconnu':
        print("\n--- Opérateur ---")
        print(f"Nom : {op_info.get('nom')}")
        print(f"Code ARCEP : {op_info.get('code')}")
        if op_info.get('site'):
            print(f"Site Web : {op_info.get('site')}")
        if op_info.get('mail'):
            print(f"Email : {op_info.get('mail')}")
    else:
        print(f"\nOpérateur : Code {result.get('code_operateur')} (Détails non trouvés)")

    if loc := result.get('location'):
        print("\n--- Localisation (Estimation) ---")
        if region := loc.get('region'):
            if 'commune' in loc:
                print(f"Région : {region}")
            else:
                print(f"Région : {region} (Détail commune non disponible)")
        
        if 'commune' in loc:
            print(f"Commune : {loc.get('commune')}")
            print(f"Département : {loc.get('departement')}")
            print(f"Code Postal : {loc.get('code_postal')}")
            if loc.get('latitude') and loc.get('longitude'):
                print(f"GPS : {loc.get('latitude')}, {loc.get('longitude')}")
    
    return True

def main():
    """CLI entry point for searching phone number information."""
    parser = argparse.ArgumentParser(description="Outil de recherche d'informations sur les numéros de téléphone français (ARCEP).")
    parser.add_argument("numero", help="Numéro de téléphone à rechercher (ex: 0123456789, +33612345678)")
    args = parser.parse_args()

    raw_tel = args.numero
    
    cleaned_number = clean_phone_number(raw_tel)
    
    if not is_valid_phone_format(cleaned_number):
        if cleaned_number and cleaned_number != raw_tel:
            print(f"Erreur: Le numéro «{raw_tel}» est invalide après normalisation («{cleaned_number}»). Il doit contenir exactement 10 chiffres.", file=sys.stderr)
        else:
             print(f"Erreur: Le numéro «{raw_tel}» est invalide. Il doit contenir exactement 10 chiffres.", file=sys.stderr)
        sys.exit(1)

    # Use valid database connection
    try:
        with closing(setup_db_connection()) as conn:
             result = get_full_info(conn, cleaned_number)
             if not print_result(result):
                 sys.exit(1)
    except DatabaseError as e:
        # Error already logged, but print to stderr to ensure visibility in all contexts
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
