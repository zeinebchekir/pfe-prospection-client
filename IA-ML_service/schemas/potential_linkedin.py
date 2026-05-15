from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class PotentialLinkedinBase(BaseModel):
    identifiantEntreprise: Optional[str] = None
    posts: Optional[Any] = None
    potential_score: Optional[int] = None
    positive_signals: Optional[Any] = None
    negative_signals: Optional[Any] = None
    needs_it: Optional[Any] = None
    recommandation: Optional[str] = None
    emailsgenerated: Optional[Any] = None


class PotentialLinkedinCreate(PotentialLinkedinBase):
    pass


class PotentialLinkedinUpdate(PotentialLinkedinBase):
    pass


class PotentialLinkedinResponse(PotentialLinkedinBase):
    identifiant: int

    class Config:
        from_attributes = True