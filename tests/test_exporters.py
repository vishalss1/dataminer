import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from models.product import Product
from exporters.csv_exporter import CSVExporter
from exporters.json_exporter import JSONExporter
from exporters.excel_exporter import ExcelExporter

SAMPLE_PRODUCTS = [
    Product(
        name="Test Product A",
        price=19.99,
        currency="USD",
        rating=4.5,
        review_count=10,
        availability="In Stock",
        url="https://example.com/a",
        image_url="https://example.com/a.jpg",
        source="test",
    ),
    Product(
        name="Test Product B",
        price=29.99,
        currency="USD",
        rating=3.0,
        review_count=5,
        availability="Out of Stock",
        url="https://example.com/b",
        image_url="https://example.com/b.jpg",
        source="test",
    ),
]


class TestCSVExporter:
    def test_export_creates_file(self, tmp_path):
        path = tmp_path / "test.csv"
        CSVExporter().export(SAMPLE_PRODUCTS, str(path))
        assert path.exists()
        content = path.read_text(encoding="utf-8-sig")
        assert "Test Product A" in content
        assert "19.99" in content

    def test_export_has_header(self, tmp_path):
        path = tmp_path / "test.csv"
        CSVExporter().export(SAMPLE_PRODUCTS, str(path))
        content = path.read_text(encoding="utf-8-sig")
        assert "name" in content or "Product Name" in content


class TestJSONExporter:
    def test_export_creates_file(self, tmp_path):
        path = tmp_path / "test.json"
        JSONExporter().export(SAMPLE_PRODUCTS, str(path))
        assert path.exists()

    def test_export_valid_json(self, tmp_path):
        path = tmp_path / "test.json"
        JSONExporter().export(SAMPLE_PRODUCTS, str(path))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["name"] == "Test Product A"
        assert data[0]["price"] == 19.99

    def test_export_empty_list(self, tmp_path):
        path = tmp_path / "empty.json"
        JSONExporter().export([], str(path))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data == []


class TestExcelExporter:
    def test_export_creates_file(self, tmp_path):
        path = tmp_path / "test.xlsx"
        ExcelExporter().export(SAMPLE_PRODUCTS, str(path))
        assert path.exists()
        assert path.stat().st_size > 0

    def test_export_with_different_currency(self, tmp_path):
        products = [
            Product(name="EUR Item", price=15.50, currency="EUR"),
        ]
        path = tmp_path / "eur.xlsx"
        ExcelExporter(currency="EUR").export(products, str(path))
        assert path.exists()

    def test_export_empty_list(self, tmp_path):
        path = tmp_path / "empty.xlsx"
        ExcelExporter().export([], str(path))
        assert path.exists()
