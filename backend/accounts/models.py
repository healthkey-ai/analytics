import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class IdentityManager(BaseUserManager):
    def get_or_create_from_claims(self, issuer, sub, email, name=""):
        uid = f"{issuer}:{sub}"
        identity, created = self.get_or_create(
            uid=uid,
            defaults={"issuer": issuer, "sub": sub, "email": email, "name": name},
        )
        if not created and (identity.email != email or identity.name != name):
            identity.email = email
            identity.name = name
            identity.save(update_fields=["email", "name"])
        return identity

    def create_user(self, email, password=None, name="", **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        sub = str(uuid.uuid4())
        uid = f"urn:local:{sub}"
        user = self.model(
            issuer="urn:local",
            sub=sub,
            uid=uid,
            email=email,
            name=name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Identity(AbstractBaseUser, PermissionsMixin):
    """
    Unmanaged model pointing at promop's `identity` table.
    Both apps share the same DB so sessions and users are shared.
    """

    issuer = models.CharField(max_length=255)
    sub = models.CharField(max_length=255)
    uid = models.CharField(max_length=512, unique=True)
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = IdentityManager()

    USERNAME_FIELD = "uid"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        managed = False
        db_table = "identity"

    def __str__(self):
        return self.email or self.uid


class Organization(models.Model):
    """
    Organisations available in the signup dropdown.
    allowed_email_domain: if blank, any email can join; otherwise only matching domains.
    """
    name                 = models.CharField(max_length=255, unique=True)
    allowed_email_domain = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering  = ["name"]
        db_table  = "accounts_organization"

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        return not self.allowed_email_domain


class UserProfile(models.Model):
    """
    Stores analytics-specific role and organisation for each Identity.
    Managed table — migrations will create accounts_userprofile.
    db_constraint=False because the identity table is unmanaged (no FK constraint in DB).
    """
    ROLE_USER    = "user"
    ROLE_STAFF   = "staff"
    ROLE_CHOICES = [
        (ROLE_USER,  "User"),
        (ROLE_STAFF, "Staff"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        db_constraint=False,
    )
    organization = models.CharField(max_length=255, blank=True)
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)

    class Meta:
        db_table = "accounts_userprofile"

    def __str__(self):
        return f"{self.user} [{self.role}] @ {self.organization}"
