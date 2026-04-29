from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Entreprise, RawLead
from sqlalchemy import func
import os
import uuid
from typing import Optional, List
from pydantic import BaseModel, field_validator
import requests
import re
from datetime import datetime, timezone, date
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

# ──────────────────────────────────────────────────────────────
#  ADD LEAD — POST /add_lead
#  Must be defined BEFORE /{identifiant} to avoid route shadowing
# ──────────────────────────────────────────────────────────────

class AddLeadPayload(BaseModel):
    """
    Payload for manually creating a lead from the frontend.
    SIREN or nom is required; all other fields are optional.
    """
    # Identity
    nom: str
    siren: Optional[str] = None
    siret: Optional[str] = None

    # Address
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    pays: Optional[str] = "France"

    # Company info
    secteur_activite: Optional[str] = None
    forme_juridique: Optional[str] = None
    taille_entreprise: Optional[str] = None      # maps → taille_entrep
    categorie_entreprise: Optional[str] = None
    nb_locaux: Optional[int] = None
    ca: Optional[float] = None
    date_creation_entreprise: Optional[str] = None   # ISO date string

    # Contact
    telephone: Optional[str] = None
    email: Optional[str] = None                      # maps → adresse_email

    # CRM
    statut: Optional[str] = "Nouveau"
    dirigeants: Optional[List[dict]] = None

    @field_validator("siren")
    @classmethod
    def validate_siren(cls, v):
        if v is not None:
            v = re.sub(r"\D", "", v)
            if v and len(v) != 9:
                raise ValueError("SIREN doit contenir exactement 9 chiffres")
        return v or None

    @field_validator("siret")
    @classmethod
    def validate_siret(cls, v):
        if v is not None:
            v = re.sub(r"\D", "", v)
            if v and len(v) != 14:
                raise ValueError("SIRET doit contenir exactement 14 chiffres")
        return v or None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is not None and v.strip():
            if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v.strip()):
                raise ValueError("Format d'email invalide")
        return v.strip() if v else None

    class Config:
        extra = "forbid"


@router.post("/add_lead", status_code=status.HTTP_201_CREATED, summary="Créer un nouveau lead manuellement")
def add_lead(payload: AddLeadPayload, db: Session = Depends(get_db)):
    """
    Crée un nouveau lead (entreprise) directement depuis le frontend.
    - Vérifie les doublons par SIREN, SIRET ou (nom + code_postal).
    - Génère un identifiant unique si le SIREN n'est pas fourni.
    - Écrit une trace dans raw_leads (audit trail).
    - Calcule le taux de complétude.
    """
    # ── 1. Unicité SIREN ─────────────────────────────────────────
    if payload.siren:
        existing = db.query(Entreprise).filter(Entreprise.siren == payload.siren).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Un lead avec le SIREN {payload.siren} existe déjà (identifiant: {existing.identifiant})",
            )

    # ── 2. Unicité SIRET ─────────────────────────────────────────
    if payload.siret:
        existing = db.query(Entreprise).filter(Entreprise.siret == payload.siret).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Un lead avec le SIRET {payload.siret} existe déjà (identifiant: {existing.identifiant})",
            )

    # ── 3. Unicité (nom + code_postal) ───────────────────────────
    if payload.nom and payload.code_postal:
        existing = db.query(Entreprise).filter(
            Entreprise.nom == payload.nom.strip(),
            Entreprise.code_postal == payload.code_postal.strip(),
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Un lead '{payload.nom}' à {payload.code_postal} existe déjà (identifiant: {existing.identifiant})",
            )

    # ── 4. Générer un identifiant ─────────────────────────────────
    identifiant = payload.siren if payload.siren else f"manual_{uuid.uuid4().hex[:12]}"
    run_id      = f"manual_ui_{uuid.uuid4().hex[:8]}"
    now         = datetime.now(timezone.utc)

    # ── 5. Parse date création ────────────────────────────────────
    date_creation = None
    if payload.date_creation_entreprise:
        try:
            date_creation = datetime.fromisoformat(payload.date_creation_entreprise).date()
        except ValueError:
            pass

    # ── 6. Taux de complétude ─────────────────────────────────────
    _completude_fields = [
        payload.siren, payload.siret, payload.nom, payload.ville,
        payload.code_postal, payload.secteur_activite, payload.forme_juridique,
        payload.taille_entreprise, payload.ca, payload.telephone, payload.email,
        payload.dirigeants,
    ]
    filled = sum(1 for f in _completude_fields if f is not None and f != "" and f != [])
    taux_completude = round((filled / len(_completude_fields)) * 100, 2)

    # ── 7. Créer l'objet ORM ──────────────────────────────────────
    obj = Entreprise(
        identifiant          = identifiant,
        siren                = payload.siren,
        siret                = payload.siret,
        nom                  = payload.nom.strip(),
        ville                = payload.ville.strip() if payload.ville else None,
        code_postal          = payload.code_postal.strip() if payload.code_postal else None,
        pays                 = payload.pays or "France",
        secteur_activite     = payload.secteur_activite,
        forme_juridique      = payload.forme_juridique,
        taille_entrep        = payload.taille_entreprise,
        categorie_entreprise = payload.categorie_entreprise,
        nb_locaux            = payload.nb_locaux,
        ca                   = payload.ca,
        date_creation_entreprise = date_creation,
        telephone            = payload.telephone,
        adresse_email        = payload.email,
        statut               = payload.statut or "Nouveau",
        dirigeants           = payload.dirigeants,
        sources              = {"source": "manual_ui"},
        taux_completude      = taux_completude,
        dag_run_id           = run_id,
        date_scraping        = now,
    )

    # ── 8. Audit trail dans raw_leads ─────────────────────────────
    raw_record = {k: str(v) if isinstance(v, (date, datetime)) else v
                  for k, v in payload.model_dump().items()}
    raw_obj = RawLead(
        source        = "manual_ui",
        raw_data      = raw_record,
        dag_run_id    = run_id,
        date_scraping = now,
    )

    try:
        db.add(raw_obj)
        db.flush()          # get raw_obj.id without committing
        obj.raw_lead_id = raw_obj.id
        db.add(obj)
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur insertion BDD: {str(e)}")

    return {
        "status":      "created",
        "message":     f"Lead '{obj.nom}' créé avec succès.",
        "identifiant": obj.identifiant,
        "lead":        obj,
    }


