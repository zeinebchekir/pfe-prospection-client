from uuid import UUID

from fastapi import APIRouter, HTTPException

from schemas.lead_scoring import (
    LeadScoringPerformanceResponse,
    LeadScoringRescoreResponse,
    LeadScoringTrainResponse,
)
from services.lead_scoring.scoring_service import rescore_lead_by_id
from services.lead_scoring.training_service import (
    latest_performance_or_none,
    train_lead_scoring_model,
)


router = APIRouter()


@router.post("/train", response_model=LeadScoringTrainResponse)
async def train_lead_scoring():
    try:
        return train_lead_scoring_model()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rescore/{lead_id}", response_model=LeadScoringRescoreResponse)
async def rescore_lead(lead_id: UUID):
    try:
        prediction = rescore_lead_by_id(lead_id)
        return {"status": "success", "prediction": prediction}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/performance/latest", response_model=LeadScoringPerformanceResponse)
async def latest_performance():
    performance = latest_performance_or_none()
    if performance is None:
        raise HTTPException(status_code=404, detail="Aucun entraînement de modèle disponible.")
    return performance
