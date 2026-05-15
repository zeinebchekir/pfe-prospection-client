from sqlalchemy.orm import Session
from db.models import Potential_linkedin
from schemas.potential_linkedin import PotentialLinkedinCreate, PotentialLinkedinUpdate
from typing import Optional


def get_by_id(db: Session, identifiant: int) -> Optional[Potential_linkedin]:
    return db.query(Potential_linkedin).filter(
        Potential_linkedin.identifiant == identifiant
    ).first()


def get_by_entreprise(db: Session, identifiantEntreprise: str) -> Optional[Potential_linkedin]:
    return db.query(Potential_linkedin).filter(
        Potential_linkedin.identifiantEntreprise == identifiantEntreprise
    ).first()


def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[Potential_linkedin]:
    return db.query(Potential_linkedin).offset(skip).limit(limit).all()


def create(db: Session, data: PotentialLinkedinCreate) -> Potential_linkedin:
    record = Potential_linkedin(
        identifiantEntreprise=data.identifiantEntreprise,
        posts=data.posts,
        potential_score=data.potential_score,
        positive_signals=data.positive_signals,
        negative_signals=data.negative_signals,
        needs_it=data.needs_it,
        recommandation=data.recommandation,
        emailsgenerated=data.emailsgenerated,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update(db: Session, identifiant: int, data: PotentialLinkedinUpdate) -> Optional[Potential_linkedin]:
    record = get_by_id(db, identifiant)
    if not record:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


def update_by_entreprise(db: Session, identifiantEntreprise: str, data: PotentialLinkedinUpdate) -> Optional[Potential_linkedin]:
    record = get_by_entreprise(db, identifiantEntreprise)
    if not record:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


def delete(db: Session, identifiant: int) -> bool:
    record = get_by_id(db, identifiant)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True