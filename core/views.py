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
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import WorkingGroupMembership, TopicMembership
from django.contrib.auth import get_user_model

User = get_user_model()


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


@require_POST
@login_required
def toggle_participation(request):
    """Toggle user's participation level in a working group or topic"""
    user = request.user
    entity_type = request.POST.get('entity_type')  # 'working_group' or 'topic'
    entity_id = request.POST.get('entity_id')
    action = request.POST.get('action')  # 'subscribe', 'contribute', or 'unassign'

    try:
        with transaction.atomic():
            if entity_type == 'working_group':
                membership, created = WorkingGroupMembership.objects.get_or_create(
                    user=user,
                    working_group_id=entity_id
                )
            elif entity_type == 'topic':
                membership, created = TopicMembership.objects.get_or_create(
                    user=user,
                    topic_id=entity_id
                )
            else:
                return JsonResponse({'success': False, 'error': 'Invalid entity type'}, status=400)

            # Check if user is a leader (cannot modify their own leadership)
            if membership.participation_level == 'leader':
                return JsonResponse({
                    'success': False,
                    'error': 'Leaders cannot modify their own participation'
                }, status=403)

            if action == 'unassign':
                membership.delete()
                return JsonResponse({'success': True, 'new_level': None})
            elif action == 'subscribe':
                membership.participation_level = 'subscriber'
                membership.save()
                return JsonResponse({'success': True, 'new_level': 'subscriber'})
            elif action == 'contribute':
                membership.participation_level = 'contributor'
                membership.save()
                return JsonResponse({'success': True, 'new_level': 'contributor'})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def users_participation_matrix(request):
    """
    Build a matrix where columns are working groups and topics (topics appear after their WG)
    and each row is a user with cell values 'S'/'C'/'L' or ''.
    """
    project_id = request.GET.get('project')
    if not project_id:
        return redirect('core:project_list')
    project = get_object_or_404(Project, pk=project_id, is_active=True)

    # Load all working groups with topics
    working_groups = list(WorkingGroup.objects.prefetch_related('topics').order_by('name').all())

    # Build ordered columns: first each WG, then its topics
    columns = []
    all_topic_ids = []
    wg_ids = []
    for wg_index, wg in enumerate(working_groups, 1):
        columns.append({'type': 'wg', 'id': wg.id, 'name': wg.name, 'wg_index': wg_index})
        wg_ids.append(wg.id)
        for topic_index, topic in enumerate(wg.topics.all().order_by('name'), 1):
            columns.append({
                'type': 'topic',
                'id': topic.id,
                'name': f"{wg.name} / {topic.name}",
                'wg_index': wg_index,
                'topic_index': topic_index
            })
            all_topic_ids.append(topic.id)

    # Fetch memberships in bulk and build lookup maps
    wg_memberships = WorkingGroupMembership.objects.filter(working_group_id__in=wg_ids).select_related('user')
    topic_memberships = TopicMembership.objects.filter(topic_id__in=all_topic_ids).select_related('user')

    wg_map = {(m.user_id, m.working_group_id): m.participation_level for m in wg_memberships}
    topic_map = {(m.user_id, m.topic_id): m.participation_level for m in topic_memberships}

    # Map participation_level to single-letter
    level_letter = {
        'leader': 'L',
        'contributor': 'C',
        'subscriber': 'S'
    }

    # Build rows for each user
    users = User.objects.order_by('username').all()
    rows = []
    for user in users:
        statuses = []
        for col in columns:
            if col['type'] == 'wg':
                lvl = wg_map.get((user.id, col['id']))
            else:
                lvl = topic_map.get((user.id, col['id']))
            statuses.append(level_letter.get(lvl, ''))
        rows.append({
            'user': user,
            'statuses': statuses
        })

    return render(request, 'core/users_participation_matrix.html', {
        'project': project,
        'columns': columns,
        'rows': rows,
    })
