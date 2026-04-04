"""
utils.py — Shared cleaning helpers
Used by all cleaner modules. Pure Python functions — no framework dependency.
"""

import re
import unicodedata
from datetime import datetime


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
    Cleans a city name: strips, uppercases.
    Example: '  paris 12ème  ' → 'PARIS 12ÈME'
    """
    if not value or not isinstance(value, str):
        return None
    value = unicodedata.normalize("NFC", value.strip())
    value = re.sub(r"\s+", " ", value)
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
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None