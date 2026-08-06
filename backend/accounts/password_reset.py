"""
Self-service password reset via an emailed single-use link.

The link carries Django's signed reset token (tied to the account's password
hash + last_login) so it is invalidated once the password changes or after
PASSWORD_RESET_TIMEOUT seconds.  Email is delivered through the configured
backend (Mailgun/anymail in production, console in development).
"""
import logging

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import Identity

logger = logging.getLogger(__name__)

# Same message for all outcomes — prevents account enumeration.
_RESET_OK = {"detail": "If an account exists with that email, a reset link has been sent."}


class _EmailError(Exception):
    pass


# Dedicated throttle scopes so reset endpoints don't share the login/signup bucket.
class _ResetRequestThrottle(AnonRateThrottle):
    scope = "password_reset_request"


class _ResetConfirmThrottle(AnonRateThrottle):
    scope = "password_reset_confirm"


def _make_reset_link(identity) -> str:
    uidb64 = urlsafe_base64_encode(force_bytes(identity.pk))
    token = default_token_generator.make_token(identity)
    # Use root URL with query params so WhiteNoise (WHITENOISE_INDEX_FILE=True)
    # serves index.html correctly — avoids SPA routing 404 for /reset-password path.
    return f"{settings.APP_BASE_URL}/?uid={uidb64}&token={token}"


def _send_reset_email(identity) -> None:
    url = _make_reset_link(identity)
    subject = "Reset your HealthKey Analytics password"
    body = (
        "Hi,\n\n"
        "We received a request to reset the password for your HealthKey Analytics account.\n\n"
        "Click the link below to choose a new password:\n\n"
        f"  {url}\n\n"
        "The link can be used once and expires after 24 hours. "
        "If you did not request a reset you can safely ignore this email — "
        "your password will not change.\n\n"
        "— The HealthKey team"
    )
    try:
        sent = send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [identity.email])
    except Exception as exc:
        logger.exception("Failed to send password reset email (identity pk=%s)", identity.pk)
        raise _EmailError from exc
    if sent != 1:
        raise _EmailError("Email backend did not confirm delivery.")


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([_ResetRequestThrottle])
def request_password_reset(request):
    """Public: request a password-reset link by email.

    Always returns 200 regardless of whether the address exists to prevent
    account enumeration.
    """
    email = (request.data.get("email") or "").strip().lower()
    if not email:
        return Response({"detail": "email is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        identity = Identity.objects.get(email__iexact=email, issuer="urn:local")
    except Identity.DoesNotExist:
        return Response(_RESET_OK)

    if not identity.has_usable_password():
        return Response(_RESET_OK)

    try:
        _send_reset_email(identity)
    except _EmailError:
        pass  # Don't leak failure — same response either way

    return Response(_RESET_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([_ResetConfirmThrottle])
def reset_password(request):
    """Public: complete a reset via the emailed link's uid + token."""
    uidb64 = (request.data.get("uid") or "").strip()
    token = (request.data.get("token") or "").strip()
    new_password = request.data.get("new_password") or ""

    if not (uidb64 and token and new_password):
        return Response(
            {"detail": "uid, token and new_password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        pk = urlsafe_base64_decode(uidb64).decode()
        identity = Identity.objects.get(pk=pk)
    except (ValueError, TypeError, OverflowError, UnicodeDecodeError, Identity.DoesNotExist):
        return Response(
            {"detail": "Invalid or expired reset link."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Only local accounts with a usable password can reset via email link.
    if identity.issuer != "urn:local" or not identity.has_usable_password():
        return Response(
            {"detail": "Invalid or expired reset link."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not identity.is_active:
        return Response(
            {"detail": "Invalid or expired reset link."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not default_token_generator.check_token(identity, token):
        return Response(
            {"detail": "Invalid or expired reset link."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password(new_password, user=identity)
    except DjangoValidationError as exc:
        return Response({"detail": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

    identity.set_password(new_password)
    identity.save(update_fields=["password"])
    return Response({"detail": "Password has been reset. You can now sign in."})
