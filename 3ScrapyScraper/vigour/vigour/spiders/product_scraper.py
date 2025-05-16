from pathlib import Path

import scrapy


class ProductScraper(scrapy.Spider):
    name = "products"

    def start_requests(self):
        with open("../urls.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        page = response.url.split("/")[-1]
        filename = f"Products/product-{page}.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")