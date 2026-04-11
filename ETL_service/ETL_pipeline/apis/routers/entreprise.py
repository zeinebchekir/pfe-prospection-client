from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Entreprise
from sqlalchemy import func
import os
from pydantic import BaseModel
import requests
import re
from datetime import datetime, timezone
router = APIRouter()

AIRFLOW_URL      = os.environ.get("AIRFLOW_URL", "http://airflow-apiserver:8080")
AIRFLOW_USER     = os.environ.get("AIRFLOW_USER", "airflow")
AIRFLOW_PASSWORD = os.environ.get("AIRFLOW_PASSWORD", "airflow")

@router.get("/")
def list_entreprises(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Liste les entreprises extraites avec pagination (Idéal pour Vue.js DataTable)."""
    total = db.query(func.count(Entreprise.identifiant)).scalar()
    data = db.query(Entreprise).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": data
    }

@router.get("/{identifiant}")
def get_entreprise(identifiant: str, db: Session = Depends(get_db)):
    """Retourne le détail d'une entreprise par son identifiant unique."""
    obj = db.query(Entreprise).filter_by(identifiant=identifiant).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    return obj

@router.get("/{identifiant}/modal", summary="Récupérer les données de la modale Edit Lead")
def get_entreprise_modal(identifiant: str, db: Session = Depends(get_db)):
    """Retourne les données formatées spécifiquement pour la modale Edit Lead."""
    obj = db.query(Entreprise).filter_by(identifiant=identifiant).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    
    # Format output for the frontend modal
    return {
        "Informations": {
            "nom_entreprise": obj.nom,
            "siren": obj.siren,
            "siret": obj.siret,
            "identifiant": obj.identifiant,
            "taille_entreprise": obj.taille_entrep,
            "secteur_activite": obj.secteur_activite,
            "forme_juridique": obj.forme_juridique,
            "ca_affiche": str(obj.ca) if obj.ca else None, 
            "statut": getattr(obj, "statut", None)
        },
        "Contact": {
            "ville": obj.ville,
            "code_postal": obj.code_postal,
            "pays": obj.pays,
            "telephone": obj.telephone,
            "email": obj.adresse_email
        },
        "Dirigeants": obj.dirigeants or []
    }

class EntrepriseUpdate(BaseModel):
    nom_entreprise: str | None = None
    siren: str | None = None
    siret: str | None = None
    identifiant: str | None = None
    taille_entreprise: str | None = None
    secteur_activite: str | None = None
    forme_juridique: str | None = None
    ca_affiche: str | None = None
    statut: str | None = None
    ville: str | None = None
    code_postal: str | None = None
    pays: str | None = None
    telephone: str | None = None
    email: str | None = None
    dirigeants: list | None = None

    class Config:
        extra = "forbid"

@router.patch("/{identifiant}", summary="Mettre à jour un Lead (partiel)")
def update_entreprise(identifiant: str, payload: EntrepriseUpdate, db: Session = Depends(get_db)):
    """Update lead editable fields from Informations + Contact only."""
    obj = db.query(Entreprise).filter_by(identifiant=identifiant).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    # Trim strings and validate
    if hasattr(payload, "model_dump"):
        update_data = payload.model_dump(exclude_unset=True)
    else:
        update_data = payload.dict(exclude_unset=True)
    
    # Custom email validation
    if "email" in update_data and update_data["email"] is not None:
        email_val = str(update_data["email"]).strip()
        if email_val and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email_val):
            raise HTTPException(status_code=422, detail="Format d'email invalide")
        update_data["email"] = email_val

    # Normalize/trim other strings
    for k, v in update_data.items():
        if isinstance(v, str) and k != "email":
            update_data[k] = v.strip()
        # For list types like dirigeants, we leave them as is

    # Map frontend fields to DB model columns
    field_mapping = {
        "nom_entreprise": "nom",
        "siren": "siren",
        "siret": "siret",
        "identifiant": "identifiant",
        "taille_entreprise": "taille_entrep",
        "secteur_activite": "secteur_activite",
        "forme_juridique": "forme_juridique",
        "statut": "statut",
        "ville": "ville",
        "code_postal": "code_postal",
        "pays": "pays",
        "telephone": "telephone",
        "email": "adresse_email",
        "dirigeants": "dirigeants"
    }

    mutated = False
    for ui_field, db_col in field_mapping.items():
        if ui_field in update_data:
            setattr(obj, db_col, update_data[ui_field])
            mutated = True
            
    # Handle ca_affiche mapping to float "ca"
    if "ca_affiche" in update_data:
        ca_str = update_data["ca_affiche"]
        if ca_str is not None:
            # simple attempt to extract the float from strings like "118.7 Md€"
            match = re.search(r"[-+]?\d*\.\d+|\d+", ca_str)
            if match:
                obj.ca = float(match.group())
            else:
                obj.ca = None
        else:
            obj.ca = None
        mutated = True

    if mutated:
        obj.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(obj)

    return {"status": "success", "message": "Lead mis à jour", "identifiant": obj.identifiant}

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



