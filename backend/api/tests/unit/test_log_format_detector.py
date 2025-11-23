"""Unit tests for LogFormatDetector.

Tests the automatic detection of CloudFront log formats and versions
based on file paths and content.
"""

import pytest

from api.utils.log_format_detector import LogFormat, LogFormatDetector, LogVersion


class TestLogFormatDetector:
    """Tests for log format and version detection."""

    def setup_method(self):
        """Setup test detector."""
        self.detector = LogFormatDetector()

    # ========== Path-based Version Detection ==========

    def test_detect_v1_from_path(self):
        """Test detecting v1 from traditional file path."""
        paths = [
            "logs/E123ABC.2025-11-23-12.abc123.gz",
            "prefix/DISTRIBUTION123.2025-01-01-00.xyz.gz",
            "/path/to/E3K6JPV795PQRV.2025-11-13-08.abcdef123.gz",
        ]

        for path in paths:
            fmt, ver = self.detector.detect_from_path(path)
            assert ver == LogVersion.V1, f"Path '{path}' should be detected as v1"

    def test_detect_v2_from_hive_partition_path(self):
        """Test detecting v2 from Hive-style partition path."""
        paths = [
            "logs/year=2025/month=11/day=23/hour=12/log.json",
            "prefix/year=2025/month=01/day=01/hour=00/data.parquet",
            "/s3/bucket/year=2025/month=12/day=31/hour=23/file.csv",
        ]

        for path in paths:
            fmt, ver = self.detector.detect_from_path(path)
            assert ver == LogVersion.V2, f"Path '{path}' should be detected as v2"

    def test_detect_v2_from_simple_partition_path(self):
        """Test detecting v2 from simple partition path."""
        paths = [
            "logs/2025/11/23/12/log.json",
            "prefix/2025/01/01/00/data.parquet",
            "/s3/bucket/2025/12/31/23/file.csv.gz",
        ]

        for path in paths:
            fmt, ver = self.detector.detect_from_path(path)
            assert ver == LogVersion.V2, f"Path '{path}' should be detected as v2"

    def test_is_v2_partitioned_path(self):
        """Test v2 partition path detection."""
        # v2 paths (must include hour for full pattern match)
        assert self.detector.is_v2_partitioned_path("year=2025/month=11/day=23/hour=12")
        assert self.detector.is_v2_partitioned_path("2025/11/23/12")
        assert self.detector.is_v2_partitioned_path("distributionid=E123/year=2025/month=11")

        # v1 paths
        assert not self.detector.is_v2_partitioned_path("E123.2025-11-23.gz")
        assert not self.detector.is_v2_partitioned_path("logs/random/path.json")

    # ========== Extension-based Format Detection ==========

    def test_detect_w3c_from_extension(self):
        """Test detecting W3C format from .gz extension."""
        paths = [
            "log.gz",
            "E123.2025-11-23.gz",
            "/path/to/file.GZ",
        ]

        for path in paths:
            fmt, ver = self.detector.detect_from_path(path)
            assert fmt == LogFormat.W3C, f"Path '{path}' should be W3C format"

    def test_detect_json_from_extension(self):
        """Test detecting JSON format from extension."""
        paths = [
            "log.json",
            "data.json.gz",
            "/path/to/file.JSON",
        ]

        for path in paths:
            fmt, ver = self.detector.detect_from_path(path)
            assert fmt == LogFormat.JSON, f"Path '{path}' should be JSON format"

    def test_detect_parquet_from_extension(self):
        """Test detecting Parquet format from extension."""
        paths = [
            "log.parquet",
            "data.PARQUET",
            "/path/to/file.parquet",
        ]

        for path in paths:
            fmt, ver = self.detector.detect_from_path(path)
            assert fmt == LogFormat.PARQUET, f"Path '{path}' should be Parquet format"

    def test_detect_csv_from_extension(self):
        """Test detecting CSV format from extension."""
        paths = [
            "log.csv",
            "data.csv.gz",
            "/path/to/file.CSV",
        ]

        for path in paths:
            fmt, ver = self.detector.detect_from_path(path)
            assert fmt == LogFormat.PLAIN, f"Path '{path}' should be Plain/CSV format"

    # ========== Content-based Format Detection ==========

    def test_detect_json_from_content(self):
        """Test detecting JSON from content sample."""
        json_content = b'{"date":"2025-11-23","time":"12:00:00"}'
        fmt, ver = self.detector.detect("unknown.txt", json_content)
        assert fmt == LogFormat.JSON

    def test_detect_w3c_from_content(self):
        """Test detecting W3C from content sample."""
        import gzip

        w3c_content = b"#Version: 1.0\n#Fields: date time\n"
        gzipped = gzip.compress(w3c_content)
        fmt, ver = self.detector.detect("unknown.dat", gzipped)
        assert fmt == LogFormat.W3C

    def test_detect_parquet_from_content(self):
        """Test detecting Parquet from magic bytes."""
        parquet_magic = b"PAR1" + b"\x00" * 100
        fmt, ver = self.detector.detect("unknown.dat", parquet_magic)
        assert fmt == LogFormat.PARQUET

    def test_detect_csv_from_content(self):
        """Test detecting CSV from content sample."""
        csv_content = b"date,time,c-ip\n2025-11-23,12:00:00,1.2.3.4"
        fmt, ver = self.detector.detect("unknown.txt", csv_content)
        assert fmt == LogFormat.PLAIN

    # ========== Parser Class Name Mapping ==========

    def test_get_parser_class_name(self):
        """Test getting parser class names."""
        assert self.detector.get_parser_class_name(LogFormat.W3C) == "W3CParser"
        assert self.detector.get_parser_class_name(LogFormat.JSON) == "JSONParser"
        assert self.detector.get_parser_class_name(LogFormat.PARQUET) == "ParquetParser"
        assert self.detector.get_parser_class_name(LogFormat.PLAIN) == "PlainParser"

    # ========== Edge Cases ==========

    def test_detect_empty_content(self):
        """Test handling empty content."""
        fmt, ver = self.detector.detect("file.txt", b"")
        # Should fall back to extension-based detection
        assert fmt == LogFormat.UNKNOWN

    def test_detect_unknown_extension(self):
        """Test handling unknown extension."""
        fmt, ver = self.detector.detect("file.unknown", None)
        assert fmt == LogFormat.UNKNOWN

    def test_detect_conflicting_signals(self):
        """Test when path suggests v1 but extension suggests JSON (v2)."""
        # .json extension should override path pattern
        path = "E123.2025-11-23.json"
        fmt, ver = self.detector.detect_from_path(path)
        assert fmt == LogFormat.JSON  # Extension wins
        assert ver == LogVersion.V1  # Path pattern suggests v1

    # ========== Combined Detection ==========

    def test_full_detection_v1_w3c(self):
        """Test full detection for v1 W3C format."""
        path = "logs/E123.2025-11-23-12.abc.gz"
        fmt, ver = self.detector.detect_from_path(path)

        assert fmt == LogFormat.W3C
        assert ver == LogVersion.V1

    def test_full_detection_v2_json(self):
        """Test full detection for v2 JSON format."""
        path = "logs/year=2025/month=11/day=23/hour=12/file.json"
        fmt, ver = self.detector.detect_from_path(path)

        assert fmt == LogFormat.JSON
        assert ver == LogVersion.V2

    def test_full_detection_v2_parquet(self):
        """Test full detection for v2 Parquet format."""
        path = "logs/2025/11/23/12/data.parquet"
        fmt, ver = self.detector.detect_from_path(path)

        assert fmt == LogFormat.PARQUET
        assert ver == LogVersion.V2
