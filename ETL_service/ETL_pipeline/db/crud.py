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


from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func, case as sa_case, or_

# Champs "propriété" de chaque source — seuls ces champs sont touchés lors d'un update
DATAGOUV_OWN_FIELDS = {
    "nom", "ville", "code_postal", "pays",
    "secteur_activite", "forme_juridique", "taille_entrep",
    "categorie_entreprise", "nb_locaux", "ca",
    "date_creation_entreprise", "date_derniere_modif_site",
    "dirigeants",
}

BOAMP_OWN_FIELDS = {
    "siret", "telephone", "nom",
    "adresse_email", "info_boamp",
     "secteur_activite", "forme_juridique",
     "ville", "code_postal", "pays",
}

TRACING_FIELDS = {"sources", "dag_run_id", "date_scraping"}
# ──────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────


def _to_date(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date_type):
        # date pure → ajoute 00:00:00
        return datetime(val.year, val.month, val.day, 0, 0, 0)
    try:
        val_str = str(val).strip()
        # Formats à essayer dans l'ordre
        formats = [
            "%Y-%m-%dT%H:%M:%S",   # 2026-04-10T14:32:19
            "%Y-%m-%d %H:%M:%S",   # 2026-04-10 14:32:19
            "%Y-%m-%dT%H:%M",      # 2026-04-10T14:32
            "%Y-%m-%d",            # 2026-04-10 → 00:00:00
            "%d/%m/%Y %H:%M:%S",   # 10/04/2026 14:32:19
            "%d/%m/%Y %H:%M",      # 10/04/2026 14:32
            "%d/%m/%Y",            # 10/04/2026 → 00:00:00
        ]
        for fmt in formats:
            try:
                return datetime.strptime(val_str, fmt)
            except ValueError:
                continue

        # Dernier recours : fromisoformat
        return datetime.fromisoformat(val_str)

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
                date_scraping        = _to_date(date_scraping),
                updated_on_source_at = updated_on_source_at,
             

            ))

        db.add_all(rows)
        db.flush()
        # Inject the generated ID back into the dictionaries
        for rec, row in zip(records, rows):
            rec["_raw_lead_id"] = row.id
            
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
    print("tauuuuuuuuuuuuuuuuuuuuux",entreprise.get("taux_completude"))

    boamp_data = entreprise.get("data_from_boamp") or {}
    # Provide identifiant exactly as needed by the PostgreSQL schema (VARCHAR 25)
    if source == "dataGouv":
        _id_raw = entreprise.get("siren")
    else:
        _id_raw = boamp_data.get("idweb") or entreprise.get("siret") or entreprise.get("siren")
    
    _identifiant = str(_id_raw) if _id_raw else None
    
    return Entreprise(
        identifiant          = _identifiant,
        raw_lead_id          = entreprise.get("_raw_lead_id"),
        siren                = entreprise.get("siren"),
        siret                = entreprise.get("siret"),
        nom                  = entreprise.get("nom"),
        description          = " -",
        ville                = entreprise.get("ville"),
        code_postal          = str(entreprise.get("code_postal")).strip() if entreprise.get("code_postal") else None,
        pays                 = entreprise.get("pays", "France"),
        secteur_activite     = entreprise.get("secteur_activite"),
        forme_juridique      = entreprise.get("forme_juridique"),
        taille_entrep        = entreprise.get("taille_entrep"),
        categorie_entreprise = entreprise.get("categorie_entreprise"),
        website_url          = "-",
        linkedin_url         = "-",
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
        date_derniere_modif_site = _to_date(entreprise.get("dateDerniereModification")) if source == "dataGouv" else _to_date(entreprise.get("dateMAJ")),
        date_scraping        = _to_date(date_scraping),
        taux_completude      = entreprise.get("taux_completude"),
        statut="Nouveau"
        
        
    )





def _build_set_clause(stmt, owned_fields: set) -> dict:
    """
    Pour chaque champ appartenant à la source :
      - si date entrante >= date en base  → on écrase
      - si date entrante <  date en base  → on garde la valeur en base
      - si date en base est NULL          → on écrase toujours
    Les champs de l'autre source ne sont JAMAIS dans le SET → préservés automatiquement.
    """
    set_clause = {}

    for field in owned_fields:
        incoming  = stmt.excluded[field]
        in_base   = getattr(Entreprise, field)

        if field == "date_derniere_modif_site":
            # Toujours garder la plus récente
            set_clause[field] = func.greatest(in_base, incoming)
        else:
            # Écraser seulement si date entrante >= date en base (ou base NULL)
            set_clause[field] = sa_case(
                (
                    or_(
                        in_base == None,
                        Entreprise.date_derniere_modif_site == None,
                        stmt.excluded.date_derniere_modif_site >= Entreprise.date_derniere_modif_site,
                    ),
                    incoming,
                ),
                else_=in_base,
            )

    # Traçabilité : toujours mise à jour quelle que soit la source
    for field in TRACING_FIELDS:
        set_clause[field] = stmt.excluded[field]

    set_clause["updated_at"] = func.now()
    return set_clause


