import os
import scrapy
from scrapy import Spider
from selectolax.parser import HTMLParser
from scrapy.http import Response
from twisted.internet.defer import Deferred


class UrlScraper(scrapy.Spider):
    name = "get_medex_urls"

    def __init__(self):
        self.urls = []

    def start_requests(self):
        with open('brand_urls.txt', "r", encoding="utf-8") as file:
            urls = [line.strip() for line in file if line.strip()]

        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse
            )

    def parse(self, response: Response, **kwargs):
        tree = HTMLParser(response.body)

        products = tree.css("li.product")
        print(f"{response.url}: {len(products)} products.")
        for p in products:
            tag = p.css_first("article figure a")
            link = tag.attributes.get("href")
            self.urls.append(link + "\n")

        next_css = tree.css_first("li.pagination-item.pagination-item--next a")
        if next_css:
            url = "https://medexsupply.com" + next_css.attributes.get("href")
            yield scrapy.Request(
                url=url,
                callback=self.parse
            )

    def close(self, reason: str):
        with open('product_urls.txt', "w") as file:
            file.writelines(self.urls)