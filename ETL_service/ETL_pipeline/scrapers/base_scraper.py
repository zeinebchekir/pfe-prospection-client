import requests
from requests.exceptions import RequestException
from abc import ABC, abstractmethod
import pandas as pd
import time
from urllib.parse import unquote  
class BaseScraper(ABC):
    """
    Classe parente pour tous les scrapers.
    Gère : HTTP, pipeline commun, hooks à implémenter par chaque source.
    """

    def __init__(self, nom_source="Inconnu"):
        self.nom_source = nom_source
        self.headers = {
            "User-Agent": "Bot-PFE-DataExtraction/1.0 (Projet Universitaire)",
            "Accept": "application/json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    # ------------------------------------------------------------------ #
    #  COUCHE HTTP — commune, ne pas surcharger                           #
    # ------------------------------------------------------------------ #

    def fetch_data(self, url, params=None, method="GET", json_data=None, retries=4, skip_encoding=False):
        """Appel HTTP sécurisé avec retry automatique sur 429."""
        print(f"[{self.nom_source}] 📡 {method} → {url}")

        for tentative in range(retries):  # ← la boucle qui définit 'tentative'
            try:
                if skip_encoding:
                    # ✅ Pour Sirene — envoie l'URL brute sans ré-encodage
                    from requests import Request
                    req  = Request(method="GET", url=url, headers=dict(self.session.headers))
                    prep = self.session.prepare_request(req)
                    prep.url = url  # ← écrase l'URL encodée par l'URL brute
                    response = self.session.send(prep)
                
                elif method.upper() == "GET":
                    # comportement existant — inchangé
                    response = self.session.get(url, params=params)
                    
                elif method.upper() == "POST":
                    response = self.session.post(url, json=json_data)
                
                else:
                    raise ValueError(f"Méthode HTTP non gérée : {method}")

                url_finale_decodee = unquote(response.url)
                print(f"[{self.nom_source}] 🔗 URL exécutée (décodée) : {url_finale_decodee}")
                # ──────────────────────────────────────────────────────────
                response.raise_for_status()
                return response.json()

            except RequestException as e:
                status = e.response.status_code if (hasattr(e, 'response') and e.response is not None) else None

                if status == 429:
                    attente = 10 * (tentative + 1)  # 10s, 20s, 30s, 40s
                    print(f"[{self.nom_source}] ⏳ Rate limit, attente {attente}s "
                        f"(tentative {tentative + 1}/{retries})")
                    time.sleep(attente)
                    # on continue la boucle pour retry
                else:
                    print(f"[{self.nom_source}] ❌ Erreur réseau : {e}")
                    return None  # erreur non-429 → pas de retry

            except ValueError as e:
                print(f"[{self.nom_source}] ❌ Réponse non-JSON : {e}")
                return None

        print(f"[{self.nom_source}] ❌ Échec après {retries} tentatives.")
        return None
    # ------------------------------------------------------------------ #
    #  HOOKS ABSTRAITS — chaque source DOIT les implémenter              #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def source_scraping(self) -> list[dict]:
        """
        Appelle fetch_data() avec les bons params (URL, filtres, pagination).
        Retourne une liste de dicts JSON bruts.
        """
        raise NotImplementedError

    

    @abstractmethod
    def data_extraction(self, avis_brut) -> tuple:
        """
        Délègue à l'extractor correspondant.
        Retourne (instance_entreprise, instance_lead) NON sauvegardés.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    #  HOOK OPTIONNEL — surcharger seulement si la source en a besoin    #
    # ------------------------------------------------------------------ #

    def necessite_nlp(self, avis_brut) -> bool:
        """Retourne True si un champ texte libre nécessite le NLP."""
        return False

    def appliquer_nlp(self, avis_brut, entreprise, lead) -> tuple:
        """Enrichit entreprise/lead via NLP. Surcharger si necessite_nlp=True."""
        return entreprise, lead

    # ------------------------------------------------------------------ #
    #  PIPELINE COMMUN — squelette fixe, ne pas surcharger               #
    # ------------------------------------------------------------------ #
    
 

 