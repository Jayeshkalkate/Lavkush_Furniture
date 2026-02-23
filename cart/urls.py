from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path("cart/", views.view_cart, name="view_cart"),
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("update/<int:item_id>/", views.update_quantity, name="update_quantity"),
    path("checkout/", views.create_payment, name="create_payment"),
    path("receipt/<int:payment_id>/", views.payment_receipt, name="payment_receipt"),
    path(
        "receipt/<int:payment_id>/download/",
        views.download_receipt_pdf,
        name="download_receipt_pdf",
    ),
]
