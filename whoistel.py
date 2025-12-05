#!/usr/bin/env python3
#-*- encoding: Utf-8 -*-
import sqlite3
import contextlib
import argparse
import sys
import os
import logging
import re
from urllib.parse import urlparse
from email_validator import validate_email, EmailNotValidError

class DatabaseError(Exception):
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
    if not raw_tel:
        return ""
    # Remove separators and parenthesis (including tabs, non-breaking spaces)
    tel = re.sub(r'[\s.\-()]', '', raw_tel)

    # Handle +33 (0) case which becomes +330... after removal
    if tel.startswith('+330'):
        tel = '0' + tel[4:]
    elif tel.startswith('+33'):
        tel = '0' + tel[3:]

    return tel

def setup_db_connection():
    if not os.path.exists(DB_FILE):
        msg = f"Erreur: La base de données '{DB_FILE}' est absente. Veuillez exécuter le script 'updatearcep.sh' ou 'generatedb.py' pour la générer."
        logger.error(msg)
        raise DatabaseError(msg)
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except sqlite3.Error as e:
        msg = f"Erreur lors de la connexion à la base de données: {e}"
        logger.error(msg)
        raise DatabaseError(msg)

def get_operator_info(conn, code_operateur):
    if not code_operateur:
        return None

    cursor = conn.cursor()
    cursor.execute("SELECT NomOperateur, TypeOperateur, MailOperateur, SiteOperateur FROM Operateurs WHERE CodeOperateur=?", (code_operateur,))
    row = cursor.fetchone()
    if row:
        mail = row[2]
        site = row[3]

        # Simple validation to prevent XSS
        # Robust validation
        if mail:
            try:
                validate_email(mail, check_deliverability=False)
            except EmailNotValidError:
                mail = None

        if site:
            try:
                parsed = urlparse(site)
                if not all([parsed.scheme, parsed.netloc]):
                    site = None
                elif parsed.scheme not in ['http', 'https']:
                    site = None
            except ValueError:
                site = None

        return {
            'code': code_operateur,
            'nom': row[0],
            'type': row[1],
            'mail': mail,
            'site': site
        }
    return None

def get_commune_info(conn, code_insee):
    if not code_insee or str(code_insee) == '0':
        return None

    cursor = conn.cursor()
    cursor.execute("SELECT NomCommune, CodePostal, NomDepartement, Latitude, Longitude FROM Communes WHERE CodeInsee=?", (code_insee,))
    row = cursor.fetchone()
    if row:
        return {
            'code_insee': code_insee,
            'commune': row[0],
            'code_postal': row[1],
            'departement': row[2],
            'latitude': row[3],
            'longitude': row[4]
        }
    return None

def search_number(conn, tel):
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
                    'code_operateur': row[0],
                    'code_insee': row[1],
                    'type': 'Geographique'
                }
                break
        else:
            cursor.execute(f"SELECT CodeOperateur FROM {table} WHERE PlageTel=?", (prefix,))
            row = cursor.fetchone()
            if row:
                best_match = {
                    'prefix': prefix,
                    'code_operateur': row[0],
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
        commune_info = get_commune_info(conn, info['code_insee'])
        result['location'] = commune_info

    # If Geo and no CodeInsee, give Region hint
    if info['type'] == 'Geographique' and (not result.get('location')):
        region_code = tel[:2]
        if region_code in REGION_MAP:
            result['location'] = {'region': REGION_MAP[region_code]}

    return result

def print_result(result):
    print(f"Numéro : {result['number']}")

    if not result['found']:
        print(f"Résultat : {result.get('error', 'Inconnu')}")
        print("Note : Certains numéros récents ou portés peuvent ne pas figurer dans le fichier public Open Data.")
        sys.exit(1)

    print(f"Type détecté : {result.get('type')}")
    print(f"Préfixe identifié : {result.get('prefix')}")

    # Operator Info
    op_info = result.get('operator')
    if op_info and op_info.get('nom') != 'Inconnu':
        print("\n--- Opérateur ---")
        print(f"Nom : {op_info.get('nom')}")
        print(f"Code ARCEP : {op_info.get('code')}")
        if op_info.get('site'):
            print(f"Site Web : {op_info.get('site')}")
        if op_info.get('mail'):
            print(f"Email : {op_info.get('mail')}")
    else:
        print(f"\nOpérateur : Code {result.get('code_operateur')} (Détails non trouvés)")

    # Location Info
    loc = result.get('location')
    if loc:
        if 'commune' in loc:
            print("\n--- Localisation (Estimation) ---")
            print(f"Commune : {loc.get('commune')}")
            print(f"Département : {loc.get('departement')}")
            print(f"Code Postal : {loc.get('code_postal')}")
            if loc.get('latitude') and loc.get('longitude'):
                print(f"GPS : {loc.get('latitude')}, {loc.get('longitude')}")
        elif 'region' in loc:
            print(f"\nLocalisation : Région {loc['region']} (Détail commune non disponible)")

def main():
    parser = argparse.ArgumentParser(description="Outil de recherche d'informations sur les numéros de téléphone français (ARCEP).")
    parser.add_argument("numero", help="Numéro de téléphone à rechercher (ex: 0123456789, +33612345678)")
    args = parser.parse_args()

    raw_tel = args.numero
    
    # Remove redundant initial regex check
    # if not re.match(r'^\+?[0-9 .()-]+$', raw_tel): ...
    # clean_phone_number handles more cases.

    cleaned_number = clean_phone_number(raw_tel)
    
    # Ensure cleaned number only contains digits
    if not cleaned_number.isdigit():
         print("Erreur: Le numéro fourni est invalide. Il doit contenir uniquement des chiffres après nettoyage.", file=sys.stderr)
         sys.exit(1)
    
    if len(cleaned_number) != 10:
        logger.warning(f"Attention: Le numéro {cleaned_number} ne fait pas 10 chiffres. La recherche peut échouer.")

    # Use valid database connection
    # Use valid database connection
    try:
        with contextlib.closing(setup_db_connection()) as conn:
             result = get_full_info(conn, cleaned_number)
             print_result(result)
    except DatabaseError as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
