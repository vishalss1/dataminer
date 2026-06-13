from utils.helpers import (
    clean_price,
    clean_rating,
    slugify,
    truncate,
    get_random_user_agent,
)


class TestCleanPrice:
    def test_simple_number(self):
        assert clean_price("19.99") == 19.99

    def test_with_currency_symbol(self):
        assert clean_price("$29.99") == 29.99
        assert clean_price("€19.99") == 19.99

    def test_with_commas(self):
        assert clean_price("1,234.56") == 1234.56

    def test_empty_string(self):
        assert clean_price("") is None

    def test_none_input(self):
        assert clean_price(None) is None

    def test_invalid_text(self):
        assert clean_price("N/A") is None


class TestCleanRating:
    def test_word_ratings(self):
        assert clean_rating("One") == 1.0
        assert clean_rating("Five") == 5.0

    def test_number_string(self):
        assert clean_rating("4.5") == 4.5

    def test_out_of_five_format(self):
        assert clean_rating("4.5 out of 5") == 4.5

    def test_none_input(self):
        assert clean_rating(None) is None

    def test_empty_string(self):
        assert clean_rating("") is None


class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("Product #1!") == "product-1"


class TestTruncate:
    def test_short_text(self):
        assert truncate("Hello", 10) == "Hello"

    def test_long_text(self):
        text = "A" * 100
        assert len(truncate(text, 20)) <= 23

    def test_exact_boundary(self):
        text = "A" * 10
        assert truncate(text, 10) == "A" * 10


class TestUserAgent:
    def test_returns_string(self):
        ua = get_random_user_agent()
        assert isinstance(ua, str)
        assert len(ua) > 20

    def test_multiple_calls_different(self):
        agents = {get_random_user_agent() for _ in range(10)}
        assert len(agents) > 1
