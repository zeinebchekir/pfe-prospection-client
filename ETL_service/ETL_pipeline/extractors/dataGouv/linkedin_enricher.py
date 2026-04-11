import os
import json
import logging
import http.client
import urllib.parse
import random

from dotenv import load_dotenv

load_dotenv()

# Logger setup specific to Airflow standard
logger = logging.getLogger(__name__)

SERPER_API_KEYS = [
    "2ed47f22976b52da7c560d0a8dccdf48854ee259",
    "4bb8a0d3b6528691d8d74d6b122bd94e7d32a89b",
    "085a9d92be4773540eb733a68ec822ddfb94df78"
]

# Global index to shuffle requests using round-robin
CURRENT_KEY_IDX = 0

# Global flag to track if ALL keys have exhausted their API quota
SERPER_API_EXHAUSTED = False

def get_linkedin_url(nom: str, prenom: str, nom_entreprise: str) -> str | None:
    """
    Interroge l'API Google Serper pour trouver le lien LinkedIn d'un dirigeant.
    Return None si non trouvé ou si quota dépassé.
    """
    global SERPER_API_EXHAUSTED, CURRENT_KEY_IDX, SERPER_API_KEYS
    
    if SERPER_API_EXHAUSTED or not SERPER_API_KEYS:
        return None

    if not nom or not prenom:
        return None
        
    entreprise_str = nom_entreprise if nom_entreprise else ""
    # Utilisation de booléens de recherche avancée pour maximiser la pertinence
    query = f'"{prenom} {nom}" "{entreprise_str}" site:linkedin.com/in/'

    # Round Robin Key Selection
    api_key = SERPER_API_KEYS[CURRENT_KEY_IDX]
    CURRENT_KEY_IDX = (CURRENT_KEY_IDX + 1) % len(SERPER_API_KEYS)

    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = res.read()
        
        if res.status == 403:
            logger.error(f"[ENRICHISSEMENT] ❌ Quota API atteint pour la clé finissant par ...{api_key[-4:]} ! On la retire.")
            SERPER_API_KEYS.remove(api_key)
            if not SERPER_API_KEYS:
                SERPER_API_EXHAUSTED = True
                logger.error("[ENRICHISSEMENT] ❌ TOUTES LES CLES SERPER API SONT ÉPUISÉES (Erreur 403) ! On arrête l'utilisation LinkedIn.")
            
            # Optionally retry immediately with the next key if any is left
            if SERPER_API_KEYS:
                # Need to reset CURRENT_KEY_IDX correctly
                CURRENT_KEY_IDX = 0  
                return get_linkedin_url(nom, prenom, nom_entreprise)
            return None
        
        if res.status != 200:
            logger.error(f"[ENRICHISSEMENT] Erreur API Serper pour la requête '{query}': statut {res.status}")
            return None
            
        data_json = json.loads(data.decode("utf-8"))
        
        # Parcourir les résultats organiques pour trouver un lien LinkedIn exact et vérifié
        organic_results = data_json.get("organic", [])
        for result in organic_results:
            link = result.get("link", "")
            
            # Validation stricte du format de profil individuel:
            # - Doit impérativement être un /in/
            # - NE DOIT PAS être un résultat de recherche de répertoire (/pub/dir/ ou /search/)
            if "linkedin.com/in/" in link:
                if "/pub/dir/" not in link and "/search/" not in link and "/title/" not in link:
                    logger.info(f"[ENRICHISSEMENT] LinkedIn EXACT trouvé ! {link}")
                    return link
                
        logger.info(f"[ENRICHISSEMENT] Aucun compte LinkedIn EXACT trouvé pour: '{query}'")
        return None

    except Exception as e:
        logger.error(f"[ENRICHISSEMENT] Exception lors de l'appel Serper pour '{query}': {str(e)}")
        return None

