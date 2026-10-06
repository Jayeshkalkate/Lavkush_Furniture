from django.urls import path
from . import views

urlpatterns = [
    path('', views.gallery_view, name='gallery'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('product/<slug:slug>/', views.furniture_detail, name='furniture_detail'),
    path('rate/<int:item_id>/', views.rate_item, name='rate_item'),
    path('upload/', views.upload_image, name='upload_image'),
    path('edit/<int:image_id>/', views.edit_image, name='edit_image'),
    path('delete/<int:image_id>/', views.delete_image, name='delete_image'),
    path('bulk-upload/', views.bulk_upload_products, name='bulk_upload'),
    path('bulk-upload/sample.csv', views.download_sample_csv, name='bulk_upload_sample'),
]
