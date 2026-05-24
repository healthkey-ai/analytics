from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
    openapi.Info(title="Analytics API", default_version="v1"),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path("api/", include("cohorts.urls")),
    path("api/", include("metrics.urls")),
    path("swagger/", schema_view.with_ui("swagger"), name="swagger"),
]
