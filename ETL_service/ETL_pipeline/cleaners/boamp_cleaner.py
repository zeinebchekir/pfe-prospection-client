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
        e["num_tel"] = clean_phone(e.get("num_tel"))

        return e

    def clean_lead(self, lead: dict) -> dict | None:
        """
        Cleans a BOAMP lead dict.
        """
        # ── 6. Status ──
        if not lead.get("status_lead"):
            lead["status_lead"] = "NOUVEAU"

        lead["data_from_boamp"]={
            "num_tel":lead.get("num_tel"),
            "besoin":normalize_text(guard(lead.get("besoin"))),
            "date_limite":clean_date(guard(lead.get("date_limite"))),
            "titulaire":guard(normalize_text(lead.get("titulaire"))),
            "nature":guard(lead.get("nature")),
            "lienOffre":clean_url(guard(lead.get("lienOffre"))),
            "info_complementaire":guard(lead.get("info_complementaire")) or "",
        }
        # ── 7. Info complémentaire ──
        print("lead cleaneeeeeeeeeeeeeeeeeeeeeeeeed",lead)
        return lead