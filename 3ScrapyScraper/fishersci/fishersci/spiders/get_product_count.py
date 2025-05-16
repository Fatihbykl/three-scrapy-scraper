from pathlib import Path
from selectolax.parser import HTMLParser
import scrapy
import os

class ProductScraper(scrapy.Spider):
    name = "fishersci_total_item"
    total_item = 0
    def start_requests(self):
        file_path = os.path.join(os.path.dirname(__file__), "../../category_urls.txt")
        with open(file_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        tree = HTMLParser(response.body)
        count = tree.css_first('span[data-result="total"]').text().strip().replace(",", "")
        self.total_item += int(count)
        self.log(f"Current item count: {self.total_item}")