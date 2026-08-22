#!/usr/bin/env python3
import sys
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

try:
    from firecrawl import FirecrawlApp
except ImportError:
    logging.error("firecrawl-py is required. Install via: pip install firecrawl-py")
    sys.exit(1)

def scrape_target(url: str, api_key: str = None):
    api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        logging.warning("⚠️  FIRECRAWL_API_KEY environment variable not set. Running in scrape mode...")

    app = FirecrawlApp(api_key=api_key) if api_key else FirecrawlApp(api_key="fc-placeholder")
    
    logging.info(f"🕸️  [FIRECRAWL]: Initiating scrape on {url}...")
    try:
        scrape_result = app.scrape_url(
            url,
            params={
                'formats': ['markdown', 'html'],
                'onlyMainContent': True
            }
        )
        
        output_dir = "data/scrapes"
        os.makedirs(output_dir, exist_ok=True)
        
        domain_slug = url.replace("https://", "").replace("http://", "").replace("/", "_").strip("_")
        output_path = os.path.join(output_dir, f"{domain_slug}.json")
        
        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump(scrape_result, fp, indent=2, ensure_ascii=False)

        logging.info(f"✅ [SCRAPE COMPLETE]: Output written to {output_path}")
        return scrape_result

    except Exception as e:
        logging.error(f"❌ [SCRAPE ERROR]: {e}")
        # Allow workflow to pass even if live scraping fails without an API key in CI
        if "API key" in str(e) or not api_key:
            logging.info("Skipping fatal exit due to unconfigured API key in runner.")
            sys.exit(0)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python firecrawl_fusion.py <target_url>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    scrape_target(target_url)
