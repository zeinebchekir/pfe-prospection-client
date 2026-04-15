"""
datagouv_cleaner.py — Cleans data extracted from data.gouv.fr.

FastAPI port: operates on plain dicts instead of Django ORM objects.

dataGouv records have NO leads — they are company enrichment data only.
Note: dataGouv does not provide phone numbers, so clean_phone is not called here.
"""

from .base_cleaner import BaseCleaner
from .utils import (
    normalize_text,
    normalize_ville,
    clean_siren,
    clean_code_postal,
    clean_date,
    clean_ca,
    guard,
)

try:
    from mapping_naf import naf_codes
except ImportError:
    naf_codes = {}

try:
    from mapping import effectifs_insee, categories_entreprise, formes_juridiques
except ImportError:
    effectifs_insee = categories_entreprise = formes_juridiques = {}


# ──────────────────────────────────────────────────────────────
#  NAF TRANSLATION
# ──────────────────────────────────────────────────────────────

def translate_secteur_activite(raw: str | None) -> str | None:
    """
    Translates a raw NAF Rev.2 code into its human-readable label.

    Lookup strategy (in order):
      1. Exact match on the raw value as-is           e.g. '62.01Z'
      2. Uppercased                                   e.g. '62.01z' → '62.01Z'
      3. Without dot, uppercased                      e.g. '6201Z'
      4. With dot re-inserted (XXYYZ → XX.YYZ)       e.g. '6201Z' → '62.01Z'

    Returns:
      - The human label if found                      e.g. 'Programmation informatique'
      - The original raw code if no match found       (keeps data rather than losing it)
      - None if the input is None or empty
    """
    if not raw:
        return None

    raw = raw.strip()
    if not raw:
        return None

    # ── 1. Exact match ──
    label = naf_codes.get(raw)
    if label:
        return label

    # ── 2. Uppercased ──
    upper = raw.upper()
    label = naf_codes.get(upper)
    if label:
        return label

    # ── 3. Without dot ──
    no_dot = upper.replace(".", "")
    label = naf_codes.get(no_dot)
    if label:
        return label

    # ── 4. Re-insert dot: '6201Z' → '62.01Z'
    if len(no_dot) in (4, 5):
        dotted = no_dot[:2] + "." + no_dot[2:]
        label = naf_codes.get(dotted)
        if label:
            return label

    # ── No match — keep raw code as fallback ──
    return raw


# ──────────────────────────────────────────────────────────────
#  CLEANER
# ──────────────────────────────────────────────────────────────

class DataGouvCleaner(BaseCleaner):

    source_name = "dataGouv"

    def clean_entreprise(self, e: dict) -> dict | None:
        """
        Cleans a dataGouv entreprise dict. These records are rich with
        financial/legal data but carry a SIREN (not SIRET).
        """
        # ── 1. Nom (required) ──
        nom = normalize_text(guard(e.get("nom")))
        if not nom:
            return None
        e["nom"] = nom

        # ── 2. SIREN ──
        e["siren"] = clean_siren(e.get("siren"))
        if not e["siren"] and not nom:
            return None

        # ── 3. Secteur d'activité (NAF code → human label) ──
        raw_naf = guard(str(e["secteur_activite"]) if e.get("secteur_activite") else None)
        e["secteur_activite"] = translate_secteur_activite(raw_naf)

        # ── 4. Forme juridique (numeric code → label) ──
        raw_forme = guard(str(e["forme_juridique"]) if e.get("forme_juridique") else None)
        e["forme_juridique"] = (
            formes_juridiques.get(raw_forme, raw_forme) if raw_forme else None
        )

        # ── 5. Taille entreprise (INSEE code → label) ──
        raw_taille = guard(str(e["taille_entrep"]) if e.get("taille_entrep") else None)
        e["taille_entrep"] = (
            effectifs_insee.get(raw_taille, raw_taille) if raw_taille else None
        )

        # ── 6. Catégorie entreprise ──
        raw_cat = guard(e.get("categorie_entreprise"))
        e["categorie_entreprise"] = (
            categories_entreprise.get(raw_cat, raw_cat) if raw_cat else None
        )

        # ── 7. Nombre de locaux ──
        try:
            e["nb_locaux"] = int(e["nb_locaux"]) if e.get("nb_locaux") else None
        except (ValueError, TypeError):
            e["nb_locaux"] = None

        # ── 8. CA ──
        e["ca"] = clean_ca(e.get("ca"))

        # ── 9. Adresse ──
        e["ville"] = normalize_ville(guard(e.get("ville")))
        e["code_postal"] = clean_code_postal(e.get("code_postal"))
        e["pays"] = "France"

        # ── 10. Dates ──
        e["dateCreation"] = clean_date(
            str(e["dateCreation"]) if e.get("dateCreation") else None
        )
        e["dateDerniereModification"] = clean_date(
            str(e["dateDerniereModification"]) if e.get("dateDerniereModification") else None
        )

        # ── 11. Source ──
        e["sourceEntreprise"] = "dataGouv"

        return e

    def clean_lead(self, lead: dict) -> None:
        """dataGouv has no leads."""
        return None