from django.urls import path
from .views import signup_view, profile_edit
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('profile/', views.profile_edit, name='profile'),
    path('profile/edit/', profile_edit, name='profile_edit'),
]
