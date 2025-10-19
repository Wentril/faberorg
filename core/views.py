# Create your views here.
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from urllib.parse import urlencode
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Project, WorkingGroup, Topic


def index(request):
    return render(request, 'core/index.html')

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


# ------------

@login_required
def project_list(request):
    """List all active projects"""
    projects = Project.objects.filter(is_active=True).prefetch_related('working_groups')
    return render(request, 'core/project_list.html', {'projects': projects})


@login_required
def project_detail(request, pk):
    """Show project details with working groups"""
    project = get_object_or_404(Project, pk=pk, is_active=True)
    working_groups = project.working_groups.all().prefetch_related('topics')
    return render(request, 'core/project_detail.html', {
        'project': project,
        'working_groups': working_groups
    })


@login_required
def working_group_detail(request, pk):
    """Show working group details with topics"""
    wg = get_object_or_404(WorkingGroup, pk=pk)
    topics = wg.topics.all()
    return render(request, 'core/working_group_detail.html', {
        'working_group': wg,
        'topics': topics
    })


@login_required
def topic_detail(request, pk):
    """Show topic details"""
    topic = get_object_or_404(Topic, pk=pk)
    return render(request, 'core/topic_detail.html', {'topic': topic})


@login_required
def hierarchy_table(request):
    """Display all projects, working groups, and topics in a table"""
    # core/views.py
    from django.shortcuts import render
    from .models import Project

    projects = Project.objects.prefetch_related(
        'working_groups',
        'working_groups__topics',
        'working_groups__memberships',
        'working_groups__topics__memberships'
    ).order_by('name')

    return render(request, 'core/hierarchy_table.html', {
        'projects': projects
    })


@login_required
def project_participation_table(request):
    """Display participation table for a specific project"""
    project_id = request.GET.get('project')
    if not project_id:
        return redirect('core:project_list')

    project = get_object_or_404(Project, pk=project_id, is_active=True)

    # Get current user's Keycloak ID
    user_keycloak_id = request.user.username  # Adjust based on your Keycloak setup
    user = request.user
    user_id = user.id

    # Get all working groups for this project with their topics and memberships
    working_groups = list(project.working_groups.prefetch_related(
        'topics',
        'topics__memberships',
        'memberships'
    ).all())

    # Annotate each working group and topic with leader and user participation
    for wg in working_groups:
        # Get all memberships for this working group
        wg_memberships_list = list(wg.memberships.all())

        # Get working group leader
        wg.leader_membership = next(
            (m for m in wg_memberships_list if m.participation_level == 'leader'),
            None
        )

        # Get current user's participation in working group
        wg.user_membership = next(
            (m for m in wg_memberships_list if m.user_id == user_id),
            None
        )

        topics_list = list(wg.topics.all())
        for topic in topics_list:
            # Get all memberships for this topic
            memberships_list = list(topic.memberships.all())

            # Get topic leader
            topic.leader_membership = next(
                (m for m in memberships_list if m.participation_level == 'leader'),
                None
            )

            # Get current user's participation
            topic.user_membership = next(
                (m for m in memberships_list if m.user_id == user_id),
                None
            )

    context = {
        'project': project,
        'working_groups': working_groups,
        'user_keycloak_id': user_keycloak_id,
    }
    return render(request, 'core/project_participation_table.html', context)
