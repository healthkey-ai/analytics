from django.urls import path
from . import views
from .password_reset import request_password_reset, reset_password

urlpatterns = [
    path("login/", views.login_view),
    path("logout/", views.logout_view),
    path("signup/", views.signup_view),
    path("user/", views.me_view),
    path("organizations/", views.organizations_view),
    path("my-orgs/", views.my_orgs_view),
    path("password-reset/", request_password_reset),
    path("password-reset-confirm/", reset_password),
]
