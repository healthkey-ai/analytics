from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework import status

from .models import Identity, Organization


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
            user = Identity.objects.create_user(email=email, password=password, name=name)
    except IntegrityError:
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


def _user_data(user):
    is_premium = getattr(user, "is_premium", False)
    role = "staff" if user.is_staff else ("premium" if is_premium else "user")
    return {
        "uid":        user.uid,
        "email":      user.email,
        "name":       user.name,
        "is_staff":   user.is_staff,
        "is_premium": is_premium,
        "role":       role,
    }
