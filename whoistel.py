#!/usr/bin/env python3
#-*- encoding: Utf-8 -*-
from urllib.parse import quote_plus
from urllib.request import urlopen
import sqlite3 # Renamed conn variable later
import socket # For timeout
from os.path import exists
from sys import argv, exit
from datetime import date
import json # Renamed loads variable later
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Se mettre dans le même dossier que le script

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Variables globales

tel = None
# useAnnu = True # Removed
# useOVH = True # Removed

is_EZABPQMCDU = False
is_special = False

# urlAnnu = 'http://v3.annu.com/cgi-bin/srch.cgi?j=1&n=10&s=' # Removed
# urlOVH = 'https://www.ovhtelecom.fr/cgi-bin/ajax/ajaxEligibilityCheck.cgi?lightRequest=yes&number=' # Removed

import argparse

# Interpréter les arguments
parser = argparse.ArgumentParser(description="Recherche d'informations sur un numéro de téléphone français.")
parser.add_argument("numero_tel", nargs='?', help="Le numéro de téléphone à rechercher (ex: 0123456789, +33612345678).")
# Deprecated arguments - kept for informational purposes but do nothing
parser.add_argument("--no-annu", help="Argument obsolète, ignoré.", action="store_true")
parser.add_argument("--no-ovh", help="Argument obsolète, ignoré.", action="store_true")

# Add a specific argument for the test number, though manual input is also fine
parser.add_argument("--test-numero", default="+33740756315", help="Numéro de test prédéfini.", dest="test_numero_arg")


args = parser.parse_args()
logging.debug(f"Arguments parsed: {args}")

if args.no_annu:
    logging.warning("Argument --no-annu is deprecated and will be ignored.")
if args.no_ovh:
    logging.warning("Argument --no-ovh is deprecated and will be ignored.")

raw_tel = args.numero_tel
logging.debug(f"Raw telephone number input: {raw_tel}")

# If numero_tel is not provided directly, consider using test_numero_arg if a specific flag for it was intended.
# For now, numero_tel being positional and optional (nargs='?') means if it's None, we might want to use a default or error out.
# The original script structure implies the number is mandatory.

if raw_tel is None:
    # This part could be enhanced, e.g. to use a default test number if a specific flag like --run-test was added.
    # For now, mirror original behavior: number is mandatory.
    parser.print_help() # This prints to stdout
    logging.error("Le numéro de téléphone est requis.")
    exit(1)

# Nettoyage du numéro de téléphone
logging.debug(f"Original tel: '{raw_tel}'")
tel = raw_tel.replace('-', '').replace(' ', '').replace('.', '')
tel = tel.replace('+33(0)', '0').replace('+330', '0').replace('+33', '0')
tel = tel.strip().lower()
logging.info(f"Cleaned telephone number: {tel}")

if not tel.isdigit():
    parser.print_help() # This prints to stdout
    logging.error(f"Le numéro '{raw_tel}' (nettoyé en '{tel}') contient des caractères non numériques.")
    exit(1)


# Fonctions d'information

def section(text):
    logging.info("")
    logging.info('+-' + '-' * len(text) + '-+')
    logging.info('| ' + text + ' |')
    logging.info('+-' + '-' * len(text) + '-+')
    logging.info("")

def erreur(text, exit_code=1):
    logging.error(text)
    logging.info("") # Add a blank line for readability in logs, similar to original print behavior
    exit(exit_code)

# Se connecter à la base de données de l'ARCEP en local

if not exists('whoistel.sqlite3'):
    erreur('Vous devez générer le fichier "whoistel.sqlite3" avec generatedb.py.')

logging.debug("Connecting to SQLite database 'whoistel.sqlite3'")
conn = sqlite3.connect('whoistel.sqlite3')
c = conn.cursor()

# Fonctions pour l'ARCEP

