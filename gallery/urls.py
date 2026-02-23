from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_image, name="upload_image"),
    path("", views.gallery_view, name="gallery"),
    path("edit/<int:image_id>/", views.edit_image, name="edit_image"),
    path("delete/<int:image_id>/", views.delete_image, name="delete_image"),
    path("item/<int:item_id>/", views.furniture_detail, name="furniture_detail"),
    path("rate/<int:item_id>/", views.rate_item, name="rate_item"),
    path("bulk-upload/", views.bulk_upload_products, name="bulk_upload"),
]
