from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LeadScoringPrediction(BaseModel):
    lead_id: UUID
    lead_score_probability: float = Field(..., ge=0.0, le=1.0)
    lead_score_predicted: int = Field(..., ge=0, le=100)
    lead_temperature: str
    model_version: str
    scored_at: datetime
    feature_values: dict[str, Any]


class LeadScoringRescoreResponse(BaseModel):
    status: str = "success"
    prediction: LeadScoringPrediction


class LeadScoringFeatureImportance(BaseModel):
    feature: str
    importance: float


class LeadScoringPerformanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_name: str
    model_version: str
    best_model: str
    stack_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    threshold: float
    training_dataset_size: int
    feature_count: int
    last_training_date: datetime
    top_importances: list[LeadScoringFeatureImportance] = []


class LeadScoringTrainResponse(LeadScoringPerformanceResponse):
    status: str = "success"
    rescored_rows: int
