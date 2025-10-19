# core/auth.py
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class KeycloakOIDCBackend(OIDCAuthenticationBackend):

    def create_user(self, claims):
        """Initialize user with Keycloak data on first login"""
        user = super().create_user(claims)
        self._sync_user_data(user, claims)
        return user

    def update_user(self, user, claims):
        """Update user with Keycloak data on each login"""
        self._sync_user_data(user, claims)
        return user

    def _sync_user_data(self, user, claims):
        """Common logic to sync user data from Keycloak claims"""
        # Sync roles and permissions
        roles = claims.get("realm_access", {}).get("roles", []) or []
        if "user" in roles:
            grp, _ = Group.objects.get_or_create(name="users")
            user.groups.add(grp)
        if "admin" in roles:
            user.is_staff = True
            user.is_superuser = True

        # Sync user profile data
        user.email = claims.get("email", user.email)
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")

        user.save()
