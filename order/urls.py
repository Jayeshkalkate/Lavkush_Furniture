from django.urls import path
from . import views

app_name = "order"

urlpatterns = [
    path("checkout/", views.create_payment, name="create_payment"),
    path("receipt/<int:payment_id>/", views.payment_receipt, name="payment_receipt"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path(
        "finance/admin/", views.admin_finance_dashboard, name="admin_finance_dashboard"
    ),
    path(
        "finance/customer/",
        views.customer_finance_dashboard,
        name="customer_finance_dashboard",
    ),
    path("refund/<int:payment_id>/", views.refund_payment, name="refund_payment"),
    path(
        "receipt/<int:payment_id>/download/",
        views.download_receipt_pdf,
        name="download_receipt_pdf",
    ),
]
