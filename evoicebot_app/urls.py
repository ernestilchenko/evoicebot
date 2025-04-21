
from django.urls import path

from .views import *

urlpatterns = [
    path('', main, name='main'),
    path('app/login/', login, name='login'),
    path('app/register/', register, name='register'),
    path('app/logout/', logout, name='logout'),
]