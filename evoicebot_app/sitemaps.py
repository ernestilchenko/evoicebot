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
            'login',
            'register',
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return timezone.now()


class StaticSectionSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7
    protocol = 'https'

    def items(self):
        return [
            ('features', 'Funkcje'),
            ('about', 'O nas'),
            ('how-it-works', 'Jak to działa'),
            ('testimonials', 'Opinie'),
            ('pricing', 'Cennik'),
            ('contact', 'Kontakt'),
        ]

    def location(self, item):
        return f'#{item[0]}'

    def lastmod(self, obj):
        return timezone.now()
