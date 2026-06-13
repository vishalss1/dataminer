import os
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from bs4 import BeautifulSoup

from scrapers.ebay_scraper import EbayScraper, ScrapeError
from models.product import Product


SAMPLE_CARD_HTML = """
<li class="s-card" data-listingid="123456789012">
  <div class="su-card-container su-card-container--horizontal">
    <div class="su-card-container__media">
      <img class="s-card__image" src="https://i.ebayimg.com/test.jpg" />
    </div>
    <div class="su-card-container__content">
      <div class="su-card-container__header">
        <a class="s-card__link" href="https://www.ebay.com/itm/123456789012">
          <span>Test Wireless Mouse</span>
        </a>
      </div>
      <div class="s-card__subtitle-row">Brand New</div>
      <div class="su-card-container__attributes">
        <div class="su-card-container__attributes__primary">
          $25.99Buy It Now+$5.99 deliveryLocated in United States
        </div>
        <div class="su-card-container__attributes__secondary">
          seller99.8% positive
        </div>
      </div>
    </div>
  </div>
</li>
"""

SAMPLE_CARD_NO_TITLE = """
<li class="s-card" data-listingid="999999999999">
  <div class="su-card-container">
    <div class="su-card-container__content">
      <div class="su-card-container__header"></div>
    </div>
  </div>
</li>
"""

SAMPLE_CARD_WITH_RATING = """
<li class="s-card" data-listingid="111111111111">
  <div class="su-card-container su-card-container--horizontal">
    <div class="su-card-container__media">
      <img class="s-card__image" src="https://i.ebayimg.com/test2.jpg" />
    </div>
    <div class="su-card-container__content">
      <div class="su-card-container__header">
        <a class="s-card__link" href="https://www.ebay.com/itm/111111111111">
          <span>Rated Mouse Product</span>
        </a>
      </div>
      <div class="s-card__subtitle-row">Pre-Owned</div>
      <div class="x-star-rating" aria-label="4.5 out of 5 stars. 200 ratings">
        <span class="clipped">4.5 out of 5 stars.</span>
      </div>
      <div class="su-card-container__attributes">
        <div class="su-card-container__attributes__primary">
          $15.50Buy It NowFree delivery
        </div>
      </div>
    </div>
  </div>
</li>
"""


class TestEbayScraper:
    def test_init(self):
        scraper = EbayScraper("wireless mouse")
        assert scraper.search_term == "wireless mouse"
        assert scraper.source_name == "ebay.com"
        assert "wireless+mouse" in scraper.search_url
        assert scraper.BASE_URL == "https://www.ebay.com"

    def test_debug_default_false(self):
        scraper = EbayScraper("test")
        assert scraper.debug is False

    def test_debug_true(self):
        scraper = EbayScraper("test", debug=True)
        assert scraper.debug is True

    def test_search_url_encoding(self):
        scraper = EbayScraper("gaming keyboard")
        assert "gaming+keyboard" in scraper.search_url

    def test_search_url_with_special_chars(self):
        scraper = EbayScraper("laptop 15-inch")
        assert "laptop+15-inch" in scraper.search_url

    def test_empty_search_term(self):
        scraper = EbayScraper("")
        assert scraper.search_term == ""

    def test_init_source_name(self):
        scraper = EbayScraper("test")
        assert scraper.source_name == "ebay.com"

    def test_init_products_empty(self):
        scraper = EbayScraper("test")
        assert scraper.products == []
        assert scraper.count == 0

    @pytest.mark.asyncio
    async def test_scrape_returns_list(self):
        scraper = EbayScraper("test")
        with patch.object(scraper, "scrape", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = []
            result = await scraper.scrape()
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_scrape_timeout_raises(self):
        scraper = EbayScraper("test")
        with patch.object(scraper, "scrape", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = ScrapeError("Timeout")
            with pytest.raises(ScrapeError):
                await scraper.scrape()

    @pytest.mark.asyncio
    async def test_capture_debug_html(self):
        scraper = EbayScraper("test debug", debug=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("scrapers.ebay_scraper.os.makedirs") as mock_makedirs:
                with patch("builtins.open") as mock_open:
                    await scraper._capture_debug_html("<html></html>")
                    mock_makedirs.assert_called_once()
                    mock_open.assert_called_once()

    def test_parse_valid_card(self):
        scraper = EbayScraper("test")
        soup = BeautifulSoup(SAMPLE_CARD_HTML, "lxml")
        card = soup.select_one("li[data-listingid]")
        product = scraper._parse_card(card)
        assert product is not None
        assert isinstance(product, Product)
        assert product.name == "Test Wireless Mouse"
        assert product.price == 25.99
        assert product.availability == "Brand New | Buy It Now"
        assert product.url == "https://www.ebay.com/itm/123456789012"
        assert "i.ebayimg.com" in product.image_url
        assert product.source == "ebay.com"
        assert product.currency == "USD"

    def test_parse_card_no_title_returns_none(self):
        scraper = EbayScraper("test")
        soup = BeautifulSoup(SAMPLE_CARD_NO_TITLE, "lxml")
        card = soup.select_one("li[data-listingid]")
        product = scraper._parse_card(card)
        assert product is None

    def test_parse_card_with_rating(self):
        scraper = EbayScraper("test")
        soup = BeautifulSoup(SAMPLE_CARD_WITH_RATING, "lxml")
        card = soup.select_one("li[data-listingid]")
        product = scraper._parse_card(card)
        assert product is not None
        assert product.name == "Rated Mouse Product"
        assert product.price == 15.50
        assert product.rating == 4.5
        assert product.review_count is not None
        assert product.availability == "Pre-Owned | Buy It Now"

    def test_parse_card_handles_missing_fields(self):
        html = """
        <li class="s-card" data-listingid="555555555555">
          <div class="su-card-container">
            <div class="su-card-container__content">
              <div class="su-card-container__header">
                <a class="s-card__link" href="https://www.ebay.com/itm/555555555555">
                  <span>Minimal Product</span>
                </a>
              </div>
            </div>
          </div>
        </li>
        """
        scraper = EbayScraper("test")
        soup = BeautifulSoup(html, "lxml")
        card = soup.select_one("li[data-listingid]")
        product = scraper._parse_card(card)
        assert product is not None
        assert product.name == "Minimal Product"
        assert product.price == 0.0
        assert product.availability == "Unknown"
        assert product.rating is None
