from pydantic import BaseModel
from typing import List

class DagSuccessRateItem(BaseModel):
    dag_id: str
    success: int
    failed: int
    up_for_retry: int
    total: int
    success_rate: float

class TaskDurationItem(BaseModel):
    task_id: str
    avg_duration_sec: float
    max_duration_sec: float

class VolumeItem(BaseModel):
    date: str
    dag_id: str
    records_processed: int

class DataQualityItem(BaseModel):
    field_name: str
    fill_rate: float   # 0.0 à 100.0

class KPISummary(BaseModel):
    global_success_rate: float
    total_runs_7d: int
    avg_pipeline_duration_min: float
    data_quality_rate: float