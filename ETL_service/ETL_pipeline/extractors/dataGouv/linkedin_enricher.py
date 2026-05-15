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
    "0b7d3fbd79172ad85f6880181b1ff89a2efdb1c3",
    "f1eeif4eaznfc5lvpzfnqe5hsfnhe7yq4tqyhoqbq",
    "d714b95e5e8790ff6b66ad2c28581d9d7af9d96c",
    "c0a1f1784010b2a7701ca2345d4a0bd5c89568be",
    "fbccd70ef0217c0f786566a3ca5fda3140c3cf32",
    "2d372bd33da77f8a68477ad0301dce4fd8dd7ed2",
    "42b143d4db596d757a2706971683960304a0e0dc",
    "6080edbc55a0a65f9b0f7813e657f31701728f8f",
    "453200c2669d653fc34e167331caf3548b60179c",
    "8247756919bf9968a59c8d401a9963681a8e1744",
    "bcac4bf937151ba5a0ce2d6945d57107884eef12",
    "a4df4a68bfc3389691cb2f906fe527cb1d959c1e",
    "27ab75d77a50d52ad5b8979a0ee97a3c86cc77cf",
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

