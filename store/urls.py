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
    path('cart/update/<int:pk>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('reviews/create/', views.review_create, name='review_create'),
    path('reviews/<int:pk>/edit/', views.review_edit, name='review_edit'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
