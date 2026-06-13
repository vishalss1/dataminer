from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Product:
    name: str
    price: float
    currency: str = "USD"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: str = "Unknown"
    url: str = ""
    image_url: str = ""
    source: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "price": self.price,
            "currency": self.currency,
            "rating": self.rating,
            "review_count": self.review_count,
            "availability": self.availability,
            "url": self.url,
            "image_url": self.image_url,
            "source": self.source,
            "scraped_at": self.scraped_at,
        }

    @property
    def formatted_price(self) -> str:
        symbols = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}
        symbol = symbols.get(self.currency, self.currency + " ")
        return f"{symbol}{self.price:.2f}"
