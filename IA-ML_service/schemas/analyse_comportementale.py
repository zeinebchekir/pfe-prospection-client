from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class BehavioralKpis(BaseModel):
    total_leads: int
    total_hot: int
    total_warm: int
    total_cold: int
    average_score: float | None
    average_bounce_rate: float | None
    active_leads_last_date: int
    new_visits: int
    last_visit_date: date | None
    segment_distribution: list[dict[str, Any]]
    visits_evolution: list[dict[str, Any]]
    device_distribution: list[dict[str, Any]]
    score_distribution: list[dict[str, Any]]
    traffic_sources: list[dict[str, Any]]


class BehavioralLeadSummary(BaseModel):
    rank_position: int
    full_visitor_id: str
    lead_score_100: float
    segment: str
    nombre_sessions: int
    last_visit_date: date | None
    device_category: str | None = None
    bounce_rate: float


class BehavioralLeadList(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    results: list[BehavioralLeadSummary]


class BehavioralSession(BaseModel):
    visit_id: int | None = None
    session_id: str
    visit_number: int | None = None
    visit_start_time: datetime | None = None
    visit_date: date | None = None
    visit_hour: int | None = None
    device_category: str | None = None
    browser: str | None = None
    operating_system: str | None = None
    country: str | None = None
    city: str | None = None
    traffic_source: str | None = None
    totals_pageviews: int
    totals_hits: int
    totals_bounces: int
    total_time_on_site: float


class BehavioralLeadDetail(BaseModel):
    full_visitor_id: str
    lead_score_100: float
    lead_score: float
    segment: str
    rank_position: int
    recency_score: float
    nombre_sessions: int
    first_visit_date: date | None
    last_visit_date: date | None
    days_since_last_visit: int
    suspicious_activity: int
    device_category: str | None = None
    browser: str | None = None
    operating_system: str | None = None
    country: str | None = None
    city: str | None = None
    traffic_source: str | None = None
    total_pageviews: float
    avg_pageviews_per_session: float
    total_hits: float
    avg_hits_per_session: float
    total_bounces: float
    bounce_rate: float
    total_time_on_site: float
    avg_time_on_site: float
    sessions: list[BehavioralSession]


class BehavioralNotification(BaseModel):
    id: int
    full_visitor_id: str
    notification_type: str
    message: str
    old_score: float | None = None
    new_score: float | None = None
    old_segment: str | None = None
    new_segment: str | None = None
    last_visit_date: date | None = None
    is_read: bool
    created_at: datetime


class RecalculateResponse(BaseModel):
    status: str = "success"
    sessions: int
    features: int
    scores: int
    notifications: int
