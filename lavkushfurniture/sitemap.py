from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'homepage',
            'aboutus',
            'services',
            'contactus',
            'userprofile',
            'terms',
            'privacy_policy',
            'password_reset',
            'password_reset_done',
            'password_reset_complete',
        ]

    def location(self, item):
        return reverse(item)
