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

]
