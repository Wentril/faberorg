from django.contrib import admin
from .models import Project, WorkingGroup, WorkingGroupMembership, Topic, TopicMembership

admin.site.register(Project)
admin.site.register(WorkingGroup)
admin.site.register(WorkingGroupMembership)
admin.site.register(Topic)
admin.site.register(TopicMembership)
