import os
import re

from django.db import transaction
from django.db.models import Avg, Count, F, Q
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LeadOpportunity, LeadScoringPerformance
from .serializers import (
    LeadOpportunitySerializer,
    LeadOpportunityWriteSerializer,
    LeadScoringPerformanceSerializer,
)
from .services.ml_client import (
    LeadScoringServiceError,
    get_opportunity_model_performance,
    rescore_opportunity,
    train_opportunity_model,
)


SCORING_INPUT_FIELDS = {
    "job_title",
    "industry",
    "company_size",
    "annual_revenue",
    "country",
    "city",
    "lead_source",
    "total_visits",
    "time_on_website_sec",
    "avg_page_views",
    "last_activity",
    "last_notable_activity",
    "interaction_history",
}


def _run_after_commit(callback):
    outcome = {"result": None, "error": None}

    def runner():
        try:
            outcome["result"] = callback()
        except Exception as exc:  # pragma: no cover
            outcome["error"] = exc

    transaction.on_commit(runner)
    return outcome


def _restore_lead_fields(lead_id, field_values):
    if field_values:
        LeadOpportunity.objects.filter(lead_id=lead_id).update(**field_values)


def _distinct_nonempty_values(field_name):
    values = []
    seen = set()

    for value in LeadOpportunity.objects.values_list(field_name, flat=True).iterator():
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        values.append(cleaned)

    return sorted(values, key=str.casefold)


def _query_value(params, name):
    raw_value = str(params.get(name, "") or "").strip()
    if not raw_value or raw_value.upper() == "ALL":
        return ""
    return raw_value


def _float_from_env(name, default):
    raw_value = os.getenv(name)
    if raw_value in {None, ""}:
        return float(default)

    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return float(default)


def _lead_type_thresholds():
    hot_min = _float_from_env("LEAD_SCORING_HOT_THRESHOLD", 0.75)
    warm_min = _float_from_env("LEAD_SCORING_WARM_THRESHOLD", 0.40)

    if warm_min > hot_min:
        warm_min, hot_min = hot_min, warm_min

    return {
        "hot_min": hot_min,
        "warm_min": warm_min,
        "warm_max": hot_min,
        "cold_max": warm_min,
    }


def _hot_limit(params):
    raw_value = _query_value(params, "hot_limit")
    if not raw_value:
        return 5

    try:
        limit = int(raw_value)
    except (TypeError, ValueError):
        return 5

    return limit if limit in {5, 10, 20} else 5


def _clean_text_excerpt(value, limit=180):
    cleaned = re.sub(r"\s+", " ", str(value or "")).strip()
    if not cleaned:
        return ""
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."


def _serialize_hot_lead_summary(lead):
    history_summary_full = re.sub(r"\s+", " ", str(lead.interaction_history or "")).strip()
    history_summary_preview = _clean_text_excerpt(history_summary_full)
    activity_parts = []

    if lead.last_activity:
        activity_parts.append(f"Derniere activite: {lead.last_activity}")
    if lead.last_notable_activity:
        activity_parts.append(f"Activite notable: {lead.last_notable_activity}")

    return {
        "lead_id": str(lead.lead_id),
        "company_name": lead.company_name,
        "contact_name": lead.contact_name,
        "job_title": lead.job_title,
        "country": lead.country,
        "industry": lead.industry,
        "company_size": lead.company_size,
        "lead_score_predicted": lead.lead_score_predicted,
        "lead_temperature": lead.lead_temperature,
        "history_summary": history_summary_preview or "Aucun historique de message disponible.",
        "history_summary_preview": history_summary_preview or "Aucun historique de message disponible.",
        "history_summary_full": history_summary_full or "Aucun historique de message disponible.",
        "activity_summary": " | ".join(activity_parts) if activity_parts else "Aucune activite recente renseignee.",
    }


def _build_opportunity_summary(queryset, params):
    aggregates = queryset.aggregate(
        total_count=Count("lead_id"),
        hot_count=Count("lead_id", filter=Q(lead_temperature="HOT")),
        warm_count=Count("lead_id", filter=Q(lead_temperature="WARM")),
        cold_count=Count("lead_id", filter=Q(lead_temperature="COLD")),
        average_score=Avg("lead_score_predicted", filter=Q(lead_score_predicted__isnull=False)),
    )
    return {
        "lead_counts": {
            "total": aggregates["total_count"] or 0,
            "hot": aggregates["hot_count"] or 0,
            "warm": aggregates["warm_count"] or 0,
            "cold": aggregates["cold_count"] or 0,
        },
        "average_score": float(aggregates["average_score"]) if aggregates["average_score"] is not None else None,
        "top_hot_limit": 0,
        "top_hot_leads": [],
    }


def _apply_opportunity_filters(queryset, params):
    search = _query_value(params, "search")
    country = _query_value(params, "country")
    source = _query_value(params, "source")
    temperature = _query_value(params, "temperature")
    job_title = _query_value(params, "job_title")
    company_size = _query_value(params, "company_size")
    industry = _query_value(params, "industry")
    score_order = _query_value(params, "score_order").lower()

    if search:
        queryset = queryset.filter(
            Q(company_name__icontains=search)
            | Q(contact_name__icontains=search)
            | Q(email__icontains=search)
            | Q(job_title__icontains=search)
            | Q(industry__icontains=search)
            | Q(company_size__icontains=search)
            | Q(city__icontains=search)
            | Q(country__icontains=search)
            | Q(lead_source__icontains=search)
        )

    if country:
        queryset = queryset.filter(country__iexact=country)

    if source:
        queryset = queryset.filter(lead_source__iexact=source)

    if temperature:
        queryset = queryset.filter(lead_temperature__iexact=temperature)

    if job_title:
        queryset = queryset.filter(job_title__iexact=job_title)

    if company_size:
        queryset = queryset.filter(company_size__iexact=company_size)

    if industry:
        queryset = queryset.filter(industry__iexact=industry)

    if score_order == "asc":
        queryset = queryset.order_by(
            F("lead_score_predicted").asc(nulls_last=True),
            "-last_modified_date",
            "company_name",
        )
    elif score_order == "desc":
        queryset = queryset.order_by(
            F("lead_score_predicted").desc(nulls_last=True),
            "-last_modified_date",
            "company_name",
        )

    return queryset


