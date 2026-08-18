import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
from datetime import datetime, timezone

base_url = "https://books.toscrape.com/"
start_url = urljoin(base_url, "catalogue/page-1.html")

headers = {
        "User-Agent": "FlyRankInternshipA9/1.0/skiller99668/scraper"
    }

urls = []
page_url = start_url

pages = 0
detail_pages = 0
while page_url and pages < 3:
    # print("processing", page_url)
    cache_file = Path(f"cache/{page_url.strip("/").split("/")[-1]}")

    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        # print("read from cache")
    else:
        time.sleep(0.5)
        try:
            response = requests.get(page_url, headers=headers, timeout=5)

            # print(response.status_code)
            if response.status_code == 200:
                Path("cache").mkdir(exist_ok=True)
                # print(response.text)

                html = response.text
                cache_file.write_text(html, encoding="utf-8")
            else:
                print(f"failed to fetch. error code: {response.status_code}")

        except requests.exceptions.Timeout:
            print("Timeout (5.0 s)")

    soup = BeautifulSoup(html, "html.parser")

    for book in soup.find_all("article"):
        link = book.find("a")
        # print(link.get("href"))
        full_url = urljoin(page_url, link.get("href"))
        urls.append(full_url)

        # Extract Records:
        path = urlparse(full_url).path
        filename = Path(path).parent.name

        
        book_cache_file = Path(f"cache/books/{filename}.json")

        if book_cache_file.exists():
            with open(book_cache_file, "r", encoding="utf-8") as f:
                book_data = json.load(f)

            book_html = book_cache_file.read_text(encoding="utf-8")

        else:
            time.sleep(0.5)

            try:
                response = requests.get(full_url, headers=headers, timeout=5)

                if response.status_code == 200:
                    Path("cache/books").mkdir(parents=True, exist_ok=True)

                    book_html = response.text
                    book_soup = BeautifulSoup(book_html, "html.parser")

                    description_element = book_soup.find("div", id="product_description")

                    description = (
                        description_element.find_next("p").get_text(strip=True)
                        if description_element and description_element.find_next("p")
                        else None
                    )

                    book_data = { 
                            "title": book_soup.find("h1").get_text(strip=True),
                            "product_url": full_url,
                            "price_text": book_soup.find("p", class_="price_color").get_text(strip=True),
                            "availability_text": book_soup.find("p", class_="instock availability").get_text(strip=True),
                            "rating_text": book_soup.find("p", class_="star-rating")["class"][1],
                            "description": description,
                            "source_page": page_url,
                            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z") 
                            }
                    with open(book_cache_file, "w", encoding="utf-8") as f:
                        json.dump(book_data, f, indent=4)

            except requests.exceptions.Timeout:
                print("Timeout (5.0 s)")

        detail_pages += 1

        # see if next page
    next_page = soup.find("li", class_="next")
    if next_page:
        next_href = next_page.find("a")["href"]
        page_url = urljoin(page_url, next_href)
    else:
        page_url = None

    pages+=1

print("catalogue_pages =", pages)
print("discovered =", len(urls))
print("unique_urls =", len(set(urls)))

with open("cache/books/a-light-in-the-attic_1000.json", "r", encoding="utf-8") as f:
    book = json.load(f)

print(book)
print("detailed_pages=", detail_pages)