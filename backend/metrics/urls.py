from django.urls import path
from . import views
from .export_views import chart_export

urlpatterns = [
    path("metrics/", views.metrics),
    path("export/", chart_export, name="chart_export"),
]
