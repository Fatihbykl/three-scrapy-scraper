import re
import csv
import scrapy
import gzip
from io import BytesIO
from lxml.html.diff import cleanup_html
from selectolax.parser import HTMLParser
from scrapy.http import Response
from pathlib import Path

def safe_get_text(element, default=""):
    return element.text(strip=True) if element else default


def safe_get_html(element, default=""):
    html_text = element.html if element else default
    text = re.sub(r'[\t\n\r]+', ' ', html_text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

headers = {
    "Host": "medexsupply.com",
    #"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Cookie": "SF-CSRF-TOKEN=a34dcc09-1a40-40ab-a139-7deb63747c39; fornax_anonymousId=8b3f0398-0878-43c8-9624-d5adcfd9ab04; athena_short_visit_id=612f500a-4c67-464d-be35-151218f83819:1746394243; Shopper-Pref=C4BEEA2FA63EFAE090C1B4FDDED8882890462142-1746999044641-x%7B%22cur%22%3A%22USD%22%7D; XSRF-TOKEN=9170732566f7ffbb8794c617457de765e89659d5e69f6901b7da702812693455; SHOP_SESSION_TOKEN=f03aa928-1b74-491f-88f3-6bb05ddc4eef; __HOST-SHOP_SESSION_TOKEN=f03aa928-1b74-491f-88f3-6bb05ddc4eef; __cf_bm=Ll7ZAP4Hqux9.N.8MaBFu98XoKiKhLfISTquXTJQzmw-1746394243-1.0.1.1-EX7QW3wMPGOFGLCtogZ6mnVRVrvPPnxSzxMIHPUI2PisH6GCz0Q1Zfx1zsmVlBo7_zhqCxXUvC8xsXJJzX8tZMAyIROn9aTnIaEPOogXnbQ; _ga_GJ70XHGTKK=GS1.1.1746394244.1.0.1746394244.60.0.0; _ga=GA1.1.1158633707.1746394244; _gcl_au=1.1.1111181584.1746394244; _ga_8QNJJX3KB5=GS2.1.s1746394244$o1$g0$t1746394245$j59$l0$h713937565; STORE_VISITOR=1; optiMonkClientId=e061ce4f-d08e-0652-f5ed-706b1646caca; optiMonkClient=N4IgjATAbBEMwgFygMYEMnAL4BoQDMA3JMAdgBYo4BOcic8vAG2MTMproYDoAOUgKx4AdgHsADqzBYsQA===; optiMonkSession=1746394245",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
}

class UrlScraper(scrapy.Spider):
    name = "scrape_medex_products"

    def __init__(self):
        self.fieldnames = ["url", "title", "sku", "upc", "mfr", "brand", "price", "unit", "description"]
        self.output_file = open(Path("medex_products.csv"), "a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.output_file)
        self.writer.writerow(self.fieldnames)

    def start_requests(self):
        with open("product_urls.txt", "r", encoding="utf-8") as file:
            urls = [line.strip() for line in file if line.strip()]

        for url in urls:
            yield scrapy.Request(
                url=url,
                #headers=headers,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                callback=self.parse
            )

    def parse(self, response: Response, **kwargs):
        tree = HTMLParser(response.body)

        title = safe_get_text(tree.css_first("div.productView-product h1.productView-title"))
        sku = safe_get_text(tree.css_first("dt.sku-label").parent.css_first("dd") if tree.css_first("dt.sku-label") else "")
        upc = safe_get_text(tree.css_first("dt.upc-label").parent.css_first("dd") if tree.css_first("dt.upc-label") else "")
        mfr = safe_get_text(tree.css_first("dt.mpn-label").parent.css_first("dd") if tree.css_first("dt.mpn-label") else "")
        price = safe_get_text(tree.css_first("div.productView-price span.price--withoutTax")).split('-')[0]
        unit = safe_get_text(tree.css_first("div.Packing dd"))
        brand = safe_get_text(tree.css_first("h2.productView-brand span"))
        description = safe_get_html(tree.css_first("div.productView-description"))

        item = {
            "url": response.url,
            "title": title,
            "sku": sku,
            "upc": upc,
            "mfr": mfr,
            "brand": brand,
            "price": price,
            "unit": unit,
            "description": description
        }
        self.writer.writerow([item[field] for field in self.fieldnames])


    def close(self, reason: str):
        self.output_file.close()