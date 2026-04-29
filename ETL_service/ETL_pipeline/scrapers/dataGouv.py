from .base_scraper import BaseScraper
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv
import time
import math
from datetime import datetime
from datetime import date

# ─────────────────────────────────────────────────────────────────────────────
#  NAF filter — 3 groups, each with its own page cap.
#
#  The DataGouv API rejects activite_principale with too many codes (>~5).
#  Each entry carries a private _max_pages key that _paginer() will respect.
#  Precise NAF prefix enforcement is done DOWNSTREAM by filters.py.
# ─────────────────────────────────────────────────────────────────────────────

_NAF_SECTION_FILTER: list[dict] = [
      # 55 — Hébergement (Hôtels, etc.)
    {
        "activite_principale": "55.10Z,55.20Z,55.30Z,55.90Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 59 — Production cinématographique, audiovisuelle
    {
        "activite_principale": "59.11C,59.12Z,59.13A,59.14Z,59.20Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 61 — Télécommunications
    {
        "activite_principale": "61.10Z,61.20Z,61.30Z,61.90Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 63 — Services d'information (Hébergement web, portails)
    {
        "activite_principale": "63.11Z,63.12Z,63.91Z,63.99Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 64 — Activités des services financiers (Banques)
    {
        "activite_principale": "64.19Z,64.20Z,64.91Z,64.92Z,64.99Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 65 — Assurance
    {
        "activite_principale": "65.11Z,65.12Z,65.20Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 66 — Activités auxiliaires de services financiers et d'assurance
    {
        "activite_principale": "66.11Z,66.19Z,66.21Z,66.29Z,66.30Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 69 — Activités juridiques et comptables
    {
        "activite_principale": "69.10Z,69.20Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 71 — Activités d'architecture et d'ingénierie
    {
        "activite_principale": "71.11Z,71.12A,71.12B,71.20A,71.20B",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 72 — Recherche-développement scientifique
    {
        "activite_principale": "72.11Z,72.19Z,72.20Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 73 — Publicité et études de marché
    {
        "activite_principale": "73.11Z,73.12Z,73.20Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 77 — Location et crédit-bail
    {
        "activite_principale": "77.11A,77.33Z,77.34Z,77.40Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 78 — Activités liées à l'emploi (Intérim, recrutement)
    {
        "activite_principale": "78.10Z,78.20Z,78.30Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 82 — Activités de soutien aux entreprises (Centres d'appel, etc.)
    {
        "activite_principale": "82.11Z,82.20Z,82.30Z,82.91Z,82.99Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 85 — Enseignement (Formation continue, etc.)
    {
        "activite_principale": "85.59A,85.59B,85.60Z,85.41Z,85.42Z",
        "etat_administratif": "A",
        "_max_pages": 10,
    },
    # 86 — Activités pour la santé humaine
    {
        "activite_principale": "86.21Z,86.22B,86.90A,86.90B,86.90C",
        "etat_administratif": "A",
        "_max_pages": 10,
    },

]


class DataGouvService(BaseScraper):
    def __init__(self):
        # On initialise avec le nom de la source
        super().__init__(nom_source="API_GOUV_RECHERCHE")

        # L'URL officielle de l'API de recherche
        self.base_url = "https://recherche-entreprises.api.gouv.fr/search"
        self.per_page = 25
        self.delai = 2.0

        # Filtre par defaut : 3 groupes NAF avec un plafond de pages par groupe.
        # L'API rejette activite_principale avec trop de codes (>~5).
        # La precision sectorielle fine est assuree en aval par filters.py.
        self.default_filtre = _NAF_SECTION_FILTER

    def _paginer(self, params: dict, max_pages: int = 80) -> list[dict]:
        resultats = []
        page = 1
        max_retries = 3
        total = 0
        total_pages = 0

        while page <= max_pages:
            params_page = {**params, "page": page, "per_page": self.per_page}
            data = None

            # Retry par page — gere le rate limit sur chaque page
            for tentative in range(max_retries):
                data = self.fetch_data(self.base_url, params=params_page)
                if data is not None:
                    break
                print(f"[{self.nom_source}] Retry page {page} ({tentative + 1}/{max_retries})")
                time.sleep(10 * (tentative + 1))

            if data is None:
                print(f"[{self.nom_source}] Echec page {page} - arret pagination")
                break

            # Premier appel — on recupere le total
            if page == 1:
                total = data.get("total_results", 0)
                if total == 0:
                    print(f"[{self.nom_source}] Aucun resultat trouve")
                    break
                total_pages = math.ceil(total / self.per_page)
                print(f"[{self.nom_source}] {total} resultats - {total_pages} pages (plafond={max_pages})")

            items = data.get("results", [])

            if not items:
                print(f"[{self.nom_source}] Aucune donnee sur la page {page}")
                break

            print(items[0].get("siren"))
            print(items[-1].get("siren"))

            resultats += items

            print(resultats[0].get("siren"))
            print(resultats[-1].get("siren"))
            print(f"[{self.nom_source}] page {page}/{min(total_pages, max_pages)} - {len(resultats)}/{total}")

            if len(resultats) >= total:
                break

            if total_pages and page >= min(total_pages, max_pages):
                break

            page += 1
            time.sleep(self.delai)

        if resultats:
            print("final", resultats[0].get("siren"), resultats[-1].get("siren"))
        else:
            print("final", "aucun resultat")

        return resultats

    def source_scraping(self, filtre: list[dict] | None = None) -> list[dict]:
        """
        Iterates over filter groups. Each group may carry a private '_max_pages'
        key to cap pagination independently. That key is stripped before the
        params dict is sent to the API.
        """
        tous_les_resultats = []

        if not filtre:
            filtre = self.default_filtre

        for entry in filtre:
            # Extract the per-group page cap (default 80 if not specified)
            max_pages = entry.pop("_max_pages", 80) if isinstance(entry, dict) else 80
            # Work on a copy so the original filter dict is not mutated
            params = {k: v for k, v in entry.items() if not k.startswith("_")}

            label = params.get("activite_principale", "?")[:30]
            print(f"[{self.nom_source}] Groupe NAF '{label}...' — plafond {max_pages} pages")

            resultats = self._paginer(params, max_pages=max_pages)
            tous_les_resultats += resultats
            time.sleep(self.delai)

        print(f"[{self.nom_source}] Total : {len(tous_les_resultats)} entreprises")
        return tous_les_resultats

    def data_extraction(self, avis_brut):
        """
        Extract data from Recherche entreprise api.
        """
        # 1. Extraction initiale
        clean_data = extract_data_from_datagouv(avis_brut)

        # 2. Fallback SIRET : si SIRET manquant mais SIREN present
        # On tente de recuperer le SIRET du siege via l'API etablissements
        for record in clean_data:
            if not record.get("siret") and record.get("siren"):
                siren = record.get("siren")
                fallback_siret = self.fetch_siege_siret(siren)
                if fallback_siret:
                    record["siret"] = fallback_siret
                    print(f"[{self.nom_source}] Fallback SIRET reussi pour {siren} -> {fallback_siret}")

        return clean_data

    def fetch_siege_siret(self, siren: str) -> str | None:
        """
        Interroge l'API etablissements pour trouver le SIRET du siege social.
        URL: https://recherche-entreprises.api.gouv.fr/etablissements?siren=XXX
        """
        url = "https://recherche-entreprises.api.gouv.fr/etablissements"
        params = {"siren": siren}
        try:
            data = self.fetch_data(url, params=params)
            if data and data.get("results"):
                # On cherche l'etablissement qui est le siege
                for etablissement in data.get("results", []):
                    if etablissement.get("est_siege"):
                        return etablissement.get("siret")
        except Exception as e:
            print(f"[{self.nom_source}] Erreur fallback SIRET pour {siren}: {e}")
        return None

    def get_data_from_siren(self, items: list[dict]) -> list[dict]:
        clean_data = []
        success_sirens = []  # Liste pour les SIREN trouves
        failed_sirens = []   # Liste pour les SIREN en echec / introuvables

        for i, item in enumerate(items):
            siren = item.get("siren")
            if not siren:
                continue

            # On interroge l'API pour ce SIREN specifique
            data = self.fetch_data(
                self.base_url,
                params={"q": siren, "per_page": 1}
            )

            # On verifie si data existe ET si la cle "results" contient quelque chose
            if data and data.get("results"):
                resultats = data.get("results")
                clean_data += resultats
                success_sirens.append(siren)
            else:
                failed_sirens.append(siren)

            # Log de progression tous les 50 elements
            if (i + 1) % 50 == 0:
                print(f"[{self.nom_source}] {i + 1}/{len(items)} enrichis")

            time.sleep(self.delai)

        # Bilan final
        print("\n" + "=" * 50)
        print(f"[{self.nom_source}] BILAN DE L'ENRICHISSEMENT")
        print(f"Succes : {len(success_sirens)}")
        if success_sirens:
            print(", ".join(success_sirens))

        if failed_sirens:
            print(f"Echecs : {len(failed_sirens)}")
            print(", ".join(failed_sirens))
        print("=" * 50 + "\n")

        return clean_data