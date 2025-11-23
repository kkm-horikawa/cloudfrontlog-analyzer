"""Unit tests for CloudFront log parsers.

Tests all parser implementations (W3C, JSON, Parquet, Plain) to ensure
they correctly parse CloudFront v1 and v2 log formats.
"""

import gzip
import os
from pathlib import Path

import pandas as pd
import pytest

from api.utils.log_parsers import (
    JSONParser,
    ParquetParser,
    PlainParser,
    W3CParser,
    create_parser,
)


# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "v2_samples"


class TestW3CParser:
    """Tests for W3C format parser (v1)."""

    def setup_method(self):
        """Setup test parser."""
        self.parser = W3CParser()

    def test_parse_v1_gzip(self):
        """Test parsing v1 gzipped W3C format."""
        # Load sample v1.gz file
        sample_path = TEST_DATA_DIR / "sample_v1.gz"
        with open(sample_path, "rb") as f:
            content = f.read()

        df = self.parser.parse(content)

        # Assertions
        assert not df.empty
        assert len(df) == 3  # 3 log entries
        assert "datetime" in df.columns
        assert "c-ip" in df.columns
        assert "cs-uri-stem" in df.columns

        # Check first row
        first_row = df.iloc[0]
        assert first_row["c-ip"] == "203.0.113.45"
        assert first_row["cs-method"] == "GET"
        assert first_row["cs-uri-stem"] == "/api/users"
        assert first_row["sc-status"] == 200

    def test_parse_handles_missing_values(self):
        """Test that parser correctly handles '-' as missing values."""
        sample_path = TEST_DATA_DIR / "sample_v1.gz"
        with open(sample_path, "rb") as f:
            content = f.read()

        df = self.parser.parse(content)

        # Check that '-' is converted to NaN/empty (use pd.isna)
        assert pd.isna(df["x-forwarded-for"].iloc[0]) or df["x-forwarded-for"].iloc[0] == ""

    def test_supports_format(self):
        """Test format detection."""
        assert self.parser.supports_format(".gz")
        assert not self.parser.supports_format(".json")


class TestJSONParser:
    """Tests for JSON format parser (v2)."""

    def setup_method(self):
        """Setup test parser."""
        self.parser = JSONParser()

    def test_parse_json_lines(self):
        """Test parsing JSON Lines format."""
        sample_path = TEST_DATA_DIR / "sample_v2.json"
        with open(sample_path, "rb") as f:
            content = f.read()

        df = self.parser.parse(content)

        # Assertions
        assert not df.empty
        assert len(df) == 5  # 5 log entries
        assert "datetime" in df.columns
        assert "c-ip" in df.columns

        # Check v2-specific fields
        assert "timestamp(ms)" in df.columns
        assert "origin-fbl" in df.columns
        assert "origin-lbl" in df.columns
        assert "asn" in df.columns
        assert "c-country" in df.columns
        assert "cache-behavior-path-pattern" in df.columns

        # Check first row v2 fields (note: JSON parser may return strings)
        first_row = df.iloc[0]
        assert int(first_row["timestamp(ms)"]) == 1732366496000
        assert int(first_row["asn"]) == 7506
        assert first_row["c-country"] == "JP"

    def test_parse_json_gzipped(self):
        """Test parsing gzipped JSON format."""
        sample_path = TEST_DATA_DIR / "sample_v2.json.gz"
        with open(sample_path, "rb") as f:
            content = f.read()

        df = self.parser.parse(content)

        assert not df.empty
        assert len(df) == 5

    def test_supports_format(self):
        """Test format detection."""
        assert self.parser.supports_format(".json")
        assert self.parser.supports_format(".json.gz")
        assert not self.parser.supports_format(".parquet")


class TestPlainParser:
    """Tests for Plain/CSV format parser (v2)."""

    def setup_method(self):
        """Setup test parser."""
        self.parser = PlainParser()

    def test_parse_csv(self):
        """Test parsing CSV format."""
        sample_path = TEST_DATA_DIR / "sample_v2.csv"
        with open(sample_path, "rb") as f:
            content = f.read()

        df = self.parser.parse(content)

        # Assertions
        assert not df.empty
        assert len(df) == 3  # 3 log entries
        assert "datetime" in df.columns

        # Check v2 fields
        assert "timestamp(ms)" in df.columns
        assert "asn" in df.columns
        assert "c-country" in df.columns

    def test_supports_format(self):
        """Test format detection."""
        assert self.parser.supports_format(".csv")
        assert self.parser.supports_format(".csv.gz")
        assert not self.parser.supports_format(".json")


