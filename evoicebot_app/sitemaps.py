from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
from django.utils import timezone


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = 'https'

    def items(self):
        return [
            'main',
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return timezone.now()
