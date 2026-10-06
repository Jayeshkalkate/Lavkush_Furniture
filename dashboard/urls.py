from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    # products
    path('products/', views.products, name='products'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/quick/', views.product_quick_update, name='product_quick'),
    path('products/<int:pk>/toggle/', views.product_toggle, name='product_toggle'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    # categories
    path('categories/', views.categories, name='categories'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    # orders & payments
    path('orders/', views.orders, name='orders'),
    path('orders/<str:invoice_number>/', views.order_detail, name='order_detail'),
    path('payments/', views.payments, name='payments'),
    # customers
    path('customers/', views.customers, name='customers'),
    path('customers/<int:pk>/toggle/', views.customer_toggle, name='customer_toggle'),
    # coupons
    path('coupons/', views.coupons, name='coupons'),
    path('coupons/add/', views.coupon_add, name='coupon_add'),
    path('coupons/<int:pk>/edit/', views.coupon_edit, name='coupon_edit'),
    path('coupons/<int:pk>/toggle/', views.coupon_toggle, name='coupon_toggle'),
    path('coupons/<int:pk>/delete/', views.coupon_delete, name='coupon_delete'),
    # reviews & team
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/<int:pk>/toggle/', views.review_toggle, name='review_toggle'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),
    path('team/', views.team, name='team'),
]
