# core/auth.py
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class KeycloakOIDCBackend(OIDCAuthenticationBackend):
    def update_user(self, user, claims):
        roles = claims.get("realm_access", {}).get("roles", []) or []
        if "user" in roles:
            grp, _ = Group.objects.get_or_create(name="users")
            user.groups.add(grp)
        if "admin" in roles:
            user.is_staff = True
            user.is_superuser = True
        user.email = claims.get("email", user.email)
        user.save()
        return user
