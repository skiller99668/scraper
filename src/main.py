import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
from datetime import datetime, timezone
from pydantic import BaseModel, ValidationError
from typing import Optional

start_time = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
start_sec = time.perf_counter()

class Book(BaseModel):
    title: str
    product_url: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: str | None
    source_page: str
    fetched_at: str

base_url = "https://books.toscrape.com/"
start_url = urljoin(base_url, "catalogue/page-1.html")

headers = {
        "User-Agent": "FlyRankInternshipA9/1.0/skiller99668/scraper"
    }

urls = []
page_url = start_url

pages = 0
detail_pages = 0
failed_pages = 0
cache_hits = 0
seen_urls = set()

books = []
errors = []

book_cache_file = Path(f"cache/output/books.json")
book_cache_file_error = Path(f"cache/output/errors.json")

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

            # success
            if response.status_code == 200:
                Path("cache").mkdir(exist_ok=True)

                html = response.text
                cache_file.write_text(html, encoding="utf-8")

            # 5xx error try again
            elif 500<=response.status_code <= 600:
                try:
                    response = requests.get(page_url, headers=headers, timeout=5)

                    if response.status_code == 200:
                        Path("cache").mkdir(exist_ok=True)

                        html = response.text
                        cache_file.write_text(html, encoding="utf-8")
                    else:
                        print(f"failed to fetch. error code: {response.status_code}")
                        failed_pages += 1
                        continue

                except requests.exceptions.Timeout:
                    print("Timeout (5.0 s)")
                    failed_pages += 1
                    continue

            # fail
            else:
                print(f"failed to fetch. error code: {response.status_code}")
                failed_pages += 1
                continue

        # timeout error try again
        except requests.exceptions.Timeout:
            try:
                response = requests.get(page_url, headers=headers, timeout=5)

                if response.status_code == 200:
                    Path("cache").mkdir(exist_ok=True)

                    html = response.text
                    cache_file.write_text(html, encoding="utf-8")
                else:
                    print(f"failed to fetch. error code: {response.status_code}")
                    failed_pages += 1
                    continue
                    
            except requests.exceptions.Timeout:
                print("Timeout (5.0 s)")
                failed_pages += 1
                continue

    soup = BeautifulSoup(html, "html.parser")

    # for every book on page (soup is for this page only)
    for book in soup.find_all("article"):
        link = book.find("a")
        full_url = urljoin(page_url, link.get("href"))
        # TEMP: prove error handling works, remove before final run
        # if full_url.endswith("a-light-in-the-attic_1000/index.html"):
        #    full_url = "https://books.toscrape.com/catalogue/this-book-totally-does-not-exist_00000/index.html"
        urls.append(full_url)

# =========================================================================================================
        # Extract Records:

        # get html of books first
        path = urlparse(full_url).path
        filename = Path(path).parent.name

        book_html_cache = Path(f"cache/books/{filename}")

        # if already cached, just read from it
        if book_html_cache.exists():
            book_html = book_html_cache.read_text(encoding="utf-8")
            cache_hits += 1

        # if not make the folder GET from site and write onto folder/files (each individual book)
        else:
            time.sleep(0.5)

            try:
                response = requests.get(full_url, headers=headers, timeout=5)

                # successful connection
                if response.status_code == 200:
                    Path("cache/books").mkdir(parents=True, exist_ok=True)

                    book_html = response.text
                    book_html_cache.write_text(book_html, encoding="utf-8")

                # try once more if server 5xx error
                elif 500<=response.status_code<=600:
                    try:
                        response = requests.get(full_url, headers=headers, timeout=5)
        
                        # successful connection
                        if response.status_code == 200:
                            Path("cache/books").mkdir(parents=True, exist_ok=True)
        
                            book_html = response.text
                            book_html_cache.write_text(book_html, encoding="utf-8")
                        else:
                            print(f"failed to fetch. error code: {response.status_code}")
                            failed_pages += 1
                            continue

                    except requests.exceptions.Timeout:
                        print("Timeout (5.0 s)")
                        failed_pages += 1
                        continue

                # fail
                else:
                    print(f"failed to fetch. error code: {response.status_code}")
                    failed_pages += 1
                    continue

            # try once more if timeout
            except requests.exceptions.Timeout:
                try:
                    response = requests.get(full_url, headers=headers, timeout=5)
    
                    # successful connection
                    if response.status_code == 200:
                        Path("cache/books").mkdir(parents=True, exist_ok=True)
    
                        book_html = response.text
                        book_html_cache.write_text(book_html, encoding="utf-8")
                    else:
                        print(f"failed to fetch. error code: {response.status_code}")
                        failed_pages += 1
                        continue

                except requests.exceptions.Timeout:
                    print("Timeout (5.0 s)")
                    failed_pages += 1
                    continue
            
        book_soup = BeautifulSoup(book_html, "html.parser")

        price_text = book_soup.find("p", class_="price_color").get_text(strip=True)
        price_gbp = price_text[2:]            

        description_element = book_soup.find("div", id="product_description")

        description = (
            description_element.find_next("p").get_text(strip=True)
            if description_element and description_element.find_next("p")
            else None
        )

        if full_url in seen_urls:
            continue

        seen_urls.add(full_url)

        book_data = {
                "title": book_soup.find("h1").get_text(strip=True),
                "product_url": full_url,
                "price_gbp": price_gbp,
                "availability_text": book_soup.find("p", class_="instock availability").get_text(strip=True),
                "rating_text": book_soup.find("p", class_="star-rating")["class"][1],
                "description": description,
                "source_page": page_url,
                "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
                }
        # TEMP: prove validation-error handling works, remove before final run
        #if full_url.endswith("tipping-the-velvet_999/index.html"):
        #    book_data["price_gbp"] = "not-a-price"

        try:
            book = Book(**book_data)
            books.append(book_data)
            

        except ValidationError:
            errors.append(book_data)

        detail_pages += 1
# =========================================================================================================

    # see if next page
    next_page = soup.find("li", class_="next")
    if next_page:
        next_href = next_page.find("a")["href"]
        page_url = urljoin(page_url, next_href)
    else:
        page_url = None

    pages+=1

# Add books from all pages to output:
if book_cache_file.exists() == False:
     Path("cache/output").mkdir(exist_ok=True)
if book_cache_file_error.exists() == False:
     Path("cache/output").mkdir(exist_ok=True)

with open(book_cache_file, "w", encoding="utf-8") as f:
    json.dump(books, f, indent=4)

with open(book_cache_file_error, "w", encoding="utf-8") as f:
    json.dump(errors, f, indent=4)


# print some stats
print("catalogue_pages =", pages)
print("discovered =", len(urls))
print("unique_urls =", len(seen_urls))
print(books[0])
print("detailed_pages=", detail_pages)

# report:
reportPath = Path("cache/output/run-report.json")

duration = str(round((time.perf_counter() - start_sec), 3)) + "s"

reportData = {
    "start time": start_time,
    "duration": duration,
    "pages fetched": pages,
    "cache hits": cache_hits,
    "valid records": len(books),
    "invalid records": len(errors),
    "failed pages": failed_pages
}

with open(reportPath, "w", encoding="utf-8") as f:
    json.dump(reportData, f, indent=4)
 
