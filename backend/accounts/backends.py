from django.contrib.auth.backends import ModelBackend
from .models import Identity


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identities = list(
            Identity.objects.filter(email__iexact=username, issuer="urn:local").order_by("id")
        )
        if not identities:
            Identity().set_password(password)
            return None
        usable_identities = [identity for identity in identities if identity.has_usable_password()]
        if len(usable_identities) != 1:
            Identity().set_password(password)
            return None
        identity = usable_identities[0]
        if identity.check_password(password) and self.user_can_authenticate(identity):
            return identity
        return None
