from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/review/', views.product_detail, name='submit_review'),  # uses same view
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='cart_add'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/oneoff/<int:pk>/', views.oneoff_checkout, name='oneoff_checkout'),
    path('checkout/success/',   views.checkout_success, name='checkout_success'),
    path('checkout/cancel/',    views.checkout_cancel,  name='checkout_cancel'),
    path('webhook/oneoff/',     views.oneoff_webhook,   name='oneoff_webhook'),


]
