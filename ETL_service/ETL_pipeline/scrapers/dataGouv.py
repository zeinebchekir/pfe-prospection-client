from .base_scraper import BaseScraper
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv
import time
from datetime import datetime
from datetime import date

class DataGouvService(BaseScraper):
    def __init__(self):
        # On initialise avec le nom de la source
        super().__init__(nom_source="API_GOUV_RECHERCHE")
        
        # L'URL officielle de l'API de recherche
        self.base_url = "https://recherche-entreprises.api.gouv.fr/search"
        self.per_page = 25
        self.delai = 1
    def _construire_filtres(self) -> list[dict]:
        """
        Retourne une liste de params — un par requête indépendante.
        Modifie uniquement cette méthode selon ton besoin.
        """

        # ── Option A : aucun filtre, tout récupérer ──────────────────────
        # return [{"etat_administratif": "A"}]
        # ⚠️  Des millions de résultats — max_pages obligatoire

        # ── Option B : par secteur NAF ────────────────────────────────────
        # codes_naf = ["62.01Z", "71.12B", "43.21A"]
        # return [
        #     {"activite_principale": code, "etat_administratif": "A"}
        #     for code in codes_naf
        # ]

        # ── Option C : par mot-clé (situation actuelle) ───────────────────
        # secteurs = ["informatique", "travaux", "conseil"]
        # return [
        #     {"q": secteur, "etat_administratif": "A"}
        #     for secteur in secteurs
        # ]

        # ── Option D : combinaison région + activité ──────────────────────
        # return [
        #     {"q": "informatique", "region": "11", "etat_administratif": "A"},
        #     {"q": "travaux",      "region": "93", "etat_administratif": "A"},
        # ]

        # ── Par défaut : aucun filtre ─────────────────────────────────────
        
        return [{
            "etat_administratif": "A",
            "activite_principale": ["62.01Z","62.02A","62.02B","63.11Z"]
            }]
    
    def _paginer(self, params: dict) -> list[dict]:
        """
        Parcourt les pages pour n'importe quels params donnés.
        S'arrête si : page vide, total atteint, max_pages, ou erreur.
        """
        resultats = []
        page = 1
        total_pages=0
        
        params_page = {**params, "page": page, "per_page": self.per_page}

        data = self.fetch_data(self.base_url, params=params_page)

        if data is None:
            print(f"[{self.nom_source}] ⚠️  Erreur page {page}, arrêt.")
            return []
        total = data.get("total_results", 0)
        total_pages=total/self.per_page 
        while page <= total_pages:
            items = data.get("results", [])
            if not items:
                break

            resultats += items

            print(f"[{self.nom_source}] 📄 page {page} — {len(resultats)}/{total}")

            if len(resultats) >= total:
                break

            page += 1
            time.sleep(self.delai)

        return resultats

    def source_scraping(self) -> list[dict]:
        """
        C'est ici que tu décides QUI cibler.
        Chaque stratégie = un appel à _paginer() avec des params différents.
        """
        tous_les_resultats = []

        for params in self._construire_filtres():
            resultats = self._paginer(params)
            tous_les_resultats += resultats
            time.sleep(self.delai)


        print(f"[{self.nom_source}] 📊 Total : {len(tous_les_resultats)} entreprises")
        return tous_les_resultats


    def data_extraction(self, avis_brut):
        """
        Extract data from Rechetche entreprise api.
        """
        # 2. On utilise tes fonctions d'extraction existantes
        # Note : Assure-toi que get_global_information prend le payload en paramètre
        clean_data = extract_data_from_datagouv(avis_brut)
        
        return clean_data   

    
    def get_data_from_siren(self, items: list[dict]) -> list[dict]:
        clean_data = []  # ← initialisé avant la boucle

        for i, item in enumerate(items[:10]):
            siren = item.get("siren")
            if not siren:
                continue

            data = self.fetch_data(
                self.base_url,
                params={"q": siren, "per_page": 1}
            )

            if data:
                resultats = data.get("results", [])
                clean_data+=resultats
            if (i + 1) % 50 == 0:
                print(f"[{self.nom_source}] ⚙️  {i+1}/{len(items)} enrichis")

            time.sleep(self.delai)
        
        return clean_data  # ← toujours défini