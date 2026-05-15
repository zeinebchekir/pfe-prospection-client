import os
import logging
import httpx
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

USER_MANAGEMENT_URL = os.getenv(
    "USER_MANAGEMENT_URL",
    "http://web:8000"
)
COOKIE_NAME = os.getenv("AUTH_COOKIE_ACCESS", "access_token")


async def get_current_user(request: Request) -> dict:
    """
    Appelle le service user_management pour valider le token
    et récupérer les infos de l'utilisateur connecté.
    Transmet le cookie HTTP-only tel quel — Django fait la validation.
    """
    token = request.cookies.get(COOKIE_NAME)
    print(f"[AUTH] Cookie reçu: {COOKIE_NAME}={token}")  # ← ajouter

    if not token:
        print("token est null")
        raise HTTPException(status_code=401, detail="Non authentifié")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_MANAGEMENT_URL}/api/auth/me/",
                cookies={COOKIE_NAME: token},
                timeout=5.0
            )
    except httpx.RequestError as e:
        logger.error("user_management injoignable : %s", e)
        raise HTTPException(
            status_code=503,
            detail="Service d'authentification indisponible"
        )

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    if response.status_code == 403:
        raise HTTPException(status_code=403, detail="Accès refusé")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur user_management : {response.status_code}"
        )

    data = response.json()
    # MeView retourne {"status": "success", "user": {...}}
    return data.get("user", data)


async def require_admin(request: Request) -> dict:
    """
    Dépendance FastAPI — lève 403 si role != ADMIN.
    """
    user = await get_current_user(request)
    if user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Accès réservé aux administrateurs"
        )
    return user