def getInfosINSEE(codeINSEE):
    logging.debug(f"Fetching INSEE info for CodeINSEE: {codeINSEE}")
    if codeINSEE == 0 or codeINSEE is None:
        logging.info("Informations de commune non disponibles pour ce bloc (CodeInsee manquant ou 0).")
        return

    c.execute('SELECT NomCommune, CodePostal, NomDepartement FROM Communes WHERE CodeInsee=?', (codeINSEE,))
    infos = c.fetchone()
    logging.debug(f"INSEE query result: {infos}")

    if infos:
        logging.info("")
        logging.info(f'Commune : {infos[0]}')
        logging.info(f'Département : {infos[2]}')
        logging.info(f'Code postal : {str(infos[1]).zfill(5)}')
        logging.info(f'Code INSEE : {str(codeINSEE).zfill(5)}')
    else:
        logging.warning(f"Aucune information trouvée pour le Code INSEE : {str(codeINSEE).zfill(5)}")


def getInfosOperateur(codeOperateur):
    logging.debug(f"Fetching operator info for CodeOperateur: {codeOperateur}")
    c.execute('SELECT NomOperateur, TypeOperateur, MailOperateur, SiteOperateur FROM Operateurs WHERE CodeOperateur=?', (codeOperateur,))
    infos = c.fetchone()
    logging.debug(f"Operator query result: {infos}")

    if not infos:
        logging.warning(f"Opérateur non trouvé pour le code : {codeOperateur}")
        return

    logging.info("")
    logging.info(f'Opérateur : {infos[0]}')
    logging.info(f'Code opérateur : {codeOperateur}')

    if infos[1]: # TypeOperateur
        logging.info(f'Type : {infos[1][0].upper() + infos[1][1:] if infos[1] else "N/A"}')
    if infos[2]: # MailOperateur
        logging.info(f'Courriel : {infos[2]}')
    if infos[3]: # SiteOperateur
        url = infos[3].lower()
        if not url.startswith('http'):
            url = 'http://' + url
        if '/' not in infos[3][8:]: # Check after "http://" or "https://"
            url += '/'
        logging.info(f'Site web : {url}')

def getGeographicNumberARCEP():
    logging.debug(f"Attempting geographic number lookup for: {tel}")
    # tel[1:6] is like "10560" for "010560xxxx"
    # DB stores PlageTel as integer, e.g. 10560
    plage_tel_query = int(tel[1:6])
    logging.debug(f"Querying PlagesNumerosGeographiques for PlageTel: {plage_tel_query} (derived from {tel[0:6]})")
    c.execute('SELECT CodeOperateur, CodeInsee FROM PlagesNumerosGeographiques WHERE PlageTel=?', (plage_tel_query,))
    infos = c.fetchone()
    logging.debug(f"Result for {plage_tel_query}: {infos}")

    if infos is None:
        logging.debug(f"No result for 5-digit prefix {plage_tel_query}. Trying 4-digit prefix.")
        # Try a shorter prefix if the 5-digit one failed (e.g. for numbers like 016xxxxxxx which might be in 4-digit blocks)
        plage_tel_query_4_digit = int(tel[1:5]) # e.g. 1056
        logging.debug(f"Querying PlagesNumerosGeographiques for 4-digit PlageTel: {plage_tel_query_4_digit} (derived from {tel[0:5]})")
        c.execute('SELECT CodeOperateur, CodeInsee FROM PlagesNumerosGeographiques WHERE PlageTel=? AND LENGTH(CAST(PlageTel AS TEXT)) = 4', (plage_tel_query_4_digit,))
        infos_4_digit = c.fetchone()
        logging.debug(f"Result for {plage_tel_query_4_digit}: {infos_4_digit}")
        if infos_4_digit:
            infos = infos_4_digit
            logging.info(f"(Information basée sur le bloc de 4 chiffres: {tel[0:5]})")
        else: # If both 5 and 4 digit block lookups fail
            logging.debug("4-digit geographic lookup also failed. Falling back to non-geographic lookup.")
            getNonGeographicNumberARCEP() # Fallback to non-geographic
            return

    # infos[0] is CodeOperateur, infos[1] is CodeInsee
    getInfosINSEE(infos[1])
    getInfosOperateur(infos[0])


