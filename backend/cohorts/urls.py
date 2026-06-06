from django.urls import path
from . import views
from . import saved_views

urlpatterns = [
    path("form-settings/", views.form_settings),
    path("cohorts/saved/", saved_views.saved_cohort_list),
    path("cohorts/saved/<int:pk>/", saved_views.saved_cohort_detail),
    path("cohorts/saved/<int:pk>/export/", saved_views.saved_cohort_export),
]
