from django.contrib import admin
from .models import Project, WorkingGroup, Membership

admin.site.register(Project)
admin.site.register(WorkingGroup)
admin.site.register(Membership)
