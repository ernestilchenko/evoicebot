from django.http import HttpResponse
from django.urls import reverse
from django.contrib.sites.models import Site
from datetime import datetime
import xml.etree.ElementTree as ET


def sitemap(request):
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    domain = Site.objects.get_current().domain
    protocol = 'https'
    static_urls = [
        {"loc": reverse('main'), "priority": "1.0", "changefreq": "weekly"},
    ]

    for url_info in static_urls:
        url_element = ET.SubElement(root, "url")
        loc = ET.SubElement(url_element, "loc")
        loc.text = f"{protocol}://{domain}{url_info['loc']}"
        lastmod = ET.SubElement(url_element, "lastmod")
        lastmod.text = datetime.now().strftime("%Y-%m-%d")
        changefreq = ET.SubElement(url_element, "changefreq")
        changefreq.text = url_info.get("changefreq", "monthly")
        priority = ET.SubElement(url_element, "priority")
        priority.text = url_info.get("priority", "0.5")

    tree = ET.ElementTree(root)
    xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_string += ET.tostring(root, encoding='unicode')
    return HttpResponse(xml_string, content_type="application/xml")