from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Brands
    path('products/brand/', views.brand_list_view, name='brand_list'),
    path('products/brand/<int:brand_id>/status/', views.toggle_brand_status, name='toggle_brand_status'),
    path('products/brand/<int:brand_id>/delete/', views.delete_brand, name='delete_brand'),

    # Main Categories
    path('products/category/', views.product_main_category_view, name='product_main_category'),
    path('products/category/<int:category_id>/status/', views.toggle_category_status, name='toggle_category_status'),
    path('products/category/<int:category_id>/delete/', views.delete_category, name='delete_category'),

    # Sub Categories
    path('products/sub-category/', views.product_sub_category_view, name='product_sub_category'),
    path('products/sub-category/<int:sub_category_id>/status/', views.toggle_sub_category_status, name='toggle_sub_category_status'),
    path('products/sub-category/<int:sub_category_id>/delete/', views.delete_sub_category, name='delete_sub_category'),

    # Products
    path('products/', views.product_list_view, name='product_list'),
    path('products/<int:product_id>/details/', views.product_detail_view, name='product_details'),
    path('products/<int:product_id>/edit/', views.edit_product_view, name='edit_product'),
    path('products/<int:product_id>/status/', views.toggle_product_status, name='toggle_product_status'),
    path('products/<int:product_id>/featured/', views.toggle_product_feature, name='toggle_product_feature'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('ajax/get-subcategories/', views.get_subcategories_ajax, name='get_subcategories_ajax'),

    # Product Images
    path('products/<int:product_id>/images/', views.product_image_list_view, name='product_image_list'),
    path('products/<int:product_id>/images/upload/', views.product_image_upload_view, name='product_image_upload'),
    path('products/images/<int:image_id>/set-primary/', views.set_primary_image, name='set_primary_image'),
    path('products/images/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),

    # Product Variants
    path('products/<int:product_id>/variants/', views.variant_list_view, name='variant_list'),
    path('products/<int:product_id>/variants/add/', views.variant_create_view, name='variant_create'),
    path('products/variants/<int:pk>/edit/', views.variant_update_view, name='variant_update'),
    path('products/variants/<int:pk>/delete/', views.variant_delete_view, name='variant_delete'),

    # Product Inventory URLs
    path('products/<int:product_id>/inventory/', views.inventory_log_list_view, name='inventory_log_list'),
    path('products/<int:product_id>/inventory/add/', views.inventory_log_create_view, name='inventory_log_create'),
    path('products/inventory/<int:pk>/edit/', views.inventory_log_update_view, name='inventory_log_update'),
    path('products/inventory/<int:pk>/delete/', views.inventory_log_delete_view, name='inventory_log_delete'),
]