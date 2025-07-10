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

# Interpréter les arguments
# Keep --no-annu and --no-ovh for now to avoid breaking existing calls, but they will do nothing.
# Or, better, remove them to simplify. Let's remove.
args_to_parse = argv[1:]
parsed_args = {}

for i, arg_val in enumerate(args_to_parse):
    clean_arg = arg_val.replace('-', '').replace(' ', '').replace('.', '')
    clean_arg = clean_arg.replace('+33(0)', '0').replace('+330', '0').replace('+33', '0')
    clean_arg = clean_arg.strip().lower()

    if clean_arg.isdigit() and tel is None:
        tel = clean_arg
    # elif clean_arg == 'noannu': # Removed
    #     useAnnu = False
    # elif clean_arg == 'noovh': # Removed
    #     useOVH = False
    elif clean_arg in ['noannu', 'noovh']:
        print(f"Warning: Argument {arg_val} is deprecated and will be ignored.")
    elif tel is None and i == 0 : # Assume first non-option arg is the number
        tel = clean_arg
    elif tel is not None : # If number is set, other args might be problematic
        print(f"Argument non reconnu ou numéro déjà défini: {arg_val}")
        tel = None # Invalidate to show usage
        break
    else: # If tel is still None and it's not a digit or known old option
        tel = None # Invalidate to show usage
        break


# Message d'utilisation
if tel is None:
    print(f'Utilisation : {argv[0]} <numéro de téléphone français>')
    exit(1)

# Fonctions d'information

def section(text):
    print()
    print('+-' + '-' * len(text) + '-+')
    print('| ' + text + ' |')
    print('+-' + '-' * len(text) + '-+')
    print()

def erreur(text):
    print('[Erreur] ' + text)
    print()
    exit(1)

# Se connecter à la base de données de l'ARCEP en local

if not exists('whoistel.sqlite3'):
    erreur('Vous devez générer le fichier "whoistel.sqlite3" avec generatedb.py.')

conn = sqlite3.connect('whoistel.sqlite3')
c = conn.cursor()

# Fonctions pour l'ARCEP

def getInfosINSEE(codeINSEE):
    if codeINSEE == 0 or codeINSEE is None:
        print("\nInformations de commune non disponibles pour ce bloc (CodeInsee manquant).")
        return

    c.execute('SELECT NomCommune, CodePostal, NomDepartement FROM Communes WHERE CodeInsee=?', (codeINSEE,))
    infos = c.fetchone()

    if infos:
        print()
        print(f'Commune : {infos[0]}')
        print(f'Département : {infos[2]}')
        print(f'Code postal : {str(infos[1]).zfill(5)}')
        print(f'Code INSEE : {str(codeINSEE).zfill(5)}')
    else:
        print(f"\nAucune information trouvée pour le Code INSEE : {str(codeINSEE).zfill(5)}")


def getInfosOperateur(codeOperateur):
    c.execute('SELECT NomOperateur, TypeOperateur, MailOperateur, SiteOperateur FROM Operateurs WHERE CodeOperateur=?', (codeOperateur,))
    infos = c.fetchone()

    if not infos:
        print(f"\nOpérateur non trouvé pour le code : {codeOperateur}")
        return

    print()
    print(f'Opérateur : {infos[0]}')
    print(f'Code opérateur : {codeOperateur}')

    if infos[1]: # TypeOperateur
        print(f'Type : {infos[1][0].upper() + infos[1][1:] if infos[1] else "N/A"}')
    if infos[2]: # MailOperateur
        print(f'Courriel : {infos[2]}')
    if infos[3]: # SiteOperateur
        url = infos[3].lower()
        if not url.startswith('http'):
            url = 'http://' + url
        if '/' not in infos[3][8:]: # Check after "http://" or "https://"
            url += '/'
        print(f'Site web : {url}')

def getGeographicNumberARCEP():
    # tel[1:6] is like "10560" for "010560xxxx"
    # DB stores PlageTel as integer, e.g. 10560
    plage_tel_query = int(tel[1:6])
    c.execute('SELECT CodeOperateur, CodeInsee FROM PlagesNumerosGeographiques WHERE PlageTel=?', (plage_tel_query,))
    infos = c.fetchone()

    if infos is None:
        # Try a shorter prefix if the 5-digit one failed (e.g. for numbers like 016xxxxxxx which might be in 4-digit blocks)
        plage_tel_query_4_digit = int(tel[1:5]) # e.g. 1056
        c.execute('SELECT CodeOperateur, CodeInsee FROM PlagesNumerosGeographiques WHERE PlageTel=? AND LENGTH(CAST(PlageTel AS TEXT)) = 4', (plage_tel_query_4_digit,))
        infos_4_digit = c.fetchone()
        if infos_4_digit:
            infos = infos_4_digit
            print(f"(Information basée sur le bloc de 4 chiffres: {tel[0:5]})")
        else: # If both 5 and 4 digit block lookups fail
            getNonGeographicNumberARCEP() # Fallback to non-geographic
            return

    # infos[0] is CodeOperateur, infos[1] is CodeInsee
    getInfosINSEE(infos[1])
    getInfosOperateur(infos[0])


