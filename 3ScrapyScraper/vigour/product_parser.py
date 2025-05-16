import csv
from pathlib import Path
from selectolax.parser import HTMLParser
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

html_folder = Path("Products")
html_files = list(html_folder.glob("*.html"))


def safe_get_text(element, default=""):
    return element.text(strip=True) if element else default


def safe_get_html(element, default=""):
    return element.html.replace("\n", "") if element else default


def parse_html_file(html_file):
    try:
        html_content = html_file.read_bytes()
        tree = HTMLParser(html_content)

        product_meta = tree.css_first("div.product-meta")
        key_features = product_meta.css("div#key-features ul li") if product_meta else []

        imgs = tree.css("div.product-gallery__thumbnail-list a")
        image_links = ",".join(["https:" + img.attrs.get("href") for img in imgs if img.attrs.get("href")])

        title = safe_get_text(product_meta.css_first("h1.product-meta__title"))
        vendor = safe_get_text(product_meta.css_first("a.product-meta__vendor"))
        sku = safe_get_text(key_features[0]).split(":")[1].strip() if len(key_features) > 0 else ""
        condition = safe_get_text(key_features[1]).split(":")[1].strip() if len(key_features) > 1 else ""
        warranty = safe_get_text(key_features[2]).split(":")[1].strip() if len(key_features) > 2 else ""
        mpn = safe_get_text(key_features[3]).split(":")[1].strip() if len(key_features) > 3 else ""

        price_node = tree.css_first("span.price")
        price = safe_get_text(price_node).split("$")[1] if price_node else ""

        description = safe_get_html(tree.css_first("div.card__section div.rte"))

        contents = tree.css("div.card.below_content div.metafield-rich_text_field")
        features = specifications = configurations = data_sheet = ""
        for content in contents:
            header = safe_get_text(content.css_first("h2"))
            if header == "Features":
                features = safe_get_html(content)
            elif header == "Specifications":
                specifications = safe_get_html(content)
            elif header == "Configurations":
                configurations = safe_get_html(content)
            elif header == "Data Sheets":
                links = [a.attrs.get("href", "") for a in content.css("a") if a.attrs.get("href")]
                data_sheet = ",".join(links)

        return [title, vendor, sku, condition, warranty, mpn, image_links, price,
                description, features, specifications, configurations, data_sheet]

    except Exception as e:
        print(f"File: {html_file.name} - Error: {e}")
        return None


fieldnames = ["title", "vendor", "sku", "condition", "warranty", "mpn",
              "images", "price", "description", "features", "specifications", "configurations", "data_sheet"]

all_rows = []

with ThreadPoolExecutor(max_workers=15) as executor:
    futures = list(tqdm(executor.map(parse_html_file, html_files), total=len(html_files), desc="Parsing HTML Files"))

    for result in futures:
        if result:
            all_rows.append(result)

with open("products.csv", "w", newline="", encoding="utf-8") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(fieldnames)
    csv_writer.writerows(all_rows)