def getNonGeographicNumberARCEP():
    logging.debug(f"Attempting non-geographic number lookup for: {tel}")
    # Search for the longest matching prefix
    # Original xrange went from min(6, len(tel)) down to 0 (exclusive for end)
    # For a 10-digit number, this means prefixes of length 6, 5, 4, 3, 2, 1
    # Example: tel = "0612345678"
    # Prefixes checked: "061234", "06123", "0612", "061", "06", "0"
    # The PlageTel in PlagesNumeros is TEXT and can be like "06", "0800", etc.

    infos = None
    # Max prefix length in DB for non-geo is usually 2 to 4 (e.g. 06, 07, 0800, 0805, 09)
    # Let's try prefixes from length 4 down to 2.
    # For example, for 0800123456, try 0800, then 080, then 08.
    # For 0612345678, try 0612, 061, 06.
    possible_prefixes = [tel[:l] for l in range(min(len(tel), 6), 1, -1)] # From 6 down to 2
    logging.debug(f"Possible non-geo prefixes to check: {possible_prefixes}")

    for prefix_to_check in possible_prefixes:
        logging.debug(f"Querying PlagesNumeros for PlageTel: {prefix_to_check}")
        c.execute('SELECT CodeOperateur FROM PlagesNumeros WHERE PlageTel=?', (prefix_to_check,))
        infos = c.fetchone()
        logging.debug(f"Result for prefix {prefix_to_check}: {infos}")
        if infos is not None:
            logging.info(f"(Information basée sur le préfixe: {prefix_to_check})")
            break

    if infos is None:
        erreur('Numéro inconnu dans la base ARCEP.', exit_code=1) # Original script exits with 1 for unknown
    else:
        # infos[0] is CodeOperateur
        getInfosOperateur(infos[0])


# Fonctions pour les numéros spéciaux

def getSurtax():
    logging.debug(f"Checking surtax for number: {tel}")
    # This function contains hardcoded tariff information from ~2013.
    # It should ideally be updated from a structured ARCEP source if available.
    # For now, porting as-is with a warning.
    logging.warning("Les informations de surtaxe peuvent être obsolètes.")
    newRates = (date.today().year >= 2015) # This logic itself is now very old.
    logging.debug(f"Using newRates logic: {newRates} (based on current year vs 2015)")

    if len(tel) == 10:
        type08 = int(tel[2:4])
        logging.debug(f"Surtax check for 10-digit number, type08 (tel[2:4]): {type08}")

        if type08 >= 90 : # Example: 0890, 0891, 0892, 0893, 0897, 0899
            logging.info('Dénomination commerciale : Numéro Audiotel (Service à valeur ajoutée)')

        # Free numbers (Numéros Verts)
        if (newRates and type08 <= 5) or (type08 in (1, 2, 3, 4, 8)): # 0800-0805, 0808
             logging.info('Dénomination commerciale : Numéro Vert')
             logging.info('Prix : Entièrement gratuit (depuis fixe et mobile)')
        elif type08 <= 9: # 0806-0809 (excluding 0808 already covered)
             logging.info('Dénomination commerciale : Numéro Vert (Service gratuit + prix appel)')
             logging.info('Surtaxe : Non (coût d\'un appel vers un fixe)')

        # Grey numbers (Numéros Gris) - cost of a local call or specific tariff
        elif 10 <= type08 <= 19 or type08 == 84: # 081x, 082x (partially, see below), 0884
            # This was complex and changed significantly in 2015.
            # Modern 081x, 082x are typically "Service gratuit + prix appel" or have a per-minute/per-call charge.
            # The old categories "Azur" and "Indigo" are less relevant.
            logging.info('Dénomination commerciale : Numéro Gris (Banalisé)')
            logging.info('Surtaxe : variable, généralement coût d\'un appel local ou tarif spécifique par minute/appel.')
            # Old details:
            # logging.debug('Dénomination commerciale : Numéro Azur')
            # logging.debug('Surtaxe par appel : 0,078 €')
            # logging.debug('Surtaxe par minute : 0,014 € en heures creuses, ou 0,028 € en heures pleines')

        elif type08 == 20 or type08 == 21 or type08 == 25 or type08 == 26: # 0820, 0821, 0825, 0826
            logging.info('Dénomination commerciale : Numéro Gris (Banalisé)')
            logging.info('Surtaxe : variable, tarif spécifique par minute/appel.')
            # Old details:
            # logging.debug('Dénomination commerciale : Numéro Indigo')
            # if type08 == 20 or type08 == 21:
            #     logging.debug('Surtaxe maximum par appel : 0,112 €')
            #     logging.debug('Surtaxe maximum par minute après 56s : 0,118 €')
            # elif type08 == 25 or type08 == 26:
            #     logging.debug('Surtaxe par appel : 0,112 €')
            #     logging.debug('Surtaxe par minute après 45s : 0,15 €')

        elif type08 == 36: # Example: 0836 - Often Minitel or specific services
            logging.info('Prix : Variable (services divers, potentiellement élevé)')

        elif 40 <= type08 <= 43: # 0840-0843
            logging.info("Utilisation : Numéro technique destiné à l'acheminement des communications, " +
                  "ne doit pas être appelé directement (cf décision n°2006-0452)")

        elif 50 <= type08 <= 58: # 085x
            logging.info('Prix : Variable (accès VPN RPC)')

        elif 60 <= type08 <= 68: # 086x
            logging.info('Prix : Variable (accès RTC)')

        # Surcharged numbers (Numéros Magenta / Audiotel) - 089x
        # Modern 089x have specific per-call or per-minute charges.
        elif type08 >= 90: # Already covered at the top, but more specific old details were here
            logging.info('Surtaxe : Tarif fortement surtaxé, variable.')
            # Old details for 0890:
            # logging.debug('Surtaxe : Dépend du numéro et du FAI.')
            # logging.debug('          - Orange : Maximum de 0,112 € toutes les 45s')
            # if tel[4:6] == '64':
            #     logging.debug('          - SFR : 0,112 € toutes les 60s')
            # elif tel[4:6] == '71':
            #     logging.debug('          - SFR : 0,15 € par minute, paliers de 45s')
            # else:
            #     logging.debug('          - SFR : Inconnu')
            # logging.debug('          - Free : 0,11 € puis, après 45s, 0,15€ par minute')

        else: # Other 08xx not covered by specific old rules
            logging.info("Type de numéro 08xx non précisément tarifé par cet outil (données obsolètes).")

    elif tel == '1044': # Example specific number
        logging.info('Surtaxe par appel : 0,078 €') # Likely outdated
        logging.info('Surtaxe par minute : 0,014 € en heures creuses, ou 0,028 € en heures pleines')

    elif tel.startswith('10') and len(tel) == 4: # Numbers like 10XY (e.g. 1013, 1023)
        logging.info('Surtaxe : Non (généralement, services opérateurs)')


