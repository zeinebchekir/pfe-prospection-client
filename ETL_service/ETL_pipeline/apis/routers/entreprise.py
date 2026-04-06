from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
# from db.models import Entreprise
import os
from pydantic import BaseModel
import requests
from datetime import datetime, timezone
router = APIRouter()

AIRFLOW_URL      = os.environ.get("AIRFLOW_URL", "http://airflow-apiserver:8080")
AIRFLOW_USER     = os.environ.get("AIRFLOW_USER", "airflow")
AIRFLOW_PASSWORD = os.environ.get("AIRFLOW_PASSWORD", "airflow")

# @router.get("/")
# def list_entreprises(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     """Liste les entreprises extraites avec pagination."""
#     return db.query(Entreprise).offset(skip).limit(limit).all()


# @router.get("/{siret}")
# def get_entreprise(siret: str, db: Session = Depends(get_db)):
#     """Retourne le détail d'une entreprise par son SIRET."""
#     obj = db.query(Entreprise).filter_by(siret=siret).first()
#     if not obj:
#         raise HTTPException(status_code=404, detail="Entreprise introuvable")
#     return obj

class SearchRequest(BaseModel):
    query  : str              # SIREN ou nom entreprise

@router.get("/searchfromApi/{query}")
def search_entreprisesFromApi(query:str):
    """
    Déclenche une recherche d'entreprise à la demande.
    Paramètres : query (SIREN ou nom), region (optionnel)
    """
    if not query:
        raise HTTPException(status_code=400, detail="query est requis")

    config = {
        "query" : query,
    }

    result = _trigger_dag("search_new_lead", config=config)
    return {
        "message": f"Recherche '{query}' déclenchée",
        "run_id" : result.get("dag_run_id"),
        "config" : config,
    }


def _trigger_dag(dag_id: str, config: dict = {}):
    """Appelle l'API Airflow v2 avec authentification JWT."""
    token    = _get_airflow_token()
    response = requests.post(
        f"{AIRFLOW_URL}/api/v2/dags/{dag_id}/dagRuns",
        json={"conf": config,       
             "logical_date": datetime.now(timezone.utc).isoformat()  # ← champ requis par Airflow 3
},
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {token}"   # ← JWT au lieu de Basic Auth
        }
    )
    if response.status_code not in [200, 201]:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Airflow erreur : {response.text}"
        )
    return response.json()


def _get_airflow_token() -> str:
    """Récupère un token JWT depuis l'API Airflow."""
    response = requests.post(
        f"{AIRFLOW_URL}/auth/token",
        json={
            "username": AIRFLOW_USER,
            "password": AIRFLOW_PASSWORD
        },
        headers={"Content-Type": "application/json"}
    )
    if response.status_code != 201:
        raise HTTPException(
            status_code=401,
            detail=f"Impossible d'obtenir le token Airflow : {response.text}"
        )
    return response.json()["access_token"]