def _hot_precision_ratio():
    aggregates = LeadOpportunity.objects.aggregate(
        hot_total=Count("lead_id", filter=Q(lead_temperature="HOT", lead_score__isnull=False)),
        hot_converted=Count("lead_id", filter=Q(lead_temperature="HOT", lead_score=1)),
    )
    hot_total = aggregates["hot_total"] or 0
    hot_converted = aggregates["hot_converted"] or 0

    if hot_total == 0:
        return None

    return hot_converted / hot_total


def _cold_precision_ratio():
    aggregates = LeadOpportunity.objects.aggregate(
        cold_total=Count("lead_id", filter=Q(lead_temperature="COLD", lead_score__isnull=False)),
        cold_not_converted=Count("lead_id", filter=Q(lead_temperature="COLD", lead_score=0)),
    )
    cold_total = aggregates["cold_total"] or 0
    cold_not_converted = aggregates["cold_not_converted"] or 0

    if cold_total == 0:
        return None

    return cold_not_converted / cold_total


def _serialize_performance(performance):
    if not performance:
        return None

    serialized = LeadScoringPerformanceSerializer(performance).data if hasattr(performance, "_meta") else dict(performance)
    serialized["lead_type_thresholds"] = _lead_type_thresholds()
    serialized["hot_precision"] = _hot_precision_ratio()
    serialized["cold_precision"] = _cold_precision_ratio()
    return serialized


class LeadOpportunityPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    summary = None

    def get_paginated_response(self, data):
        return Response(
            {
                "status": "success",
                "count": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages,
                "summary": self.summary or {},
                "results": data,
            }
        )


class LeadOpportunityListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LeadOpportunityPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LeadOpportunityWriteSerializer
        return LeadOpportunitySerializer

    def get_queryset(self):
        queryset = LeadOpportunity.objects.filter(is_commercial_created=True)
        return _apply_opportunity_filters(queryset, self.request.query_params)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        summary = _build_opportunity_summary(queryset, request.query_params)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        self.paginator.summary = summary
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            lead = serializer.save()
            scoring_state = _run_after_commit(lambda: rescore_opportunity(lead.lead_id))

        if scoring_state["error"]:
            LeadOpportunity.objects.filter(lead_id=lead.lead_id).delete()
            exc = scoring_state["error"]
            return Response(
                {
                    "status": "error",
                    "message": "Le lead a ete rejete car le scoring automatique a echoue.",
                    "detail": str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        lead.refresh_from_db()
        response_serializer = LeadOpportunitySerializer(lead)
        return Response(
            {
                "status": "success",
                "message": "Lead opportunite cree et score automatiquement.",
                "lead": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class LeadOpportunityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LeadOpportunity.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "lead_id"

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return LeadOpportunityWriteSerializer
        return LeadOpportunitySerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        changed_fields = set(serializer.validated_data.keys())
        original_values = {field: getattr(instance, field) for field in changed_fields}
        original_values["last_modified_date"] = instance.last_modified_date
        requires_rescore = bool(changed_fields.intersection(SCORING_INPUT_FIELDS))

        with transaction.atomic():
            lead = serializer.save()
            scoring_state = _run_after_commit(lambda: rescore_opportunity(lead.lead_id)) if requires_rescore else None

        if requires_rescore and scoring_state and scoring_state["error"]:
            _restore_lead_fields(lead.lead_id, original_values)
            lead.refresh_from_db()
            exc = scoring_state["error"]
            return Response(
                {
                    "status": "error",
                    "message": "La mise a jour a ete annulee car le rescoring a echoue.",
                    "detail": str(exc),
                    "lead": LeadOpportunitySerializer(lead).data,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if requires_rescore:
            lead.refresh_from_db()

        return Response(
            {
                "status": "success",
                "lead": LeadOpportunitySerializer(lead).data,
            }
        )


class LeadOpportunityFormOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "status": "success",
                "options": {
                    "countries": _distinct_nonempty_values("country"),
                    "industries": _distinct_nonempty_values("industry"),
                    "company_sizes": _distinct_nonempty_values("company_size"),
                    "job_titles": _distinct_nonempty_values("job_title"),
                    "lead_sources": _distinct_nonempty_values("lead_source"),
                    "last_activities": _distinct_nonempty_values("last_activity"),
                    "last_notable_activities": _distinct_nonempty_values("last_notable_activity"),
                },
            }
        )


class LeadOpportunityPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            performance = get_opportunity_model_performance()
        except LeadScoringServiceError:
            performance = LeadScoringPerformance.objects.order_by("-last_training_date", "-id").first()
        return Response(
            {
                "status": "success",
                "performance": _serialize_performance(performance),
            }
        )


class LeadOpportunityTrainView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            performance = train_opportunity_model()
        except LeadScoringServiceError as exc:
            return Response(
                {
                    "status": "error",
                    "message": "Impossible de lancer l'entrainement du modele.",
                    "detail": str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "status": "success",
                "performance": _serialize_performance(performance),
            }
        )