@router.post("/search_from_query/{query}", summary="Rechercher et prévisualiser un lead (sans sauvegarder)")
def search_lead_preview(query: str):
    """
    Étape 1 du workflow d'ajout de lead :
    Scrape + Extract + Clean → renvoie les données au frontend pour prévisualisation.
    Aucune écriture en base. Le commercial valide ensuite via /confirm_lead.
    """
    from scrapers.dataGouv import DataGouvService
    from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv
    from cleaners.dataGouv_cleaner import DataGouvCleaner

    # 1. Scrape — top 5 résultats pour que le commercial puisse choisir
    try:
        service = DataGouvService()
        data = service.fetch_data(service.base_url, params={"q": query, "per_page": 5})
        if not data or not data.get("results"):
            raise HTTPException(status_code=404, detail="Aucune entreprise trouvée dans DataGouv")
        raw = data.get("results", [])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur scraping DataGouv: {str(e)}")

    # 2. Extract (dirigeants, CA, etc.)
    try:
        extracted = extract_data_from_datagouv(raw)
        if not extracted:
            raise HTTPException(status_code=500, detail="L'extraction a échoué")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur extraction: {str(e)}")

    # 3. Clean
    records = [{"entreprise": item, "lead": None} for item in extracted]
    try:
        cleaned_records, _ = DataGouvCleaner().clean(records)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur nettoyage: {str(e)}")

    # On retourne les données nettoyées — pas de sauvegarde
    preview = [r["entreprise"] for r in cleaned_records]
    return {
        "status": "preview",
        "message": f"{len(preview)} résultat(s) trouvé(s) — choisissez une entreprise à ajouter",
        "results": preview
    }


class ConfirmLeadPayload(BaseModel):
    entreprise: dict  # le dict nettoyé que le frontend renvoie après sélection

    class Config:
        extra = "allow"



@router.post("/confirm_lead", summary="Confirmer et déclencher la sauvegarde en BDD (via DAG Airflow)")
def confirm_lead(payload: ConfirmLeadPayload, db: Session = Depends(get_db)):
    """
    Étape 2 du workflow d'ajout de lead :
    Le frontend renvoie l'entreprise choisie (depuis /search_from_query).
    On déclenche un DAG Airflow spécial ('load_manual_lead') pour enregistrer cette 
    entreprise proprement en laissant la trace dans Airflow.
    """
    entreprise_data = payload.entreprise

    if not entreprise_data or not entreprise_data.get("siren"):
        raise HTTPException(status_code=422, detail="Données d'entreprise invalides ou SIREN manquant")

    config = {
        "entreprise": entreprise_data
    }

    # On déclenche le DAG Airflow que nous venons de créer
    result = _trigger_dag("load_manual_lead", config=config)
    
    return {
        "status": "success", 
        "message": "Enregistrement du lead validé et lancé. Le lead sera disponible dans quelques secondes.",
        "run_id": result.get("dag_run_id"),
        "lead_preview": entreprise_data
    }


