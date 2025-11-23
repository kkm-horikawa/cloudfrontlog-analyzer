"""CloudFrontログフォーマット検出ユーティリティ。

このモジュールは、ログファイルのパスや内容からフォーマットとバージョンを
自動検出する機能を提供します。

対応フォーマット:
    - W3C (v1): タブ区切りgzip形式
    - JSON (v2): JSON/JSON.gz形式
    - Parquet (v2): Parquet形式
    - Plain (v2): CSV/CSV.gz形式

Example:
    >>> detector = LogFormatDetector()
    >>> format_type, version = detector.detect_from_path("logs/dist.2025-11-23.gz")
    >>> format_type
    'w3c'
    >>> version
    'v1'
"""

import re
from enum import Enum
from typing import Optional
from typing import Tuple


class LogFormat(Enum):
    """ログフォーマットの種類。"""

    W3C = "w3c"
    JSON = "json"
    PARQUET = "parquet"
    PLAIN = "plain"
    UNKNOWN = "unknown"


class LogVersion(Enum):
    """ログバージョン。"""

    V1 = "v1"
    V2 = "v2"
    UNKNOWN = "unknown"


class LogFormatDetector:
    """CloudFrontログのフォーマットとバージョンを検出するクラス。

    ファイルパス、拡張子、内容のサンプルから、ログフォーマットを判定します。

    Example:
        >>> detector = LogFormatDetector()
        >>> fmt, ver = detector.detect("path/to/log.json")
        >>> fmt
        <LogFormat.JSON: 'json'>
        >>> ver
        <LogVersion.V2: 'v2'>
    """

    # v1パスパターン: prefix/DISTRIBUTION_ID.YYYY-MM-DD-HH.xxx.gz
    V1_PATH_PATTERN = re.compile(
        r"[A-Z0-9]+\.\d{4}-\d{2}-\d{2}-\d{2}\.[a-zA-Z0-9]+\.gz$"
    )

    # v2パーティションパターン
    V2_PARTITION_PATTERNS = [
        # year=2025/month=11/day=23/hour=12 (Hive形式)
        re.compile(r"year=\d{4}/month=\d{2}/day=\d{2}/hour=\d{2}"),
        # 2025/11/23/12 (シンプル形式)
        re.compile(r"\d{4}/\d{2}/\d{2}/\d{2}"),
        # distributionId=XXX/year=2025/... (Distribution ID付き)
        re.compile(r"distributionid=[A-Z0-9]+/year=\d{4}"),
    ]

    def detect(
        self, file_path: str, content_sample: Optional[bytes] = None
    ) -> Tuple[LogFormat, LogVersion]:
        """ファイルパスと内容からログフォーマットとバージョンを検出します。

        Args:
            file_path (str): ログファイルのパス
            content_sample (Optional[bytes]): ファイル内容のサンプル（先頭1KB程度）

        Returns:
            Tuple[LogFormat, LogVersion]: (フォーマット, バージョン)

        Example:
            >>> detector = LogFormatDetector()
            >>> fmt, ver = detector.detect("logs/E123.2025-11-23-12.abc.gz")
            >>> fmt == LogFormat.W3C and ver == LogVersion.V1
            True
        """
        # パスからバージョンを推定
        version = self._detect_version_from_path(file_path)

        # 拡張子からフォーマットを検出
        format_type = self._detect_format_from_extension(file_path)

        # 内容サンプルがある場合、より正確に判定
        if content_sample:
            detected_format = self._detect_format_from_content(content_sample)
            if detected_format != LogFormat.UNKNOWN:
                format_type = detected_format

        return format_type, version

    def detect_from_path(self, file_path: str) -> Tuple[LogFormat, LogVersion]:
        """ファイルパスのみからフォーマットとバージョンを検出します。

        Args:
            file_path (str): ログファイルのパス

        Returns:
            Tuple[LogFormat, LogVersion]: (フォーマット, バージョン)
        """
        return self.detect(file_path, None)

    def is_v2_partitioned_path(self, path: str) -> bool:
        """パスがv2のパーティション構造を持つか判定します。

        Args:
            path (str): S3パスまたはファイルパス

        Returns:
            bool: v2パーティション構造の場合True

        Example:
            >>> detector = LogFormatDetector()
            >>> detector.is_v2_partitioned_path("logs/year=2025/month=11/day=23")
            True
            >>> detector.is_v2_partitioned_path("logs/E123.2025-11-23.gz")
            False
        """
        for pattern in self.V2_PARTITION_PATTERNS:
            if pattern.search(path):
                return True
        return False

    def _detect_version_from_path(self, file_path: str) -> LogVersion:
        """ファイルパスからバージョンを検出します。

        Args:
            file_path (str): ログファイルのパス

        Returns:
            LogVersion: 検出されたバージョン
        """
        # v2パーティション構造の場合
        if self.is_v2_partitioned_path(file_path):
            return LogVersion.V2

        # v1パターンに一致する場合
        if self.V1_PATH_PATTERN.search(file_path):
            return LogVersion.V1

        # デフォルトではv1と判定（後方互換性）
        return LogVersion.V1

    def _detect_format_from_extension(self, file_path: str) -> LogFormat:
        """ファイル拡張子からフォーマットを検出します。

        Args:
            file_path (str): ログファイルのパス

        Returns:
            LogFormat: 検出されたフォーマット
        """
        path_lower = file_path.lower()

        # Parquet
        if path_lower.endswith(".parquet"):
            return LogFormat.PARQUET

        # JSON (.json or .json.gz)
        if path_lower.endswith(".json") or path_lower.endswith(".json.gz"):
            return LogFormat.JSON

        # Plain/CSV (.csv or .csv.gz)
        if path_lower.endswith(".csv") or path_lower.endswith(".csv.gz"):
            return LogFormat.PLAIN

        # W3C (.gz without .json or .csv prefix)
        if path_lower.endswith(".gz"):
            # .json.gz や .csv.gz でない場合はW3C
            if not (path_lower.endswith(".json.gz") or path_lower.endswith(".csv.gz")):
                return LogFormat.W3C

        return LogFormat.UNKNOWN

    def _detect_format_from_content(self, content_sample: bytes) -> LogFormat:
        """ファイル内容のサンプルからフォーマットを検出します。

        Args:
            content_sample (bytes): ファイル内容の先頭サンプル

        Returns:
            LogFormat: 検出されたフォーマット
        """
        if not content_sample or len(content_sample) == 0:
            return LogFormat.UNKNOWN

        # Parquet magic bytes (PAR1)
        if content_sample[:4] == b"PAR1":
            return LogFormat.PARQUET

        # JSONの検出（先頭が { または [）
        try:
            # gzipかもしれないのでデコード試行
            import gzip

            try:
                decompressed = gzip.decompress(content_sample)
                content_to_check = decompressed
            except Exception:
                content_to_check = content_sample

            # UTF-8デコード
            text_sample = content_to_check[:1000].decode("utf-8", errors="ignore").strip()

            # JSON判定
            if text_sample.startswith("{") or text_sample.startswith("["):
                return LogFormat.JSON

            # W3C判定（#Version: で始まる）
            if text_sample.startswith("#Version:"):
                return LogFormat.W3C

            # Plain/CSV判定（カンマ区切り）
            # 簡易的に最初の行にカンマが含まれているかチェック
            first_line = text_sample.split("\n")[0] if "\n" in text_sample else text_sample
            if "," in first_line and not text_sample.startswith("#"):
                return LogFormat.PLAIN

        except Exception:
            pass

        return LogFormat.UNKNOWN

    def get_parser_class_name(self, format_type: LogFormat) -> str:
        """フォーマットに対応するパーサークラス名を取得します。

        Args:
            format_type (LogFormat): ログフォーマット

        Returns:
            str: パーサークラス名

        Example:
            >>> detector = LogFormatDetector()
            >>> detector.get_parser_class_name(LogFormat.JSON)
            'JSONParser'
        """
        parser_map = {
            LogFormat.W3C: "W3CParser",
            LogFormat.JSON: "JSONParser",
            LogFormat.PARQUET: "ParquetParser",
            LogFormat.PLAIN: "PlainParser",
        }
        return parser_map.get(format_type, "W3CParser")