def getSurtax118():
    logging.debug(f"Checking surtax for 118xxx number: {tel}")
    # This function contains hardcoded tariff information from ~2013 for 118xxx numbers.
    # It should ideally be updated. Porting as-is with a warning.
    logging.warning("Les informations de surtaxe 118 peuvent être obsolètes.")
    surtax118 = {
          0: '1,46 € / appel, 1,46 € les 2 premières min puis 0,90 € à partir 3ème min',
		  6: '1,35 €/appel + 0,34 €/min',
		  7: '1,35 €/appel + 0,34 €/min',
		  8: '1,46 €/appel + 0,45 €/min',
		218: '0,90 €/appel + 0,90 €/min',
		222: '0,90 €/appel + 0,90 €/min',
		318: '0,90 €/appel + 0,90 €/min',
		612: '1,01 €/appel',
		700: '3 €/appel',
		710: '0 €', # Free
		711: '0,79 €/appel + 0,225 €/min',
		712: '1,35 €/appel + 0,225 €/min',
		713: '0 €', # Free
		777: '1,20 €/appel (SFR uniquement)', # Operator specific, may have changed
		888: '1,12 €/appel + 1,11 €/min',
	}

    try:
        suffix = int(tel[3:])
        logging.debug(f"118xxx suffix: {suffix}")
        if suffix in surtax118:
            logging.info('Surtaxe : ' + surtax118[suffix])
        else:
            erreur(f'Numéro 118 inconnu ou tarif non listé pour suffixe {suffix}.')
    except ValueError:
        erreur(f'Suffixe du numéro 118 invalide: {tel[3:]}.')


def getSpecial():
    logging.debug(f"Checking special number (short code): {tel}")
    special_numbers_map = { # Renamed from 'special' to avoid conflict
		15: 'SAMU',
		17: 'Police et gendarmerie',
		18: 'Pompiers',
		110: 'Collecte de dons', # May vary
		112: "Numéro d'urgence européen",
		115: 'SAMU social',
		116000: 'SOS enfants disparus'
	}
    try:
        num_int = int(tel)
        if num_int in special_numbers_map:
            logging.info('Type : Spécial (Urgence/Service Public)')
            logging.info('Fonction : ' + special_numbers_map[num_int])
        else:
            erreur(f'Numéro spécial {num_int} inconnu.')
    except ValueError:
        erreur(f'Numéro spécial invalide: {tel}.')

