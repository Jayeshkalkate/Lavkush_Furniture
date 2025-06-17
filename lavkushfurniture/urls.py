from django.contrib import admin
from django.urls import path, include, re_path
from lavkushfurniture import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.views.static import serve

# Sitemap imports
from django.contrib.sitemaps.views import sitemap
from lavkushfurniture.sitemap import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='homepage'),

    path('account/', include('account.urls')),
    path('gallery/', include('gallery.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('cart/', include('cart.urls')),

    path('termsandconditions/', TemplateView.as_view(template_name='termsandconditions.html'), name='terms'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('services/', views.services, name='services'),
    path('contactus/', views.contact, name='contactus'),
    path('profile/', views.userprofile, name='userprofile'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),

    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('our-team/', include('team.urls')),

    # Sitemap URL
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),

    # Robots.txt
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    # Google Search Console Verification File
    re_path(
        r'^googleb98d5f288b41cce2\.html$',
        serve,
        {
            'document_root': settings.STATIC_ROOT,
            'path': 'googleb98d5f288b41cce2.html',
        }
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
