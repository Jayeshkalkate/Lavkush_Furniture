from django.contrib import admin
from django.urls import path, include
from lavkushfurniture import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('custom-admin/', admin.site.urls),

    # Login is handled in account.urls
    path('', views.homepage, name='homepage'),

    # Include the account app URLs
    path('account/', include('account.urls')),

    # Gallery app
    path('gallery/', include('gallery.urls')),

    # Other protected views
    path('aboutus/', views.aboutus, name='aboutus'),
    path('services/', views.services, name='services'),
    path('blog/', views.blog, name='blog'),
    path('contactus/', views.contact, name='contactus'),
    path('cart/', views.cart, name='cart'),
    path('profile/', views.userprofile, name='userprofile'),
    path('ourteam/', views.ourteam, name='ourteam'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('our-team/', include('team.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
