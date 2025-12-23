from django.urls import path

from . import views

urlpatterns = [
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/<int:coupon_id>/delete/', views.delete_coupon, name='delete_coupon'),
    path('coupons/<int:coupon_id>/toggle/', views.toggle_coupon_status, name='toggle_coupon_status'),

    # frontend urls for cart
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/get/", views.get_cart, name="get_cart"),
    path('cart/update-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
]