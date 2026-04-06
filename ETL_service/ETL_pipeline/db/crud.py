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
from datetime import date as date_type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models import RawLead, Entreprise

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────

def _to_date(value) -> date_type | None:
    """Convert a string 'YYYY-MM-DD' or None to a Python date."""
    if value is None:
        return None
    if isinstance(value, date_type):
        return value
    try:
        from datetime import datetime
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
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
                updated_on_source_at = rec.get("date_scraping"),

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

def _map_data(rec: dict, source: str,dag_run_id: str | None) -> Entreprise:
    """
    Map a cleaned DataGouv entreprise dict → CleanLead ORM object.

    Expected keys (from DataGouvCleaner.clean_entreprise + datagouv_extractor):
      siren, nom, secteur_activite, forme_juridique, taille_entrep,
      categorie_entreprise, nb_locaux, ca, ville, code_postal, pays,
      dateCreation, dateDerniereModification, sourceEntreprise, sources
    """
    # Handle nested structure from BaseCleaner: {"entreprise": {...}, "lead": None}
    entreprise = rec.get("entreprise", rec)

    return Entreprise(
        identifiant          = entreprise.get("siret") if source=="datagouv" else entreprise.get("idAvis"),
        source               = source,
        siren                = entreprise.get("siren"),
        siret                = entreprise.get("siret"),
        nom                  = entreprise.get("nom"),
        ville                = entreprise.get("ville"),
        code_postal          = _to_int(entreprise.get("code_postal")),
        pays                 = entreprise.get("pays", "France"),
        secteur_activite     = entreprise.get("secteur_activite"),
        forme_juridique      = entreprise.get("forme_juridique"),
        taille_entrep        = entreprise.get("taille_entrep"),
        categorie_entreprise = entreprise.get("categorie_entreprise"),
        nb_locaux            = _to_int(entreprise.get("nb_locaux")),
        ca                   = _to_float(entreprise.get("ca")),
        date_creation_entreprise = _to_date(entreprise.get("dateCreation")),
        # Lead fields: NULL for DataGouv
        info_boamp           = entreprise.get("data_from_boamp"),
        sources              = entreprise.get("sources"),
        dag_run_id           = dag_run_id,
        date_derniere_modif_site = _to_date(entreprise.get("dateDerniereModification")) if source == "dataGouv" else entreprise.get("dateMAJ"),
        date_scraping        = _to_date(entreprise.get("date_scraping")),
        
    )


# def _map_data(rec: dict, dag_run_id: str | None,source: str) -> CleanLead:
#     """
#     Map a cleaned BOAMP record dict → CleanLead ORM object.

#     BOAMP records come out of BaseCleaner as:
#       {"entreprise": {...}, "lead": {...}}

#     Entreprise keys (from BoampCleaner.clean_entreprise + data_extraction):
#       siret, nom, secteur_activite, forme_juridique, ville, code_postal,
#       adresse_email, pays, telephone, sourceEntreprise

#     Lead keys (from BoampCleaner.clean_lead):
#       besoin, date_limite, titulaire, nature, lienOffre, status_lead,
#       info_complementaire
#     """
#     entreprise = rec.get("entreprise", rec)

#     # Derive SIREN from SIRET when available
#     raw_siret = entreprise.get("siret")
#     siren = None
#     if raw_siret and len(str(raw_siret)) >= 9:
#         siren = str(raw_siret)[:9]

#     return CleanLead(
#         source               = "BOAMP",
#         siren                = siren,
#         siret                = raw_siret,
#         nom                  = entreprise.get("nom"),
#         ville                = entreprise.get("ville"),
#         code_postal          = _to_int(entreprise.get("code_postal")),
#         pays                 = entreprise.get("pays", "France"),
#         secteur_activite     = entreprise.get("secteur_activite"),
#         forme_juridique      = entreprise.get("forme_juridique"),
#         # DataGouv-only fields: NULL
#         taille_entrep        = None,
#         categorie_entreprise = None,
#         nb_locaux            = None,
#         ca                   = None,
#         date_creation        = None,
#         date_derniere_modif  = None,
#         data_from_boamp      = entreprise.get("data_from_boamp") if source == "BOAMP" else None,
#         # Contact
#         telephone            = entreprise.get("num_tel"),
#         adresse_email        = entreprise.get("adresse_email"),
#         # Lead / tender
#         besoin               = entreprise.get("besoin"),
#         date_limite          = _to_date(entreprise.get("date_limite")),
#         titulaire            = entreprise.get("titulaire"),
#         nature               = entreprise.get("nature"),
#         lien_offre           = entreprise.get("lienOffre"),
#         status_lead          = entreprise.get("status_lead", "NOUVEAU"),
#         info_complementaire  = entreprise.get("info_complementaire"),
#         sources              = entreprise.get("sources"),
#         dag_run_id           = dag_run_id,
#         updated_on_source_at=entreprise.get("dateMAJ"),
#     )


def insert_clean_leads(
    db: Session,
    records: list[dict],
    source: str,
    dag_run_id: str | None = None,

) -> int:
    """
    Bulk-insert cleaned records into `clean_leads`.

    Args:
        db         : SQLAlchemy session
        records    : list of cleaned dicts from DataGouvCleaner or BoampCleaner
                     each in shape {"entreprise": {...}, "lead": {...}|None}
        source     : 'dataGouv' or 'BOAMP'
        dag_run_id : Airflow run_id for traceability

    Returns:
        Number of rows successfully inserted.
    """
    if not records:
        logger.warning(f"[CLEAN INSERT] {source}: empty records list, nothing to insert.")
        return 0

    inserted = 0
    mapper   = _map_data

    try:
        rows = []
        for rec in records:
            try:
                entreprise = rec.get("entreprise", rec)
                source_rec = entreprise.get("sourceEntreprise", source)
                rows.append(_map_data(entreprise, source_rec, dag_run_id))
            except Exception as e:
                logger.warning(f"[CLEAN INSERT] {source}: skipping record — {e}")

        db.bulk_save_objects(rows)
        db.commit()
        inserted = len(rows)
        logger.info(f"[CLEAN INSERT] {source}: {inserted} rows inserted into clean_leads.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[CLEAN INSERT] {source}: DB error — {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"[CLEAN INSERT] {source}: unexpected error — {e}")

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
