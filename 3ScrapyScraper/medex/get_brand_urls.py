import requests
from selectolax.parser import HTMLParser
from playwright.sync_api import sync_playwright

url = "https://medexsupply.com/brands"

with sync_playwright() as pw:
    p = pw.chromium.launch(headless=True)
    page = p.new_page()
    page.goto(url)

    page.wait_for_selector("div.brands-name-container div.card-item")
    html = page.content()
    tree = HTMLParser(html)

    urls = []
    categories = tree.css("div.brands-name-container div.card-item")
    for category in categories:
        tag = category.css_first("h4.card-item-title a")
        link = tag.attributes.get("href")
        urls.append(link + "\n")

    with open("brand_urls.txt", "w") as file:
        file.writelines(urls)