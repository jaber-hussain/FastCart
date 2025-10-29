# manager/urls.py
from django.urls import path
from . import views

app_name = "manager"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),

    # -------------------- ORDERS --------------------
    path("manage-orders/", views.manage_orders, name="manage_orders"),
    path("view-order/<str:order_id>/", views.view_order, name="view_order"),
    path("add-order/", views.add_order, name="add_order"),
    path("edit-order/<str:order_id>/", views.edit_order, name="edit_order"),
    path("delete-order/<str:order_id>/", views.delete_order, name="delete_order"),

    # -------------------- PRODUCTS --------------------
    path("manage-products/", views.manage_products, name="manage_products"),
    path("edit-product/<str:product_id>/", views.edit_product, name="edit_product"),
    path("delete-product/<str:product_id>/", views.delete_product, name="delete_product"),
    path("gallery/delete/<int:image_id>/", views.delete_gallery_image, name="delete_gallery_image"),
    path("variant/delete/<int:variant_id>/", views.delete_variant, name="delete_variant"),


    # -------------------- BLOGS --------------------
    path("manage-blogs/", views.manage_blogs, name="manage_blogs"),
    path("add-blog/", views.add_blog, name="add_blog"),
    path("edit-blog/<str:blog_id>/", views.edit_blog, name="edit_blog"),
    path("delete-blog/<str:blog_id>/", views.delete_blog, name="delete_blog"),

    # -------------------- CATEGORIES --------------------
    path("categories/", views.manage_categories, name="manage_categories"),
    path("category/add/", views.add_category, name="add_category"),
    path("category/<int:pk>/", views.view_category, name="view_category"),
    path("category/<int:pk>/edit/", views.edit_category, name="edit_category"),
    path("category/<int:pk>/delete/", views.delete_category, name="delete_category"),


    # -------------------- USERS / CUSTOMERS --------------------
    path("manage-users/", views.manage_users, name="manage_users"),
    path("delete-user/<str:user_id>/", views.delete_user, name="delete_user"),

    path("manage-customers/", views.manage_customers, name="manage_customers"),
    path("view-customer/<str:customer_id>/", views.view_customer, name="view_customer"),
    path("delete-customer/<str:customer_id>/", views.delete_customer, name="delete_customer"),

    # -------------------- COMMENTS --------------------
    path("manage-comments/", views.manage_comments, name="manage_comments"),
    path("approve-comment/<str:comment_id>/", views.approve_comment, name="approve_comment"),
    path("delete-comment/<str:comment_id>/", views.delete_comment, name="delete_comment"),

    # -------------------- VENDORS --------------------
    path("manage-vendors/", views.manage_vendors, name="manage_vendors"),
    path("add-vendor/", views.add_vendor, name="add_vendor"),
    path("edit-vendor/<str:vendor_id>/", views.edit_vendor, name="edit_vendor"),
    path("view-vendor/<str:vendor_id>/", views.view_vendor, name="view_vendor"),
    path("delete-vendor/<str:vendor_id>/", views.delete_vendor, name="delete_vendor"),



    path("approve-vendor/<str:vendor_id>/", views.approve_vendor, name="approve_vendor"),
    path("reject-vendor/<str:vendor_id>/",  views.reject_vendor,  name="reject_vendor"),
]