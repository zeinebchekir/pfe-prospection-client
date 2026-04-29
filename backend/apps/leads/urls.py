from django.urls import path

from .views import (
    LeadOpportunityDetailView,
    LeadOpportunityFormOptionsView,
    LeadOpportunityListCreateView,
    LeadOpportunityPerformanceView,
    LeadOpportunityTrainView,
)

app_name = "leads"

urlpatterns = [
    path("opportunities/", LeadOpportunityListCreateView.as_view(), name="lead-opportunity-list-create"),
    path("opportunities/form-options/", LeadOpportunityFormOptionsView.as_view(), name="lead-opportunity-form-options"),
    path("opportunities/performance/latest/", LeadOpportunityPerformanceView.as_view(), name="lead-opportunity-performance"),
    path("opportunities/train/", LeadOpportunityTrainView.as_view(), name="lead-opportunity-train"),
    path("opportunities/<uuid:lead_id>/", LeadOpportunityDetailView.as_view(), name="lead-opportunity-detail"),
]
