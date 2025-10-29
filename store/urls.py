from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path("", views.index, name="index"),
    path("shop/", views.shop, name="shop"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
    path("category/<id>/", views.category, name="category"),
    path("categories/", views.category_list, name="category_list"),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('delete_cart_item/', views.delete_cart_item, name='delete_cart_item'),
    path('create_order/', views.create_order, name='create_order'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('remove_from_wishlist/<int:id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('search/', views.search, name='search'),

    # Checkout & shipping
    path('checkout/<str:order_id>/', views.checkout, name='checkout'),
    path('checkout/<str:order_id>/update-shipping/', views.update_shipping, name='update_shipping'),  # <— NEW

    path('coupon_apply/<str:order_id>/', views.coupon_apply, name='coupon_apply'),

    path("filter_products/", views.filter_products, name="filter_products"),

    # Payment URLs
    path('cod_payment/<str:order_id>/', views.cod_payment, name='cod_payment'),
    path('credit_card_payment/<str:order_id>/', views.credit_card_payment, name='credit_card_payment'),
    path('jazzcash_payment/<str:order_id>/', views.jazzcash_payment, name='jazzcash_payment'),
    path('easypaisa_payment/<str:order_id>/', views.easypaisa_payment, name='easypaisa_payment'),
    path('payment_status/<str:order_id>/', views.payment_status, name='payment_status'),

    path("order_tracker_page/", views.order_tracker_page, name="order_tracker_page"),
    path("order_tracker_detail/<str:order_id>/", views.order_tracker_detail, name="order_tracker_detail"),

    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("faqs/", views.faqs, name="faqs"),
    path("privacy_policy/", views.privacy_policy, name="privacy_policy"),
    path("terms_conditions/", views.terms_conditions, name="terms_conditions"),
]
