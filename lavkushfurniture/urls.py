from django.contrib import admin
from django.urls import path, include
from lavkushfurniture import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('custom-admin/', admin.site.urls),

    # Login is handled in account.urls
    path('', views.homepage, name='homepage'),

    # Include the account app URLs
    path('account/', include('account.urls')),

    # Gallery app
    path('gallery/', include('gallery.urls')),

    # Wishlist and Cart
    path('wishlist/', include('wishlist.urls')),
    path('cart/', include('cart.urls')),

    path('termsandconditions/', TemplateView.as_view(template_name='termsandconditions.html'), name='terms'),

    # Other protected views
    path('aboutus/', views.aboutus, name='aboutus'),
    path('services/', views.services, name='services'),
    path('contactus/', views.contact, name='contactus'),
    path('profile/', views.userprofile, name='userprofile'),
    path('ourteam/', views.ourteam, name='ourteam'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('our-team/', include('team.urls')),

    
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

