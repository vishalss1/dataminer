from models.product import Product


class TestProduct:
    def test_create_product(self):
        p = Product(name="Test Book", price=19.99)
        assert p.name == "Test Book"
        assert p.price == 19.99
        assert p.currency == "USD"
        assert p.availability == "Unknown"

    def test_product_with_all_fields(self):
        p = Product(
            name="Test Product",
            price=29.99,
            currency="EUR",
            rating=4.5,
            review_count=120,
            availability="In Stock",
            url="https://example.com/p",
            image_url="https://example.com/img.jpg",
            source="example.com",
        )
        assert p.rating == 4.5
        assert p.review_count == 120
        assert p.availability == "In Stock"
        assert p.url == "https://example.com/p"

    def test_to_dict(self):
        p = Product(name="Widget", price=9.99, rating=3.0)
        d = p.to_dict()
        assert d["name"] == "Widget"
        assert d["price"] == 9.99
        assert d["rating"] == 3.0
        assert "scraped_at" in d

    def test_formatted_price_usd(self):
        p = Product(name="Item", price=12.50, currency="USD")
        assert p.formatted_price == "$12.50"

    def test_formatted_price_eur(self):
        p = Product(name="Item", price=12.50, currency="EUR")
        assert p.formatted_price == "€12.50"

    def test_formatted_price_gbp(self):
        p = Product(name="Item", price=12.50, currency="GBP")
        assert p.formatted_price == "£12.50"

    def test_formatted_price_inr(self):
        p = Product(name="Item", price=12.50, currency="INR")
        assert "₹" in p.formatted_price

    def test_optional_fields_default_none(self):
        p = Product(name="Test", price=0.0)
        assert p.rating is None
        assert p.review_count is None
        assert p.image_url == ""

    def test_scraped_at_is_set(self):
        p = Product(name="Test", price=0.0)
        assert p.scraped_at is not None
        assert len(p.scraped_at) > 0
