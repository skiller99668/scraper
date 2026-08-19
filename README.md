## Target Classification

This program scrapes book data from [books.toscrape.com](https://books.toscrape.com/), limited to the first
3 catalogue pages. It is appropriate because that is what toscrape.com exists for (a sandbox site for people
to practice scraping).

No `robots.txt` was found on the site.

I will not reuse this code on another site without checking that site's rules and terms first.

## Lane & Installation

**Lane:** static HTML, no browser automation. Every page this script needs (catalogue listings and book detail
pages) is returned as plain server-rendered HTML on the first request, so `requests` + `BeautifulSoup` is
enough — there's nothing here that needs a JS-executing browser.

Install the dependencies:

```
pip install requests beautifulsoup4 pydantic
```

## How to Run

From the repo root:

```
python src/main.py
```

This produces (or refreshes) three files under `cache/output/`:

- `books.json` — validated records
- `errors.json` — records/fetches that failed
- `run-report.json` — summary stats for that run

## Record Schema

Each entry in `books.json` matches this shape (enforced with a pydantic model):

| Field                | Type          | Notes                                          |
|-----------------------|---------------|-------------------------------------------------|
| `title`               | `str`         | Book title                                       |
| `product_url`         | `str`         | Full URL of the book's detail page               |
| `price_gbp`           | `float`       | Price in GBP, parsed from the page's price text  |
| `availability_text`   | `str`         | Raw availability string (e.g. "In stock (22 available)") |
| `rating_text`         | `str`         | Star rating as a word (e.g. "Three")             |
| `description`         | `str \| None` | Product description, if present                 |
| `source_page`         | `str`         | Catalogue page the book was discovered on        |
| `fetched_at`          | `str`         | UTC timestamp (ISO 8601) of when it was fetched  |

## Politeness Rules

- **User-Agent:** every request identifies itself as `FlyRankInternshipA9/1.0/skiller99668/scraper`, not a
  browser UA.
- **Delay:** a `time.sleep(0.5)` throttle before every outbound HTTP request (catalogue pages and book pages
  alike).
- **Timeout:** every request is capped at `timeout=5` seconds; on a timeout or a 5xx server error, the script
  retries the same URL exactly once before giving up and moving on.
- **Cache:** catalogue pages are cached to `cache/page-N.html` and book detail pages to `cache/books/<slug>`.
  If a cached copy already exists, it's read from disk and the network is never touched — so re-running the
  script doesn't cost the target site anything for pages it's already served once.

## Known Limitation

`price_gbp` is coerced from scraped text into a Python `float`. Floats can't represent trailing zeros, so a
price like `£50.10` round-trips through the pipeline as `50.1` instead of `50.10` — the trailing zero is lost
in `books.json`. This is harmless for sorting/comparison but wrong if the output needs to be displayed back
as currency; the honest fix is to keep the price as a formatted string instead of a `float`.

## Proof of a Real Run

Actual `run-report.json` from a completed run:

```json
{
    "start time": "2026-08-18T23:19:41Z",
    "duration": "1.367s",
    "pages fetched": 3,
    "cache hits": 60,
    "valid records": 60,
    "invalid records": 0,
    "failed pages": 0
}
```

## Why No Browser

All the data this assignment needs (title, price, availability, rating, description) is already present in the
raw HTML the server sends back on the very first request — nothing is loaded or rendered by client-side
JavaScript — so running a real browser here would only add startup and render cost without unlocking any data
that a plain HTTP `GET` doesn't already have.

## Ethics Note

Prefer an official API over scraping whenever one exists. Never bypass logins, paywalls, CAPTCHAs, or other
explicit blocks — those are a signal to stop, not an obstacle to work around. Only collect the fields actually
needed for the task, identify the scraper honestly via its User-Agent, and check a site's `robots.txt` and
terms of service before pointing this at anything other than a scraping sandbox.
