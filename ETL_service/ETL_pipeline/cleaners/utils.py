"""
utils.py — Shared cleaning helpers
Used by all cleaner modules. Pure Python functions — no framework dependency.
"""

import re
import unicodedata
from datetime import datetime
from db.models import Entreprise

# ─────────────────────────────────────────────
# TEXT NORMALIZATION
# ─────────────────────────────────────────────

def normalize_text(value: str | None) -> str | None:
    """
    Strips whitespace, normalizes unicode, and title-cases a name.
    Example: '  mairie de  PARIS  ' → 'Mairie De Paris'
    """
    if not value or not isinstance(value, str):
        return None
    value = unicodedata.normalize("NFC", value.strip())
    value = re.sub(r"\s+", " ", value)
    return value.strip() or None


def normalize_ville(value: str | None) -> str | None:
    """
    Cleans a city name: strips, uppercases and removes embedded postal codes.

    Handles all known BOAMP / DataGouv formats:
      - '92400 COURBEVOIE'    → 'COURBEVOIE'  (leading CP)
      - 'COURBEVOIE 92400'    → 'COURBEVOIE'  (trailing CP)
      - '92400'               → None           (CP seul, pas de nom)
      - 'Saint-Denis (93)'    → 'SAINT-DENIS'  (CP entre parenthèses)
      - 'PARIS 12ÈME'         → 'PARIS 12ÈME'  (inchangé — pas de CP)
    """
    if not value or not isinstance(value, str):
        return None
    value = unicodedata.normalize("NFC", value.strip())
    # Remove postal code in parentheses e.g. 'Saint-Denis (93)' → 'Saint-Denis'
    value = re.sub(r"\s*\(\d{2,5}\)", "", value)
    # Remove leading 5-digit postal code: '92400 COURBEVOIE' → 'COURBEVOIE'
    value = re.sub(r"^\d{5}\s+", "", value)
    # Remove trailing 5-digit postal code: 'COURBEVOIE 92400' → 'COURBEVOIE'
    value = re.sub(r"\s+\d{5}$", "", value)
    # Collapse multiple spaces
    value = re.sub(r"\s+", " ", value).strip()
    # If what remains is only digits (just a postal code, no city name) → discard
    if re.fullmatch(r"\d+", value):
        return None
    return value.upper().strip() or None


# ─────────────────────────────────────────────
# SIRET / SIREN VALIDATION
# ─────────────────────────────────────────────

def clean_siret(value) -> str | None:
    if not value:
        return None
    raw = re.sub(r"\D", "", str(value))
    return raw if len(raw) == 14 else None


def clean_siren(value) -> str | None:
    if not value:
        return None
    raw = re.sub(r"\D", "", str(value))
    if len(raw) == 9:
        return raw
    if len(raw) == 14:
        return raw[:9]
    return None


# ─────────────────────────────────────────────
# PHONE NORMALIZATION
# ─────────────────────────────────────────────

def clean_phone(value: str | None) -> str | None:
    """
    Normalizes a French phone number to E.164 format (+33XXXXXXXXX).

    Accepted inputs:
      - 0612345678        → +33612345678
      - 06 12 34 56 78   → +33612345678
      - +33 6 12 34 56 78 → +33612345678
      - 0033612345678    → +33612345678

    Returns None if the number is missing, too short, or clearly invalid.
    """
    if not value or not isinstance(value, str):
        return None

    # Strip all non-digit characters except leading +
    digits = re.sub(r"[^\d+]", "", value.strip())
    digits = re.sub(r"\s", "", digits)

    # Remove all separators and work with digits only
    raw = re.sub(r"\D", "", digits)

    # Already in international format: +33XXXXXXXXX → strip the +
    if value.strip().startswith("+33"):
        if len(raw) == 11 and raw.startswith("33"):
            return f"+{raw}"
        return None

    # 0033XXXXXXXXX
    if raw.startswith("0033"):
        raw = raw[4:]        # drop 0033
        if len(raw) == 9:
            return f"+33{raw}"
        return None

    # French local format: 0XXXXXXXXX (10 digits)
    if raw.startswith("0") and len(raw) == 10:
        return f"+33{raw[1:]}"  # replace leading 0 with +33

    # Already a 9-digit national number without leading 0
    if len(raw) == 9 and raw[0] in "67891":
        return f"+33{raw}"

    return None


