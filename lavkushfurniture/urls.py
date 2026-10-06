from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from lavkushfurniture.sitemap import StaticViewSitemap, ProductSitemap, CategorySitemap
from lavkushfurniture import views

sitemaps = {'static': StaticViewSitemap, 'categories': CategorySitemap, 'products': ProductSitemap}

urlpatterns = [
    path(f'{settings.ADMIN_URL}/', admin.site.urls),
    path('', views.homepage, name='homepage'),
    path('healthz/', views.healthz, name='healthz'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('services/', views.services, name='services'),
    path('contactus/', views.contact, name='contactus'),
    path('profile/', views.userprofile, name='userprofile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('termsandconditions/', TemplateView.as_view(template_name='termsandconditions.html'), name='terms'),
    path('account/', include('account.urls')),
    path('gallery/', include('gallery.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),
    path('our-team/', include('team.urls')),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots_txt'),
    re_path(r'^googleb98d5f288b41cce2\.html$', serve, {'document_root': settings.STATIC_ROOT, 'path': 'googleb98d5f288b41cce2.html'}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'lavkushfurniture.views.handler404'
handler500 = 'lavkushfurniture.views.handler500'
