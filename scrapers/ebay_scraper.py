import os
import re
from typing import List, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from models.product import Product
from scrapers.base_scraper import BaseScraper, ScrapeError
from utils.helpers import clean_price, clean_rating, get_random_user_agent
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EbayScraper(BaseScraper):
    BASE_URL = "https://www.ebay.com"
    SEARCH_PATH = "/sch/i.html"

    def __init__(self, search_term: str, debug: bool = False):
        super().__init__(source_name="ebay.com")
        self.search_term = search_term
        self.debug = debug
        self.search_url = (
            f"{self.BASE_URL}{self.SEARCH_PATH}"
            f"?_nkw={quote_plus(search_term)}&_ipg=60&_sop=12"
        )

    async def _capture_debug_html(self, html: str):
        if not self.debug:
            return
        debug_dir = os.path.join(os.path.dirname(__file__), "..", "debug")
        os.makedirs(debug_dir, exist_ok=True)
        safe_name = re.sub(r"[^\w]+", "_", self.search_term)[:40]
        path = os.path.join(debug_dir, f"ebay_{safe_name}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"Debug HTML saved to {path}")

    async def scrape(self, **kwargs) -> List[Product]:
        self.products = []
        logger.info(f"Searching eBay for: {self.search_term}")

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent=get_random_user_agent(),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
            )
            page = await context.new_page()

            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # Visit homepage first to set cookies, then search
            try:
                await page.goto(
                    self.BASE_URL,
                    wait_until="domcontentloaded",
                    timeout=20000,
                )
                await page.wait_for_timeout(1000)
            except Exception:
                logger.warning("Homepage load failed, proceeding directly to search")

            logger.info(f"Navigating to search URL")
            try:
                resp = await page.goto(
                    self.search_url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                status = resp.status if resp else "none"
                logger.info(f"Search page HTTP status: {status}")
            except PlaywrightTimeout:
                raise ScrapeError(
                    f"Timeout loading eBay search: {self.search_url}"
                )

            # Wait for the results list to appear
            try:
                await page.wait_for_selector(
                    "ul.srp-results",
                    timeout=15000,
                )
                logger.info("Results container appeared")
            except PlaywrightTimeout:
                raise ScrapeError(
                    "eBay results container not found. "
                    "The site may be blocking the request."
                )

            # Small buffer for dynamic rendering
            await page.wait_for_timeout(2000)

            html = await page.content()
            await self._capture_debug_html(html)
            await browser.close()

        soup = BeautifulSoup(html, "lxml")
        results_container = soup.select_one("ul.srp-results")
        if not results_container:
            raise ScrapeError("Could not find results container in parsed HTML")

        all_cards = results_container.find_all(
            "li", attrs={"data-listingid": True}, recursive=False
        )
        logger.info(f"Found {len(all_cards)} listing containers")

        parsed_count = 0
        skipped_count = 0

        for card in all_cards:
            product = self._parse_card(card)
            if product:
                self.products.append(product)
                parsed_count += 1
            else:
                skipped_count += 1

        logger.info(
            f"Successfully parsed {parsed_count} products"
        )
        if skipped_count:
            logger.info(f"Skipped {skipped_count} incomplete listings")

        return self.products

    def _parse_card(self, card) -> Optional[Product]:
        listing_id = card.get("data-listingid", "")
        try:
            # Title
            title_el = card.select_one(
                "a[href*='itm'] span, "
                ".s-card__link span, "
                ".su-card-container__header a span"
            )
            if not title_el:
                title_el = card.select_one(".su-card-container__header a[href*='itm']")
            name = title_el.get_text(strip=True) if title_el else ""

            # Clean title: remove "Opens in a new window..." and "New listing" suffix
            name = re.sub(
                r"\s*Opens in a new window.*$", "", name
            ).strip()
            name = re.sub(r"^\s*New\s+listing\s*", "", name).strip()

            if not name:
                logger.debug(f"Card {listing_id}: no title found, skipping")
                return None

            # Price
            price_el = card.select_one(
                ".s-card__price.large-1, "
                "span.su-styled-text.primary.bold.large-1"
            )
            price = 0.0
            if price_el:
                price = clean_price(price_el.get_text(strip=True)) or 0.0
            if not price:
                attrs_primary = card.select_one(
                    ".su-card-container__attributes__primary"
                )
                if attrs_primary:
                    dollar_match = re.search(
                        r"\$([\d.,]+)", attrs_primary.get_text(" ", strip=True)
                    )
                    if dollar_match:
                        price = clean_price(f"${dollar_match.group(1)}") or 0.0

            # Condition
            condition_el = card.select_one(".s-card__subtitle-row")
            condition = condition_el.get_text(strip=True) if condition_el else ""

            # Shipping - extract from attributes primary section
            shipping = ""
            attrs_primary = card.select_one(
                ".su-card-container__attributes__primary"
            )
            if attrs_primary:
                attrs_text = attrs_primary.get_text(" ", strip=True)
                ship_match = re.search(
                    r"\+?\$?([\d.,]+)\s*(delivery|shipping)",
                    attrs_text,
                    re.IGNORECASE,
                )
                if ship_match:
                    shipping = ship_match.group(0).strip()
                elif "Free" in attrs_text and "delivery" in attrs_text.lower():
                    shipping = "Free delivery"
                elif "Free" in attrs_text and "shipping" in attrs_text.lower():
                    shipping = "Free shipping"

            # Listing type (Buy It Now / Auction)
            listing_type = ""
            if attrs_primary:
                lt_match = re.search(
                    r"(Buy It Now|Auction|Best Offer)",
                    attrs_primary.get_text(" ", strip=True),
                )
                if lt_match:
                    listing_type = lt_match.group(1)

            # Availability: combine condition + listing type + shipping
            avail_parts = []
            if condition:
                avail_parts.append(condition)
            if listing_type:
                avail_parts.append(listing_type)
            availability = " | ".join(avail_parts) if avail_parts else "Unknown"

            # URL
            link_el = card.select_one("a[href*='itm']")
            url = ""
            if link_el:
                href = link_el.get("href", "")
                id_match = re.search(r"https://www\.ebay\.com/itm/(\d+)", href)
                if id_match:
                    url = f"https://www.ebay.com/itm/{id_match.group(1)}"

            # Image
            img_el = card.select_one(
                "img.s-card__image, "
                ".su-card-container__media img"
            )
            image_url = ""
            if img_el:
                image_url = (
                    img_el.get("src", "")
                    or img_el.get("data-src", "")
                    or ""
                )

            # Rating - only available on some listings
            rating = None
            review_count = None
            rating_el = card.select_one(".x-star-rating")
            if rating_el:
                aria_label = rating_el.get("aria-label", "")
                if aria_label:
                    rating = clean_rating(aria_label)
                    nums = re.findall(r"(\d[\d,.]*)", aria_label)
                    if len(nums) > 1:
                        try:
                            review_count = int(
                                nums[-1].replace(",", "")
                            )
                        except ValueError:
                            pass

            return Product(
                name=name,
                price=price,
                currency="USD",
                rating=rating,
                review_count=review_count,
                availability=availability,
                url=url,
                image_url=image_url,
                source=self.source_name,
            )

        except Exception as e:
            logger.debug(f"Card {listing_id}: parse error: {e}")
            return None
