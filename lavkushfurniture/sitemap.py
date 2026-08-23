from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from gallery.models import ImageWithCaption


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'homepage', 'aboutus', 'services', 'contactus',
            'userprofile', 'terms', 'privacy_policy',
            'password_reset', 'password_reset_done', 'password_reset_complete',
        ]

    def location(self, item):
        return reverse(item)


class GallerySitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.6

    def items(self):
        return ImageWithCaption.objects.all()

    def lastmod(self, obj):
        return obj.uploaded_at