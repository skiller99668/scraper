import requests
from pathlib import Path

cache_file = Path("cache/catalogue-page-1.html")

if cache_file.exists():
    Path("cache/catalogue-page-1.html")
    print("read from cache")

else:
    url = "https://books.toscrape.com/catalogue/page-1.html"
    headers = {
        "User-Agent": "FlyRankInternshipA9/1.0/skiller99668/scraper"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)

        print(response.status_code)
        if response.status_code == 200:
            Path("cache").mkdir(exist_ok=True)
            # print(response.text)

            Path("cache/catalogue-page-1.html").write_text(
                response.text
            )
        else:
            print(f"failed to fetch. error code: {response.status_code}")

    except requests.exceptions.Timeout:
        print("Timeout (5.0 s)")