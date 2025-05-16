from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', views.plan_list, name='plan_list'),
    path('subscribe/<int:plan_id>/', views.subscribe_plan, name='subscribe_plan'),
    path('success/', views.subscription_success, name='subscription_success'),
    path('cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]
