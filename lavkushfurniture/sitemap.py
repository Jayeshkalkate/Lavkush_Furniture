from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from gallery.models import Category, ImageWithCaption


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return ['homepage', 'aboutus', 'services', 'contactus', 'gallery', 'our_team', 'privacy_policy', 'terms']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == 'homepage' else 0.6


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return ImageWithCaption.objects.filter(is_active=True).order_by('id')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.85

    def items(self):
        return Category.objects.filter(is_active=True).order_by('slug')

    def location(self, obj):
        return obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else reverse('category_detail', kwargs={'slug': obj.slug})
