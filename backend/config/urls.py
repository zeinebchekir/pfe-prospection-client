"""URL configuration for the project."""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/leads/", include("apps.leads.urls")),

    # ── OpenAPI / Swagger UI ───────────────────────────────────────────────
    # Schema JSON/YAML download  →  GET /api/schema/
    # Swagger UI (interactive)   →  GET /api/docs/
    # Redoc (read-only)          →  GET /api/redoc/
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/",  SpectacularRedocView.as_view(url_name="schema"),   name="redoc"),
]
