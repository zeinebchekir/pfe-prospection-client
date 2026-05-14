from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from core.db import engine
from schemas.analyse_comportementale import (
    BehavioralKpis,
    BehavioralLeadDetail,
    BehavioralLeadList,
    BehavioralLeadSummary,
    BehavioralNotification,
    RecalculateResponse,
)
from services.analyse_comportementale.import_service import create_tables, has_activity_data, recalculate_behavior


router = APIRouter()


def _rows(query: str, params: dict | None = None) -> list[dict]:
    create_tables()
    with engine.begin() as connection:
        return [dict(row._mapping) for row in connection.execute(text(query), params or {})]


def _one(query: str, params: dict | None = None) -> dict | None:
    rows = _rows(query, params)
    return rows[0] if rows else None


@router.get("/kpis", response_model=BehavioralKpis)
async def kpis(visits_period: str = Query("month", pattern="^(month|year)$")):
    if not has_activity_data():
        return {
            "total_leads": 0,
            "total_hot": 0,
            "total_warm": 0,
            "total_cold": 0,
            "average_score": None,
            "average_bounce_rate": None,
            "active_leads_last_date": 0,
            "new_visits": 0,
            "last_visit_date": None,
            "segment_distribution": [],
            "visits_evolution": [],
            "device_distribution": [],
            "score_distribution": [],
            "traffic_sources": [],
        }

    summary = _one(
        """
        SELECT
            COUNT(*)::int AS total_leads,
            COUNT(*) FILTER (WHERE s.segment = 'HOT')::int AS total_hot,
            COUNT(*) FILTER (WHERE s.segment = 'WARM')::int AS total_warm,
            COUNT(*) FILTER (WHERE s.segment = 'COLD')::int AS total_cold,
            ROUND(AVG(s.lead_score_100)::numeric, 2)::float AS average_score,
            ROUND(AVG(f.bounce_rate)::numeric, 4)::float AS average_bounce_rate,
            MAX(f.last_visit_date) AS last_visit_date
        FROM public.lead_scores s
        JOIN public.lead_behavior_features f ON f.full_visitor_id = s.full_visitor_id
        """
    ) or {}

    last_visit_date = summary.get("last_visit_date")
    active = _one(
        """
        SELECT COUNT(DISTINCT full_visitor_id)::int AS active_leads_last_date
        FROM public.lead_behavior_features
        WHERE last_visit_date = :last_visit_date
        """,
        {"last_visit_date": last_visit_date},
    )
    visits = _one(
        """
        SELECT COUNT(*)::int AS new_visits
        FROM public.lead_sessions_raw
        WHERE visit_date = :last_visit_date
        """,
        {"last_visit_date": last_visit_date},
    )

    period_unit = "year" if visits_period == "year" else "month"
    period_format = "YYYY" if period_unit == "year" else "YYYY-MM"
    period_limit = 12 if period_unit == "year" else 24

    return {
        **summary,
        "active_leads_last_date": active["active_leads_last_date"] if active else 0,
        "new_visits": visits["new_visits"] if visits else 0,
        "segment_distribution": _rows(
            """
            SELECT segment, COUNT(*)::int AS count
            FROM public.lead_scores
            GROUP BY segment
            ORDER BY CASE segment WHEN 'HOT' THEN 1 WHEN 'WARM' THEN 2 ELSE 3 END
            """
        ),
        "visits_evolution": _rows(
            f"""
            SELECT
                date_trunc('{period_unit}', visit_date)::date AS period_start,
                to_char(date_trunc('{period_unit}', visit_date), '{period_format}') AS period_label,
                COUNT(*)::int AS visits
            FROM public.lead_sessions_raw
            WHERE visit_date IS NOT NULL
            GROUP BY date_trunc('{period_unit}', visit_date)
            ORDER BY period_start DESC
            LIMIT :limit
            """
            ,
            {"limit": period_limit},
        )[::-1],
        "device_distribution": _rows(
            """
            SELECT COALESCE(device_category, 'Non disponible') AS device_category, COUNT(*)::int AS count
            FROM public.lead_sessions_raw
            GROUP BY COALESCE(device_category, 'Non disponible')
            ORDER BY count DESC
            LIMIT 8
            """
        ),
        "score_distribution": _rows(
            """
            SELECT bucket, COUNT(*)::int AS count
            FROM (
                SELECT floor(lead_score_100 / 10) * 10 AS bucket
                FROM public.lead_scores
            ) scored
            GROUP BY bucket
            ORDER BY bucket
            """
        ),
        "traffic_sources": _rows(
            """
            SELECT COALESCE(traffic_source, 'Non disponible') AS traffic_source, COUNT(*)::int AS count
            FROM public.lead_sessions_raw
            GROUP BY COALESCE(traffic_source, 'Non disponible')
            ORDER BY count DESC
            LIMIT 8
            """
        ),
    }


