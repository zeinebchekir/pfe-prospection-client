from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from db.models import SyncState
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def update_sync_state(db: Session, source: str, date, count: int = 0) -> SyncState | None:
    """Met à jour ou crée l'état de synchronisation pour une source donnée."""

    # Conversion string → datetime
    if isinstance(date, str):
        try:
            sync_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            try:
                sync_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                sync_date = datetime.now()
    else:
        sync_date = date

    try:
        sync_entry = db.query(SyncState).filter(SyncState.source == source).first()

        if sync_entry:
            sync_entry.last_sync         = sync_date
            sync_entry.nbEnregistrements = count
        else:
            sync_entry = SyncState(
                source           = source,
                last_sync        = sync_date,
                nbEnregistrements= count,
            )
            db.add(sync_entry)

        db.commit()
        db.refresh(sync_entry)
        logger.info(f"[SYNC] {source} mis à jour — {sync_date} | {count} enregistrements")
        return sync_entry

    except SQLAlchemyError as e:
        db.rollback()   # ← annule la transaction en cas d'erreur
        logger.error(f"[SYNC] Erreur sauvegarde {source} : {e}")
        return None

    except Exception as e:
        db.rollback()
        logger.error(f"[SYNC] Erreur inattendue {source} : {e}")
        return None


def get_last_sync_date(db: Session, source: str) -> datetime:
    """
    Récupère la date de dernière sync.
    Retourne 2020-01-01 par défaut si aucune entrée n'existe.
    """
    try:
        state = db.query(SyncState).filter(SyncState.source == source).first()

        if state and state.last_sync:
            return state.last_sync

        logger.warning(f"[SYNC] Aucune sync trouvée pour {source} — retour 2020-01-01")
        return datetime(2020, 1, 1)

    except SQLAlchemyError as e:
        logger.error(f"[SYNC] Erreur lecture {source} : {e}")
        return datetime.now()  # ← valeur sûre par défaut