from .base_scraper import BaseScraper
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv
import time
from datetime import datetime
from datetime import date
import math
class DataGouvService(BaseScraper):
    def __init__(self):
        # On initialise avec le nom de la source
        super().__init__(nom_source="API_GOUV_RECHERCHE")
        
        # L'URL officielle de l'API de recherche
        self.base_url = "https://recherche-entreprises.api.gouv.fr/search"
        self.per_page = 25
        self.delai = 2.0
   
    def _paginer(self, params: dict) -> list[dict]:
        resultats   = []
        page        = 1
        max_retries = 3

        while True and page <= 40: 
            params_page = {**params, "page": page, "per_page": self.per_page}
            data        = None

            # Retry par page — gère le rate limit sur chaque page
            for tentative in range(max_retries):
                data = self.fetch_data(self.base_url, params=params_page)
                if data is not None:
                    break
                print(f"[{self.nom_source}] ⚠️  Retry page {page} ({tentative+1}/{max_retries})")
                time.sleep(10 * (tentative + 1))
            
            if data is None:
                print(f"[{self.nom_source}] ⚠️  Échec page {page} — arrêt pagination")
                break

            # Premier appel — on récupère le total
            if page == 1:
                total = data.get("total_results", 0)
                if total == 0:
                    print(f"[{self.nom_source}] ℹ️  Aucun résultat trouvé")
                    break
                total_pages = math.ceil(total / self.per_page)
                print(f"[{self.nom_source}] 📊 {total} résultats — {total_pages} pages")

            items = data.get("results", [])
           
            print(items[0].get("siren"))
            print(items[-1].get("siren"))

            if not items:
                break

            resultats += items
            print(resultats[0].get("siren"))
            print(resultats[-1].get("siren"))
            print(f"[{self.nom_source}] 📄 page {page} — {len(resultats)}/{total}")

            if len(resultats) >= total:
                break

            page += 1
            time.sleep(self.delai)
        print("final",resultats[0].get("siren"),resultats[-1].get("siren"))    
        return resultats
    def source_scraping(self,filtre:list[dict]) -> list[dict]:
        """
        C'est ici que tu décides QUI cibler.
        Chaque stratégie = un appel à _paginer() avec des params différents.
        """
        tous_les_resultats = []

        for params in filtre:
            resultats = self._paginer(params)
            tous_les_resultats += resultats
            time.sleep(self.delai)

        
        print(f"[{self.nom_source}] 📊 Total : {len(tous_les_resultats)} entreprises")
        return tous_les_resultats


    def data_extraction(self, avis_brut):
        """
        Extract data from Recherche entreprise api.
        """
        # 1. Extraction initiale
        clean_data = extract_data_from_datagouv(avis_brut)
        
        # 2. Fallback SIRET : si SIRET manquant mais SIREN présent
        # On tente de récupérer le SIRET du siège via l'API établissements
        for record in clean_data:
            if not record.get("siret") and record.get("siren"):
                siren = record.get("siren")
                fallback_siret = self.fetch_siege_siret(siren)
                if fallback_siret:
                    record["siret"] = fallback_siret
                    print(f"[{self.nom_source}] 💡 Fallback SIRET réussi pour {siren} -> {fallback_siret}")

        return clean_data   

    def fetch_siege_siret(self, siren: str) -> str | None:
        """
        Interroge l'API établissements pour trouver le SIRET du siège social.
        URL: https://recherche-entreprises.api.gouv.fr/etablissements?siren=XXX
        """
        url = "https://recherche-entreprises.api.gouv.fr/etablissements"
        params = {"siren": siren}
        try:
            data = self.fetch_data(url, params=params)
            if data and data.get("results"):
                # On cherche l'établissement qui est le siège
                for etablissement in data.get("results", []):
                    if etablissement.get("est_siege"):
                        return etablissement.get("siret")
        except Exception as e:
            print(f"[{self.nom_source}] ⚠️  Erreur fallback SIRET pour {siren}: {e}")
        return None
    
    def get_data_from_siren(self, items: list[dict]) -> list[dict]:
        clean_data = []  
        success_sirens = [] # 🟢 Liste pour les SIREN trouvés
        failed_sirens = []  # 🔴 Liste pour les SIREN en échec / introuvables

        for i, item in enumerate(items):
            siren = item.get("siren")
            if not siren:
                continue

            # On interroge l'API pour ce SIREN spécifique
            data = self.fetch_data(
                self.base_url,
                params={"q": siren, "per_page": 1}
            )

            # On vérifie si data existe ET si la clé "results" contient quelque chose
            if data and data.get("results"):
                resultats = data.get("results")
                clean_data += resultats
                success_sirens.append(siren) # ✅ Succès !
            else:
                failed_sirens.append(siren)  # ❌ Échec (API vide ou erreur)

            # Log de progression tous les 50 éléments
            if (i + 1) % 50 == 0:
                print(f"[{self.nom_source}] ⚙️  {i+1}/{len(items)} enrichis")

            time.sleep(self.delai)
        
        # --- 📊 AFFICHAGE DU BILAN FINAL ---
        print("\n" + "=" * 50)
        print(f"[{self.nom_source}] 📊 BILAN DE L'ENRICHISSEMENT")
        print(f"✅ {len(success_sirens)} Succès : {', '.join(success_sirens)}")
        
        if failed_sirens:
            print(f"❌ {len(failed_sirens)} Échecs : {', '.join(failed_sirens)}")
        print("=" * 50 + "\n")

        return clean_data 
        # ← toujours défini    