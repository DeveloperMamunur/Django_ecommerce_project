from django.urls import path

from . import views

urlpatterns = [
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/get/", views.get_cart, name="get_cart"),
    path('cart/update-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
]