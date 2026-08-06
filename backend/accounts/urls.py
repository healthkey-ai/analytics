from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view),
    path("logout/", views.logout_view),
    path("signup/", views.signup_view),
    path("user/", views.me_view),
    path("organizations/", views.organizations_view),
    path("my-orgs/", views.my_orgs_view),
    path("password-reset/", views.password_reset_request_view),
    path("password-reset/confirm/", views.password_reset_confirm_view),
]
