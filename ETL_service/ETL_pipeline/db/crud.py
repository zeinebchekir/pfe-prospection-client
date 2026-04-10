"""
crud.py — Synchronous SQLAlchemy CRUD helpers for the ETL pipeline.

Two public pairs:
  insert_raw_leads(db, records, source, dag_run_id)  → int (rows inserted)
  insert_clean_leads(db, records, source, dag_run_id) → int (rows inserted)

  query_raw_leads(db, source, limit)   → list[RawLead]
  query_clean_leads(db, source, siren, ville, limit) → list[CleanLead]

Source differentiation
──────────────────────
  DataGouv records : company-only data, lead fields left as NULL
  BOAMP records    : company + lead data, JSONB donnees blob preserved in raw table

BOAMP `donnees` JSONB
──────────────────────
The raw BOAMP record contains a `donnees` key whose schema varies by
`perimetre` (MAPA / FNSimple / DIRECTIVE-24 / DIRECTIVE-25 / AUTRE).
`insert_raw_leads` detects BOAMP source and copies `donnees` (or the full
`raw_data` dict entry under key 'donnees') into the `donnees_boamp` column.
"""

import logging
from datetime import date as date_type, datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db.models import RawLead, Entreprise
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────


def _to_date(val):
    if val is None:
        return None
    if isinstance(val, date_type):   # ← utilise l'alias partout
        return val
    try:
        return datetime.fromisoformat(str(val)).date()
    except (ValueError, TypeError):
        return None

def _to_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# ──────────────────────────────────────────────────────────────
#  RAW INSERT
# ──────────────────────────────────────────────────────────────

