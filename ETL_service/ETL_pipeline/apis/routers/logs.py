# routers/logs.py
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/logs", tags=["logs"])

LOGS_DIR = "/opt/airflow/exports/etl_logs"



@router.get("/")
def list_log_files():
    """Retourne la liste des fichiers .txt disponibles."""
    if not os.path.exists(LOGS_DIR):
        return []
    files = sorted(
        [f for f in os.listdir(LOGS_DIR) if f.endswith(".txt")],
        reverse=True  # les plus récents en premier
    )
    return files


@router.get("/{filename}", response_class=PlainTextResponse)
def get_log_file(filename: str):
    """Retourne le contenu brut d'un fichier de log."""
    if not filename.endswith(".txt") or "/" in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    path = os.path.join(LOGS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()