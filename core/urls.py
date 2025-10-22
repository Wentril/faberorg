from django.urls import path
from core import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/table/', views.hierarchy_table, name='hierarchy_table'),
    path('working-groups/<int:pk>/', views.working_group_detail, name='working_group_detail'),
    path('topics/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('projects/participation/', views.project_participation_table, name='project_participation_table'),
    path('toggle-participation/', views.toggle_participation, name='toggle_participation'),
    path('users_matrix/', views.users_participation_matrix, name='users_participation_matrix'),
]
