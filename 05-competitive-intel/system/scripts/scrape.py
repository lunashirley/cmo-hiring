import os
from datetime import datetime, timezone

import requests

FIRECRAWL_API = "https://api.firecrawl.dev/v1/scrape"


def scrape_competitor(urls_config: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {os.environ['FIRECRAWL_API_KEY']}",
        "Content-Type": "application/json",
    }
    results = {}

    for key, config in urls_config["urls"].items():
        print(f"  Scraping {config['label']} ({config['url']})...")
        try:
            response = requests.post(
                FIRECRAWL_API,
                headers=headers,
                json={"url": config["url"], "formats": ["markdown"]},
                timeout=30,
            )
            response.raise_for_status()
            content = (response.json().get("data", {}).get("markdown") or "").strip()
            content = content or "[No content returned]"
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