def getNonGeographicNumberARCEP():
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

    for prefix_to_check in possible_prefixes:
        c.execute('SELECT CodeOperateur FROM PlagesNumeros WHERE PlageTel=?', (prefix_to_check,))
        infos = c.fetchone()
        if infos is not None:
            print(f"(Information basée sur le préfixe: {prefix_to_check})")
            break

    if infos is None:
        erreur('Numéro inconnu dans la base ARCEP.')
    else:
        # infos[0] is CodeOperateur
        getInfosOperateur(infos[0])


# Fonctions pour les numéros spéciaux

def getSurtax():
    # This function contains hardcoded tariff information from ~2013.
    # It should ideally be updated from a structured ARCEP source if available.
    # For now, porting as-is with a warning.
    print("\n[AVERTISSEMENT] Les informations de surtaxe peuvent être obsolètes.")
    newRates = (date.today().year >= 2015) # This logic itself is now very old.

    if len(tel) == 10:
        type08 = int(tel[2:4])

        if type08 >= 90 : # Example: 0890, 0891, 0892, 0893, 0897, 0899
            print('Dénomination commerciale : Numéro Audiotel (Service à valeur ajoutée)')

        # Free numbers (Numéros Verts)
        if (newRates and type08 <= 5) or (type08 in (1, 2, 3, 4, 8)): # 0800-0805, 0808
             print('Dénomination commerciale : Numéro Vert')
             print('Prix : Entièrement gratuit (depuis fixe et mobile)')
        elif type08 <= 9: # 0806-0809 (excluding 0808 already covered)
             print('Dénomination commerciale : Numéro Vert (Service gratuit + prix appel)')
             print('Surtaxe : Non (coût d\'un appel vers un fixe)')

        # Grey numbers (Numéros Gris) - cost of a local call or specific tariff
        elif 10 <= type08 <= 19 or type08 == 84: # 081x, 082x (partially, see below), 0884
            # This was complex and changed significantly in 2015.
            # Modern 081x, 082x are typically "Service gratuit + prix appel" or have a per-minute/per-call charge.
            # The old categories "Azur" and "Indigo" are less relevant.
            print('Dénomination commerciale : Numéro Gris (Banalisé)')
            print('Surtaxe : variable, généralement coût d\'un appel local ou tarif spécifique par minute/appel.')
            # Old details:
            # print('Dénomination commerciale : Numéro Azur')
            # print('Surtaxe par appel : 0,078 €')
            # print('Surtaxe par minute : 0,014 € en heures creuses, ou 0,028 € en heures pleines')

        elif type08 == 20 or type08 == 21 or type08 == 25 or type08 == 26: # 0820, 0821, 0825, 0826
            print('Dénomination commerciale : Numéro Gris (Banalisé)')
            print('Surtaxe : variable, tarif spécifique par minute/appel.')
            # Old details:
            # print('Dénomination commerciale : Numéro Indigo')
            # if type08 == 20 or type08 == 21:
            #     print('Surtaxe maximum par appel : 0,112 €')
            #     print('Surtaxe maximum par minute après 56s : 0,118 €')
            # elif type08 == 25 or type08 == 26:
            #     print('Surtaxe par appel : 0,112 €')
            #     print('Surtaxe par minute après 45s : 0,15 €')

        elif type08 == 36: # Example: 0836 - Often Minitel or specific services
            print('Prix : Variable (services divers, potentiellement élevé)')

        elif 40 <= type08 <= 43: # 0840-0843
            print("Utilisation : Numéro technique destiné à l'acheminement des communications, " +
                  "ne doit pas être appelé directement (cf décision n°2006-0452)")

        elif 50 <= type08 <= 58: # 085x
            print('Prix : Variable (accès VPN RPC)')

        elif 60 <= type08 <= 68: # 086x
            print('Prix : Variable (accès RTC)')

        # Surcharged numbers (Numéros Magenta / Audiotel) - 089x
        # Modern 089x have specific per-call or per-minute charges.
        elif type08 >= 90: # Already covered at the top, but more specific old details were here
            print('Surtaxe : Tarif fortement surtaxé, variable.')
            # Old details for 0890:
            # print('Surtaxe : Dépend du numéro et du FAI.')
            # print('          - Orange : Maximum de 0,112 € toutes les 45s')
            # if tel[4:6] == '64':
            #     print('          - SFR : 0,112 € toutes les 60s')
            # elif tel[4:6] == '71':
            #     print('          - SFR : 0,15 € par minute, paliers de 45s')
            # else:
            #     print('          - SFR : Inconnu')
            # print('          - Free : 0,11 € puis, après 45s, 0,15€ par minute')

        else: # Other 08xx not covered by specific old rules
            print("Type de numéro 08xx non précisément tarifé par cet outil (données obsolètes).")

    elif tel == '1044': # Example specific number
        print('Surtaxe par appel : 0,078 €') # Likely outdated
        print('Surtaxe par minute : 0,014 € en heures creuses, ou 0,028 € en heures pleines')

    elif tel.startswith('10') and len(tel) == 4: # Numbers like 10XY (e.g. 1013, 1023)
        print('Surtaxe : Non (généralement, services opérateurs)')


