from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LeadOpportunity
from .serializers import (
    LeadOpportunitySerializer,
    LeadOpportunityWriteSerializer,
)


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


def _build_opportunity_summary(queryset, params):
    aggregates = queryset.aggregate(
        total_count=Count("lead_id"),
    )
    return {
        "lead_counts": {
            "total": aggregates["total_count"] or 0,
        },
    }


def _apply_opportunity_filters(queryset, params):
    search = _query_value(params, "search")
    country = _query_value(params, "country")
    source = _query_value(params, "source")
    job_title = _query_value(params, "job_title")
    company_size = _query_value(params, "company_size")
    industry = _query_value(params, "industry")

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

    if job_title:
        queryset = queryset.filter(job_title__iexact=job_title)

    if company_size:
        queryset = queryset.filter(company_size__iexact=company_size)

    if industry:
        queryset = queryset.filter(industry__iexact=industry)

    return queryset


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

        lead = serializer.save()
        response_serializer = LeadOpportunitySerializer(lead)
        return Response(
            {
                "status": "success",
                "message": "Lead opportunite cree.",
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
        lead = serializer.save()

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
