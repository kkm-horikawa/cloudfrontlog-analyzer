"""CloudFront Parquet形式ログパーサー。

このモジュールは、CloudFront Standard logs (v2) のParquet形式ログを解析します。

フォーマット:
    - Parquet形式 (.parquet)
    - 列指向フォーマット
    - 最高の圧縮率と読み込み速度

Example:
    >>> parser = ParquetParser()
    >>> with open("log.parquet", "rb") as f:
    ...     content = f.read()
    >>> df = parser.parse(content)
    >>> df.columns
    ['date', 'time', 'c-ip', 'timestamp(ms)', ...]
"""

import io
from typing import Optional

import pandas as pd

from .base import AbstractLogParser


class ParquetParser(AbstractLogParser):
    """CloudFront Parquet形式ログパーサー。

    CloudFront Standard logs (v2) のParquet形式を解析します。
    Parquetは列指向フォーマットで、高速な読み込みと高い圧縮率を実現します。

    Attributes:
        format_type (str): 'parquet'
        version (str): 'v2'

    Example:
        >>> parser = ParquetParser()
        >>> df = parser.parse(parquet_content)
        >>> df.empty
        False
    """

    def __init__(self):
        """Parquetパーサーを初期化します。"""
        super().__init__(format_type="parquet", version="v2")

    def parse(self, content: bytes) -> pd.DataFrame:
        """Parquet形式のログコンテンツを解析します。

        Args:
            content (bytes): Parquet形式ログデータ

        Returns:
            pd.DataFrame: 解析されたログデータ

        Raises:
            ValueError: Parquet解析に失敗した場合

        Example:
            >>> parser = ParquetParser()
            >>> df = parser.parse(content)
            >>> isinstance(df, pd.DataFrame)
            True
        """
        try:
            # BytesIOでラップしてpd.read_parquetで読み込み
            buffer = io.BytesIO(content)
            df = pd.read_parquet(buffer, engine="pyarrow")

            # 正規化処理
            df = self.normalize_dataframe(df)

            return df

        except Exception as e:
            print(f"Error parsing Parquet log: {str(e)}")
            raise ValueError(f"Invalid Parquet format: {str(e)}")

    def supports_format(
        self, file_extension: str, content_sample: Optional[bytes] = None
    ) -> bool:
        """Parquet形式をサポートするか判定します。

        Args:
            file_extension (str): ファイル拡張子
            content_sample (Optional[bytes]): ファイル内容のサンプル

        Returns:
            bool: .parquet拡張子またはPAR1マジックバイトの場合True

        Example:
            >>> parser = ParquetParser()
            >>> parser.supports_format(".parquet")
            True
            >>> parser.supports_format(".parquet", b'PAR1...')
            True
        """
        ext_lower = file_extension.lower()

        # 拡張子で判定
        if ext_lower == ".parquet":
            return True

        # 内容サンプルで判定（Parquetマジックバイト: PAR1）
        if content_sample and len(content_sample) >= 4:
            if content_sample[:4] == b"PAR1":
                return True

        return False
