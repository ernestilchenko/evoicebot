from django.urls import path

from .views import *

urlpatterns = [
    path('', main, name='main'),
    path('app/login/', login, name='login'),
    path('app/register/', register, name='register'),
    path('app/logout/', logout, name='logout'),

    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/teams/', team_list, name='team_list'),
    path('dashboard/teams/<uuid:uuid>/', team_detail, name='team_detail'),
    path('dashboard/teams/create/', create_team, name='create_team'),
    path('dashboard/projects/', project_list, name='project_list'),
    path('dashboard/projects/<int:id>/', project_detail, name='project_detail'),
    path('dashboard/projects/create/', create_project, name='create_project'),
]