def getSurtax118():
    # This function contains hardcoded tariff information from ~2013 for 118xxx numbers.
    # It should ideally be updated. Porting as-is with a warning.
    print("\n[AVERTISSEMENT] Les informations de surtaxe 118 peuvent être obsolètes.")
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
        if suffix in surtax118:
            print('Surtaxe : ' + surtax118[suffix])
        else:
            erreur('Numéro 118 inconnu ou tarif non listé.')
    except ValueError:
        erreur('Suffixe du numéro 118 invalide.')


def getSpecial():
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
            print('Type : Spécial (Urgence/Service Public)')
            print('Fonction : ' + special_numbers_map[num_int])
        else:
            erreur('Numéro spécial inconnu.')
    except ValueError:
        erreur('Numéro spécial invalide.')

# Fonctions pour Annu.com - REMOVED
# def getAnnu(): ...

# Fonctions pour OVH Telecom - REMOVED
# def getOVH(): ...

# Déterminer le type de numéro de téléphone
section('Informations ARCEP')
print('Numéro : ' + tel)

if tel.startswith('0') and len(tel) == 10: # EZABPQMCDU
    print('Type : EZABPQMCDU (Numéro géographique ou mobile/VoIP)')
    is_EZABPQMCDU = True
elif len(tel) == 4 and tel.startswith('3'): # 3BPQ (e.g. 3000, 3949)
    print('Type : Numéro court 3BPQ')
    is_special = True # Treat as special for surtax check, may or may not be surtaxed
    getSurtax() # Some 3xxx numbers can be surtaxed
elif (len(tel) == 4 and tel.startswith('10')) or \
     (len(tel) == 6 and tel.startswith('118')): # 10XY, 118XYZ
    if tel.startswith('118'):
        print('Type : 118XYZ (Service de renseignements)')
        getSurtax118()
    else: # 10XY
        print(f'Type : Numéro court {tel[:2]}XY (Service opérateur/spécial)')
        getSurtax() # Check for potential surtax for 10XY
    is_special = True
elif len(tel) in [2, 3] and tel.isdigit(): # Short codes like 15, 17, 18, 112, 115
    is_special = True
    getSpecial()
else:
    # Could be other international, malformed, or new types not covered
    print("Type de numéro non formellement identifié par les règles de base (longueur/préfixe).")
    # Attempt ARCEP lookup anyway
    if tel.startswith('0') and len(tel) > 6 : # Likely a standard French number
         if tel[1] in '12345':
             getGeographicNumberARCEP()
         else:
             getNonGeographicNumberARCEP()
    else:
        erreur('Numéro non reconnu ou format invalide pour recherche ARCEP.')


# Afficher les informations de l'ARCEP (if not already done by specific type logic)
if not is_special: # If it's a standard EZABPQMCDU
    if is_EZABPQMCDU and tel[1] in '12345': # Geographic 01-05
        getGeographicNumberARCEP()
    elif is_EZABPQMCDU: # Other 0Z (06,07,08,09)
        getNonGeographicNumberARCEP()
        if tel[1] == '8': # Surtax check for 08 numbers
            getSurtax()
    # else: already handled by the more generic fallback in type determination

# Afficher les informations d'Annu.com - REMOVED
# if useAnnu and is_EZABPQMCDU and tel[1] != '8':
# 	getAnnu()

# Afficher les informations d'OVH - REMOVED
# if useOVH and is_EZABPQMCDU and '1' <= tel[1] <= '5':
# 	getOVH()

# Fermer la connexion à la base de données de l'ARCEP
print()
conn.close()
