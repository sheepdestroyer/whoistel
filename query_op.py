import sqlite3
DB_FILE = "whoistel.sqlite3"
phone_number_to_check = "0740756315"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

op_code = None
op_name = None
found_prefix_in_db = None

print(f"Querying for number: {phone_number_to_check}")

# Try prefixes from most specific (e.g., "0740756") down to least specific (e.g., "07")
# The PlageTel in PlagesNumeros is TEXT.
# Max length of EZABPQM in MAJNUM for non-geo can be up to 7 (e.g. "0800000")
# For a 10 digit number, it's unlikely the prefix in DB is longer than 7.
# whoistel.py tries from length 6. Let's match that for consistency, then go shorter.
# Max prefix length in MAJNUM.csv for EZABPQM seems to be 7 based on "0700000" example.
# Let's try from length 7 down to 2.
max_prefix_len_to_try = 7
for length in range(min(len(phone_number_to_check), max_prefix_len_to_try), 1, -1):
    prefix = phone_number_to_check[:length]
    # print(f"DEBUG: Trying prefix: {prefix}")
    cursor.execute("SELECT CodeOperateur FROM PlagesNumeros WHERE PlageTel = ?", (prefix,))
    result = cursor.fetchone()
    if result:
        op_code = result[0]
        found_prefix_in_db = prefix
        # print(f"DEBUG: Found op_code '{op_code}' for prefix '{prefix}' in PlagesNumeros")
        break

if op_code:
    cursor.execute("SELECT NomOperateur FROM Operateurs WHERE CodeOperateur = ?", (op_code,))
    op_result = cursor.fetchone()
    if op_result:
        op_name = op_result[0]
        print(f"Operator for most specific prefix '{found_prefix_in_db}': {op_name} (Code: {op_code})")
    else:
        print(f"Operator name not found for CodeOperateur '{op_code}' (from prefix '{found_prefix_in_db}')")
else:
    print(f"No operator code found in PlagesNumeros for prefixes derived from {phone_number_to_check}.")
    print("\nDEBUG: Sample of PlagesNumeros for '07%':")
    cursor.execute("SELECT PlageTel, CodeOperateur FROM PlagesNumeros WHERE PlageTel LIKE '07%' LIMIT 20")
    for row in cursor.fetchall():
        print(row)

conn.close()
