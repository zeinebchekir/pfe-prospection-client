import time
from datetime import datetime
from .base_scraper import BaseScraper
from .dataGouv import DataGouvService
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv

class SireneService(BaseScraper):

    def __init__(self, token: str):
        super().__init__(nom_source="SIRENE_INSEE")
        self.source=DataGouvService()
        self.base_url = "https://api.insee.fr/api-sirene/3.11/siren"
        self.nombre_par_page = 200   # max autorisé par Sirene
        self.delai = 0.5             # Sirene est plus restrictif que DataGouv
        
        # Token INSEE obligatoire
        self.session.headers.update({
            "X-INSEE-Api-Key-Integration": f"{token}",
            "Accept": "application/json;charset=utf-8;qs=1",
        })

    # ------------------------------------------------------------------ #
    #  SCRAPING — récupère les SIREN modifiés depuis date_sync           #
    # ------------------------------------------------------------------ #

    def source_scraping(self,date_sync) -> list[dict]:

       
        date_str = date_sync.strftime("%Y-%m-%dT%H:%M:%S")

        print(f"[{self.nom_source}] 🗓️  Sync depuis : {date_str}")

        # Filtre Sirene natif par date de modification
        filtre = f"dateDernierTraitementUniteLegale:[{date_str} TO *]"

        
        results= self._paginer(filtre)
        
        data=self.source.get_data_from_siren(results)
        return data

    def _paginer(self, filtre: str) -> list[dict]:
        resultats = []
        curseur = "*"   # curseur initial obligatoire
        total = None

        while True:
            # Curseur encodé manuellement pour éviter les problèmes d'encodage requests
            url = (
                f"{self.base_url}"
                f"?q={filtre}"
                f"&nombre={self.nombre_par_page}"
                f"&curseur={curseur}"
                f"&champs=siren,dateDernierTraitementUniteLegale,"
                f"denominationUniteLegale,etatAdministratifUniteLegale"
            )

            data = self.fetch_data(url)

            if data is None:
                print(f"[{self.nom_source}] ⚠️  Erreur, arrêt pagination.")
                break

            items = data.get("unitesLegales", [])
            if not items:
                print(f"[{self.nom_source}] ✅ Plus de données.")
                break

            resultats += items

            if total is None:
                total = data.get("header", {}).get("total", 0)
                print(f"[{self.nom_source}] 📊 {total} SIREN modifiés détectés")

            print(f"[{self.nom_source}] 📄 {len(resultats)}/{total} récupérés")

            # Condition d'arrêt 1 — tout récupéré
            if len(resultats) >= total:
                print(f"[{self.nom_source}] ✅ Pagination complète.")
                break

            # Condition d'arrêt 2 — pas de curseur suivant
            curseur = data.get("header", {}).get("curseurSuivant")
            if not curseur:
                print(f"[{self.nom_source}] ✅ Fin de pagination.")
                break

            time.sleep(self.delai)

        return resultats

    #  EXTRACTION — retourne juste les SIREN pour le cronjob             #
    # ------------------------------------------------------------------ #

    def data_extraction(self, avis_brut):
        """
        Extract data from Rechetche entreprise api.
        """
        # 2. On utilise tes fonctions d'extraction existantes
        # Note : Assure-toi que get_global_information prend le payload en paramètre
        clean_data = extract_data_from_datagouv(avis_brut)
        
        return clean_data

  

      