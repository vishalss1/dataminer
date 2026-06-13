import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from models.product import Product
from scrapers.base_scraper import BaseScraper, ScrapeError
from utils.helpers import clean_price, clean_rating, get_random_user_agent
from utils.logger import setup_logger

logger = setup_logger(__name__)

PRODUCT_SELECTORS = {
    "container": [
        "[data-component='product']",
        "[data-testid='product']",
        ".product-item",
        ".product",
        ".card-product",
        "[class*='product']",
        "article",
        ".item",
    ],
    "name": [
        "h2 a",
        "h3 a",
        "[data-product-name]",
        ".product-title",
        ".product-name",
        ".name",
        "[class*='productName']",
        "[class*='product-name']",
        "h2",
        "h3",
    ],
    "price": [
        "[data-price]",
        ".price",
        ".price-amount",
        ".amount",
        "[class*='price']",
        ".sale-price",
        ".regular-price",
    ],
    "rating": [
        "[data-rating]",
        ".rating",
        ".stars",
        "[class*='rating']",
        "[class*='stars']",
    ],
    "review_count": [
        "[data-reviews]",
        ".review-count",
        ".reviews",
        "[class*='review']",
    ],
    "availability": [
        "[data-availability]",
        ".availability",
        ".stock-status",
        "[class*='stock']",
        "[class*='availability']",
    ],
    "image": [
        ".product-image img",
        ".image img",
        "img[src*='product']",
        "img[src*='/images/']",
        ".photo img",
        "[class*='image'] img",
    ],
}


class GenericScraper(BaseScraper):
    def __init__(self, url: str):
        super().__init__(source_name=urlparse(url).netloc if url else "generic")
        self.url = url
        self.base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}" if url else ""

    async def scrape(self, **kwargs) -> List[Product]:
        self.products = []
        logger.info(f"Launching browser for {self.url}")
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=get_random_user_agent(),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()
            try:
                await page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                html = await page.content()
            except PlaywrightTimeout:
                raise ScrapeError(f"Timeout loading {self.url}")
            finally:
                await browser.close()

        soup = BeautifulSoup(html, "lxml")
        containers = self._find_elements(soup, "container")
        if not containers:
            containers = [soup]

        for container in containers:
            product = self._parse_container(container)
            if product:
                self.products.append(product)

        logger.info(f"Extracted {len(self.products)} products from {self.url}")
        return self.products

    def _find_elements(self, soup, key: str) -> List:
        for selector in PRODUCT_SELECTORS[key]:
            elements = soup.select(selector)
            if elements:
                return elements
        return []

    def _get_text(self, container, key: str) -> Optional[str]:
        for selector in PRODUCT_SELECTORS[key]:
            tag = container.select_one(selector)
            if tag:
                text = tag.get_text(strip=True)
                if text:
                    return text
        return None

    def _get_attr(self, container, key: str, attr: str = "href") -> Optional[str]:
        for selector in PRODUCT_SELECTORS[key]:
            tag = container.select_one(selector)
            if tag and tag.get(attr):
                val = tag[attr]
                if val.startswith("/") and self.base_url:
                    return urljoin(self.base_url, val)
                return val
        return None

    def _parse_container(self, container) -> Optional[Product]:
        try:
            name = self._get_text(container, "name")
            if not name:
                return None

            price_text = self._get_text(container, "price")
            price = clean_price(price_text) if price_text else 0.0

            rating_text = self._get_text(container, "rating")
            rating = clean_rating(rating_text) if rating_text else None

            reviews_text = self._get_text(container, "review_count")
            review_count = None
            if reviews_text:
                match = re.search(r"(\d+)", reviews_text)
                if match:
                    review_count = int(match.group(1))

            availability = self._get_text(container, "availability") or "Unknown"
            url = self._get_attr(container, "name") or self.url
            image_url = self._get_attr(container, "image", "src") or ""

            return Product(
                name=name,
                price=price,
                rating=rating,
                review_count=review_count,
                availability=availability,
                url=url,
                image_url=image_url,
                source=self.source_name,
            )
        except Exception as e:
            logger.warning(f"Failed to parse product container: {e}")
            return None
