from django.urls import path
from .views import signup_view, profile_edit

app_name = 'users'

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('profile/edit/', profile_edit, name='profile_edit'),
]
