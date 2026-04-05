"""
boamp_cleaner.py — Cleans data extracted from BOAMP.

FastAPI port: operates on plain dicts instead of Django ORM objects.

Input shape per record:
  {"entreprise": {...}, "lead": {...}}
"""

from .base_cleaner import BaseCleaner
from .utils import (
    normalize_text,
    normalize_ville,
    clean_siret,
    clean_email,
    clean_phone,
    clean_code_postal,
    clean_date,
    clean_url,
    guard,
)

try:
    from mapping import map_juridique, map_secteurs
except ImportError:
    map_juridique = {}
    map_secteurs = {}


class BoampCleaner(BaseCleaner):

    source_name = "BOAMP"

    def clean_entreprise(self, e: dict) -> dict | None:
        """
        Cleans a BOAMP entreprise dict in-place and returns it.
        Returns None if the record is completely unusable.
        """
        # ── 1. Nom (required) ──
        nom = normalize_text(guard(e.get("nom")))
        if not nom:
            return None
        e["nom"] = nom

        # ── 2. SIRET ──
        e["siret"] = clean_siret(e.get("siret"))

        # ── 3. Email ──
        e["adresse_email"] = clean_email(e.get("adresse_email"))

        # ── 4. Ville ──
        e["ville"] = normalize_ville(guard(e.get("ville")))

        # ── 5. Code postal ──
        e["code_postal"] = clean_code_postal(e.get("code_postal"))

        # ── 6. Secteur ──
        raw_secteur = guard(e.get("secteur_activite"))
        e["secteur_activite"] = (
            map_secteurs.get(raw_secteur.lower(), raw_secteur) if raw_secteur else None
        )

        # ── 7. Forme juridique ──
        raw_forme = guard(e.get("forme_juridique"))
        e["forme_juridique"] = (
            map_juridique.get(raw_forme.lower(), raw_forme) if raw_forme else None
        )

        # ── 8. Pays ──
        e["pays"] = "France"

        # ── 9. Source ──
        e["sourceEntreprise"] = "BOAMP"

        # ── 10. Téléphone ──
        e["telephone"] = clean_phone(e.get("telephone"))

        return e

    def clean_lead(self, lead: dict) -> dict | None:
        """
        Cleans a BOAMP lead dict.
        """
        # ── 1. Besoin (required) ──
        besoin = normalize_text(guard(lead.get("besoin")))
        if not besoin:
            return None
        lead["besoin"] = besoin

        # ── 2. Date limite ──
        lead["date_limite"] = clean_date(guard(lead.get("date_limite")))

        # ── 3. Titulaire ──
        lead["titulaire"] = guard(normalize_text(lead.get("titulaire")))

        # ── 4. Nature ──
        lead["nature"] = guard(lead.get("nature"))

        # ── 5. Lien offre ──
        lead["lienOffre"] = clean_url(guard(lead.get("lienOffre")))

        # ── 6. Status ──
        if not lead.get("status_lead"):
            lead["status_lead"] = "NOUVEAU"

        # ── 7. Info complémentaire ──
        lead["info_complementaire"] = guard(lead.get("info_complementaire")) or ""

        return lead