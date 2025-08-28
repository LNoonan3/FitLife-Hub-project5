# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.progress_list, name='progress_list'),
    path('progress/new/', views.progress_create, name='progress_create'),
    path(
        'newsletter/subscribe/',
        views.newsletter_subscribe,
        name='newsletter_subscribe'
    ),
    path(
        'progress/<int:pk>/delete/',
        views.progress_delete,
        name='progress_delete'
    ),
]