def _lead_summary_query(where_clause: str = "", limit_clause: str = "") -> str:
    return f"""
        SELECT
            s.rank_position,
            s.full_visitor_id,
            s.lead_score_100,
            s.segment,
            f.nombre_sessions,
            f.last_visit_date,
            (
                SELECT r.device_category
                FROM public.lead_sessions_raw r
                WHERE r.full_visitor_id = s.full_visitor_id
                ORDER BY r.visit_start_time DESC NULLS LAST, r.id DESC
                LIMIT 1
            ) AS device_category,
            f.bounce_rate
        FROM public.lead_scores s
        JOIN public.lead_behavior_features f ON f.full_visitor_id = s.full_visitor_id
        {where_clause}
        ORDER BY s.lead_score_100 DESC, s.rank_position ASC
        {limit_clause}
    """


@router.get("/top-leads", response_model=list[BehavioralLeadSummary])
async def top_leads(limit: int = Query(10, ge=1, le=100)):
    return _rows(_lead_summary_query(limit_clause="LIMIT :limit"), {"limit": limit})


@router.get("/leads", response_model=BehavioralLeadList)
async def leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    segment: str | None = Query(None),
    device_category: str | None = Query(None),
    search: str | None = Query(None),
):
    filters = []
    params = {"limit": page_size, "offset": (page - 1) * page_size}
    if segment:
        filters.append("s.segment = :segment")
        params["segment"] = segment.upper()
    if device_category:
        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM public.lead_sessions_raw r
                WHERE r.full_visitor_id = s.full_visitor_id
                  AND COALESCE(r.device_category, 'Non disponible') = :device_category
            )
            """
        )
        params["device_category"] = device_category
    if search:
        filters.append("s.full_visitor_id ILIKE :search")
        params["search"] = f"%{search.strip()}%"

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    total = _one(
        f"""
        SELECT COUNT(*)::int AS total
        FROM public.lead_scores s
        {where_clause}
        """,
        params,
    )["total"]
    results = _rows(_lead_summary_query(where_clause, "LIMIT :limit OFFSET :offset"), params)

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, math.ceil(total / page_size)),
        "results": results,
    }


@router.get("/leads/{full_visitor_id}", response_model=BehavioralLeadDetail)
async def lead_detail(full_visitor_id: str):
    lead = _one(
        """
        WITH latest_session AS (
            SELECT DISTINCT ON (full_visitor_id)
                full_visitor_id,
                device_category,
                browser,
                operating_system,
                country,
                city,
                traffic_source
            FROM public.lead_sessions_raw
            WHERE full_visitor_id = :full_visitor_id
            ORDER BY full_visitor_id, visit_start_time DESC NULLS LAST, id DESC
        )
        SELECT
            s.full_visitor_id,
            s.lead_score_100,
            s.lead_score,
            s.segment,
            s.rank_position,
            f.recency_score,
            f.nombre_sessions,
            f.first_visit_date,
            f.last_visit_date,
            f.days_since_last_visit,
            f.suspicious_activity,
            ls.device_category,
            ls.browser,
            ls.operating_system,
            ls.country,
            ls.city,
            ls.traffic_source,
            f.total_pageviews,
            f.avg_pageviews_per_session,
            f.total_hits,
            f.avg_hits_per_session,
            f.total_bounces,
            f.bounce_rate,
            f.total_time_on_site,
            f.avg_time_on_site
        FROM public.lead_scores s
        JOIN public.lead_behavior_features f ON f.full_visitor_id = s.full_visitor_id
        LEFT JOIN latest_session ls ON ls.full_visitor_id = s.full_visitor_id
        WHERE s.full_visitor_id = :full_visitor_id
        """,
        {"full_visitor_id": full_visitor_id},
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead introuvable.")

    sessions = _rows(
        """
        SELECT
            visit_id,
            session_id,
            visit_number,
            visit_start_time,
            visit_date,
            visit_hour,
            device_category,
            browser,
            operating_system,
            country,
            city,
            traffic_source,
            totals_pageviews,
            totals_hits,
            totals_bounces,
            total_time_on_site
        FROM public.lead_sessions_raw
        WHERE full_visitor_id = :full_visitor_id
        ORDER BY visit_start_time DESC NULLS LAST, id DESC
        """,
        {"full_visitor_id": full_visitor_id},
    )
    lead["sessions"] = sessions
    return lead


@router.get("/notifications", response_model=list[BehavioralNotification])
async def notifications(limit: int = Query(50, ge=1, le=200)):
    return _rows(
        """
        SELECT
            id,
            full_visitor_id,
            notification_type,
            message,
            old_score,
            new_score,
            old_segment,
            new_segment,
            last_visit_date,
            is_read,
            created_at
        FROM public.lead_notifications
        ORDER BY created_at DESC, id DESC
        LIMIT :limit
        """,
        {"limit": limit},
    )


@router.post("/recalculate", response_model=RecalculateResponse)
async def recalculate():
    return {"status": "success", **recalculate_behavior()}
