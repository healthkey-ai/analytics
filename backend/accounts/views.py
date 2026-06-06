from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Identity


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email", "")
    password = request.data.get("password", "")
    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    login(request, user)
    return Response(_user_data(user))


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response({"detail": "Logged out."})


@api_view(["POST"])
@permission_classes([AllowAny])
def signup_view(request):
    email = request.data.get("email", "").strip()
    password = request.data.get("password", "")
    name = request.data.get("name", "").strip()

    if not email or not password:
        return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(password)
    except DjangoValidationError as exc:
        return Response({"detail": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

    if Identity.objects.filter(email__iexact=email, issuer="urn:local").exists():
        return Response({"detail": "An account with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

    user = Identity.objects.create_user(email=email, password=password, name=name)
    login(request, user, backend="accounts.backends.EmailBackend")
    return Response(_user_data(user), status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(_user_data(request.user))


def _user_data(user):
    return {
        "uid": user.uid,
        "email": user.email,
        "name": user.name,
        "is_staff": user.is_staff,
    }
