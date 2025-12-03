# Data Sources for Whoistel

This project uses open data from ARCEP and other sources to provide information about French phone numbers.

## Primary Sources

### ARCEP (Autorité de régulation des communications électroniques)
Data is downloaded from [data.gouv.fr](https://www.data.gouv.fr) and [Arcep Open Data](https://data.arcep.fr).

*   **Ressources en numérotation (MAJNUM.csv)**
    *   **Source:** [data.gouv.fr - Ressources en numérotation](https://www.data.gouv.fr/fr/datasets/ressources-en-numerotation-telephonique/)
    *   **Content:** Allocations of phone number blocks (`EZABPQM`) to operators.
    *   **Usage:** Used to identify the operator and type (Geo/Non-Geo) of a number.
    *   **Known Issues:** Some mobile ranges (e.g., `0740`) appear to be missing from the public dataset, leading to "Unknown" results for valid numbers in these ranges.

*   **Identifiants des opérateurs (identifiants_ce.csv)**
    *   **Source:** [data.gouv.fr - Liste des opérateurs de communications électroniques](https://www.data.gouv.fr/fr/datasets/liste-des-operateurs-de-communications-electroniques/)
    *   **Content:** Mapping between Operator Codes (`CodeOperateur`) and names/details.

### INSEE / Geographic Data
*   **Code INSEE and Communes (insee.csv)**
    *   **Source:** Currently downloaded from `http://www.galichon.com/codesgeo/data/insee.zip`.
    *   **Content:** Mapping of INSEE codes to Commune names and Departments.
    *   **Usage:** Used to provide location details for Geographic numbers.

## Potential Additional Sources (Research Findings)

The following areas were investigated for potential integration but no suitable **Open Data** sources were found.

### Subscriber Identification (Reverse Directory / "Annuaire Inversé")
*   **Status:** Not available as Open Data.
*   **Reason:** Subscriber data (name, address) is personal data protected by GDPR (RGPD).
*   **Alternatives:**
    *   **PagesJaunes / PagesBlanches:** Offers a web-based lookup service but no free public API.
    *   **Commercial APIs:** Services like API Data Store offer this data for a fee.
    *   **Sirene (Businesses):** The official Sirene database (Open Data) allows searching by Siren/Siret or Name, but does not provide a reliable "Search by Phone Number" feature for reverse lookup.

### Spam and Reputation
*   **Status:** No free Open Data API available.
*   **Reason:** Spam lists are often community-maintained (closed DB) or commercial value-added services.
*   **Official Channels:**
    *   **33700:** The official French platform for reporting spam (SMS/Voice). It is a reporting mechanism, not a lookup API.
    *   **Bloctel:** Do-not-call list for consumers. Not a public lookup API.
*   **Commercial/Community APIs:** Services like Tellows, Dois-je répondre, or Twilio Lookup exist but require API keys and/or subscriptions.

### SVA (Service à Valeur Ajoutée)
*   **Source:** [Infos SVA](https://www.infosva.org/)
*   **Content:** Directory of Surtaxed Numbers (08xx, 3xxx, 118xxx).
*   **Usage:** Can be used manually to find the "Editeur" (Service Provider) of a specific premium number. No public API found.

## Limitations

*   **Location Mapping:** The direct mapping between Number Prefixes (`EZABPQM`) and ZNE/INSEE codes is currently not available in the open data files used. As a result, the location for geographic numbers is estimated at the **Region** level (based on `01`-`05` prefix) unless a specific link can be re-established. The `CodeInsee` field in `PlagesNumerosGeographiques` is currently populated with `0`.
*   **Missing Ranges:** As noted above, some allocated ranges are not present in `MAJNUM.csv`.
