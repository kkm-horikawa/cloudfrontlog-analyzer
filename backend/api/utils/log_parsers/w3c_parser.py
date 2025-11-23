"""CloudFront W3C形式ログパーサー。

このモジュールは、CloudFront Standard logs (v1) のW3C形式
（タブ区切りgzip圧縮）ログを解析します。

フォーマット:
    - タブ区切り (.tsv)
    - gzip圧縮 (.gz)
    - "#"で始まるヘッダー行
    - "-" が欠損値

Example:
    >>> parser = W3CParser()
    >>> with open("log.gz", "rb") as f:
    ...     content = f.read()
    >>> df = parser.parse(content)
    >>> df.columns
    ['date', 'time', 'x-edge-location', 'c-ip', ...]
"""

import gzip
import io
from typing import Optional

import pandas as pd

from api.utils.cloudfront_constants import CLOUDFRONT_LOG_COLUMNS

from .base import AbstractLogParser


class W3CParser(AbstractLogParser):
    """CloudFront W3C形式ログパーサー。

    CloudFront Standard logs (v1) のタブ区切りgzip形式を解析します。

    Attributes:
        format_type (str): 'w3c'
        version (str): 'v1'

    Example:
        >>> parser = W3CParser()
        >>> df = parser.parse(gzip_content)
        >>> 'c-ip' in df.columns
        True
    """

    def __init__(self):
        """W3Cパーサーを初期化します。"""
        super().__init__(format_type="w3c", version="v1")

    def parse(self, content: bytes) -> pd.DataFrame:
        """W3C形式のログコンテンツを解析します。

        Args:
            content (bytes): gzip圧縮されたW3C形式ログデータ

        Returns:
            pd.DataFrame: 解析されたログデータ
                カラム: CLOUDFRONT_LOG_COLUMNS + 'datetime'

        Raises:
            ValueError: gzip解凍に失敗した場合
            Exception: ログ解析に失敗した場合

        Example:
            >>> parser = W3CParser()
            >>> df = parser.parse(content)
            >>> df.empty
            False
        """
        try:
            # gzipコンテンツを解凍
            with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz_file:
                decompressed_content = gz_file.read().decode("utf-8")

            # タブ区切りCSVとして読み込み
            df = pd.read_csv(
                io.StringIO(decompressed_content),
                sep="\t",
                comment="#",  # ヘッダー行をスキップ
                names=CLOUDFRONT_LOG_COLUMNS,
                na_values="-",  # "-" を欠損値として扱う
                dtype={
                    "date": str,
                    "time": str,
                    "x-edge-location": str,
                    "c-ip": str,
                    "cs-method": str,
                    "cs-host": str,
                    "cs-uri-stem": str,
                    "cs-referer": str,
                    "cs-user-agent": str,
                    "cs-uri-query": str,
                },
                on_bad_lines="skip",  # 不正な行をスキップ
                engine="python",
            )

            # 正規化処理
            df = self.normalize_dataframe(df)

            # User-AgentのURLデコード
            if "cs-user-agent" in df.columns:
                df["cs-user-agent"] = df["cs-user-agent"].str.replace(
                    "%20", " ", regex=False
                )

            return df

        except gzip.BadGzipFile as e:
            raise ValueError(f"Invalid gzip file: {str(e)}")
        except Exception as e:
            print(f"Error parsing W3C log: {str(e)}")
            # 空のDataFrameを返す
            return pd.DataFrame(columns=CLOUDFRONT_LOG_COLUMNS + ["datetime"])

    def supports_format(
        self, file_extension: str, content_sample: Optional[bytes] = None
    ) -> bool:
        """W3C形式をサポートするか判定します。

        Args:
            file_extension (str): ファイル拡張子
            content_sample (Optional[bytes]): ファイル内容のサンプル

        Returns:
            bool: .gz拡張子または #Version: で始まる場合True

        Example:
            >>> parser = W3CParser()
            >>> parser.supports_format(".gz")
            True
        """
        # .gz拡張子
        if file_extension.lower() == ".gz":
            return True

        # 内容サンプルがある場合、#Version: をチェック
        if content_sample:
            try:
                # gzip解凍を試行
                with gzip.GzipFile(fileobj=io.BytesIO(content_sample[:1000])) as gz:
                    first_line = gz.read(100).decode("utf-8", errors="ignore")
                    if first_line.startswith("#Version:"):
                        return True
            except Exception:
                pass

        return False
