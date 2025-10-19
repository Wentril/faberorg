from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseModel(models.Model):
    """Abstract base model with common fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(BaseModel):
    """Represents a project in the Faber ecosystem"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkingGroup(BaseModel):
    """Represents a working group within a project"""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='working_groups'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ['project', 'name']
        ordering = ['project', 'name']

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class Topic(BaseModel):
    """Represents a topic/subtopic within a working group"""
    working_group = models.ForeignKey(
        WorkingGroup,
        on_delete=models.CASCADE,
        related_name='topics'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ['working_group', 'name']
        ordering = ['working_group', 'name']

    def __str__(self):
        return f"{self.working_group} - {self.name}"


class WorkingGroupMembership(BaseModel):
    """Tracks user membership in working groups"""
    PARTICIPATION_CHOICES = [
        ('subscriber', 'Subscriber'),
        ('contributor', 'Contributor'),
        ('leader', 'Leader'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='working_group_memberships'
    )
    # Store Keycloak user ID instead
    # keycloak_user_id = models.CharField(max_length=255, db_index=True)
    # user_display_name = models.CharField(max_length=200)  # Cache from Keycloak
    working_group = models.ForeignKey(
        WorkingGroup,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    participation_level = models.CharField(
        max_length=20,
        choices=PARTICIPATION_CHOICES,
        default='subscriber'
    )

    class Meta:
        unique_together = ['user', 'working_group']
        # unique_together = ['keycloak_user_id', 'working_group']
        ordering = ['working_group', 'user']

    @property
    def is_leader(self):
        return self.participation_level == 'leader'

    @property
    def is_contributor(self):
        return self.participation_level in ['contributor', 'leader']

    @property
    def is_subscriber(self):
        return self.participation_level == 'subscriber'

    def __str__(self):
        return f"{self.user_display_name} - {self.working_group} ({self.get_participation_level_display()})"


class TopicMembership(BaseModel):
    """Tracks user membership in topics"""
    PARTICIPATION_CHOICES = [
        ('subscriber', 'Subscriber'),
        ('contributor', 'Contributor'),
        ('leader', 'Leader'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='topic_memberships'
    )
    # Store Keycloak user ID instead
    # keycloak_user_id = models.CharField(max_length=255, db_index=True)
    # user_display_name = models.CharField(max_length=200)  # Cache from Keycloak
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    participation_level = models.CharField(
        max_length=20,
        choices=PARTICIPATION_CHOICES,
        default='subscriber'
    )

    class Meta:
        unique_together = ['user', 'topic']
        # unique_together = ['keycloak_user_id', 'topic']
        ordering = ['topic', 'user']

    @property
    def is_leader(self):
        return self.participation_level == 'leader'

    @property
    def is_contributor(self):
        return self.participation_level in ['contributor', 'leader']

    @property
    def is_subscriber(self):
        return self.participation_level == 'subscriber'

    def __str__(self):
        return f"{self.user_display_name} - {self.topic} ({self.get_participation_level_display()})"
