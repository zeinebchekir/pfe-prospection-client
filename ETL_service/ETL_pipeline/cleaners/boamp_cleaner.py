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
    clean_siren,
    clean_ca
)

try:
    from .dataGouv_cleaner import translate_secteur_activite
except ImportError:
    def translate_secteur_activite(raw): return raw

try:
    from mapping import effectifs_insee, categories_entreprise, formes_juridiques
except ImportError:
    effectifs_insee = categories_entreprise = formes_juridiques = {}


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

        # ── 2. SIRET & SIREN ──
        e["siret"] = clean_siret(e.get("siret"))
        e["siren"] = clean_siren(e.get("siren")) or clean_siren(e.get("siret"))

        # ── 3. Email ──
        e["adresse_email"] = clean_email(e.get("adresse_email"))

        # ── 4. Ville ──
        e["ville"] = normalize_ville(guard(e.get("ville")))

        # ── 5. Code postal ──
        e["code_postal"] = clean_code_postal(e.get("code_postal"))

        # ── 6. Secteur d'activité (Logic from DataGouv) ──
        raw_naf = guard(str(e["secteur_activite"]) if e.get("secteur_activite") else None)
        e["secteur_activite"] = translate_secteur_activite(raw_naf)

        # ── 7. Forme juridique (Logic from DataGouv) ──
        raw_forme = guard(str(e["forme_juridique"]) if e.get("forme_juridique") else None)
        e["forme_juridique"] = (
            formes_juridiques.get(raw_forme, raw_forme) if raw_forme else None
        )

        # ── Nouveaux champs enrichis via DataGouv ──
        # Taille entreprise
        raw_taille = guard(str(e.get("taille_entrep")) if e.get("taille_entrep") else None)
        e["taille_entrep"] = (
            effectifs_insee.get(raw_taille, raw_taille) if raw_taille else None
        )
        
        # Catégorie entreprise
        raw_cat = guard(e.get("categorie_entreprise"))
        e["categorie_entreprise"] = (
            categories_entreprise.get(raw_cat, raw_cat) if raw_cat else None
        )
        
        # Nombre de locaux
        try:
            e["nb_locaux"] = int(e["nb_locaux"]) if e.get("nb_locaux") else None
        except (ValueError, TypeError):
            e["nb_locaux"] = None
            
        # CA
        e["ca"] = clean_ca(e.get("ca"))
        
        # Dates Création & MAJ
        e["dateCreation"] = clean_date(
            str(e["dateCreation"]) if e.get("dateCreation") else None
        )
        e["dateDerniereModification"] = clean_date(
            str(e["dateMAJ"] or e.get("dateDerniereModification")) if e.get("dateMAJ") or e.get("dateDerniereModification") else None
        )
        
        # Les dirigeants sont passés intacts car prétraités dans extract_data_from_datagouv
        
        # ── 8. Pays ──
        e["pays"] = "France"

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
            "adresse_email":clean_email(lead.get("adresse_email")),
            "valeurMarche":float(lead.get("valeurMarche")) if lead.get("valeurMarche") else None,
        }
        # ── 7. Info complémentaire ──
        return lead