from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Organization

Identity = get_user_model()


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display  = ["name", "allowed_email_domain"]
    list_editable = ["allowed_email_domain"]
    search_fields = ["name", "allowed_email_domain"]
    ordering      = ["name"]


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    """Read-only view of identities — Premium is managed in PRomop's admin."""
    list_display    = ["email", "name", "is_premium", "is_staff", "is_active", "created_at"]
    search_fields   = ["email", "name", "uid"]
    list_filter     = ["is_staff", "is_active", "is_premium"]
    ordering        = ["email"]
    readonly_fields = ["uid", "issuer", "sub", "email", "name", "is_premium",
                       "created_at", "last_login", "is_active", "is_staff", "is_superuser"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
