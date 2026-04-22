import os
from datetime import datetime, timezone

from firecrawl import FirecrawlApp


def scrape_competitor(urls_config: dict) -> dict:
    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
    results = {}

    for key, config in urls_config["urls"].items():
        print(f"  Scraping {config['label']} ({config['url']})...")
        try:
            # firecrawl-py v2: scrape() replaces scrape_url(), response is an object not a dict
            response = app.scrape(config["url"], formats=["markdown"])
            content = (response.markdown or "").strip() or "[No content returned]"
        except Exception as e:
            print(f"  Warning: failed to scrape {config['label']}: {e}")
            content = f"[Scrape failed: {e}]"

        results[key] = {
            "label": config["label"],
            "url": config["url"],
            "content": content,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

    return results
