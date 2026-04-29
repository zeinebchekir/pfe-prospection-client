import os
import json
import logging
import http.client

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SERPER_API_KEYS = os.getenv("SERPER_API_KEY")

CURRENT_KEY_IDX = 0
SERPER_API_EXHAUSTED = False


def get_linkedin_url(nom_entreprise: str, pays: str = "france") -> str | None:
    global SERPER_API_EXHAUSTED, CURRENT_KEY_IDX, SERPER_API_KEYS

    if SERPER_API_EXHAUSTED or not SERPER_API_KEYS:
        return None

    if not nom_entreprise:
        return None

    # ✅ Query corrigée : pas de guillemets globaux, site: ciblé, nom entre guillemets seul
    query = f'site:linkedin.com/company "{nom_entreprise}"'
    # Exemples de résultats :
    # → https://www.linkedin.com/company/matmut/
    # → https://fr.linkedin.com/company/matmut

    api_key = SERPER_API_KEYS[CURRENT_KEY_IDX]
    CURRENT_KEY_IDX = (CURRENT_KEY_IDX + 1) % len(SERPER_API_KEYS)

    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({
            "q": query,
            "num": 5,
            "gl": "fr",   # ✅ résultats géolocalisés France
            "hl": "fr"    # ✅ langue française
        })
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = res.read()

        if res.status == 403:
            logger.error(f"❌ Quota API atteint pour la clé ...{api_key[-4:]} ! On la retire.")
            SERPER_API_KEYS.remove(api_key)
            if not SERPER_API_KEYS:
                SERPER_API_EXHAUSTED = True
                logger.error("❌ TOUTES LES CLES SERPER API SONT ÉPUISÉES.")
                return None
            CURRENT_KEY_IDX = 0
            return get_linkedin_url(nom_entreprise, pays)

        if res.status != 200:
            logger.error(f"Erreur Serper statut {res.status} pour '{query}'")
            return None

        data_json = json.loads(data.decode("utf-8"))
        organic_results = data_json.get("organic", [])

        for result in organic_results:
            link = result.get("link", "")
            # ✅ Validation : doit contenir /company/ et pas être une page de recherche
            if (
                "linkedin.com/company/" in link
                and "/pub/dir/" not in link
                and "/search/" not in link
                and "/title/" not in link
            ):
                logger.info(f"✅ LinkedIn trouvé : {link}")
                return link

        # ✅ Fallback : si site: trop strict, retry sans guillemets
        return _retry_without_quotes(nom_entreprise, api_key)

    except Exception as e:
        logger.error(f"Exception Serper pour '{query}': {e}")
        return None


def _retry_without_quotes(nom_entreprise: str, api_key: str) -> str | None:
    """Fallback si la recherche avec guillemets ne donne rien."""
    query_fallback = f'site:linkedin.com/company {nom_entreprise} entreprise'
    logger.info(f"🔁 Retry sans guillemets : {query_fallback}")

    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({"q": query_fallback, "num": 5, "gl": "fr", "hl": "fr"})
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = res.read()

        if res.status != 200:
            return None

        data_json = json.loads(data.decode("utf-8"))
        for result in data_json.get("organic", []):
            link = result.get("link", "")
            if (
                "linkedin.com/company/" in link
                and "/pub/dir/" not in link
                and "/search/" not in link
            ):
                logger.info(f"✅ LinkedIn trouvé (fallback) : {link}")
                return link

        logger.info(f"Aucun LinkedIn trouvé pour '{nom_entreprise}'")
        return None

    except Exception as e:
        logger.error(f"Exception retry Serper : {e}")
        return None