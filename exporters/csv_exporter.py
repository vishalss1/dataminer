from typing import List
import pandas as pd
from models.product import Product
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CSVExporter:
    def export(self, products: List[Product], filepath: str) -> str:
        data = [p.to_dict() for p in products]
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"Exported {len(products)} products to {filepath}")
        return filepath
