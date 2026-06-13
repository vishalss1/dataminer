<div align="center">

# 🕷️ DataMiner

**A professional web scraping toolkit for extracting e-commerce product data and exporting to CSV, JSON, and beautifully formatted Excel files.**

[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat-square)](https://github.com/astral-sh/ruff)
[![Dependencies: uv](https://img.shields.io/badge/deps-uv-2B3A42?style=flat-square&logo=python&logoColor=white)](https://github.com/astral-sh/uv)

</div>

---

## ✨ Features

- **Multi-source scraping** — BooksToScrape, generic e-commerce pages (Playwright-powered), eBay product search
- **Multiple export formats** — CSV, JSON, and **professionally formatted Excel** (.xlsx) with styling
- **Beautiful CLI** — Rich-powered progress bars, colored output, and interactive tables
- **Extensible architecture** — Abstract base scraper makes adding new sources trivial
- **Resilient** — Built-in retry logic, timeout handling, and comprehensive error management
- **Client-ready output** — Excel files with bold headers, frozen panes, auto-width columns, filters, alternating row colors, currency formatting, and hyperlinks

## 📦 Installation

### Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Playwright browsers

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/dataminer.git
cd dataminer

# Install dependencies with uv
uv sync

# Install Playwright browsers
playwright install chromium

# Or with pip
pip install -e .
playwright install chromium
```

## 🚀 Usage

### Scrape books.toscrape.com

```bash
python main.py books
python main.py books --pages 3
python main.py books --currency GBP
```

### Scrape any e-commerce page

```bash
python main.py generic https://books.toscrape.com
python main.py generic https://example-store.com/products
```

### Search eBay products

```bash
python main.py ebay "wireless mouse"
python main.py ebay "gaming keyboard"
```

Extracted fields:
- Product name
- Price
- Shipping cost
- Condition
- Rating (if available)
- Review count (if available)
- Product URL
- Image URL

### Display project info

```bash
python main.py info
```

## 📁 Project Structure

```
dataminer/
├── scrapers/
│   ├── base_scraper.py       # Abstract base class
│   ├── books_scraper.py      # BooksToScrape implementation
│   ├── generic_scraper.py    # Playwright-powered generic scraper
│   └── ebay_scraper.py       # eBay product search
├── exporters/
│   ├── csv_exporter.py       # CSV export
│   ├── json_exporter.py      # JSON export
│   └── excel_exporter.py     # Formatted Excel export
├── models/
│   └── product.py            # Product dataclass
├── utils/
│   ├── logger.py             # Rich logging
│   └── helpers.py            # Utilities (retry, price parsing, etc.)
├── output/                   # Exported files land here
├── tests/                    # pytest test suite
├── main.py                   # CLI entry point (Typer)
├── pyproject.toml            # Project configuration
└── README.md
```

## 📊 Output Formats

### CSV (`output/products.csv`)

Clean, UTF-8 encoded CSV with headers, ready for Excel or any data analysis tool.

### JSON (`output/products.json`)

Formatted JSON array of product objects, suitable for APIs and programmatic consumption.

### Excel (`output/products.xlsx`)

Professionally styled spreadsheet including:

| Feature | Description |
|---------|-------------|
| **Bold headers** | White text on dark blue background |
| **Frozen top row** | Headers always visible when scrolling |
| **Auto-width columns** | No more squished text |
| **Filters** | Dropdown filters on every column |
| **Alternating rows** | Light blue / white zebra striping |
| **Currency formatting** | Proper `$12.99` display |
| **Hyperlinks** | Clickable product URLs |
| **Summary sheet** | Statistics and metadata |

## 🧪 Testing

```bash
pytest
pytest -v           # verbose
pytest --cov        # with coverage (if installed)
```

## 🧩 Architecture

```
CLI (Typer)
  │
  ├── Scraper (BaseScraper ABC)
  │     ├── BooksScraper    (httpx + BeautifulSoup)
  │     ├── GenericScraper  (Playwright + BeautifulSoup)
  │     └── EbayScraper     (Playwright + BeautifulSoup)
  │
  ├── Product model (dataclass)
  │
  └── Exporter
        ├── CSVExporter
        ├── JSONExporter
        └── ExcelExporter   (OpenPyXL with formatting)
```

## 🔧 Extending

Adding a new scraper is straightforward:

1. Create `scrapers/your_source_scraper.py`
2. Subclass `BaseScraper`
3. Implement the `async def scrape(self, **kwargs) -> List[Product]` method
4. Add a new Typer command in `main.py`

```python
from scrapers.base_scraper import BaseScraper
from models.product import Product

class MyScraper(BaseScraper):
    async def scrape(self, **kwargs) -> List[Product]:
        # Your scraping logic here
        return products
```

## 📸 Screenshots

| CLI Output | Excel Output |
|------------|--------------|
| *(screenshot placeholder)* | *(screenshot placeholder)* |