def insert_raw_leads(
    db: Session,
    records: list[dict],
    source: str,
    dag_run_id: str | None = None,
    date_scraping: date_type | None = None,
) -> int:
    """
    Bulk-insert extracted records (pre-cleaning) into `raw_leads`.

    Args:
        db         : SQLAlchemy session
        records    : list of flat dicts from extract_data_from_datagouv()
                     or get_global_information()
        source     : 'dataGouv' or 'BOAMP'
        dag_run_id : Airflow run_id for traceability

    Returns:
        Number of rows successfully inserted.
    """
    if not records:
        logger.warning(f"[RAW INSERT] {source}: empty records list, nothing to insert.")
        return 0

    inserted = 0
    is_boamp = source.upper() == "BOAMP"

    try:
        rows = []
        for rec in records:
            updated_on_source_at = None
            # For BOAMP: preserve the raw `donnees` blob separately
            if is_boamp:
                updated_on_source_at = _to_date(rec.get("dateMAJ"))
            else:
                updated_on_source_at = _to_date(rec.get("dateDerniereModification"))    
            rows.append(RawLead(
                source        = source,
                raw_data      = rec,
                dag_run_id    = dag_run_id,
                updated_on_source_at = updated_on_source_at,
                date_scraping        = _to_date(date_scraping),

            ))

        db.bulk_save_objects(rows)
        db.commit()
        inserted = len(rows)
        logger.info(f"[RAW INSERT] {source}: {inserted} rows inserted into raw_leads.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[RAW INSERT] {source}: DB error — {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"[RAW INSERT] {source}: unexpected error — {e}")

    return inserted


# ──────────────────────────────────────────────────────────────
#  CLEAN INSERT
# ──────────────────────────────────────────────────────────────

def _map_data(rec: dict, source: str,date_scraping: date_type | None,dag_run_id: str | None) -> Entreprise:
    """
    Map a cleaned DataGouv entreprise dict → CleanLead ORM object.

    Expected keys (from DataGouvCleaner.clean_entreprise + datagouv_extractor):
      siren, nom, secteur_activite, forme_juridique, taille_entrep,
      categorie_entreprise, nb_locaux, ca, ville, code_postal, pays,
      dateCreation, dateDerniereModification, sourceEntreprise, sources
    """
    # Handle nested structure from BaseCleaner: {"entreprise": {...}, "lead": None}
    entreprise = rec.get("entreprise", rec)
    boamp_data = entreprise.get("data_from_boamp") or {}
    return Entreprise(
        identifiant          = entreprise.get("siren") if source=="dataGouv" else entreprise.get("idAvis"),
        siren                = entreprise.get("siren"),
        siret                = entreprise.get("siret"),
        nom                  = entreprise.get("nom"),
        ville                = entreprise.get("ville"),
        code_postal          = str(entreprise.get("code_postal")).strip() if entreprise.get("code_postal") else None,
        pays                 = entreprise.get("pays", "France"),
        secteur_activite     = entreprise.get("secteur_activite"),
        forme_juridique      = entreprise.get("forme_juridique"),
        taille_entrep        = entreprise.get("taille_entrep"),
        categorie_entreprise = entreprise.get("categorie_entreprise"),
        nb_locaux            = _to_int(entreprise.get("nb_locaux")),
        ca                   = _to_float(entreprise.get("ca")),
        date_creation_entreprise = _to_date(entreprise.get("dateCreation")),
        telephone=entreprise.get("num_tel"),
        adresse_email=boamp_data.get("adresse_email") if boamp_data else None,
        # Lead fields: NULL for DataGouv
        info_boamp           = boamp_data if source == "BOAMP" else None,
        dirigeants           = entreprise.get("dirigeants"),
        sources              = entreprise.get("sources"),
        dag_run_id           = dag_run_id,
        date_derniere_modif_site = _to_date(entreprise.get("dateDerniereModification")) if source == "dataGouv" else entreprise.get("dateMAJ"),
        date_scraping        = _to_date(date_scraping),
        
    )



def insert_clean_leads(
    db: Session,
    records: list[dict],
    source: str,
    dag_run_id: str | None = None,
    date_scraping: date_type | None = None,
) -> int:
    """
    Upsert cleaned records into the `entreprise` table.

    Behaviour by source
    ───────────────────
    BOAMP   : full UPSERT — updates all enrichable columns when the identifiant
              already exists.  This allows subsequent BOAMP sync runs to refresh
              company data (dirigeants, CA, taille, etc.) for known entreprises.
    dataGouv: INSERT … ON CONFLICT DO NOTHING — DataGouv is the authoritative
              initial load; existing rows are not overwritten to preserve any
              manual edits made through the CRM.

    Args:
        db         : SQLAlchemy session
        records    : list of cleaned dicts from DataGouvCleaner or BoampCleaner
                     each in shape {"entreprise": {...}, "lead": {...}|None}
        source     : 'dataGouv' or 'BOAMP'
        dag_run_id : Airflow run_id for traceability
        date_scraping : scraping date watermark

    Returns:
        Number of rows affected (inserted + updated).
    """
    if not records:
        logger.warning(f"[CLEAN INSERT] {source}: empty records list, nothing to insert.")
        return 0

    inserted = 0

    try:
        rows = []
        for rec in records:
            try:
                orm_obj = _map_data(rec=rec, source=source,
                                   date_scraping=date_scraping,
                                   dag_run_id=dag_run_id)
                rows.append({
                    c.key: getattr(orm_obj, c.key)
                    for c in orm_obj.__mapper__.column_attrs
                })
            except Exception as e:
                logger.warning(f"[CLEAN INSERT] {source}: skipping record mapping — {e}")

        if not rows:
            logger.warning(f"[CLEAN INSERT] {source}: all records failed mapping.")
            return 0

        insert_stmt = pg_insert(Entreprise).values(rows)

        if source.upper() == "BOAMP":
            # Full UPSERT for BOAMP: update enrichable fields on conflict
            # Columns excluded from update: primary key + immutable audit fields
            _excluded = {"identifiant", "raw_lead_id", "created_at"}
            update_cols = {
                col.name: insert_stmt.excluded[col.name]
                for col in Entreprise.__table__.columns
                if col.name not in _excluded
            }
            stmt = insert_stmt.on_conflict_do_update(
                index_elements=["identifiant"],
                set_=update_cols,
            )
            logger.info(f"[CLEAN INSERT] {source}: using UPSERT (update on conflict).")
        else:
            # DataGouv: preserve existing rows, do not overwrite CRM edits
            stmt = insert_stmt.on_conflict_do_nothing(index_elements=["identifiant"])
            logger.info(f"[CLEAN INSERT] {source}: using INSERT IGNORE (do nothing on conflict).")

        result = db.execute(stmt)
        db.commit()
        inserted = result.rowcount if result.rowcount >= 0 else len(rows)
        logger.info(f"[CLEAN INSERT] {source}: {inserted} rows affected in entreprise.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[CLEAN INSERT] {source}: DB error — {e}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[CLEAN INSERT] {source}: unexpected error — {e}")
        raise

    return inserted


# ──────────────────────────────────────────────────────────────
#  QUERY HELPERS
# ──────────────────────────────────────────────────────────────

def query_raw_leads(
    db: Session,
    source: str | None = None,
    limit: int = 100,
    
) -> list[RawLead]:
    """
    Query raw_leads with optional source filter.

    Args:
        source : 'dataGouv', 'BOAMP', or None (returns all)
        limit  : max rows returned

    Returns:
        List of RawLead ORM objects.
    """
    q = db.query(RawLead)
    if source:
        q = q.filter(RawLead.source == source)
    return q.order_by(RawLead.loaded_at.desc()).limit(limit).all()


def query_clean_leads(
    db: Session,
    source: str | None = None,
    siren: str | None = None,
    ville: str | None = None,
    status_lead: str | None = None,
    limit: int = 100,
) -> list[Entreprise]:
    """
    Query clean_leads with optional filters.

    Args:
        source      : 'dataGouv', 'BOAMP', or None
        siren       : exact SIREN match
        ville       : case-insensitive substring match on ville
        status_lead : e.g. 'NOUVEAU' (BOAMP leads only)
        limit       : max rows returned

    Returns:
        List of CleanLead ORM objects.

    Example queries
    ───────────────
    # All DataGouv companies
    query_clean_leads(db, source='dataGouv')

    # All BOAMP new leads in Paris
    query_clean_leads(db, source='BOAMP', ville='PARIS', status_lead='NOUVEAU')

    # Lookup a specific company by SIREN
    query_clean_leads(db, siren='123456789')
    """
    q = db.query(Entreprise)
    if source:
        q = q.filter(Entreprise.source == source)
    if siren:
        q = q.filter(Entreprise.siren == siren)
    if ville:
        q = q.filter(Entreprise.ville.ilike(f"%{ville}%"))
    if status_lead:
        q = q.filter(Entreprise.status_lead == status_lead)
    return q.order_by(Entreprise.created_at.desc()).limit(limit).all()
