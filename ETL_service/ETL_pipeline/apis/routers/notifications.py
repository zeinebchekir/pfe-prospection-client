import asyncio
import json
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi import Request, Depends
from .authDependency import require_admin,get_current_user
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# ── File d'attente globale ──────────────────────────────────────────────────
# Airflow → /send → notification_queue → dispatch_notifications → _subscribers
# ─────────────────────────────────────────────────────────────────────────────

# Un asyncio.Queue par client SSE connecté
_subscribers: dict[str, asyncio.Queue] = {}  # user_id → queue
notification_queue: asyncio.Queue = asyncio.Queue()



class AlertPayload(BaseModel):
    dag_id:   str
    task_id:  str
    message:  str
    log_file: str = ""   # nom du fichier txt, ex: sync_boamp__2026-05-04.txt


# ── SSE stream (client Vue) ───────────────────────────────────────────────────
@router.get("/stream")
async def stream_notifications(request: Request, db: Session = Depends(get_db)):
    
    # ← Ajoute ces 2 lignes
    user    = await require_admin(request)
    user_id = str(user["id"])

    queue: asyncio.Queue = asyncio.Queue()
    _subscribers[user_id] = queue          # ← dict au lieu de list

    async def event_generator():
        try:
            yield "data: {\"type\": \"connected\"}\n\n"
            while True:
                try:
                    alert = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(alert)}\n\n"
                except asyncio.TimeoutError:
                    yield "data: {\"type\": \"ping\"}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _subscribers.pop(user_id, None)   # ← nettoie par user_id

    return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
        "Cache-Control":     "no-cache",
        "X-Accel-Buffering": "no",
        # ← supprimer les headers CORS ici, le middleware s'en charge
    },
)

# ── Endpoint appelé par Airflow (etl_logger) ─────────────────────────────────
@router.post("/send")
async def send_alert(payload: AlertPayload, db: Session = Depends(get_db)):
    """
    Appelé par etl_logger quand une tâche échoue.
    Répond IMMÉDIATEMENT (pas de timeout côté Airflow).
    La distribution aux clients SSE se fait en arrière-plan via dispatch_notifications().
    """
    # ← Sauvegarde en BDD
    notif = Notification(
        dag_id=payload.dag_id,
        task_id=payload.task_id,
        message=payload.message,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    alert = {
        "type":      "failure",
        "id":        notif.id,
        "dag_id":    payload.dag_id,
        "task_id":   payload.task_id,
        "message":   payload.message,
        "log_file":  payload.log_file,
        "timestamp": notif.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
    await notification_queue.put(alert)
    return {"status": "queued", "notification_id": notif.id, "subscribers": len(_subscribers)}

# ── Tâche de fond (lancée dans main.py au startup) ───────────────────────────
async def dispatch_notifications():
    """
    Tourne en permanence.
    Lit notification_queue et distribue chaque alerte à tous les clients SSE connectés.
    """
    while True:
        alert = await notification_queue.get()
        for client_queue in list(_subscribers.values()):
            try:
                client_queue.put_nowait(alert)
            except asyncio.QueueFull:
                pass  # client trop lent — on ignore silencieusement


@router.get("/")
async def get_notifications(
    request: Request,
    db: Session = Depends(get_db)
):
    user = await require_admin(request)
    
    notifications = db.query(Notification)\
        .order_by(Notification.created_at.desc())\
        .limit(50)\
        .all()
    
    return [
        {
            "type":      "failure",
            "id":        n.id,
            "dag_id":    n.dag_id,
            "task_id":   n.task_id,
            "message":   n.message,
            "timestamp": n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "read":      n.is_read
        }
        for n in notifications
    ]


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    await require_admin(request)
    
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    
    notif.is_read = True
    db.commit()
    
    return {"status": "ok", "id": notification_id}


@router.patch("/read-all")
async def mark_all_read(
    request: Request,
    db: Session = Depends(get_db)
):
    await require_admin(request)
    
    db.query(Notification)\
      .filter(Notification.is_read == False)\
      .update({"is_read": True})
    db.commit()
    
    return {"status": "ok"}    