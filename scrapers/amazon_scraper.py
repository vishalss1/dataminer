"""
Amazon Scraper — Template / Example Implementation

⚠️  DISCLAIMER
Amazon employs aggressive anti-bot measures (CAPTCHAs, IP tracking,
request fingerprinting). This scraper is provided as a structural
template showing how an Amazon scraper *could* be organised. It will
NOT work out of the box and is intended as a starting point for
clients who require Amazon scraping via proxies, residential IPs, or
third-party APIs.

Recommended approaches for production:
1. Use a paid proxy service (BrightData, ScrapingBee, etc.)
2. Use Amazon's Product Advertising API (official)
3. Use a specialised scraping API (RapidAPI, etc.)
"""

from typing import List, Optional
from urllib.parse import quote_plus
from models.product import Product
from scrapers.base_scraper import BaseScraper
from utils.logger import setup_logger

logger = setup_logger(__name__)

AMAZON_SELECTORS = {
    "container": '[data-component-type="s-search-result"]',
    "name": "h2 a span",
    "price_whole": ".a-price-whole",
    "price_fraction": ".a-price-fraction",
    "rating": ".a-icon-alt",
    "review_count": ".a-size-base.s-underline-text",
    "availability": ".a-row .a-size-base.a-color-price",
    "image": ".s-image",
    "url": "h2 a.a-link-normal",
}


class AmazonScraper(BaseScraper):
    BASE_URL = "https://www.amazon.com"

    def __init__(self, search_term: str):
        super().__init__(source_name="amazon.com")
        self.search_term = search_term
        self.search_url = f"{self.BASE_URL}/s?k={quote_plus(search_term)}"

    async def scrape(self, **kwargs) -> List[Product]:
        logger.warning(
            "Amazon scraping is blocked by anti-bot measures. "
            "Use a proxy service or the Product Advertising API instead."
        )
        logger.info(f"Search URL (for reference): {self.search_url}")
        self.products = []
        return self.products
