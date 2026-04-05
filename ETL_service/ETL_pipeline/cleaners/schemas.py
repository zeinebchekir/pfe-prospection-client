"""
schemas.py — Pydantic models for request/response validation.
These replace Django ORM models for the FastAPI port.
"""

from pydantic import BaseModel
from typing import Optional


# ─────────────────────────────────────────────
# INPUT MODELS (raw data coming in)
# ─────────────────────────────────────────────

class EntrepriseInput(BaseModel):
    nom: Optional[str] = None
    siret: Optional[str] = None
    siren: Optional[str] = None
    adresse_email: Optional[str] = None
    telephone: Optional[str] = None          # ← NEW: raw phone, any format
    ville: Optional[str] = None
    code_postal: Optional[str | int] = None
    pays: Optional[str] = None
    secteur_activite: Optional[str] = None
    forme_juridique: Optional[str] = None
    taille_entrep: Optional[str] = None
    categorie_entreprise: Optional[str] = None
    nb_locaux: Optional[str | int] = None
    ca: Optional[float | str] = None
    dateCreation: Optional[str] = None
    dateDerniereModification: Optional[str] = None
    sourceEntreprise: Optional[str] = None


class LeadInput(BaseModel):
    besoin: Optional[str] = None
    date_limite: Optional[str] = None
    titulaire: Optional[str] = None
    nature: Optional[str] = None
    lienOffre: Optional[str] = None
    status_lead: Optional[str] = None
    info_complementaire: Optional[str] = None


class RawRecord(BaseModel):
    entreprise: EntrepriseInput
    lead: Optional[LeadInput] = None


# ─────────────────────────────────────────────
# OUTPUT MODELS (cleaned data going out)
# ─────────────────────────────────────────────

class EntrepriseOutput(BaseModel):
    nom: Optional[str] = None
    siret: Optional[str] = None
    siren: Optional[str] = None
    adresse_email: Optional[str] = None
    telephone: Optional[str] = None          # ← NEW: normalized +33XXXXXXXXX or None
    ville: Optional[str] = None
    code_postal: Optional[int] = None
    pays: Optional[str] = None
    secteur_activite: Optional[str] = None
    forme_juridique: Optional[str] = None
    taille_entrep: Optional[str] = None
    categorie_entreprise: Optional[str] = None
    nb_locaux: Optional[int] = None
    ca: Optional[float] = None
    dateCreation: Optional[str] = None
    dateDerniereModification: Optional[str] = None
    sourceEntreprise: Optional[str] = None


class LeadOutput(BaseModel):
    besoin: Optional[str] = None
    date_limite: Optional[str] = None
    titulaire: Optional[str] = None
    nature: Optional[str] = None
    lienOffre: Optional[str] = None
    status_lead: Optional[str] = None
    info_complementaire: Optional[str] = None


class CleanedRecord(BaseModel):
    entreprise: EntrepriseOutput
    lead: Optional[LeadOutput] = None


# ─────────────────────────────────────────────
# REPORT MODELS
# ─────────────────────────────────────────────

class IssueDetail(BaseModel):
    index: int
    reason: str


class CleaningReportOutput(BaseModel):
    source: str
    total_input: int
    total_cleaned: int
    total_rejected: int
    issues: list[IssueDetail] = []
    summary: str


# ─────────────────────────────────────────────
# ENDPOINT RESPONSE WRAPPERS
# ─────────────────────────────────────────────

class CleanResponse(BaseModel):
    results: list[CleanedRecord]
    report: CleaningReportOutput