# ─────────────────────────────────────────────
# EMAIL VALIDATION
# ─────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")

def clean_email(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    value = value.strip().lower()
    return value if _EMAIL_RE.match(value) else None


# ─────────────────────────────────────────────
# CODE POSTAL VALIDATION
# ─────────────────────────────────────────────

def clean_code_postal(value) -> int | None:
    if value is None:
        return None
    raw = re.sub(r"\D", "", str(value))
    if len(raw) == 5:
        try:
            cp = int(raw)
            if 1000 <= cp <= 99999:
                return cp
        except ValueError:
            pass
    return None


# ─────────────────────────────────────────────
# DATE NORMALIZATION
# ─────────────────────────────────────────────

_DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
]

def clean_date(value) -> str | None:
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if value.lower() in ("non spécifié", "n/a", ""):
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


# ─────────────────────────────────────────────
# GENERIC FIELD GUARDS
# ─────────────────────────────────────────────

_EMPTY_SENTINELS = {
    "non spécifié", "non spécifiée", "non spécifie",
    "n/a", "na", "none", "null", "", "non renseigné",
    "non trouvé", "non trouvée", "inconnue", "inconnu"
}

def guard(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    stripped = value.strip().lower()
    if stripped in _EMPTY_SENTINELS:
        return None
    return value.strip()


def clean_url(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    return value if value.lower().startswith(("http://", "https://")) else None


def clean_ca(value) -> float | None:
    """
    Converts a CA value to float. Returns None if:
    - value is None or unparseable
    - value is 0 or negative (unknown/invalid, stored as NULL not 0.0)
    """
    if value is None:
        return None
    try:
        ca = float(value)
        return ca if ca > 0 else None  # 0.0 and negatives → NULL
    except (ValueError, TypeError):
        return None

def _calculer_taux_completude_entreprise(obj: dict) -> float:
    """
    Taux simple = champs renseignés / total champs attendus × 100
    Fonctionne sur un dict (sorti du cleaner), pas un ORM Entreprise.
    """
    CHAMPS_DIRECTS = [
        "siren", "siret", "nom",
        "ville", "code_postal",
        "num_tel", "adresse_email",
        "secteur_activite", "forme_juridique", "ca",
        "taille_entrep", "categorie_entreprise",
        "dateCreation", "dirigeants", "nb_locaux"
    ]

    CHAMPS_BOAMP = [
        "besoin", "date_limite", "lienOffre","nature", "num_tel",
        "adresse_email", "info_complementaire","valeurMarche","lienOffre"
    ]

    total      = 0
    renseignes = 0

    # ✅ .get() sur le dict
    for champ in CHAMPS_DIRECTS:
        total += 1
        if _champ_est_renseigne(obj.get(champ)):
            renseignes += 1
    
    # Sous-champs BOAMP seulement si source BOAMP
    info_boamp = obj.get("data_from_boamp") or {}
    if info_boamp:
        for champ in CHAMPS_BOAMP:
            total += 1
            if _champ_est_renseigne(info_boamp.get(champ)):
                renseignes += 1

    return round(renseignes / total * 100, 2) if total > 0 else 0.0

def _champ_est_renseigne(valeur) -> bool:
    """
    Retourne True si la valeur est considérée comme renseignée.
    Gère les cas : None, string vide, liste vide, dict vide, JSON vide.
    """
    if valeur is None:
        return False
    if isinstance(valeur, str) and valeur.strip() == "":
        return False
    if isinstance(valeur, (list, dict)) and len(valeur) == 0:
        return False
    return True    