class TestParserFactory:
    """Tests for parser factory function."""

    def test_create_w3c_parser(self):
        """Test creating W3C parser."""
        parser = create_parser("w3c")
        assert isinstance(parser, W3CParser)

    def test_create_json_parser(self):
        """Test creating JSON parser."""
        parser = create_parser("json")
        assert isinstance(parser, JSONParser)

    def test_create_parquet_parser(self):
        """Test creating Parquet parser."""
        parser = create_parser("parquet")
        assert isinstance(parser, ParquetParser)

    def test_create_plain_parser(self):
        """Test creating Plain parser."""
        parser = create_parser("plain")
        assert isinstance(parser, PlainParser)

    def test_create_parser_case_insensitive(self):
        """Test factory is case-insensitive."""
        parser = create_parser("JSON")
        assert isinstance(parser, JSONParser)

    def test_create_parser_invalid_format(self):
        """Test error handling for unknown format."""
        with pytest.raises(ValueError, match="Unknown format type"):
            create_parser("invalid")


class TestParserDataNormalization:
    """Tests for data normalization across all parsers."""

    def test_datetime_normalization(self):
        """Test that all parsers create UTC datetime columns."""
        # Test W3C parser
        w3c_parser = W3CParser()
        sample_path = TEST_DATA_DIR / "sample_v1.gz"
        with open(sample_path, "rb") as f:
            df_w3c = w3c_parser.parse(f.read())

        assert "datetime" in df_w3c.columns
        assert df_w3c["datetime"].dtype == "datetime64[ns, UTC]"

        # Test JSON parser
        json_parser = JSONParser()
        sample_path = TEST_DATA_DIR / "sample_v2.json"
        with open(sample_path, "rb") as f:
            df_json = json_parser.parse(f.read())

        assert "datetime" in df_json.columns
        # JSON parser creates datetime from timestamp(ms)
        assert df_json["datetime"].dtype == "datetime64[ns, UTC]"

    def test_missing_value_handling(self):
        """Test that '-' is properly handled as missing value."""
        w3c_parser = W3CParser()
        sample_path = TEST_DATA_DIR / "sample_v1.gz"
        with open(sample_path, "rb") as f:
            df = w3c_parser.parse(f.read())

        # Fields with '-' should be NaN or empty string
        # Check x-forwarded-for which has '-' in sample
        assert pd.isna(df["x-forwarded-for"].iloc[0]) or df["x-forwarded-for"].iloc[0] == ""


class TestV2FieldPresence:
    """Tests for v2-specific field presence."""

    def test_json_parser_includes_v2_fields(self):
        """Test that JSON parser includes v2 fields."""
        parser = JSONParser()
        sample_path = TEST_DATA_DIR / "sample_v2.json"
        with open(sample_path, "rb") as f:
            df = parser.parse(f.read())

        v2_fields = [
            "timestamp(ms)",
            "origin-fbl",
            "origin-lbl",
            "asn",
            "c-country",
            "cache-behavior-path-pattern",
        ]

        for field in v2_fields:
            assert field in df.columns, f"v2 field '{field}' missing"

    def test_csv_parser_includes_v2_fields(self):
        """Test that CSV parser includes v2 fields."""
        parser = PlainParser()
        sample_path = TEST_DATA_DIR / "sample_v2.csv"
        with open(sample_path, "rb") as f:
            df = parser.parse(f.read())

        v2_fields = [
            "timestamp(ms)",
            "origin-fbl",
            "origin-lbl",
            "asn",
            "c-country",
            "cache-behavior-path-pattern",
        ]

        for field in v2_fields:
            assert field in df.columns, f"v2 field '{field}' missing"

    def test_w3c_parser_no_v2_fields(self):
        """Test that W3C (v1) parser doesn't have v2 fields."""
        parser = W3CParser()
        sample_path = TEST_DATA_DIR / "sample_v1.gz"
        with open(sample_path, "rb") as f:
            df = parser.parse(f.read())

        v2_fields = ["timestamp(ms)", "origin-fbl", "asn", "c-country"]

        for field in v2_fields:
            assert field not in df.columns, f"v2 field '{field}' should not be in v1 logs"