def _find_conflict_target(db: Session, obj: Entreprise) -> str | None:
    """
    Cherche si l'entreprise existe déjà en base par siren, siret,
    ou (nom + code_postal) — dans cet ordre de priorité.
    Retourne l'identifiant existant ou None.
    """
    if obj.siren:
        exists = db.query(Entreprise.identifiant)\
                   .filter(Entreprise.siren == obj.siren)\
                   .first()
        if exists:
            return exists[0]

    if obj.siret:
        exists = db.query(Entreprise.identifiant)\
                   .filter(Entreprise.siret == obj.siret)\
                   .first()
        if exists:
            return exists[0]

    if obj.nom and obj.code_postal:
        exists = db.query(Entreprise.identifiant)\
                   .filter(
                       Entreprise.nom         == obj.nom,
                       Entreprise.code_postal == obj.code_postal,
                   ).first()
        if exists:
            return exists[0]

    return None  # pas de doublon → INSERT pur


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
        logger.warning(f"[CLEAN INSERT] {source}: empty records list.")
        return 0

    is_datagouv  = source == "dataGouv"
    owned_fields = DATAGOUV_OWN_FIELDS if is_datagouv else BOAMP_OWN_FIELDS
    new_inserts = updates = skipped = 0

    # Cache en mémoire pour éviter d'insérer des doublons (SIREN identiques)
    # dans le même batch, car la BD ne les voit pas encore sans autoflush
    batch_seen_siren = {}
    batch_seen_siret = {}

    try:
        with db.no_autoflush:
            for rec in records:
                try:
                    obj = _map_data(
                        rec=rec, source=source,
                        date_scraping=date_scraping,
                        dag_run_id=dag_run_id,
                    )
                except Exception as e:
                    logger.warning(f"[CLEAN INSERT] {source}: skipping map — {e}")
                    skipped += 1
                    continue

                if not obj.identifiant:
                    logger.warning(f"[CLEAN INSERT] {source}: skipping insert, missing identifiant.")
                    skipped += 1
                    continue

                existing_id = _find_conflict_target(db, obj)

                # Vérification dans le cache du batch (si non trouvé en base)
                if not existing_id:
                    if obj.siren and obj.siren in batch_seen_siren:
                        existing_id = batch_seen_siren[obj.siren]
                    elif obj.siret and obj.siret in batch_seen_siret:
                        existing_id = batch_seen_siret[obj.siret]

                if existing_id:
                    # On force l'identifiant à correspondre à la base pour déclencher l'UPSERT
                    obj.identifiant = existing_id
                    
                    row_dict = {
                        c.name: getattr(obj, c.name)
                        for c in Entreprise.__table__.columns
                        if c.name not in ("created_at", "updated_at")
                    }
                    stmt = pg_insert(Entreprise).values(**row_dict)
                    set_clause = _build_set_clause(stmt, owned_fields)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["identifiant"],
                        set_=set_clause,
                    )
                    db.execute(stmt)
                    updates += 1
                else:
                    row_dict = {
                        c.name: getattr(obj, c.name)
                        for c in Entreprise.__table__.columns
                        if c.name not in ("created_at", "updated_at")
                    }
                    db.execute(Entreprise.__table__.insert().values(**row_dict))
                    
                    # Store in cache for subsequent records in the same batch
                    if obj.siren:
                        batch_seen_siren[obj.siren] = obj.identifiant
                    if obj.siret:
                        batch_seen_siret[obj.siret] = obj.identifiant
                        
                    new_inserts += 1

        db.commit()
        logger.info(
            f"[CLEAN INSERT] {source}: "
            f"{new_inserts} nouvelles lignes | "
            f"{updates} mises à jour | "
            f"{skipped} ignorées"
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[CLEAN INSERT] {source}: DB error — {e}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[CLEAN INSERT] {source}: unexpected error — {e}")
        raise

    return new_inserts + updates
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



def update_clean_lead(db: Session, lead_id: int, **kwargs) -> bool:
    try:
        lead = db.query(Entreprise).filter(Entreprise.id == lead_id).first()
        if not lead:
            logger.warning(f"[UPDATE] Lead with ID {lead_id} not found.")
            return False
        
        for key, value in kwargs.items():
            setattr(lead, key, value)
            
        db.commit()
        logger.info(f"[UPDATE] Lead with ID {lead_id} updated successfully.")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[UPDATE] DB error — {e}")
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"[UPDATE] Unexpected error — {e}")
        return False