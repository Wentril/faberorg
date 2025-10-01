# Create your views here.
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from urllib.parse import urlencode
from django.views.decorators.http import require_http_methods


def default_view(request):
    return render(request, 'core/default.html')

@login_required
def authenticated_view(request):
    return render(request, 'core/authenticated.html')

@require_http_methods(["POST"])
def logout_view(request):
    """
    Logs out from Django and redirects to Keycloak logout endpoint
    to terminate the SSO session.
    """
    # Get the ID token before destroying the session
    id_token = request.session.get('oidc_id_token', '')

    # Destroy Django session
    logout(request)

    # Build Keycloak logout URL
    keycloak_logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT
    redirect_uri = request.build_absolute_uri('/')  # Where to go after logout

    logout_params = {
        'post_logout_redirect_uri': redirect_uri,
        'id_token_hint': id_token,
    }

    return redirect(f"{keycloak_logout_url}?{urlencode(logout_params)}")
