#!/usr/bin/env python3
#-*- encoding: Utf-8 -*-
import sqlite3
import argparse
import sys
import os
import logging

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
    # Remove separators and parenthesis
    tel = raw_tel.replace(' ', '').replace('.', '').replace('-', '').replace('(', '').replace(')', '')

    # Handle +33 (0) case which becomes +330... after removal
    if tel.startswith('+330'):
        tel = '0' + tel[4:]
    elif tel.startswith('+33'):
        tel = '0' + tel[3:]

    return tel

def setup_db_connection():
    if not os.path.exists(DB_FILE):
        logger.error(f"Erreur: La base de données '{DB_FILE}' est absente.")
        logger.error("Veuillez exécuter le script 'updatearcep.sh' ou 'generatedb.py' pour la générer.")
        sys.exit(1)
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de la connexion à la base de données: {e}")
        sys.exit(1)

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
        if mail and ('@' not in mail or '<' in mail or '>' in mail):
            mail = None
        if site and not (site.startswith('http://') or site.startswith('https://')):
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
    if not code_insee or code_insee == 0:
        return None

    cursor = conn.cursor()
    cursor.execute("SELECT NomCommune, CodePostal, NomDepartement FROM Communes WHERE CodeInsee=?", (code_insee,))
    row = cursor.fetchone()
    if row:
        return {
            'code_insee': code_insee,
            'commune': row[0],
            'code_postal': row[1],
            'departement': row[2]
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
    if info['code_insee'] and info['code_insee'] != 0:
        commune_info = get_commune_info(conn, info['code_insee'])
        result['location'] = commune_info

    # If Geo and no CodeInsee, give Region hint
    if info['type'] == 'Geographique' and (not result.get('location')):
        region_code = tel[:2]
        if region_code in REGION_MAP:
            result['location'] = {'region': REGION_MAP[region_code]}

    return result

def print_result(conn, tel, info):
    print(f"Numéro : {tel}")

    if not info:
        print("Résultat : Numéro inconnu dans la base ARCEP (pas d'opérateur assigné trouvé).")
        # Add a note about possible reasons
        print("Note : Certains numéros récents ou portés peuvent ne pas figurer dans le fichier public Open Data.")
        sys.exit(1)

    print(f"Type détecté : {info['type']}")
    print(f"Préfixe identifié : {info['prefix']}")

    # Operator Info
    op_info = get_operator_info(conn, info['code_operateur'])
    if op_info:
        print("\n--- Opérateur ---")
        print(f"Nom : {op_info['nom']}")
        print(f"Code ARCEP : {op_info['code']}")
        if op_info['site']:
            print(f"Site Web : {op_info['site']}")
        if op_info['mail']:
            print(f"Email : {op_info['mail']}")
    else:
        print(f"\nOpérateur : Code {info['code_operateur']} (Détails non trouvés)")

    # Location Info
    if info['code_insee'] and info['code_insee'] != 0:
        commune_info = get_commune_info(conn, info['code_insee'])
        if commune_info:
            print("\n--- Localisation (Estimation) ---")
            print(f"Commune : {commune_info['commune']}")
            print(f"Département : {commune_info['departement']}")
            print(f"Code Postal : {commune_info['code_postal']}")

    # If Geo and no CodeInsee, give Region hint
    if info['type'] == 'Geographique' and (not info['code_insee'] or info['code_insee'] == 0):
        region_code = tel[:2]
        if region_code in REGION_MAP:
            print(f"\nLocalisation : Région {REGION_MAP[region_code]} (Détail commune non disponible)")

def main():
    parser = argparse.ArgumentParser(description="Outil de recherche d'informations sur les numéros de téléphone français (ARCEP).")
    parser.add_argument("numero", help="Numéro de téléphone à rechercher (ex: 0123456789, +33612345678)")
    args = parser.parse_args()

    raw_tel = args.numero

    # Clean number
    tel = clean_phone_number(raw_tel)

    if not tel.isdigit():
        logger.error("Erreur: Le numéro doit contenir uniquement des chiffres (ou commencer par +33).")
        sys.exit(1)

    if len(tel) != 10:
        # Warning for non-10 digit numbers?
        # Short numbers exist (3xxx, 118xxx, 15, 17...)
        # Logic for short numbers could be added here.
        if len(tel) <= 4 or tel.startswith('118'):
             print(f"Numéro court ou spécial : {tel}")
             # We could look it up in PlagesNumeros too if it's there?
             # 3xxx are in PlagesNumeros?
             # Let's try searching anyway.
             pass
        else:
             logger.warning(f"Attention: Le numéro {tel} ne fait pas 10 chiffres. La recherche peut échouer.")

    conn = setup_db_connection()
    result = search_number(conn, tel)
    print_result(conn, tel, result)
    conn.close()

if __name__ == "__main__":
    main()
