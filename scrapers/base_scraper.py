from abc import ABC, abstractmethod
from typing import List, Optional
from models.product import Product


class ScrapeError(Exception):
    pass


class TimeoutError(ScrapeError):
    pass


class ParseError(ScrapeError):
    pass


class BaseScraper(ABC):
    def __init__(self, source_name: str = "unknown"):
        self.source_name = source_name
        self.products: List[Product] = []

    @abstractmethod
    async def scrape(self, **kwargs) -> List[Product]:
        pass

    def get_results(self) -> List[Product]:
        return self.products

    @property
    def count(self) -> int:
        return len(self.products)
