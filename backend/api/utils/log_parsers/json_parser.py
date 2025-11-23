"""CloudFront JSON形式ログパーサー。

このモジュールは、CloudFront Standard logs (v2) のJSON形式ログを解析します。

フォーマット:
    - JSON形式 (.json)
    - gzip圧縮も対応 (.json.gz)
    - 1行1レコード (JSON Lines) または 配列形式

Example:
    >>> parser = JSONParser()
    >>> with open("log.json", "rb") as f:
    ...     content = f.read()
    >>> df = parser.parse(content)
    >>> df.columns
    ['date', 'time', 'c-ip', 'timestamp(ms)', ...]
"""

import gzip
import io
import json
from typing import Optional

import pandas as pd

from .base import AbstractLogParser


class JSONParser(AbstractLogParser):
    """CloudFront JSON形式ログパーサー。

    CloudFront Standard logs (v2) のJSON形式を解析します。
    JSON Lines形式（1行1レコード）と配列形式の両方に対応します。

    Attributes:
        format_type (str): 'json'
        version (str): 'v2'

    Example:
        >>> parser = JSONParser()
        >>> df = parser.parse(json_content)
        >>> 'timestamp(ms)' in df.columns
        True
    """

    def __init__(self):
        """JSONパーサーを初期化します。"""
        super().__init__(format_type="json", version="v2")

    def parse(self, content: bytes) -> pd.DataFrame:
        """JSON形式のログコンテンツを解析します。

        Args:
            content (bytes): JSON形式ログデータ（gzip圧縮可）

        Returns:
            pd.DataFrame: 解析されたログデータ

        Raises:
            ValueError: JSON解析に失敗した場合

        Example:
            >>> parser = JSONParser()
            >>> content = b'{"date":"2025-11-23","c-ip":"1.2.3.4"}'
            >>> df = parser.parse(content)
            >>> df.empty
            False
        """
        try:
            # gzip圧縮されているか判定・解凍
            decompressed_content = self._decompress_if_needed(content)

            # JSONとして解析
            df = self._parse_json(decompressed_content)

            # 正規化処理
            df = self.normalize_dataframe(df)

            return df

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            print(f"Error parsing JSON log: {str(e)}")
            return pd.DataFrame()

    def _decompress_if_needed(self, content: bytes) -> str:
        """必要に応じてgzip解凍します。

        Args:
            content (bytes): 圧縮または非圧縮のコンテンツ

        Returns:
            str: UTF-8デコードされた文字列

        Raises:
            ValueError: デコードに失敗した場合
        """
        try:
            # gzip圧縮されているか試行
            with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
                return gz.read().decode("utf-8")
        except (gzip.BadGzipFile, OSError):
            # gzip圧縮されていない場合、そのままデコード
            return content.decode("utf-8")

    def _parse_json(self, json_str: str) -> pd.DataFrame:
        """JSON文字列をDataFrameに変換します。

        JSON Lines形式（1行1レコード）と配列形式の両方に対応します。

        Args:
            json_str (str): JSON文字列

        Returns:
            pd.DataFrame: 解析されたDataFrame

        Raises:
            json.JSONDecodeError: JSON解析に失敗した場合
        """
        json_str = json_str.strip()

        # 配列形式の場合 (e.g., [{"...": "..."}, {...}])
        if json_str.startswith("["):
            data = json.loads(json_str)
            return pd.DataFrame(data)

        # JSON Lines形式の場合 (1行1レコード)
        # e.g.,
        # {"date": "2025-11-23", ...}
        # {"date": "2025-11-23", ...}
        lines = json_str.strip().split("\n")
        records = []
        for line in lines:
            line = line.strip()
            if line:  # 空行をスキップ
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    # 不正な行はスキップ
                    print(f"Warning: Skipping invalid JSON line: {line[:100]}")
                    continue

        if not records:
            return pd.DataFrame()

        return pd.DataFrame(records)

    def supports_format(
        self, file_extension: str, content_sample: Optional[bytes] = None
    ) -> bool:
        """JSON形式をサポートするか判定します。

        Args:
            file_extension (str): ファイル拡張子
            content_sample (Optional[bytes]): ファイル内容のサンプル

        Returns:
            bool: .json または .json.gz拡張子、または先頭が{/[の場合True

        Example:
            >>> parser = JSONParser()
            >>> parser.supports_format(".json")
            True
            >>> parser.supports_format(".json.gz")
            True
        """
        ext_lower = file_extension.lower()

        # 拡張子で判定
        if ext_lower in [".json", ".json.gz"]:
            return True

        # 内容サンプルで判定
        if content_sample:
            try:
                text = self._decompress_if_needed(content_sample[:1000])
                text_stripped = text.strip()
                if text_stripped.startswith("{") or text_stripped.startswith("["):
                    return True
            except Exception:
                pass

        return False
