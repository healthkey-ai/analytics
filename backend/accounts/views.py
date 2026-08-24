import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework import status

logger = logging.getLogger(__name__)

from .models import Identity, Organization, PasswordResetToken
from .utils import has_org_admin_access


class _EmailAlreadyExists(Exception):
    """Raised when a local account with a usable password already exists for this email."""


def _create_or_claim_signup_identity(email, password, name):
    local_identities = list(
        Identity.objects.select_for_update()
        .filter(email__iexact=email, issuer="urn:local")
        .order_by("id")
    )

    for identity in local_identities:
        if identity.has_usable_password():
            raise _EmailAlreadyExists

    if local_identities:
        identity = local_identities[0]
        identity.email = Identity.objects.normalize_email(email)
        identity.name = name
        identity.set_password(password)
        identity.save(update_fields=["email", "name", "password"])
        return identity

    return Identity.objects.create_user(email=email, password=password, name=name)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def login_view(request):
    email = request.data.get("email", "")
    password = request.data.get("password", "")
    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    request.session.cycle_key()
    login(request, user)
    get_token(request)
    return Response(_user_data(user))


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response({"detail": "Logged out."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def signup_view(request):
    email    = request.data.get("email", "").strip()
    password = request.data.get("password", "")
    name     = request.data.get("name", "").strip()

    if not email or not password:
        return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(password)
    except DjangoValidationError as exc:
        return Response({"detail": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user = _create_or_claim_signup_identity(email, password, name)
    except _EmailAlreadyExists:
        return Response({"detail": "An account with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        # DB-level uniqueness violation (e.g. uid collision or a unique constraint on email)
        return Response({"detail": "An account with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

    request.session.cycle_key()
    login(request, user, backend="accounts.backends.EmailBackend")
    get_token(request)
    return Response(_user_data(user), status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    get_token(request)
    return Response(_user_data(request.user))


@api_view(["GET"])
@permission_classes([AllowAny])
def organizations_view(request):
    """Return alphabetical org names from the Organization table for the signup dropdown."""
    orgs = list(Organization.objects.values_list("name", flat=True))
    return Response(orgs)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orgs_view(request):
    """Return org options visible to the current user.

    Staff: all distinct orgs present in PatientInfo.
    Others: their own org plus any org that has granted trust to their org
            (or email domain) via PROMOP's OrgTrust table.
    """
    from patients.models import PatientInfo
    from accounts.utils import get_visible_org_names

    if request.user.is_staff:
        orgs = (
            PatientInfo.objects
            .exclude(organization__isnull=True)
            .values_list("organization__name", flat=True)
            .distinct()
            .order_by("organization__name")
        )
        return Response([{"value": o, "label": o} for o in orgs])

    visible = get_visible_org_names(request.user)
    return Response([{"value": o, "label": o} for o in visible])


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def password_reset_request_view(request):
    email = request.data.get("email", "").strip()
    if not email:
        return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Always return 200 — never reveal whether the email exists
    try:
        identity = Identity.objects.get(email__iexact=email, issuer="urn:local")
    except Identity.DoesNotExist:
        return Response({"detail": "If that email is registered you will receive a reset link shortly."})

    token_obj = PasswordResetToken.objects.create(identity=identity)
    reset_url = f"{settings.FRONTEND_URL}?token={token_obj.token}"
    try:
        send_mail(
            subject="Reset your PRism password",
            message=(
                f"Hi {identity.name or identity.email},\n\n"
                f"Click the link below to reset your password. This link expires in 1 hour.\n\n"
                f"{reset_url}\n\n"
                f"If you did not request a password reset, you can ignore this email.\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[identity.email],
        )
    except Exception:
        logger.exception("Failed to send password reset email to %s", identity.email[:3] + "***")
    return Response({"detail": "If that email is registered you will receive a reset link shortly."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def password_reset_confirm_view(request):
    token_str = request.data.get("token", "").strip()
    password = request.data.get("password", "")

    if not token_str or not password:
        return Response({"detail": "Token and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token_obj = PasswordResetToken.objects.select_related("identity").get(token=token_str)
    except (PasswordResetToken.DoesNotExist, ValueError):
        return Response({"detail": "Invalid or expired reset link."}, status=status.HTTP_400_BAD_REQUEST)

    if not token_obj.is_valid():
        return Response({"detail": "This reset link has expired or has already been used."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(password, token_obj.identity)
    except DjangoValidationError as exc:
        return Response({"detail": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

    token_obj.identity.set_password(password)
    token_obj.identity.save(update_fields=["password"])
    token_obj.used_at = timezone.now()
    token_obj.save(update_fields=["used_at"])

    request.session.cycle_key()
    login(request, token_obj.identity, backend="accounts.backends.EmailBackend")
    get_token(request)
    return Response(_user_data(token_obj.identity))


def _user_data(user):
    is_premium = getattr(user, "is_premium", False)
    is_org_admin = has_org_admin_access(user)
    return {
        "uid":        user.uid,
        "email":      user.email,
        "name":       user.name,
        "is_staff":   user.is_staff,
        "is_premium": is_premium,
        "is_org_admin": is_org_admin,
        "role":       "admin" if user.is_superuser else "staff" if user.is_staff else "user",
    }
