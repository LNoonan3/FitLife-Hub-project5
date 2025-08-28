from django.urls import path, include
from . import views

app_name = 'users'

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]
