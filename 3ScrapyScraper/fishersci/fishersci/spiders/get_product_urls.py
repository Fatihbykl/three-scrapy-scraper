from pathlib import Path
from scrapy.http import FormRequest
from selectolax.parser import HTMLParser
import csv
import scrapy
import os
import re
import json


def safe_get_text(element, default=""):
    return element.text(strip=True) if element else default


def safe_get_html(element, default=""):
    html_text = element.html if element else default
    text = re.sub(r'[\t\n\r]+', ' ', html_text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


class ProductScraper(scrapy.Spider):
    name = "get_all_products"
    custom_settings = {"PLAYWRIGHT_ENABLED": False}

    def __init__(self):
        self.fieldnames = ["url", "title", "subhead", "subhead2", "category", "images", "price", "unit", "catalogNo", "certificates",
                           "description", "specifications", "safetyHandling"]
        self.output_file = open(Path("fisher_products.csv"), "a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.output_file)
        self.writer.writerow(self.fieldnames)

    def start_requests(self):
        file_path = os.path.join(os.path.dirname(__file__), "../../output_chunk_1.txt")
        with open(file_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        for url in urls:
            yield scrapy.Request(
                url=url,
                meta={"proxy": ""},
                callback=self.parse)

    def parse(self, response, **kwargs):
        tree = HTMLParser(response.body)

        title = safe_get_text(tree.css_first('h1#item_header_text'))
        if not title:
            title = safe_get_text(tree.css_first('h1#qa_item_header_text'))
        subhead = safe_get_html(tree.css_first('div.subhead'))
        subhead_2 = safe_get_html(tree.css_first('h3.subhead'))

        breadcrumb = tree.css('ol.breadcrumb li')
        category = safe_get_text(breadcrumb[-2].css_first('span.messageDialog'))

        img_links = tree.css('ul#product_carousel li a')
        hrefs = [img.attributes.get("href", "") for img in img_links if img.attributes.get("href")]
        images = ",".join(hrefs)

        unit = safe_get_text(tree.css_first('label.price span[data-unit-string-uom="EA"]'))
        if not unit:
            unit = safe_get_text(tree.css_first('label.price span.qa_single_display_unit span'))
        catalog_no = safe_get_text(tree.css_first('span#qa_prod_code_labl'))
        if not catalog_no:
            catalog_no = response.url.split('/')[-1]
        price = safe_get_text(tree.css_first('label.price b'))

        certificate_links = tree.css('a.certificate_link')
        cert_hrefs = [cert.attributes.get("href", "") for cert in certificate_links if cert.attributes.get("href")]
        certificates = ",".join(cert_hrefs)

        description = safe_get_html(tree.css_first('div#tab1'))
        specifications = safe_get_html(tree.css_first('div#tab2'))
        if not specifications:
            specifications = safe_get_html(tree.css_first('table.spec_table'))
        safety_handling = safe_get_html(tree.css_first('div#tab22'))

        item = {
            "url": response.url,
            "title": title,
            "subhead": subhead,
            "subhead2": subhead_2,
            "category": category,
            "images": images,
            "price": price,
            "unit": unit,
            "catalogNo": catalog_no,
            "certificates": certificates,
            "description": description,
            "specifications": specifications,
            "safetyHandling": safety_handling
        }

        if not price:
            yield FormRequest(
                url='https://www.fishersci.com/shop/products/service/pricing',
                headers={
                    "Host": "www.fishersci.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
                    "Accept": "*/*",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "x-b3-traceid": "86f2f9682d8e2ea41738af79ab90eb39",
                    "X-Requested-With": "XMLHttpRequest",
                    "Origin": "https://www.fishersci.com",
                    "Connection": "keep-alive",
                    "Referer": response.url,
                    "Cookie": "new_hf=true; new_cart=true; new_overlay=true; f_num=gmr; estore=estore-scientific; notice_preferences=0:; notice_gdpr_prefs=0:; cmapi_gtm_bl=ga-ms-ua-ta-asp-bzi-sp-awct-cts-csm-img-flc-fls-mpm-mpr-m6d-tc-tdc; cmapi_cookie_privacy=permit 1 required; optout_domains_pc={}; preventSingleResultRedirect=true; akacd_FS_Prod_AWS_EKS=3923737642~rv=85~id=953e875e668efc92df8800dedcc1c417; locale=en_US; usertype=G; formSecurity=qo6v0m9igw; ak_bmsc=9784408881D963CC75832991D339A67E~000000000000000000000000000000~YAAQdoYUAoTMkoqWAQAAHYL5lhv9vVBOkeJHPXcUIixPTJd0KaUT+72KJR+OeErZ3Gyk3wC8ahndvGy6oHYdok0EO3sS7rMU6jlhFYONnsaObloKwQjEBQC55DjxHZkv2lHfAjVUszTUyA2qXSuZ68cpyJl19rNQwrK/JQ0o3A65pkPt+haOoNwcKXyMaMsXdWe5jSaf7FOJnzCGdZb2yAWqSTyJYs37VXqmFvS9/eRYrmCs9tZR+4sxotu7waCUNu9nF921he8qPzlnQ2MdwWdOQMqfNgwbuDU8+OOMB92kWL4JoV6AS++ABB13TTmcLUSfctAtufiJY6mxNjFnIR1RqIkBaNw93i6OcU1Bkaqb7OIo6I9M5PMSCKppL6fcThbDk5TWNuR/lY+y4NxdOd08Emw6YYn4+sYgz3yoJuFQiesr4oJ2LtTQn0VEXdA6mdG0kmKfvgpvSDM8MVZdO5tStALptADE; akacd_FS_US_ProdA_Search_LucidWorks=3923737644~rv=18~id=c429dfd33686742a96d97321de6a1344; userTypeDescription=guest; akacd_FS_Prod_AWS_EKS_Users=3923737644~rv=88~id=7b199b92fea9fbc1bf416d2e39d835e9; bm_sv=5950518C05EAE30E57DFB3EB240E5E47~YAAQdoYUAnwJg4qWAQAA/WG2lhsiMOtYNL0eMfgGEZ5BMZ5YjKzfpKXvU5czbXLlrInz2sbBya5G3qCIpftxfeyf6cPhrW9anJBcmB6f7CyZFBpf0vTKGlwUFgbwAWyLLq17FrN9aCFdVDwLUOhHCF2vSSMKaPpx/5ASp/4CT5ByCZsLjYN6zEfPpDWLVnnVx3cCSZMvK1j5OhSHxaHZbKLl3E7d4+YthraXQjIF2QHKvvwKafLpTt6tU5utOIc5Tnoj~1; bm_mi=5A1BFFC436106DF5C29C15C8F90AA73B~YAAQdoYUAkf7goqWAQAADTC2lht8C6Wf00ygXKg8u7aQLivSzecHAwbTQyK/jbZsgx6UvEu4hCOfeyBWgvvx9iy1kiRPNdSZ9PIUUPob7xAEy5brLcqwNnrzxfKQEeAjXSqy2qUVV91PLSCEn6CkZbDGXLZDRWi7jDh6BKN05UGbiZ+Q37wQt53ooFm5i+9ZHJ6A6aTyFt9OYd0nfS2y8C8JFuBm/W2WuZXw08ReBBg+Aggn/ezRdcxs7QcMTn2tPGe3OBPKz53kG/4gSUq/TPq370t6ZhIgkkbngQ7tDa/KjPoce1XOS0mhlorTTynxDsbEsJZy6VeY0ky+crG0gceEXU7u/JFv71ZbXLboEAlP3U1c/zY=~1; TAsessionID=5c3fc85f-2394-4e93-80a8-f37c97ca8c8e|EXISTING; notice_behavior=implied,eu",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin"
                },
                formdata={'partNumber': catalog_no, 'callerId': 'products-ui-single-page'},
                callback=self.parse_price,
                meta={'item': item}
            )
        else:
            self.writer.writerow([item[field] for field in self.fieldnames])

    def parse_price(self, response):
        item = response.meta['item']
        try:
            data = json.loads(response.text)
            item['price'] = data['priceAndAvailability'][response.meta['item']['catalogNo']][0]['price']
            item['unit'] = data['priceAndAvailability'][response.meta['item']['catalogNo']][0]['displayUnitString']
        except Exception:
            item['price'] = ''

        self.writer.writerow([item[field] for field in self.fieldnames])

    def close(self, reason):
        self.output_file.close()
