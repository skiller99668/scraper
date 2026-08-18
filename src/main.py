import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

base_url = "https://books.toscrape.com/"
start_url = urljoin(base_url, "catalogue/page-1.html")

headers = {
        "User-Agent": "FlyRankInternshipA9/1.0/skiller99668/scraper"
    }

urls = []
page_url = start_url

pages = 0
while page_url and pages < 3:
    # print("processing", page_url)
    cache_file = Path(f"cache/{page_url.strip("/").split("/")[-1] }")

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