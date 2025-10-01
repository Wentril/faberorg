from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Project(models.Model):
    """
    Represents a project in the Faber ecosystem (e.g., Faber, FaberGenAI).
    Maps to a top-level Keycloak group.
    """
    name = models.CharField(max_length=100, unique=True)
    keycloak_group_path = models.CharField(
        max_length=255,
        unique=True,
        help_text="Keycloak group path, e.g., /projects/faber"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkingGroup(models.Model):
    """
    Represents a working group within a project.
    Maps to a subgroup in Keycloak under the project.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='working_groups'
    )
    name = models.CharField(max_length=100)
    keycloak_group_name = models.CharField(
        max_length=255,
        help_text="Keycloak group name, e.g., wg1-data-acquisition-own"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['project', 'keycloak_group_name']
        ordering = ['project', 'name']

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    @property
    def full_keycloak_path(self):
        """Returns the complete Keycloak group path"""
        return f"{self.project.keycloak_group_path}/{self.keycloak_group_name}"

    @property
    def leaders(self):
        """Returns QuerySet of users who are leaders of this WG"""
        return User.objects.filter(
            wgmembership__working_group=self,
            wgmembership__participation_level='leader',
            wgmembership__status='approved'
        )

    @property
    def contributors(self):
        """Returns QuerySet of contributors (including leaders)"""
        return User.objects.filter(
            wgmembership__working_group=self,
            wgmembership__participation_level__in=['contributor', 'leader'],
            wgmembership__status='approved'
        )


class WGMembership(models.Model):
    """
    Tracks user membership in working groups.
    Stores business logic like participation level and leadership.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    PARTICIPATION_CHOICES = [
        ('subscriber', 'Subscriber'),      # Passive - receives updates only
        ('contributor', 'Contributor'),    # Active - participates in work
        ('leader', 'Leader'),              # Leads the working group
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    working_group = models.ForeignKey(
        WorkingGroup,
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    participation_level = models.CharField(
        max_length=20,
        choices=PARTICIPATION_CHOICES,
        default='subscriber',
        help_text="Level of participation: Subscriber, Contributor, or Leader"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    keycloak_synced = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'working_group']
        indexes = [
            models.Index(fields=['user', 'participation_level']),
            models.Index(fields=['working_group', 'status']),
            models.Index(fields=['participation_level']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.working_group} ({self.get_participation_level_display()}, {self.get_status_display()})"

    def clean(self):
        if self.participation_level == 'leader' and self.status != 'approved':
            raise ValidationError("Leaders must have approved membership")

    @property
    def is_leader(self):
        return self.participation_level == 'leader'

    @property
    def is_contributor(self):
        return self.participation_level in ['contributor', 'leader']

    @property
    def is_subscriber(self):
        return self.participation_level == 'subscriber'


class Topic(models.Model):
    """
    Represents a topic/subtopic within a working group.
    """
    working_group = models.ForeignKey(
        WorkingGroup,
        on_delete=models.CASCADE,
        related_name='topics'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['working_group', 'name']

    def __str__(self):
        return f"{self.working_group} - {self.name}"


class TopicMembership(models.Model):
    """
    Tracks user membership in topics.
    """
    PARTICIPATION_CHOICES = [
        ('subscriber', 'Subscriber'),
        ('contributor', 'Contributor'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='memberships')
    participation_level = models.CharField(
        max_length=20,
        choices=PARTICIPATION_CHOICES,
        default='subscriber'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'topic']

    def __str__(self):
        return f"{self.user.username} - {self.topic} ({self.get_participation_level_display()})"
