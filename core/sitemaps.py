from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return [
            'home',
            'store:product_list',
            'subscriptions:plan_list',
            'core:progress_list',
        ]

    def location(self, item):
        return reverse(item)
