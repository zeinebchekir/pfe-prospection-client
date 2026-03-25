from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from db.database import get_db
from db.models import SyncState
from api.schemas.sync import SyncStatusResponse

router = APIRouter()

@router.get("/status", response_model=list[SyncStatusResponse])
def get_all_sync_status(db: Session = Depends(get_db)):
    """Retourne la date de dernière sync pour toutes les sources."""
    return db.query(SyncState).all()


@router.get("/status/{source}", response_model=SyncStatusResponse)
def get_sync_status(source: str, db: Session = Depends(get_db)):
    """Retourne la date de dernière sync pour une source précise."""
    obj = db.query(SyncState).filter_by(source=source).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Source '{source}' introuvable")
    return obj


@router.post("/reset/{source}")
def reset_sync(source: str, db: Session = Depends(get_db)):
    """Remet la sync à zéro pour forcer un re-scraping complet."""
    obj = db.query(SyncState).filter_by(source=source).first()
    if obj:
        obj.last_sync = datetime(2020, 1, 1)
        obj.nb_enregistrements = 0
        db.commit()
    return {"message": f"Sync {source} réinitialisée"}