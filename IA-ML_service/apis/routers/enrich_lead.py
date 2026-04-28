# ia-ml/apis/routers/linkedin_posts.py
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional
import requests
from datetime import date

router = APIRouter()

class EnrichRequest(BaseModel):
    identifiant: str  # identifiant ETL de l'entreprise, pas l'URL LinkedIn
    linkedin_url: str
    description: Optional[str] = None
    phone: Optional[dict] = None   # {"number": "...", "extension": null}
    website: Optional[str] = None
    specialities: Optional[List[str]] = None
    taille: Optional[str] = None
    date_creation_entreprise: Optional[int] = None
    nb_locaux: Optional[int] = None

@router.post("/")
async def enrich_entreprise(request: EnrichRequest):
    try:
        # Mapper les champs LinkedIn → champs ETL EntrepriseUpdate
        etl_payload = {}

        if request.description:
            etl_payload["description"] = request.description

        if request.website:
            etl_payload["website_url"] = request.website

        if request.linkedin_url:
            etl_payload["linkedin_url"] = request.linkedin_url

        if request.taille:
            etl_payload["taille_entreprise"] = request.taille
        if request.date_creation_entreprise:
            date_objet = date(request.date_creation_entreprise, 1, 1)
            etl_payload["date_creation_entreprise"] = date_objet.isoformat()      
        if request.nb_locaux:
            etl_payload["nb_locaux"] = request.nb_locaux
        if request.phone:
            number = request.phone.get("number")
            if number:
                etl_payload["telephone"] = number

        if not etl_payload:
            raise HTTPException(status_code=400, detail="Aucun champ à enrichir")

        etl_url = os.getenv("ETL_SERVICE_URL", "http://fastapi:8000")
        etl_response = requests.patch(
            f"{etl_url}/entreprises/{request.identifiant}",
            json=etl_payload,
            timeout=30
        )

        if etl_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Entreprise introuvable dans la base ETL")
        
        if etl_response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"ETL error: {etl_response.text}")

        return {
            "message": "✅ Entreprise enrichie avec succès",
            "identifiant": request.identifiant,
            "updated_fields": list(etl_payload.keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))