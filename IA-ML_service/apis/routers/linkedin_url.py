from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.serper_service import get_linkedin_url

router = APIRouter()

class LinkedInUrlRequest(BaseModel):
    nom_entreprise: str
    pays: str = "france"

class LinkedInUrlResponse(BaseModel):
    nom_entreprise: str
    pays: str
    linkedin_url: str | None
    message: str

@router.post("/url", response_model=LinkedInUrlResponse)
async def find_linkedin_url(request: LinkedInUrlRequest):
    linkedin_url = get_linkedin_url(request.nom_entreprise, request.pays)

    if not linkedin_url:
        raise HTTPException(
            status_code=404,
            detail=f"URL LinkedIn introuvable pour '{request.nom_entreprise}'"
        )

    return LinkedInUrlResponse(
        nom_entreprise=request.nom_entreprise,
        pays=request.pays,
        linkedin_url=linkedin_url,
        message="✅ URL LinkedIn trouvée"
    )