# Fonctions pour Annu.com - REMOVED
# def getAnnu(): ...

# Fonctions pour OVH Telecom - REMOVED
# def getOVH(): ...

# Déterminer le type de numéro de téléphone
section('Informations ARCEP')
logging.info('Numéro : ' + tel)

if tel.startswith('0') and len(tel) == 10: # EZABPQMCDU
    logging.info('Type : EZABPQMCDU (Numéro géographique ou mobile/VoIP)')
    is_EZABPQMCDU = True
elif len(tel) == 4 and tel.startswith('3'): # 3BPQ (e.g. 3000, 3949)
    logging.info('Type : Numéro court 3BPQ')
    is_special = True # Treat as special for surtax check, may or may not be surtaxed
    getSurtax() # Some 3xxx numbers can be surtaxed
elif (len(tel) == 4 and tel.startswith('10')) or \
     (len(tel) == 6 and tel.startswith('118')): # 10XY, 118XYZ
    if tel.startswith('118'):
        logging.info('Type : 118XYZ (Service de renseignements)')
        getSurtax118()
    else: # 10XY
        logging.info(f'Type : Numéro court {tel[:2]}XY (Service opérateur/spécial)')
        getSurtax() # Check for potential surtax for 10XY
    is_special = True
elif len(tel) in [2, 3] and tel.isdigit(): # Short codes like 15, 17, 18, 112, 115
    is_special = True
    getSpecial()
else:
    # Could be other international, malformed, or new types not covered
    logging.warning("Type de numéro non formellement identifié par les règles de base (longueur/préfixe).")
    # Attempt ARCEP lookup anyway
    # This logic seems to duplicate the main if/else block for ARCEP lookup.
    # The original script has this fallback. Let's keep it but log it.
    logging.debug("Attempting ARCEP lookup as a fallback for unidentified number type.")
    if tel.startswith('0') and len(tel) == 10 : # Enforce 10-digit length for standard numbers
         if tel[1] in '12345':
             logging.debug("Fallback: Treating as geographic due to 01-05 prefix.")
             getGeographicNumberARCEP()
         else:
             logging.debug("Fallback: Treating as non-geographic.")
             getNonGeographicNumberARCEP()
    else:
        # If it's not a 10-digit '0' number, and not special, then it's an error.
        erreur('Numéro non reconnu ou format invalide pour recherche ARCEP.')


# Afficher les informations de l'ARCEP (if not already done by specific type logic)
if not is_special: # If it's a standard EZABPQMCDU
    logging.debug("Number is not special, proceeding with standard ARCEP lookup.")
    if is_EZABPQMCDU and tel[1] in '12345': # Geographic 01-05
        logging.debug("Standard lookup: Geographic (01-05).")
        getGeographicNumberARCEP()
    elif is_EZABPQMCDU: # Other 0Z (06,07,08,09)
        logging.debug("Standard lookup: Non-geographic (06,07,08,09).")
        getNonGeographicNumberARCEP()
        if tel[1] == '8': # Surtax check for 08 numbers
            logging.debug("Number starts with 08, checking surtax.")
            getSurtax()
    # else:
    #    logging.debug("Standard lookup: Not EZABPQMCDU or already handled by fallback in type determination.")
    #    This 'else' branch seems unlikely to be hit if the initial type determination logic is correct.
    #    If it's not special and not EZABPQMCDU, it should have errored out or been handled by the fallback.

# Afficher les informations d'Annu.com - REMOVED
# if useAnnu and is_EZABPQMCDU and tel[1] != '8':
# 	getAnnu()

# Afficher les informations d'OVH - REMOVED
# if useOVH and is_EZABPQMCDU and '1' <= tel[1] <= '5':
# 	getOVH()

# Fermer la connexion à la base de données de l'ARCEP
logging.info("") # For spacing before closing message if any
logging.debug("Closing SQLite database connection.")
conn.close()
