from django.urls import path
from . import views

urlpatterns = [
    path("form-settings/", views.form_settings),
]
