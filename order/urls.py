from django.urls import path
from . import views
app_name = 'order'
urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('webhook/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),
    path('receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
    path('receipt/<int:payment_id>/download/', views.download_receipt_pdf, name='download_receipt_pdf'),
    path('orders/', views.customer_orders, name='customer_orders'),
    path('orders/<str:invoice_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:invoice_number>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<str:invoice_number>/return/', views.request_return, name='request_return'),
    path('finance/admin/', views.admin_finance_dashboard, name='admin_finance_dashboard'),
    path('finance/customer/', views.customer_finance_dashboard, name='customer_finance_dashboard'),
    path('refund/<int:payment_id>/', views.refund_payment, name='refund_payment'),
]