# ──────────────────────────────────────────────────────────────
#  DELETE LEAD — DELETE /{identifiant}
#  Defined BEFORE GET /{identifiant} to guarantee correct match
# ──────────────────────────────────────────────────────────────

@router.delete("/{identifiant}", status_code=status.HTTP_200_OK, summary="Supprimer un lead de la base de données")
def delete_entreprise(identifiant: str, db: Session = Depends(get_db)):
    """
    Supprime définitivement un lead (entreprise) et ses entrées raw_leads associées.
    Retourne un message de confirmation avec les métadonnées du lead supprimé.
    """
    obj = db.query(Entreprise).filter_by(identifiant=identifiant).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    # Snapshot des infos avant suppression pour la réponse
    deleted_info = {
        "identifiant": obj.identifiant,
        "nom":         obj.nom,
        "siren":       obj.siren,
        "siret":       obj.siret,
        "ville":       obj.ville,
        "statut":      obj.statut,
    }

    try:
        # Sauvegarder l'id avant suppression
        raw_lead_id_to_delete = obj.raw_lead_id

        # Supprimer le lead d'abord pour éviter l'erreur de clé étrangère
        db.delete(obj)
        db.flush()

        # Supprimer les raw_leads liées (si raw_lead_id exist)
        if raw_lead_id_to_delete:
            db.query(RawLead).filter(RawLead.id == raw_lead_id_to_delete).delete()

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur suppression BDD: {str(e)}")

    return {
        "status":  "deleted",
        "message": f"Lead '{deleted_info['nom']}' supprimé avec succès.",
        "deleted": deleted_info,
    }


# ──────────────────────────────────────────────────────────────
#  GET ONE — parameterized route (must come AFTER static routes)
# ──────────────────────────────────────────────────────────────

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
    description: str | None = None
    website_url: str | None = None
    linkedin_url: str | None = None
    date_creation_entreprise: date | None = None
    nb_locaux: int | None = None

    @field_validator("date_creation_entreprise", mode="before")
    @classmethod
    def validate_date_creation(cls, v):
        if isinstance(v, int):
            return date(v, 1, 1)
        return v

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
        "dirigeants": "dirigeants",
        "description": "description",
        "website_url": "website_url",
        "linkedin_url": "linkedin_url",
        "date_creation_entreprise": "date_creation_entreprise",
        "nb_locaux": "nb_locaux"
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



@router.post("/confirm_lead", summary="Confirmer et sauvegarder un lead choisi en BDD")
def confirm_lead(payload: ConfirmLeadPayload, db: Session = Depends(get_db)):
    """
    Étape 2 du workflow d'ajout de lead :
    Le frontend renvoie l'entreprise choisie (depuis /search_from_query).
    On nettoie une dernière fois et on sauvegarde directement en BDD (synchrone).
    """
    from cleaners.dataGouv_cleaner import DataGouvCleaner
    from db import crud
    import uuid

    entreprise_data = payload.entreprise

    if not entreprise_data or not entreprise_data.get("siren"):
        raise HTTPException(status_code=422, detail="Données d'entreprise invalides ou SIREN manquant")

    run_id  = f"manual_ui_{uuid.uuid4().hex[:8]}"
    now_str = datetime.now().isoformat()

    # Re-nettoyage pour garantir la cohérence
    record = {"entreprise": entreprise_data, "lead": None}
    try:
        cleaned_records, _ = DataGouvCleaner().clean([record])
        if not cleaned_records:
            raise HTTPException(status_code=422, detail="Données entreprise invalides après nettoyage")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur nettoyage: {str(e)}")

    try:
        # 1. Raw trace
        crud.insert_raw_leads(
            db, [entreprise_data], source="dataGouv",
            dag_run_id=run_id, date_scraping=now_str
        )
        raw_id = entreprise_data.get("_raw_lead_id")
        
        # 2. Clean insert/upsert
        for cr in cleaned_records:
            cr["date_scraping"] = now_str
            if raw_id and cr.get("entreprise"):
                cr["entreprise"]["_raw_lead_id"] = raw_id
                
        crud.insert_clean_leads(
            db, cleaned_records, source="dataGouv",
            dag_run_id=run_id, date_scraping=now_str
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur insertion BDD: {str(e)}")

    # Retourne l'objet final depuis la BDD
    siren = cleaned_records[0]["entreprise"].get("siren")
    lead_obj = db.query(Entreprise).filter_by(identifiant=siren).first() if siren else None

    return {
        "status":  "success",
        "message": "Lead sauvegardé avec succès en base de données.",
        "lead":    lead_obj or cleaned_records[0]["entreprise"],
    }

