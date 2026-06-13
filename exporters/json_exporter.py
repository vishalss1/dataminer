import json
from typing import List
from models.product import Product
from utils.logger import setup_logger

logger = setup_logger(__name__)


class JSONExporter:
    def export(self, products: List[Product], filepath: str, indent: int = 2) -> str:
        data = [p.to_dict() for p in products]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        logger.info(f"Exported {len(products)} products to {filepath}")
        return filepath
