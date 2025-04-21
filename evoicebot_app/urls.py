from django.urls import path

from .views import *

urlpatterns = [
    path('', main, name='main'),
    path('app/login/', login, name='login'),
    path('app/register/', register, name='register'),
    path('app/logout/', logout, name='logout'),

    path('app/dashboard/', dashboard, name='dashboard'),
    path('app/dashboard/teams/', team_list, name='team_list'),
    path('app/dashboard/teams/<uuid:uuid>/', team_detail, name='team_detail'),
    path('app/dashboard/teams/<uuid:uuid>/edit/', edit_team, name='edit_team'),
    path('app/dashboard/teams/<uuid:uuid>/members/', manage_team_members, name='manage_team_members'),
    path('app/dashboard/teams/create/', create_team, name='create_team'),
    path('app/dashboard/projects/', project_list, name='project_list'),
    path('app/dashboard/projects/<uuid:uuid>/', project_detail, name='project_detail'),
    path('app/dashboard/projects/create/', create_project, name='create_project'),
    path('app/dashboard/projects/<uuid:uuid>/edit/', edit_project, name='edit_project'),
    path('app/dashboard/projects/<uuid:uuid>/delete/', delete_project, name='delete_project'),
    path('app/dashboard/documents/', document_list, name='document_list'),
    path('app/dashboard/documents/<uuid:uuid>/', document_detail, name='document_detail'),
    path('app/dashboard/documents/create/', create_document, name='create_document'),
    path('app/dashboard/documents/<uuid:uuid>/edit/', edit_document, name='edit_document'),
    path('app/dashboard/documents/<uuid:uuid>/delete/', delete_document, name='delete_document'),
]
