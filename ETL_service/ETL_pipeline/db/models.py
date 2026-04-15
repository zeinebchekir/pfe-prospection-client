"""
models.py — SQLAlchemy ORM models for the ETL pipeline.

Two tables:
  - raw_leads   : extracted data (pre-cleaning), one row per scraped record
  - clean_leads : fully cleaned / normalised data ready for CRM use

Both tables carry a `source` column ('dataGouv' or 'BOAMP') so that each
dataset can be queried independently without any JOIN.

DataGouv rows  → company fields populated, lead fields (besoin, date_limite…) NULL
BOAMP rows     → company + lead fields populated, DataGouv-only fields (ca, taille…) NULL
"""

from alembic.util.sqla_compat import AUTOINCREMENT_DEFAULT
from sqlalchemy import (
    Column, String, Text, Float, Integer,
    DateTime, Date, func, ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base
from sqlalchemy import LargeBinary

# ──────────────────────────────────────────────────────────────
#  TABLE 1 — raw_leads  (staging, pre-cleaning)
# ──────────────────────────────────────────────────────────────

class RawLead(Base):
    """
    Stores every record exactly as returned by the extractor, before
    any cleaning.  Serves as an audit trail and allows re-processing.

    BOAMP specifics
    ───────────────
    The BOAMP API returns a `donnees` field whose schema varies by
    `perimetre` (MAPA / FNSimple / DIRECTIVE-24 / DIRECTIVE-25 / AUTRE).
    This blob is preserved verbatim in `donnees_boamp` JSONB so it can
    be re-parsed or audited without hitting the API again.

    `raw_data` stores the full flat dict returned by:
      - extract_data_from_datagouv()   for DataGouv records
      - get_global_information()       for BOAMP records
    """
    __tablename__ = "raw_leads"

    id             = Column(Integer, primary_key=True, autoincrement=True)

    # Which pipeline produced this row
    source         = Column(String(20), nullable=False, index=True)   # 'dataGouv' | 'BOAMP'

    # Full flattened extracted dict (all sources)
    raw_data       = Column(JSONB, nullable=False)

    # BOAMP only — the original variable-schema `donnees` blob
    # NULL for DataGouv rows

    # Airflow run traceability
    dag_run_id     = Column(String, nullable=True)

    loaded_at      = Column(DateTime(timezone=True), server_default=func.now())
    date_scraping  = Column(DateTime, nullable=True)
    updated_on_source_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<RawLead(id={self.id}, source={self.source})>"


# ──────────────────────────────────────────────────────────────
#  TABLE 2 — clean_leads  (production, post-cleaning)
# ──────────────────────────────────────────────────────────────

class Entreprise(Base):
    """
    Stores every cleaned/normalised record produced by DataGouvCleaner
    or BoampCleaner.  This is the table queried by downstream CRM tools.

    Column groups
    ─────────────
    shared       : source, siren, nom, ville, code_postal, pays, sources JSONB
    DataGouv     : secteur_activite (NAF label), forme_juridique, taille_entrep,
                   categorie_entreprise, nb_locaux, ca, date_creation,
                   date_derniere_modif
    BOAMP        : siret, telephone, adresse_email, besoin, date_limite,
                   titulaire, nature, lien_offre, status_lead, info_complementaire
    """
    __tablename__ = "entreprise"

    identifiant    = Column(String(25), primary_key=True,autoincrement=True)

    # Link back to the raw staging row (nullable — bulk loads may skip it)
    raw_lead_id    = Column(Integer, ForeignKey("raw_leads.id"), nullable=True, index=True)
    # ── Shared identity ──────────────────────────────────────
    siren          = Column(String(9),  nullable=True, index=True, unique=True)   # DataGouv always; BOAMP: siret[:9]
    siret          = Column(String(14), nullable=True, index=True, unique=True)   # BOAMP when available
    nom            = Column(String,     nullable=True)

    # ── Address ──────────────────────────────────────────────
    ville          = Column(String,  nullable=True)
    code_postal    = Column(String,  nullable=True)
    pays           = Column(String,  nullable=True, default="France")

    # ── Company info (DataGouv-rich, BOAMP-partial) ───────────
    secteur_activite     = Column(String,  nullable=True)   # DataGouv: NAF label; BOAMP: code or label
    forme_juridique      = Column(String,  nullable=True)   # both sources
    taille_entrep        = Column(String,  nullable=True)   # DataGouv only (INSEE effectif label)
    categorie_entreprise = Column(String,  nullable=True)   # DataGouv only
    nb_locaux            = Column(Integer, nullable=True)   # DataGouv only
    ca                   = Column(Float,   nullable=True)   # DataGouv only (chiffre d'affaires)
    date_creation_entreprise = Column(Date,    nullable=True)   # DataGouv only
    date_derniere_modif_site  = Column(DateTime,    nullable=True)   # DataGouv only
    date_scraping        = Column(DateTime,    nullable=True)   # DataGouv only
    # ── Contact (BOAMP-rich) ──────────────────────────────────
    telephone      = Column(String, nullable=True)   # BOAMP only
    adresse_email  = Column(String, nullable=True)   # BOAMP only
    info_boamp  = Column(JSONB, nullable=True)
    dirigeants = Column(JSONB, nullable=True)
    statut         = Column(String, nullable=True, default="Nouveau")
    # ── Lead / Tender (BOAMP only) ────────────────────────────
    # ── Source provenance (field-level, already produced by extractors) ──
    sources        = Column(JSONB, nullable=True)
    taux_completude = Column(Float, nullable=True)
    # ── Airflow traceability ─────────────────────────────────
    dag_run_id     = Column(String, nullable=True)
    # ── Timestamps ───────────────────────────────────────────
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    def __repr__(self):
        return f"<Entreprise(identifiant={self.identifiant}, siren={self.siren}, nom={self.nom})>"


# ──────────────────────────────────────────────────────────────
#  TABLE 3 — sync_state  (unchanged)
# ──────────────────────────────────────────────────────────────

class SyncState(Base):
    __tablename__ = "sync_state"

    source            = Column(String, nullable=False, primary_key=True)
    last_sync         = Column(DateTime(timezone=True), server_default=func.now())
    nbEnregistrements = Column(Integer, nullable=False)

class RapportPDF(Base):
    __tablename__ = "rapport_pdf"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    report_date  = Column(Date, nullable=False, unique=True)  # ← unique=True ajouté    nb_runs        = Column(Integer, nullable=False)
    nb_runs=Column(Integer, nullable=False)
    nb_alertes     = Column(Integer, nullable=False)
    success_rate   = Column(Float,   nullable=False)
    generated_at     = Column(DateTime(timezone=True), server_default=func.now())
    summary_json   = Column(JSONB,   nullable=True)
    pdf_bytes      = Column(LargeBinary, nullable=False)
    file_size_kb   = Column(Integer, nullable=False)
    