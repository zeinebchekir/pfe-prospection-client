from django.urls import path

from .views import (
    LeadOpportunityDetailView,
    LeadOpportunityFormOptionsView,
    LeadOpportunityListCreateView,
)

app_name = "leads"

urlpatterns = [
    path("opportunities/", LeadOpportunityListCreateView.as_view(), name="lead-opportunity-list-create"),
    path("opportunities/form-options/", LeadOpportunityFormOptionsView.as_view(), name="lead-opportunity-form-options"),
    path("opportunities/<uuid:lead_id>/", LeadOpportunityDetailView.as_view(), name="lead-opportunity-detail"),
]
