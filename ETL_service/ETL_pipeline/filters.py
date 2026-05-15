"""
filters.py — Business-rule filters for the DataGouv ETL pipeline.

Two filters applied in sequence during the extract_datagouv task:

  1. NAF prefix filter   — keeps only companies whose activite_principale
                           starts with one of the allowed 2-digit NAF prefixes.

  2. Completeness filter — keeps only companies that have all four required
                           business fields filled in the extracted dict.

Usage (from dag_initial_load.py / extract_datagouv task):

    from filters import filter_by_naf_prefix, filter_by_completeness

Design notes:
  - NAF filter runs on the RAW API payload (field: activite_principale)
    because the cleaner later translates the code into a human label.
  - Completeness filter runs on the EXTRACTED dict produced by
    extract_data_from_datagouv() (field names: ca, categorie_entreprise,
    taille_entrep, region).
  - "region" is derived from code_postal (first 2 digits) because the
    DataGouv API /search endpoint does not expose a region field directly.
    A company is considered to have a usable region if its code_postal is
    a valid 5-digit French postal code (from which the département/région
    can be resolved).
"""

from __future__ import annotations

import re
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
#  ALLOWED NAF PREFIXES
#  These 2-digit section codes cover IT/digital, services, finance, consulting,
#  wholesale trade, hospitality, media, education and health — as per business
#  requirements.
# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_NAF_PREFIXES: frozenset[str] = frozenset({
    "46", "47",         # Commerce de gros / détail
    "55",               # Hébergement
    "59",               # Production cinéma, audiovisuel
    "61",               # Télécommunications
    "62",               # Programmation, conseil informatique ← core IT
    "63",               # Services d'information
    "64", "65", "66",   # Finance, assurance
    "69",               # Activités juridiques et comptables
    "71",               # Ingénierie, conseil technique
    "72",               # Recherche-développement
    "73",               # Publicité, études de marché
    "77",               # Location et crédit-bail
    "78",               # Activités liées à l'emploi
    "82",               # Activités de soutien aux entreprises
    "85",               # Enseignement
    "86",               # Activités pour la santé humaine
})

# ─────────────────────────────────────────────────────────────────────────────
#  NAF FILTER  (operates on raw API records)
# ─────────────────────────────────────────────────────────────────────────────

def _get_naf_prefix(naf_code: Optional[str]) -> Optional[str]:
    """
    Extracts the 2-digit numeric prefix from a NAF Rev.2 code.

    Handles all known formats:
      '62.01Z' → '62'
      '6201Z'  → '62'
      '62'     → '62'
      None / '' → None
    """
    if not naf_code or not isinstance(naf_code, str):
        return None
    # Strip whitespace, remove dots, take first 2 chars
    cleaned = naf_code.strip().replace(".", "")
    if len(cleaned) < 2:
        return None
    prefix = cleaned[:2]
    # Must be all digits to be a valid NAF prefix
    return prefix if prefix.isdigit() else None


def is_naf_allowed(naf_code: Optional[str]) -> bool:
    """
    Returns True if the NAF code starts with one of the allowed prefixes.
    Returns False for None, empty, or malformed codes (safe by default).
    """
    prefix = _get_naf_prefix(naf_code)
    if prefix is None:
        return False
    return prefix in ALLOWED_NAF_PREFIXES


def filter_by_naf_prefix(raw_records: list[dict]) -> tuple[list[dict], int]:
    """
    Filters a list of raw DataGouv API records, keeping only those whose
    'activite_principale' field starts with an allowed NAF prefix.

    Args:
        raw_records: list of raw dicts from the DataGouv API (pre-extraction)

    Returns:
        (kept_records, dropped_count)
    """
    kept = []
    dropped = 0
    for record in raw_records:
        naf = record.get("activite_principale")
        if is_naf_allowed(naf):
            kept.append(record)
        else:
            dropped += 1
    return kept, dropped


# ─────────────────────────────────────────────────────────────────────────────
#  COMPLETENESS FILTER  (operates on extracted dicts)
# ─────────────────────────────────────────────────────────────────────────────

# "region" is considered present when the company has a valid 5-digit French
# postal code (first 2 digits encode the département, which maps 1-to-1 to a
# région for mainland France and DROM-COM).
_POSTAL_CODE_RE = re.compile(r"^\d{5}$")

_COMPLETENESS_INVALID_SENTINELS = {
    "", "null", "none", "n/a", "na", "non spécifié",
    "non renseigné", "non trouvé", "inconnue", "inconnu",
}


def _is_filled(value) -> bool:
    """
    Returns True when a field is considered usable / filled.

    Rejects:
      - None
      - empty string / whitespace-only string
      - known invalid placeholder strings (case-insensitive)
      - empty list / empty dict
      - numeric 0 and negative numbers (for financial fields like CA)
    """
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return False
        if stripped.lower() in _COMPLETENESS_INVALID_SENTINELS:
            return False
        return True
    if isinstance(value, (int, float)):
        return value > 0  # 0 and negatives are treated as missing for CA
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True  # any other truthy type passes


def _has_usable_region(extracted: dict) -> bool:
    """
    'region' is considered present when code_postal is a valid 5-digit
    French postal code (integer or string).

    The DataGouv /search endpoint does not return an explicit region field.
    The département (first 2 digits of the postal code) is the reliable
    geographic anchor available post-extraction.
    """
    code_postal = extracted.get("code_postal")
    if code_postal is None:
        return False
    # code_postal may have already been cleaned to an int by the extractor
    raw = str(code_postal).strip().zfill(5)
    return bool(_POSTAL_CODE_RE.match(raw))


def is_complete(extracted: dict) -> tuple[bool, list[str]]:
    """
    Checks whether all required business fields are filled.

    Required fields (using extracted dict field names):
      - ca                   → chiffre_affaire in business language
      - categorie_entreprise → categorie_entreprise
      - taille_entrep        → taille_entreprise in business language
      - region               → derived from code_postal

    Returns:
        (passes: bool, missing_fields: list[str])
    """
    missing = []

    if not _is_filled(extracted.get("ca")):
        missing.append("ca (chiffre_affaire)")

    if not _is_filled(extracted.get("categorie_entreprise")):
        missing.append("categorie_entreprise")

    if not _is_filled(extracted.get("taille_entrep")):
        missing.append("taille_entrep (taille_entreprise)")

    if not _has_usable_region(extracted):
        missing.append("region (via code_postal)")

    return len(missing) == 0, missing


def filter_by_completeness(extracted_records: list[dict]) -> tuple[list[dict], int, list[dict]]:
    """
    Filters a list of extracted dicts, keeping only those where all four
    required business fields are present and usable.

    Args:
        extracted_records: list of dicts produced by extract_data_from_datagouv()

    Returns:
        (kept_records, dropped_count, drop_log)
        drop_log: list of {siren, missing_fields} for observability
    """
    kept = []
    dropped = 0
    drop_log = []

    for record in extracted_records:
        passes, missing = is_complete(record)
        if passes:
            kept.append(record)
        else:
            dropped += 1
            drop_log.append({
                "siren": record.get("siren", "unknown"),
                "nom": record.get("nom", ""),
                "missing_fields": missing,
            })

    return kept, dropped, drop_log
