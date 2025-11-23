"""CloudFrontログパーサーの基底クラス。

このモジュールは、すべてのログパーサーが継承すべき抽象基底クラスを定義します。
統一的なインターフェースにより、異なるフォーマットのログを同じ方法で処理できます。
"""

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Optional

import pandas as pd

from api.utils.cloudfront_constants import FIELD_NAME_MAPPING


class AbstractLogParser(ABC):
    """CloudFrontログパーサーの抽象基底クラス。

    すべてのログフォーマットパーサーはこのクラスを継承し、
    parse()メソッドを実装する必要があります。

    Attributes:
        format_type (str): ログフォーマットの種類
        version (str): ログフォーマットのバージョン (v1/v2)

    Example:
        >>> class CustomParser(AbstractLogParser):
        ...     def parse(self, content: bytes) -> pd.DataFrame:
        ...         # カスタムパース処理
        ...         return df
    """

    def __init__(self, format_type: str, version: str = "v1"):
        """パーサーを初期化します。

        Args:
            format_type (str): ログフォーマットの種類 (w3c, json, parquet, plain)
            version (str): ログフォーマットのバージョン (v1/v2)
        """
        self.format_type = format_type
        self.version = version

    @abstractmethod
    def parse(self, content: bytes) -> pd.DataFrame:
        """ログコンテンツを解析してDataFrameを返します。

        Args:
            content (bytes): ログファイルの生データ

        Returns:
            pd.DataFrame: 解析されたログデータ
                必須カラム: datetime, c-ip, cs-uri-stem など

        Raises:
            ValueError: ログフォーマットが不正な場合
            Exception: 解析に失敗した場合
        """
        pass

    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrameを標準形式に正規化します。

        - datetime列の作成（UTCタイムゾーン付き）
        - 欠損値の処理
        - データ型の変換

        Args:
            df (pd.DataFrame): 生のDataFrame

        Returns:
            pd.DataFrame: 正規化されたDataFrame
        """
        if df.empty:
            return df

        # DataFrameのコピーを作成（SettingWithCopyWarning回避）
        df = df.copy()

        # datetime列の作成・正規化
        df = self._normalize_datetime(df)

        # 欠損値の処理
        df = self._handle_missing_values(df)

        return df

    def _normalize_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """datetime列を正規化します。

        v1形式: date + time 列から datetime を作成
        v2形式: timestamp(ms) または timestamp から datetime を作成

        Args:
            df (pd.DataFrame): 入力DataFrame

        Returns:
            pd.DataFrame: datetime列が正規化されたDataFrame
        """
        if "datetime" in df.columns and df["datetime"].dtype == "datetime64[ns, UTC]":
            # 既にUTCのdatetime列が存在する場合
            return df

        # v2: timestamp(ms) から datetime を作成
        if "timestamp(ms)" in df.columns:
            df["datetime"] = pd.to_datetime(
                df["timestamp(ms)"], unit="ms", utc=True, errors="coerce"
            )
        # v2: timestamp から datetime を作成
        elif "timestamp" in df.columns:
            df["datetime"] = pd.to_datetime(
                df["timestamp"], unit="s", utc=True, errors="coerce"
            )
        # v1: date + time から datetime を作成
        elif "date" in df.columns and "time" in df.columns:
            # date/time列の欠損値フィルタ
            df = df[df["date"].notna() & df["time"].notna()]
            df["datetime"] = pd.to_datetime(
                df["date"] + " " + df["time"],
                format="%Y-%m-%d %H:%M:%S",
                utc=True,
                errors="coerce",
            )

        # datetime解析失敗行を削除
        if "datetime" in df.columns:
            df = df[df["datetime"].notna()]

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """欠損値を適切に処理します。

        CloudFrontログでは "-" が欠損値として使用されます。

        Args:
            df (pd.DataFrame): 入力DataFrame

        Returns:
            pd.DataFrame: 欠損値が処理されたDataFrame
        """
        # "-" を NaN に変換（pd.read_csv の na_values で処理済みの場合が多い）
        # 念のため追加処理
        str_columns = df.select_dtypes(include=["object"]).columns
        for col in str_columns:
            df[col] = df[col].replace("-", pd.NA)

        return df

    def convert_to_api_format(
        self, df: pd.DataFrame, include_v2_fields: bool = False
    ) -> pd.DataFrame:
        """DataFrameをAPI応答形式に変換します。

        - フィールド名をキャメルケースに変換
        - JSTタイムゾーンに変換
        - 数値型の変換

        Args:
            df (pd.DataFrame): 入力DataFrame
            include_v2_fields (bool): v2フィールドを含めるか

        Returns:
            pd.DataFrame: API形式のDataFrame
        """
        if df.empty:
            return df

        # コピーを作成
        df = df.copy()

        # datetimeをUTCからJST（UTC+9）に変換
        if "datetime" in df.columns:
            jst = timezone(timedelta(hours=9))
            df["datetime_jst"] = df["datetime"].dt.tz_convert(jst)
            # dateとtime列をJSTに更新
            df["date"] = df["datetime_jst"].dt.strftime("%Y-%m-%d")
            df["time"] = df["datetime_jst"].dt.strftime("%H:%M:%S")

        # 列をAPI形式にリネーム
        rename_dict = FIELD_NAME_MAPPING.copy()

        # v2フィールドのマッピングを追加
        if include_v2_fields:
            from api.utils.cloudfront_constants import V2_FIELD_NAME_MAPPING

            rename_dict.update(V2_FIELD_NAME_MAPPING)

        df_renamed = df.rename(columns=rename_dict)

        # NaN値を空文字列に変換
        df_renamed = df_renamed.fillna("")

        # 数値列を変換
        numeric_cols = ["bytes", "statusCode", "bytes_sent", "timeTaken"]
        for col in numeric_cols:
            if col in df_renamed.columns:
                df_renamed[col] = df_renamed[col].fillna(0)
                if col == "timeTaken":
                    df_renamed[col] = df_renamed[col].astype(float)
                else:
                    df_renamed[col] = df_renamed[col].astype(int)

        return df_renamed

    def supports_format(self, file_extension: str, content_sample: Optional[bytes] = None) -> bool:
        """このパーサーが指定されたフォーマットをサポートするか判定します。

        Args:
            file_extension (str): ファイル拡張子 (.gz, .json, .parquet等)
            content_sample (Optional[bytes]): ファイル内容のサンプル（先頭数バイト）

        Returns:
            bool: サポートする場合True
        """
        # サブクラスでオーバーライドして実装
        return False
