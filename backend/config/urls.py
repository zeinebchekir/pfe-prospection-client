"""URL configuration for the project."""
from django.contrib import admin
from django.urls import include, path

from apps.leads.views import (
    SegmentationLeadsView,
    SegmentationRunView,
    SegmentationSummaryView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/segmentation/summary/", SegmentationSummaryView.as_view(), name="segmentation-summary"),
    path("api/segmentation/run/", SegmentationRunView.as_view(), name="segmentation-run"),
    path("api/segmentation/leads/", SegmentationLeadsView.as_view(), name="segmentation-leads"),
    path("api/leads/", include("apps.leads.urls")),
]
