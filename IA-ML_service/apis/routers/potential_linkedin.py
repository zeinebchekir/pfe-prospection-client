from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from schemas.potential_linkedin import (
    PotentialLinkedinCreate,
    PotentialLinkedinUpdate,
    PotentialLinkedinResponse,
)
from db import crud_potential_linkedin as crud

router = APIRouter(
    prefix="/potential-linkedin",
    tags=["Potential LinkedIn"],
)

@router.get("/entreprise/{identifiantEntreprise}/all", response_model=List[PotentialLinkedinResponse])
def get_all_by_entreprise(identifiantEntreprise: str, db: Session = Depends(get_db)):
    return crud.get_all_by_entreprise(db, identifiantEntreprise)
@router.get("/", response_model=List[PotentialLinkedinResponse])
def get_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all(db, skip=skip, limit=limit)


@router.get("/{identifiant}", response_model=PotentialLinkedinResponse)
def get_by_id(identifiant: int, db: Session = Depends(get_db)):
    record = crud.get_by_id(db, identifiant)
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement non trouvé")
    return record


@router.get("/entreprise/{identifiantEntreprise}", response_model=PotentialLinkedinResponse)
def get_by_entreprise(identifiantEntreprise: str, db: Session = Depends(get_db)):
    record = crud.get_by_entreprise(db, identifiantEntreprise)
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement non trouvé pour cette entreprise")
    return record


@router.post("/", response_model=PotentialLinkedinResponse, status_code=status.HTTP_201_CREATED)
def create(data: PotentialLinkedinCreate, db: Session = Depends(get_db)):
    return crud.create(db, data)


@router.put("/{identifiant}", response_model=PotentialLinkedinResponse)
def update(identifiant: int, data: PotentialLinkedinUpdate, db: Session = Depends(get_db)):
    record = crud.update(db, identifiant, data)
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement non trouvé")
    return record


@router.put("/entreprise/{identifiantEntreprise}", response_model=PotentialLinkedinResponse)
def update_by_entreprise(identifiantEntreprise: str, data: PotentialLinkedinUpdate, db: Session = Depends(get_db)):
    record = crud.update_by_entreprise(db, identifiantEntreprise, data)
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement non trouvé pour cette entreprise")
    return record


@router.delete("/{identifiant}", status_code=status.HTTP_204_NO_CONTENT)
def delete(identifiant: int, db: Session = Depends(get_db)):
    success = crud.delete(db, identifiant)
    if not success:
        raise HTTPException(status_code=404, detail="Enregistrement non trouvé")