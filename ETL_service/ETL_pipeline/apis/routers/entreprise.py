from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Entreprise
from api.schemas.entreprise import EntrepriseResponse

router = APIRouter()

@router.get("/", response_model=list[EntrepriseResponse])
def list_entreprises(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Liste les entreprises extraites avec pagination."""
    return db.query(Entreprise).offset(skip).limit(limit).all()


@router.get("/{siret}", response_model=EntrepriseResponse)
def get_entreprise(siret: str, db: Session = Depends(get_db)):
    """Retourne le détail d'une entreprise par son SIRET."""
    obj = db.query(Entreprise).filter_by(siret=siret).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    return obj