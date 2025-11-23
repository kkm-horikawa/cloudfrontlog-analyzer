"""CloudFront Plain/CSV形式ログパーサー。

このモジュールは、CloudFront Standard logs (v2) のPlain/CSV形式ログを解析します。

フォーマット:
    - CSV形式 (.csv)
    - gzip圧縮も対応 (.csv.gz)
    - カンマ区切り
    - ヘッダー行あり

Example:
    >>> parser = PlainParser()
    >>> with open("log.csv", "rb") as f:
    ...     content = f.read()
    >>> df = parser.parse(content)
    >>> df.columns
    ['date', 'time', 'c-ip', ...]
"""

import gzip
import io
from typing import Optional

import pandas as pd

from .base import AbstractLogParser


class PlainParser(AbstractLogParser):
    """CloudFront Plain/CSV形式ログパーサー。

    CloudFront Standard logs (v2) のPlain/CSV形式を解析します。
    カンマ区切りのシンプルなテキスト形式です。

    Attributes:
        format_type (str): 'plain'
        version (str): 'v2'

    Example:
        >>> parser = PlainParser()
        >>> df = parser.parse(csv_content)
        >>> df.empty
        False
    """

    def __init__(self):
        """Plainパーサーを初期化します。"""
        super().__init__(format_type="plain", version="v2")

    def parse(self, content: bytes) -> pd.DataFrame:
        """Plain/CSV形式のログコンテンツを解析します。

        Args:
            content (bytes): CSV形式ログデータ（gzip圧縮可）

        Returns:
            pd.DataFrame: 解析されたログデータ

        Raises:
            ValueError: CSV解析に失敗した場合

        Example:
            >>> parser = PlainParser()
            >>> content = b'date,time,c-ip\\n2025-11-23,12:00:00,1.2.3.4'
            >>> df = parser.parse(content)
            >>> df.empty
            False
        """
        try:
            # gzip圧縮されているか判定・解凍
            decompressed_content = self._decompress_if_needed(content)

            # CSVとして読み込み
            df = pd.read_csv(
                io.StringIO(decompressed_content),
                na_values="-",  # "-" を欠損値として扱う
                on_bad_lines="skip",  # 不正な行をスキップ
            )

            # 正規化処理
            df = self.normalize_dataframe(df)

            return df

        except Exception as e:
            print(f"Error parsing Plain/CSV log: {str(e)}")
            raise ValueError(f"Invalid CSV format: {str(e)}")

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

    def supports_format(
        self, file_extension: str, content_sample: Optional[bytes] = None
    ) -> bool:
        """Plain/CSV形式をサポートするか判定します。

        Args:
            file_extension (str): ファイル拡張子
            content_sample (Optional[bytes]): ファイル内容のサンプル

        Returns:
            bool: .csv または .csv.gz拡張子、またはカンマ区切りの場合True

        Example:
            >>> parser = PlainParser()
            >>> parser.supports_format(".csv")
            True
            >>> parser.supports_format(".csv.gz")
            True
        """
        ext_lower = file_extension.lower()

        # 拡張子で判定
        if ext_lower in [".csv", ".csv.gz"]:
            return True

        # 内容サンプルで判定（カンマ区切り）
        if content_sample:
            try:
                text = self._decompress_if_needed(content_sample[:1000])
                # 最初の行にカンマが含まれているかチェック
                first_line = text.split("\n")[0] if "\n" in text else text
                if "," in first_line and not text.strip().startswith("#"):
                    return True
            except Exception:
                pass

        return False
