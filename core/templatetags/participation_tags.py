# core/templatetags/participation_tags.py
from django import template
from core.models import WorkingGroupMembership, TopicMembership

register = template.Library()


@register.filter
def get_participation_status(obj, request):
    """
    Get participation status for a WorkingGroup or Topic.
    Returns the participation level or None if not a member.
    """
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return None

    keycloak_id = getattr(request.user, 'keycloak_id', None)
    if not keycloak_id:
        return None

    # Check if it's a WorkingGroup
    if hasattr(obj, 'working_groups'):  # It's a Project, skip
        return None
    elif hasattr(obj, 'topics'):  # It's a WorkingGroup
        try:
            membership = WorkingGroupMembership.objects.get(
                working_group=obj,
                keycloak_user_id=keycloak_id
            )
            return membership.get_participation_level_display()
        except WorkingGroupMembership.DoesNotExist:
            return None
    else:  # It's a Topic
        try:
            membership = TopicMembership.objects.get(
                topic=obj,
                keycloak_user_id=keycloak_id
            )
            return membership.get_participation_level_display()
        except TopicMembership.DoesNotExist:
            return None
