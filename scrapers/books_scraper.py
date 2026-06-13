from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from models.product import Product
from scrapers.base_scraper import BaseScraper, ScrapeError, ParseError
from utils.helpers import clean_price, clean_rating, retry
from utils.logger import setup_logger

logger = setup_logger(__name__)

RATING_MAP = {
    "One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0, "Five": 5.0,
}


class BooksScraper(BaseScraper):
    BASE_URL = "https://books.toscrape.com"

    def __init__(self):
        super().__init__(source_name="books.toscrape.com")
        self.client = httpx.Client(follow_redirects=True, timeout=30.0)

    @retry(max_retries=3, delay=1.0)
    def _fetch_page(self, url: str) -> str:
        response = self.client.get(url)
        response.raise_for_status()
        return response.text

    def _parse_rating(self, star_class: str) -> Optional[float]:
        for key, value in RATING_MAP.items():
            if key in star_class:
                return value
        return None

    def _parse_book(self, article) -> Optional[Product]:
        try:
            name_tag = article.select_one("h3 a")
            if not name_tag:
                return None
            name = name_tag.get("title", "").strip()
            relative_url = name_tag.get("href", "")
            url = self.BASE_URL + "/" + relative_url.lstrip("../")

            price_tag = article.select_one(".price_color")
            price_text = price_tag.text.strip() if price_tag else "0"
            price = clean_price(price_text) or 0.0

            rating_tag = article.select_one(".star-rating")
            rating = None
            if rating_tag:
                for cls in rating_tag.get("class", []):
                    if cls in ("star-rating",):
                        continue
                    rating = self._parse_rating(cls)
                    break

            avail_tag = article.select_one(".instock.availability")
            availability = "In stock" if avail_tag else "Unknown"

            img_tag = article.select_one(".image_container img")
            img_url = ""
            if img_tag:
                src = img_tag.get("src", "")
                img_url = self.BASE_URL + "/" + src.lstrip("../")

            return Product(
                name=name,
                price=price,
                currency="GBP",
                rating=rating,
                availability=availability,
                url=url,
                image_url=img_url,
                source=self.source_name,
            )
        except Exception as e:
            logger.warning(f"Failed to parse a book: {e}")
            return None

    async def scrape(self, max_pages: int = 1, **kwargs) -> List[Product]:
        self.products = []
        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/catalogue/page-{page}.html"
            logger.info(f"Scraping page {page}: {url}")
            try:
                html = self._fetch_page(url)
            except Exception as e:
                logger.error(f"Failed to fetch page {page}: {e}")
                break
            soup = BeautifulSoup(html, "lxml")
            articles = soup.select("article.product_pod")
            if not articles:
                logger.info("No more products found, stopping.")
                break
            for article in articles:
                product = self._parse_book(article)
                if product:
                    self.products.append(product)
            logger.info(f"Found {len(articles)} books on page {page}")
        logger.info(f"Scraped {len(self.products)} books total.")
        return self.products
