"""CloudFrontログ操作のためのログサービスモジュール。

このモジュールは、S3に保存されたCloudFrontアクセスログの検索、解析、集約機能を提供します。
効率的なキャッシング戦略により、大量のログデータを高速に処理します。

主な機能:
- ログ検索（URL、IP、時刻範囲による）
- ログ集約（IP、User Agent、リファラー等でグループ化）
- Parquetキャッシュによる高速化
- 日次ログの統合処理

Example:
    >>> log_service = LogService(profile_name="production")
    >>> logs = log_service.list_raw_logs(
    ...     distribution_id="E1234567890ABC",
    ...     start_date=date(2024, 1, 1),
    ...     end_date=date(2024, 1, 1)
    ... )
    >>> logs['pagination']['total']
    15234
"""

import gzip
import io
import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Dict
from typing import List
from typing import Optional

import pandas as pd
from botocore.exceptions import ClientError

from api.utils.aws_base import AWSServiceBase
from api.utils.cloudfront_constants import CLOUDFRONT_LOG_COLUMNS
from api.utils.cloudfront_constants import FIELD_NAME_MAPPING


class LogService(AWSServiceBase):
    """CloudFrontログ操作のためのサービスクラス。

    S3に保存されたCloudFrontアクセスログの検索、解析、集約を行います。
    Parquetキャッシュと日次統合により高速な処理を実現します。

    Example:
        >>> service = LogService(profile_name="production")
        >>> logs = service.search_logs(
        ...     distribution_id="E1234567890ABC",
        ...     target_url="/api/users",
        ...     target_datetime=datetime.now()
        ... )
        >>> len(logs)
        23
    """

    def search_logs(
        self,
        distribution_id: str,
        target_url: str,
        target_datetime: datetime,
        time_window_minutes: int = 5,
    ) -> List[Dict]:
        """特定のURLと時刻でCloudFrontログを検索します。

        指定されたURLパスと時刻の前後の時間枠内でログエントリを検索します。
        時刻はUTCに変換されて処理されます。

        Args:
            distribution_id (str): CloudFront Distribution ID
                例: "E1234567890ABC"
            target_url (str): 検索対象のURLパス
                例: "/api/users", "/index.html"
            target_datetime (datetime): 対象の日時（JSTの場合はUTCに変換されます）
            time_window_minutes (int, optional): 検索時間枠（分単位）。デフォルトは5分。

        Returns:
            List[Dict]: 条件に一致するログエントリのリスト。
                各エントリには日時、IP、ステータスコード等が含まれます。

        Raises:
            ValueError: ログ設定が無効な場合

        Example:
            >>> service = LogService()
            >>> target_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            >>> logs = service.search_logs(
            ...     distribution_id="E1234567890ABC",
            ...     target_url="/api/users",
            ...     target_datetime=target_time,
            ...     time_window_minutes=10
            ... )
            >>> logs[0]['uriStem']
            '/api/users'
        """
        from api.endpoints.distributions.services import DistributionService

        distribution_service = DistributionService(self.profile_name)

        # ログバケット情報を取得
        log_info = distribution_service.get_log_bucket_info(distribution_id)
        if not log_info:
            raise ValueError(
                f"Logging is not enabled for distribution {distribution_id}"
            )

        bucket = log_info["bucket"]
        prefix = log_info["prefix"]

        # target_datetimeは既にUTCです（Djangoが自動的に変換します）
        # 検索ウィンドウを設定
        start_time = target_datetime - timedelta(minutes=time_window_minutes)
        end_time = target_datetime + timedelta(minutes=time_window_minutes)

        # 対象日のログファイルをリスト化
        log_files = self._list_log_files(
            bucket, prefix, distribution_id, start_time, end_time
        )

        # ログファイルを解析し、一致するエントリを検索
        matching_entries = []
        for log_file in log_files:
            entries = self._parse_log_file(
                bucket, log_file, target_url, start_time, end_time
            )
            matching_entries.extend(entries)

        # Sort by datetime
        matching_entries.sort(key=lambda x: (x["date"], x["time"]))

        return matching_entries

    def list_raw_logs(
        self,
        distribution_id: str,
        start_date: datetime,
        end_date: datetime,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        client_ip: Optional[str] = None,
        client_ips: Optional[List[str]] = None,
        uri_path: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        query_string: Optional[str] = None,
        page: int = 1,
        per_page: int = 10000,
        exclude_static_files: bool = False,
    ) -> Dict:
        """
        ページネーションとフィルタリング機能付きで生ログをリスト化

        Args:
            distribution_id: CloudFront ディストリビューションID
            start_date: 開始日 (dateオブジェクト)
            end_date: 終了日 (dateオブジェクト)
            start_time: オプションの開始時刻 HH:MM:SS形式 (JST)
            end_time: オプションの終了時刻 HH:MM:SS形式 (JST)
            client_ip: オプションのクライアントIPフィルタ (単一IP)
            client_ips: オプションのクライアントIPsフィルタ (複数IP)
            uri_path: オプションのURIパスフィルタ (部分一致)
            user_agent: オプションのUser Agentフィルタ (完全一致)
            referrer: オプションのreferrerフィルタ (部分一致)
            query_string: オプションのクエリ文字列フィルタ (部分一致)
            page: ページ番号 (1始まり)
            per_page: 1ページあたりのログ数
            exclude_static_files: 静的ファイル（js, css, 画像等）を除外するか

        Returns:
            ログ、ページネーション情報、合計数を含む辞書
        """
        from api.endpoints.distributions.services import DistributionService

        distribution_service = DistributionService(self.profile_name)
        log_bucket_info = distribution_service.get_log_bucket_info(distribution_id)
        if not log_bucket_info:
            raise ValueError(
                f"Logging is not enabled for distribution: {distribution_id}"
            )

        # 日付をタイムゾーン付きのdatetimeに変換
        # start_time/end_timeが提供された場合(JST)、UTCに変換
        jst = timezone(timedelta(hours=9))

        if start_time:
            # Parse time string (HH:MM:SS)
            time_parts = [int(p) for p in start_time.split(":")]
            start_datetime = (
                datetime.combine(
                    start_date,
                    datetime.min.time().replace(
                        hour=time_parts[0],
                        minute=time_parts[1] if len(time_parts) > 1 else 0,
                        second=time_parts[2] if len(time_parts) > 2 else 0,
                    ),
                )
                .replace(tzinfo=jst)
                .astimezone(timezone.utc)
            )
        else:
            start_datetime = datetime.combine(start_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )

        if end_time:
            # Parse time string (HH:MM:SS)
            time_parts = [int(p) for p in end_time.split(":")]
            end_datetime = (
                datetime.combine(
                    end_date,
                    datetime.min.time().replace(
                        hour=time_parts[0],
                        minute=time_parts[1] if len(time_parts) > 1 else 0,
                        second=time_parts[2] if len(time_parts) > 2 else 0,
                    ),
                )
                .replace(tzinfo=jst)
                .astimezone(timezone.utc)
            )
        else:
            end_datetime = datetime.combine(end_date, datetime.max.time()).replace(
                tzinfo=timezone.utc
            )

        # Get list of log files for the date range
        log_files = self._list_log_files(
            bucket=log_bucket_info["bucket"],
            prefix=log_bucket_info["prefix"],
            distribution_id=distribution_id,
            start_time=start_datetime,
            end_time=end_datetime,
        )

        # パフォーマンス向上のため日次統合キャッシュを使用してログを読み込み
        all_dfs = []

        # Group log files by date
        from collections import defaultdict

        files_by_date = defaultdict(list)
        for log_file_key in log_files:
            # ログファイル名から日付を抽出: prefix/E3K6JPV795PQRV.2025-11-13-XX.xxx.gz
            try:
                # '.'で分割して日付部分を見つける (YYYY-MM-DD-HH形式)
                parts = log_file_key.split(".")
                for part in parts:
                    # 日付パターン YYYY-MM-DD を探す
                    if len(part) >= 10 and part[4] == "-" and part[7] == "-":
                        date_str = part[:10]  # "2025-11-13"
                        file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        files_by_date[file_date].append(log_file_key)
                        break
                else:
                    # 期待される形式で日付が見つからない場合、フォールバック
                    df = self._load_log_as_dataframe(
                        log_bucket_info["bucket"], log_file_key
                    )
                    if not df.empty:
                        all_dfs.append(df)
            except (ValueError, IndexError) as e:
                # 解析が失敗した場合、個別ファイル読み込みにフォールバック
                print(f"⚠ Could not parse date from {log_file_key}: {e}")
                df = self._load_log_as_dataframe(
                    log_bucket_info["bucket"], log_file_key
                )
                if not df.empty:
                    all_dfs.append(df)

        # 各日付のログを読み込み（過去の日付には日次キャッシュを使用）
        today = datetime.now(timezone.utc).date()
        for file_date, date_log_files in files_by_date.items():
            is_today = file_date == today

            df = self._load_daily_logs(
                bucket=log_bucket_info["bucket"],
                distribution_id=distribution_id,
                target_date=file_date,
                log_files=date_log_files,
                is_current_day=is_today,
            )

            if not df.empty:
                all_dfs.append(df)

        if not all_dfs:
            return {
                "logs": [],
                "pagination": {
                    "page": page,
                    "perPage": per_page,
                    "total": 0,
                    "totalPages": 0,
                },
            }

        # Combine all DataFrames
        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Filter by time range
        combined_df = combined_df[
            (combined_df["datetime"] >= start_datetime)
            & (combined_df["datetime"] <= end_datetime)
        ]

        # フィルタを適用
        if client_ip:
            combined_df = combined_df[combined_df["c-ip"] == client_ip]
        elif client_ips:
            # 複数のIPでフィルタ
            combined_df = combined_df[combined_df["c-ip"].isin(client_ips)]

        if uri_path:
            combined_df = combined_df[
                combined_df["cs-uri-stem"].str.contains(uri_path, na=False)
            ]

        if user_agent:
            combined_df = combined_df[combined_df["cs-user-agent"] == user_agent]

        if referrer:
            combined_df = combined_df[
                combined_df["cs-referer"].str.contains(referrer, na=False)
            ]

        if query_string:
            combined_df = combined_df[
                combined_df["cs-uri-query"].str.contains(query_string, na=False)
            ]

        if exclude_static_files:
            from api.utils.cloudfront_constants import is_static_file

            combined_df = combined_df[~combined_df["cs-uri-stem"].apply(is_static_file)]

        # 日時で降順にソート（新しいものが先）
        combined_df = combined_df.sort_values("datetime", ascending=False)

        # ページネーションを計算
        total = len(combined_df)
        total_pages = (total + per_page - 1) // per_page  # 切り上げ除算
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        # ページデータを取得
        page_df = combined_df.iloc[start_idx:end_idx]

        # Convert to list of dictionaries
        logs = self._dataframe_to_dict_list(page_df)

        # Add mark information to logs
        from api.endpoints.log_marks.services import add_marks_to_logs

        logs = add_marks_to_logs(logs, distribution_id)

        return {
            "logs": logs,
            "pagination": {
                "page": page,
                "perPage": per_page,
                "total": total,
                "totalPages": total_pages,
            },
        }

    def _list_log_files(
        self,
        bucket: str,
        prefix: str,
        distribution_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[str]:
        """時間範囲内のCloudFrontログファイルをリスト化（v1/v2両対応）。

        Args:
            bucket (str): S3バケット名
            prefix (str): S3プレフィックス
            distribution_id (str): CloudFront Distribution ID
            start_time (datetime): 開始時刻（UTC）
            end_time (datetime): 終了時刻（UTC）

        Returns:
            List[str]: ログファイルのS3キーのリスト
        """
        from api.utils.s3_path_helper import detect_log_version_from_s3_structure

        # S3構造からログバージョンを検出
        log_version = detect_log_version_from_s3_structure(
            self.s3_client, bucket, prefix, distribution_id
        )

        if log_version == "v2":
            return self._list_log_files_v2(
                bucket, prefix, distribution_id, start_time, end_time
            )
        else:
            return self._list_log_files_v1(
                bucket, prefix, distribution_id, start_time, end_time
            )

    def _list_log_files_v1(
        self,
        bucket: str,
        prefix: str,
        distribution_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[str]:
        """v1形式のログファイルをリスト化（既存ロジック）。

        CloudFrontログファイルの命名規則: <prefix><distribution-id>.YYYY-MM-DD-HH.xxx.gz
        """
        log_files = []
        current_date = start_time.date()
        end_date = end_time.date()

        while current_date <= end_date:
            date_prefix = (
                f"{prefix}{distribution_id}.{current_date.strftime('%Y-%m-%d')}"
            )

            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=bucket, Prefix=date_prefix
                )

                if "Contents" in response:
                    for obj in response["Contents"]:
                        log_files.append(obj["Key"])
            except ClientError:
                pass  # 特定の日付にログがない場合でも続行

            current_date += timedelta(days=1)

        return log_files

    def _list_log_files_v2(
        self,
        bucket: str,
        prefix: str,
        distribution_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[str]:
        """v2形式のログファイルをリスト化（パーティション構造対応）。

        v2パーティション構造:
            - year=2025/month=11/day=23/hour=12/ (Hive形式)
            - 2025/11/23/12/ (シンプル形式)
        """
        from api.utils.s3_path_helper import generate_v2_partition_paths

        log_files = []

        # パーティション形式を推定（Hive形式とシンプル形式の両方を試行）
        partition_formats = [
            "year={yyyy}/month={MM}/day={dd}/hour={HH}",
            "{yyyy}/{MM}/{dd}/{HH}",
        ]

        for partition_format in partition_formats:
            # パーティションパスを生成
            partition_paths = generate_v2_partition_paths(
                prefix=prefix,
                start_date=start_time.date(),
                end_date=end_time.date(),
                start_hour=start_time.hour,
                end_hour=end_time.hour,
                partition_format=partition_format,
                distribution_id=distribution_id,
            )

            # 各パーティションパス配下のファイルをリスト
            for partition_path in partition_paths:
                try:
                    response = self.s3_client.list_objects_v2(
                        Bucket=bucket, Prefix=partition_path
                    )

                    if "Contents" in response:
                        for obj in response["Contents"]:
                            # ディレクトリでないものだけ追加
                            if not obj["Key"].endswith("/"):
                                log_files.append(obj["Key"])
                except ClientError:
                    # このパーティションにファイルがない場合はスキップ
                    continue

            # ファイルが見つかった場合は、このフォーマットを採用
            if log_files:
                break

        return log_files

    def _parse_log_file(
        self,
        bucket: str,
        log_file_key: str,
        target_url: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict]:
        """単一のCloudFrontログファイルを解析し、一致するエントリを抽出（DataFrameを使用）"""
        try:
            # DataFrameとして読み込み（Parquetキャッシュを使用）
            df = self._load_log_as_dataframe(bucket, log_file_key)

            if df.empty:
                return []

            # URLでフィルタ
            df_filtered = df[df["cs-uri-stem"].str.contains(target_url, na=False)]

            # Filter by time range
            start_utc = (
                start_time.astimezone(timezone.utc)
                if start_time.tzinfo
                else start_time.replace(tzinfo=timezone.utc)
            )
            end_utc = (
                end_time.astimezone(timezone.utc)
                if end_time.tzinfo
                else end_time.replace(tzinfo=timezone.utc)
            )

            df_filtered = df_filtered[
                (df_filtered["datetime"] >= start_utc)
                & (df_filtered["datetime"] <= end_utc)
            ]

            # Convert to list of dictionaries
            return self._dataframe_to_dict_list(df_filtered)

        except Exception as e:
            print(f"Error parsing log file {log_file_key}: {str(e)}")
            return []

    def _load_daily_logs(
        self,
        bucket: str,
        distribution_id: str,
        target_date,
        log_files: List[str],
        is_current_day: bool = False,
    ) -> pd.DataFrame:
        """
        特定の日のすべてのログを単一のDataFrameとして読み込み
        過去の日付には日次統合Parquetキャッシュを使用（効率性）
        当日には個別の時間単位ファイルを使用（鮮度）

        Args:
            bucket: S3バケット名
            distribution_id: CloudFront ディストリビューションID
            target_date: 対象日 (dateオブジェクト)
            log_files: この日付のログファイルキーのリスト
            is_current_day: 今日のデータの場合はTrue（統合しない）

        Returns:
            その日のすべてのログを含むDataFrame
        """
        # 日次キャッシュディレクトリとパス
        daily_cache_dir = os.path.join(self.CACHE_DIR, "daily")
        os.makedirs(daily_cache_dir, exist_ok=True)

        cache_filename = f"{distribution_id}_{target_date.strftime('%Y-%m-%d')}.parquet"
        daily_cache_path = os.path.join(daily_cache_dir, cache_filename)

        # 当日は常に個別ファイルを読み込み（データが更新される可能性があるため）
        if is_current_day:
            print(f"📅 Loading current day data (no consolidation): {target_date}")
            all_dfs = self._load_logs_parallel(bucket, log_files)
            return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

        # 過去の日付には日次統合キャッシュを使用
        if os.path.exists(daily_cache_path):
            file_size_mb = os.path.getsize(daily_cache_path) / (1024 * 1024)
            print(f"✓ Using daily cache: {cache_filename} ({file_size_mb:.2f} MB)")
            return pd.read_parquet(daily_cache_path)

        # 日次キャッシュが存在しない場合 - 作成
        print(f"📦 Creating daily cache for {target_date}...")

        all_dfs = self._load_logs_parallel(bucket, log_files)

        # クリーンアップ用に時間単位キャッシュファイルパスを追跡
        hourly_cache_paths = []
        for log_file_key in log_files:
            safe_filename = log_file_key.replace("/", "_").replace(".gz", ".parquet")
            hourly_cache = os.path.join(self.CACHE_DIR, f"{bucket}_{safe_filename}")
            if os.path.exists(hourly_cache):
                hourly_cache_paths.append(hourly_cache)

        if not all_dfs:
            return pd.DataFrame()

        # すべての時間単位ログを日次DataFrameに結合
        daily_df = pd.concat(all_dfs, ignore_index=True)

        # より良い圧縮のため日時でソート
        daily_df = daily_df.sort_values("datetime", ascending=True)

        # 日次統合Parquetとして保存
        daily_df.to_parquet(
            daily_cache_path,
            engine="pyarrow",
            compression="zstd",
            compression_level=22,
            index=False,
        )

        daily_size_mb = os.path.getsize(daily_cache_path) / (1024 * 1024)
        print(f"💾 Created daily cache: {cache_filename} ({daily_size_mb:.2f} MB)")

        # スペースを節約するため、この日付のすべての個別時間単位Parquetファイルを削除
        # （ロードしたものだけでなく - 以前のリクエストから孤立したファイルがある可能性があります）
        import glob

        date_pattern = target_date.strftime("%Y-%m-%d")
        hourly_pattern = os.path.join(
            self.CACHE_DIR, f"{bucket}_*{date_pattern}*.parquet"
        )
        all_hourly_files = glob.glob(hourly_pattern)

        deleted_count = 0
        for hourly_path in all_hourly_files:
            # 日次キャッシュファイル自体はスキップ
            if hourly_path == daily_cache_path:
                continue
            try:
                os.remove(hourly_path)
                deleted_count += 1
            except OSError:
                pass

        if deleted_count > 0:
            print(f"🗑️  Deleted {deleted_count} hourly cache files for {target_date}")

        return daily_df

    def _load_logs_parallel(
        self, bucket: str, log_files: List[str], max_workers: int = 20
    ) -> List[pd.DataFrame]:
        """
        複数のログファイルを並列でダウンロード・解析

        Args:
            bucket: S3バケット名
            log_files: S3オブジェクトキーのリスト
            max_workers: 並列ワーカー数（デフォルト20）

        Returns:
            DataFrameのリスト
        """
        if not log_files:
            return []

        print(
            f"⚡ Parallel download: {len(log_files)} files with {max_workers} workers..."
        )

        all_dfs = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 各ファイルのダウンロードをサブミット
            future_to_file = {
                executor.submit(self._load_log_as_dataframe, bucket, log_file): log_file
                for log_file in log_files
            }

            # 完了したものから順次処理
            completed = 0
            for future in as_completed(future_to_file):
                log_file = future_to_file[future]
                try:
                    df = future.result()
                    if not df.empty:
                        all_dfs.append(df)
                    completed += 1
                    if completed % 10 == 0 or completed == len(log_files):
                        print(f"  ✓ {completed}/{len(log_files)} files processed")
                except Exception as e:
                    print(f"  ✗ Error loading {log_file}: {e}")
                    completed += 1

        return all_dfs

    def _load_log_as_dataframe(self, bucket: str, log_file_key: str) -> pd.DataFrame:
        """
        CloudFrontログファイルをpandas DataFrameとして読み込み（v1/v2対応、Parquetキャッシュ付き）

        Args:
            bucket: S3バケット名
            log_file_key: S3オブジェクトキー

        Returns:
            CloudFrontログデータを含むDataFrame
        """
        from api.utils.log_format_detector import LogFormatDetector
        from api.utils.log_parsers import create_parser

        # フォーマットを検出
        detector = LogFormatDetector()
        log_format, log_version = detector.detect_from_path(log_file_key)

        # v2のParquetファイルの場合、Parquet→Parquet変換は不要
        # 直接読み込んでキャッシュとして保存
        if log_format.value == "parquet":
            return self._load_parquet_log(bucket, log_file_key)

        # Parquetキャッシュ用の安全なファイル名を作成
        safe_filename = log_file_key.replace("/", "_")
        # 拡張子を.parquetに統一
        for ext in [".gz", ".json.gz", ".csv.gz", ".json", ".csv"]:
            safe_filename = safe_filename.replace(ext, "")
        safe_filename += ".parquet"
        cache_path = os.path.join(self.CACHE_DIR, f"{bucket}_{safe_filename}")

        # Parquetキャッシュが存在するかチェック
        if os.path.exists(cache_path):
            print(f"✓ Using cached Parquet: {cache_path}")
            try:
                return pd.read_parquet(cache_path)
            except Exception as e:
                print(f"⚠ Error reading cached Parquet, re-downloading: {str(e)}")
                os.remove(cache_path)

        # S3からダウンロードし、解析し、Parquetとしてキャッシュ
        print(f"⬇ Downloading from S3: {log_file_key} (format: {log_format.value})")
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=log_file_key)
            content = response["Body"].read()

            # 適切なパーサーを使用して解析
            parser = create_parser(log_format.value)
            df = parser.parse(content)

            if df.empty:
                print(f"⚠ Warning: Empty DataFrame from {log_file_key}")
                return df

            # 高圧縮でParquetとして保存
            df.to_parquet(
                cache_path,
                engine="pyarrow",
                compression="zstd",
                compression_level=22,  # 最大圧縮
                index=False,
            )

            file_size_mb = os.path.getsize(cache_path) / (1024 * 1024)
            print(f"💾 Cached as Parquet: {cache_path} ({file_size_mb:.2f} MB)")

            return df

        except Exception as e:
            print(f"❌ Error loading log file {log_file_key}: {str(e)}")
            return pd.DataFrame(columns=CLOUDFRONT_LOG_COLUMNS + ["datetime"])

    def _load_parquet_log(self, bucket: str, log_file_key: str) -> pd.DataFrame:
        """
        Parquet形式のログファイルを直接読み込み（v2専用）

        Args:
            bucket: S3バケット名
            log_file_key: S3オブジェクトキー

        Returns:
            CloudFrontログデータを含むDataFrame
        """
        from api.utils.log_parsers import ParquetParser

        # Parquetはそのままキャッシュとして使用可能
        safe_filename = log_file_key.replace("/", "_")
        cache_path = os.path.join(self.CACHE_DIR, f"{bucket}_{safe_filename}")

        # キャッシュが存在するかチェック
        if os.path.exists(cache_path):
            print(f"✓ Using cached Parquet: {cache_path}")
            try:
                return pd.read_parquet(cache_path)
            except Exception as e:
                print(f"⚠ Error reading cached Parquet, re-downloading: {str(e)}")
                os.remove(cache_path)

        # S3からダウンロード
        print(f"⬇ Downloading Parquet from S3: {log_file_key}")
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=log_file_key)
            content = response["Body"].read()

            # Parquetパーサーで解析
            parser = ParquetParser()
            df = parser.parse(content)

            # キャッシュとして保存
            with open(cache_path, "wb") as f:
                f.write(content)

            file_size_mb = os.path.getsize(cache_path) / (1024 * 1024)
            print(f"💾 Cached Parquet: {cache_path} ({file_size_mb:.2f} MB)")

            return df

        except Exception as e:
            print(f"❌ Error loading Parquet log file {log_file_key}: {str(e)}")
            return pd.DataFrame()

    def _dataframe_to_dict_list(self, df: pd.DataFrame) -> List[Dict]:
        """
        DataFrameをAPIレスポンス形式に一致する辞書のリストに変換（v1/v2対応）

        Args:
            df: CloudFrontログデータを含むDataFrame

        Returns:
            フィールド名が変更された辞書のリスト
        """
        from api.utils.cloudfront_constants import V2_ADDITIONAL_FIELDS
        from api.utils.cloudfront_constants import V2_FIELD_NAME_MAPPING

        if df.empty:
            return []

        # SettingWithCopyWarningを回避するためにコピーを作成
        df = df.copy()

        # v2フィールドが含まれているかチェック
        has_v2_fields = any(field in df.columns for field in V2_ADDITIONAL_FIELDS)

        # datetimeをUTCからJST（UTC+9）に変換
        if "datetime" in df.columns:
            jst = timezone(timedelta(hours=9))
            df["datetime_jst"] = df["datetime"].dt.tz_convert(jst)
            # dateとtime列をJSTに更新
            df["date"] = df["datetime_jst"].dt.strftime("%Y-%m-%d")
            df["time"] = df["datetime_jst"].dt.strftime("%H:%M:%S")

        # 列をAPI形式にリネーム
        rename_dict = FIELD_NAME_MAPPING.copy()

        # v2フィールドが含まれている場合、v2マッピングも追加
        if has_v2_fields:
            rename_dict.update(V2_FIELD_NAME_MAPPING)

        df_renamed = df.rename(columns=rename_dict)

        # NaN値を埋める
        df_renamed = df_renamed.fillna("")

        # 数値列を変換
        numeric_cols = ["bytes", "statusCode", "bytes_sent", "timeTaken"]
        # v2の数値列も追加
        if has_v2_fields:
            numeric_cols.extend(["timestampMs", "originFirstByteLatency", "originLastByteLatency", "asn"])

        for col in numeric_cols:
            if col in df_renamed.columns:
                df_renamed[col] = df_renamed[col].fillna(0)
                if col in ["timeTaken", "originFirstByteLatency", "originLastByteLatency"]:
                    df_renamed[col] = df_renamed[col].astype(float)
                else:
                    df_renamed[col] = df_renamed[col].astype(int)

        # 必要な列のみを保持（APIレスポンス用にdatetimeとdatetime_jstを削除）
        result_columns = list(FIELD_NAME_MAPPING.values())
        if has_v2_fields:
            result_columns.extend(list(V2_FIELD_NAME_MAPPING.values()))

        df_result = df_renamed[
            [col for col in result_columns if col in df_renamed.columns]
        ]

        return df_result.to_dict("records")

    def search_logs_by_path(
        self,
        distribution_id: str,
        uri_path: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict]:
        """
        時間範囲内でURIパスによってCloudFrontログを検索

        Args:
            distribution_id: CloudFront ディストリビューションID
            uri_path: 検索するURIパス
            start_time: 時間範囲の開始 (datetimeオブジェクト)
            end_time: 時間範囲の終了 (datetimeオブジェクト)

        Returns:
            一致するログエントリのリスト
        """
        from api.endpoints.distributions.services import DistributionService

        distribution_service = DistributionService(self.profile_name)
        log_bucket_info = distribution_service.get_log_bucket_info(distribution_id)
        if not log_bucket_info:
            raise ValueError(
                f"Logging is not enabled for distribution: {distribution_id}"
            )

        # Get list of log files for the date range
        log_files = self._list_log_files(
            bucket=log_bucket_info["bucket"],
            prefix=log_bucket_info["prefix"],
            distribution_id=distribution_id,
            start_time=start_time,
            end_time=end_time,
        )

        matching_entries = []
        for log_file_key in log_files:
            # Use pandas-based search for better performance
            entries = self._search_log_file_by_path_pandas(
                bucket=log_bucket_info["bucket"],
                log_file_key=log_file_key,
                uri_path=uri_path,
                start_time=start_time,
                end_time=end_time,
            )
            matching_entries.extend(entries)

        return matching_entries

    def _search_log_file_by_path_pandas(
        self,
        bucket: str,
        log_file_key: str,
        uri_path: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict]:
        """
        URIパスに一致するエントリを単一のログファイルから検索（pandasを使用）

        Args:
            bucket: S3バケット名
            log_file_key: S3オブジェクトキー
            uri_path: 検索するURIパス
            start_time: 開始時刻（タイムゾーン付き）
            end_time: 終了時刻（タイムゾーン付き）

        Returns:
            一致するログエントリのリスト
        """
        try:
            # Load as DataFrame
            df = self._load_log_as_dataframe(bucket, log_file_key)

            if df.empty:
                return []

            # URIパスでフィルタ
            df_filtered = df[df["cs-uri-stem"].str.contains(uri_path, na=False)]

            # Filter by time range (convert start/end to UTC)
            start_utc = start_time.astimezone(timezone.utc)
            end_utc = end_time.astimezone(timezone.utc)

            df_filtered = df_filtered[
                (df_filtered["datetime"] >= start_utc)
                & (df_filtered["datetime"] <= end_utc)
            ]

            # Convert to list of dictionaries
            return self._dataframe_to_dict_list(df_filtered)

        except Exception as e:
            print(f"Error searching log file {log_file_key} with pandas: {str(e)}")
            return []

    def search_logs_by_ip(
        self,
        distribution_id: str,
        client_ip: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict]:
        """
        時間範囲内でクライアントIPによってCloudFrontログを検索

        Args:
            distribution_id: CloudFront ディストリビューションID
            client_ip: 検索するクライアントIPアドレス
            start_time: 時間範囲の開始 (datetimeオブジェクト)
            end_time: 時間範囲の終了 (datetimeオブジェクト)

        Returns:
            一致するログエントリのリスト
        """
        from api.endpoints.distributions.services import DistributionService

        distribution_service = DistributionService(self.profile_name)
        log_bucket_info = distribution_service.get_log_bucket_info(distribution_id)
        if not log_bucket_info:
            raise ValueError(
                f"Logging is not enabled for distribution: {distribution_id}"
            )

        # Get list of log files for the date range
        log_files = self._list_log_files(
            bucket=log_bucket_info["bucket"],
            prefix=log_bucket_info["prefix"],
            distribution_id=distribution_id,
            start_time=start_time,
            end_time=end_time,
        )

        matching_entries = []
        for log_file_key in log_files:
            # Use pandas-based search for better performance
            entries = self._search_log_file_by_ip_pandas(
                bucket=log_bucket_info["bucket"],
                log_file_key=log_file_key,
                client_ip=client_ip,
                start_time=start_time,
                end_time=end_time,
            )
            matching_entries.extend(entries)

        return matching_entries

    def _search_log_file_by_ip_pandas(
        self,
        bucket: str,
        log_file_key: str,
        client_ip: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict]:
        """
        クライアントIPに一致するエントリを単一のログファイルから検索（pandasを使用）

        Args:
            bucket: S3バケット名
            log_file_key: S3オブジェクトキー
            client_ip: クライアントIPアドレス
            start_time: 開始時刻（タイムゾーン付き）
            end_time: 終了時刻（タイムゾーン付き）

        Returns:
            一致するログエントリのリスト
        """
        try:
            # Load as DataFrame
            df = self._load_log_as_dataframe(bucket, log_file_key)

            if df.empty:
                return []

            # クライアントIPでフィルタ
            df_filtered = df[df["c-ip"] == client_ip]

            # Filter by time range (convert start/end to UTC)
            start_utc = start_time.astimezone(timezone.utc)
            end_utc = end_time.astimezone(timezone.utc)

            df_filtered = df_filtered[
                (df_filtered["datetime"] >= start_utc)
                & (df_filtered["datetime"] <= end_utc)
            ]

            # Convert to list of dictionaries
            return self._dataframe_to_dict_list(df_filtered)

        except Exception as e:
            print(f"Error searching log file {log_file_key} with pandas: {str(e)}")
            return []

    def _load_logs_from_db(
        self,
        distribution_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> pd.DataFrame:
        """
        データベースからログを読み込み

        Args:
            distribution_id: CloudFront ディストリビューションID
            start_datetime: 開始日時
            end_datetime: 終了日時

        Returns:
            ログデータを含むDataFrame
        """
        from api.models import AccessLog

        try:
            print(f"Loading logs from DB for {distribution_id}...")

            logs = AccessLog.objects.filter(
                distribution_id=distribution_id,
                log_datetime__gte=start_datetime,
                log_datetime__lte=end_datetime,
            ).values(
                "log_datetime",
                "c_ip",
                "cs_method",
                "cs_host",
                "cs_uri_stem",
                "cs_uri_query",
                "sc_status",
                "sc_bytes",
                "time_taken",
                "cs_user_agent",
                "cs_referer",
                "x_edge_result_type",
                "edge_location",
            )

            df = pd.DataFrame(list(logs))

            if not df.empty:
                # CloudFrontログ形式に一致するように列をリネーム
                df.rename(
                    columns={
                        "log_datetime": "datetime",
                        "edge_location": "x-edge-location",
                        "c_ip": "c-ip",
                        "cs_method": "cs-method",
                        "cs_host": "cs-host",
                        "cs_uri_stem": "cs-uri-stem",
                        "cs_uri_query": "cs-uri-query",
                        "sc_status": "sc-status",
                        "sc_bytes": "sc-bytes",
                        "time_taken": "time-taken",
                        "cs_user_agent": "cs-user-agent",
                        "cs_referer": "cs-referer",
                        "x_edge_result_type": "x-edge-result-type",
                    },
                    inplace=True,
                )

            print(f"✓ Loaded {len(df)} logs from DB")
            return df

        except Exception as e:
            print(f"Error loading logs from DB: {str(e)}")
            return pd.DataFrame()

    def _save_log_file_to_db(
        self, distribution_id: str, log_file_key: str, df: pd.DataFrame
    ) -> None:
        """
        ログファイルデータをデータベースに保存
        注意: ジオロケーション情報は既にDBまたはメモリにキャッシュされていることを前提とします

        Args:
            distribution_id: CloudFront ディストリビューションID
            log_file_key: S3オブジェクトキー
            df: ログデータを含むDataFrame
        """
        from api.models import AccessLog
        from api.models import IPGeolocation
        from api.models import ProcessedLogFile

        try:
            print(f"Saving log file to DB: {log_file_key} ({len(df)} records)")

            # Create ProcessedLogFile entry
            log_file_obj = ProcessedLogFile.objects.create(
                distribution_id=distribution_id,
                log_file_key=log_file_key,
                file_size=0,  # S3メタデータから計算できます
                record_count=len(df),
                log_start_time=df["datetime"].min() if not df.empty else None,
                log_end_time=df["datetime"].max() if not df.empty else None,
            )

            # このファイルのすべてのIPGeolocationオブジェクトを一括取得
            unique_ips = df["c-ip"].unique().tolist()
            ip_geo_objects = {
                geo.ip_address: geo
                for geo in IPGeolocation.objects.filter(ip_address__in=unique_ips)
            }

            # AccessLogエントリを一括作成
            access_logs = []
            for _, row in df.iterrows():
                ip = row["c-ip"]
                geolocation_obj = ip_geo_objects.get(ip)

                access_logs.append(
                    AccessLog(
                        distribution_id=distribution_id,
                        log_file=log_file_obj,
                        log_datetime=row["datetime"],
                        edge_location=row.get("x-edge-location"),
                        c_ip=ip,
                        geolocation=geolocation_obj,
                        cs_method=row.get("cs-method"),
                        cs_host=row.get("cs-host"),
                        cs_uri_stem=row.get("cs-uri-stem"),
                        cs_uri_query=row.get("cs-uri-query"),
                        sc_status=row.get("sc-status"),
                        sc_bytes=row.get("sc-bytes"),
                        time_taken=row.get("time-taken"),
                        cs_user_agent=row.get("cs-user-agent"),
                        cs_referer=row.get("cs-referer"),
                        x_edge_result_type=row.get("x-edge-result-type"),
                    )
                )

            # 大規模データセット用のバッチ処理で一括作成
            batch_size = 1000
            for i in range(0, len(access_logs), batch_size):
                batch = access_logs[i : i + batch_size]
                AccessLog.objects.bulk_create(batch, ignore_conflicts=True)

            print(f"✓ Saved {len(access_logs)} logs to DB from file: {log_file_key}")

        except Exception as e:
            print(f"Error saving log file to DB: {str(e)}")

    def _get_processed_log_files(
        self, distribution_id: str, log_files: List[str]
    ) -> tuple[List[str], List[str]]:
        """
        どのログファイルが処理済みかチェックし、未処理のものを返す

        Args:
            distribution_id: CloudFront ディストリビューションID
            log_files: S3からのログファイルキーのリスト

        Returns:
            (processed_files, unprocessed_files)のタプル
        """
        from api.models import ProcessedLogFile

        # このディストリビューションの処理済みファイルキーをすべて取得
        processed_keys = set(
            ProcessedLogFile.objects.filter(
                distribution_id=distribution_id, log_file_key__in=log_files
            ).values_list("log_file_key", flat=True)
        )

        processed = [f for f in log_files if f in processed_keys]
        unprocessed = [f for f in log_files if f not in processed_keys]

        return processed, unprocessed

    def _mark_log_file_as_processed(
        self, distribution_id: str, log_file_key: str
    ) -> None:
        """
        実際のログデータを保存せずにログファイルを処理済みとしてマーク。
        同じ日の複数のファイルが1つの日次キャッシュに統合される場合に使用。

        Args:
            distribution_id: CloudFront ディストリビューションID
            log_file_key: S3オブジェクトキー
        """
        from api.models import ProcessedLogFile

        try:
            # 関連するAccessLogレコードなしでProcessedLogFileエントリを作成
            ProcessedLogFile.objects.create(
                distribution_id=distribution_id,
                log_file_key=log_file_key,
                file_size=0,
                record_count=0,  # 個別のレコードは保存されていません
                log_start_time=None,
                log_end_time=None,
            )
        except Exception as e:
            print(f"Error marking log file as processed: {str(e)}")

    def aggregate_logs(
        self,
        distribution_id: str,
        start_date: datetime,
        end_date: datetime,
        group_by: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 1000,
        min_count: int = 1,
        exclude_static_files: bool = False,
        client_ip: Optional[str] = None,
        client_ips: Optional[List[str]] = None,
        uri_path: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        query_string: Optional[str] = None,
    ) -> Dict:
        """指定されたグループ化キーでCloudFrontログを集約します。

        ログエントリを指定されたキー（IP、User Agent、リファラー等）でグループ化し、
        各グループの統計情報を計算します。静的ファイルの除外や最小リクエスト数でのフィルタリングが可能です。

        Args:
            distribution_id (str): CloudFront Distribution ID
                例: "E1234567890ABC"
            start_date (datetime): 開始日（dateオブジェクト）
            end_date (datetime): 終了日（dateオブジェクト）
            group_by (str): グループ化キー
                指定可能: "ip", "user_agent", "referrer", "query_string"
            start_time (Optional[str]): 開始時刻（HH:MM:SS形式、JST）
                例: "09:00:00"
            end_time (Optional[str]): 終了時刻（HH:MM:SS形式、JST）
                例: "18:00:00"
            limit (int, optional): 結果の最大件数（上位N件）。デフォルトは1000。
            min_count (int, optional): 最小リクエスト数フィルタ。デフォルトは1。
            exclude_static_files (bool, optional): 静的ファイルを除外するか。デフォルトはFalse。
            client_ip (Optional[str]): 単一のクライアントIPでフィルタ
            client_ips (Optional[List[str]]): 複数のクライアントIPでフィルタ
            uri_path (Optional[str]): URIパスでフィルタ（部分一致）
            user_agent (Optional[str]): User Agentでフィルタ（完全一致）
            referrer (Optional[str]): リファラーでフィルタ（部分一致）
            query_string (Optional[str]): クエリ文字列でフィルタ（部分一致）

        Returns:
            Dict: 集約結果を含む辞書。以下のキーが含まれます:
                - distribution_id (str): Distribution ID
                - date_range (Dict): 日付範囲
                - group_by (str): グループ化キー
                - total_requests (int): 総リクエスト数
                - unique_values (int): ユニークな値の数
                - aggregations (List[Dict]): 集約結果のリスト

        Raises:
            ValueError: ログ設定が無効、またはgroup_byが不正な場合

        Example:
            >>> service = LogService()
            >>> result = service.aggregate_logs(
            ...     distribution_id="E1234567890ABC",
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 1, 1),
            ...     group_by="ip",
            ...     limit=10
            ... )
            >>> result['total_requests']
            15234
            >>> len(result['aggregations'])
            10
        """
        from api.endpoints.distributions.services import DistributionService

        distribution_service = DistributionService(self.profile_name)
        log_bucket_info = distribution_service.get_log_bucket_info(distribution_id)
        if not log_bucket_info:
            raise ValueError(
                f"Logging is not enabled for distribution: {distribution_id}"
            )

        # Convert dates to datetime with timezone
        jst = timezone(timedelta(hours=9))

        if start_time:
            # Parse time string (HH:MM:SS)
            time_parts = [int(p) for p in start_time.split(":")]
            start_datetime = (
                datetime.combine(
                    start_date,
                    datetime.min.time().replace(
                        hour=time_parts[0],
                        minute=time_parts[1] if len(time_parts) > 1 else 0,
                        second=time_parts[2] if len(time_parts) > 2 else 0,
                    ),
                )
                .replace(tzinfo=jst)
                .astimezone(timezone.utc)
            )
        else:
            start_datetime = datetime.combine(start_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )

        if end_time:
            # Parse time string (HH:MM:SS)
            time_parts = [int(p) for p in end_time.split(":")]
            end_datetime = (
                datetime.combine(
                    end_date,
                    datetime.min.time().replace(
                        hour=time_parts[0],
                        minute=time_parts[1] if len(time_parts) > 1 else 0,
                        second=time_parts[2] if len(time_parts) > 2 else 0,
                    ),
                )
                .replace(tzinfo=jst)
                .astimezone(timezone.utc)
            )
        else:
            end_datetime = datetime.combine(end_date, datetime.max.time()).replace(
                tzinfo=timezone.utc
            )

        # Get list of log files for the date range
        log_files = self._list_log_files(
            bucket=log_bucket_info["bucket"],
            prefix=log_bucket_info["prefix"],
            distribution_id=distribution_id,
            start_time=start_datetime,
            end_time=end_datetime,
        )

        # Load logs using daily consolidated cache
        all_dfs = []

        # Group log files by date
        from collections import defaultdict

        files_by_date = defaultdict(list)
        for log_file_key in log_files:
            try:
                # Extract date from log file name
                parts = log_file_key.split(".")
                for part in parts:
                    if len(part) >= 10 and part[4] == "-" and part[7] == "-":
                        date_str = part[:10]
                        file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        files_by_date[file_date].append(log_file_key)
                        break
                else:
                    # 日付が見つからない場合、個別ファイル読み込みにフォールバック
                    df = self._load_log_as_dataframe(
                        log_bucket_info["bucket"], log_file_key
                    )
                    if not df.empty:
                        all_dfs.append(df)
            except (ValueError, IndexError):
                # 個別ファイル読み込みにフォールバック
                df = self._load_log_as_dataframe(
                    log_bucket_info["bucket"], log_file_key
                )
                if not df.empty:
                    all_dfs.append(df)

        # 各日付のログを読み込み
        today = datetime.now(timezone.utc).date()
        for file_date, date_log_files in files_by_date.items():
            is_today = file_date == today

            df = self._load_daily_logs(
                bucket=log_bucket_info["bucket"],
                distribution_id=distribution_id,
                target_date=file_date,
                log_files=date_log_files,
                is_current_day=is_today,
            )

            if not df.empty:
                all_dfs.append(df)

        if not all_dfs:
            return {
                "distribution_id": distribution_id,
                "date_range": {
                    "start": start_datetime.astimezone(jst),
                    "end": end_datetime.astimezone(jst),
                },
                "group_by": group_by,
                "total_requests": 0,
                "unique_values": 0,
                "aggregations": [],
            }

        # Combine all DataFrames
        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Filter by time range
        combined_df = combined_df[
            (combined_df["datetime"] >= start_datetime)
            & (combined_df["datetime"] <= end_datetime)
        ]

        # リクエストがあれば静的ファイルをフィルタアウト
        if exclude_static_files:
            from api.utils.cloudfront_constants import is_static_file

            combined_df = combined_df[~combined_df["cs-uri-stem"].apply(is_static_file)]

        # 追加のフィルタを適用
        if client_ip:
            combined_df = combined_df[combined_df["c-ip"] == client_ip]
        elif client_ips:
            # 複数のIPでフィルタ
            combined_df = combined_df[combined_df["c-ip"].isin(client_ips)]

        if uri_path:
            combined_df = combined_df[
                combined_df["cs-uri-stem"].str.contains(uri_path, na=False)
            ]

        if user_agent:
            combined_df = combined_df[combined_df["cs-user-agent"] == user_agent]

        if referrer:
            combined_df = combined_df[
                combined_df["cs-referer"].str.contains(referrer, na=False)
            ]

        if query_string:
            combined_df = combined_df[
                combined_df["cs-uri-query"].str.contains(query_string, na=False)
            ]

        if combined_df.empty:
            return {
                "distribution_id": distribution_id,
                "date_range": {
                    "start": start_datetime.astimezone(jst),
                    "end": end_datetime.astimezone(jst),
                },
                "group_by": group_by,
                "total_requests": 0,
                "unique_values": 0,
                "aggregations": [],
            }

        # group_byを列名にマッピング
        group_column_map = {
            "ip": "c-ip",
            "user_agent": "cs-user-agent",
            "referrer": "cs-referer",
            "query_string": "cs-uri-query",
        }
        group_column = group_column_map.get(group_by)
        if not group_column:
            raise ValueError(f"Invalid group_by value: {group_by}")

        # 集約前の総リクエスト数を計算
        total_requests = len(combined_df)

        # 集約を実行
        agg_result = combined_df.groupby(group_column).agg(
            {
                "datetime": ["min", "max", "count"],
                "cs-uri-stem": "nunique",
                "cs-user-agent": "nunique",
                "sc-status": lambda x: x.value_counts().to_dict(),
                "cs-method": lambda x: x.value_counts().to_dict(),
            }
        )

        # 列名をフラット化
        agg_result.columns = [
            "_".join(col).strip() if col[1] else col[0] for col in agg_result.columns
        ]
        agg_result = agg_result.reset_index()

        # 明確化のため列をリネーム
        agg_result = agg_result.rename(
            columns={
                group_column: "value",
                "datetime_min": "first_seen",
                "datetime_max": "last_seen",
                "datetime_count": "request_count",
                "cs-uri-stem_nunique": "unique_paths",
                "cs-user-agent_nunique": "unique_user_agents",
                "sc-status_<lambda>": "status_distribution",
                "cs-method_<lambda>": "method_distribution",
            }
        )

        # パーセンテージを計算
        agg_result["percentage"] = agg_result["request_count"] / total_requests * 100

        # min_countでフィルタ
        agg_result = agg_result[agg_result["request_count"] >= min_count]

        # request_countで降順にソート
        agg_result = agg_result.sort_values("request_count", ascending=False)

        # リミットを適用（上位N件）
        agg_result = agg_result.head(limit)

        # IP集約用にgeo_infoを追加
        if group_by == "ip":
            from api.endpoints.ip_info.services import get_ip_info_batch
            from api.endpoints.ip_info.services import get_ip_info_from_db

            unique_ips = agg_result["value"].tolist()

            # DBにないIPをチェック
            ips_not_in_db = []
            for ip in unique_ips:
                ip_info = get_ip_info_from_db(ip)
                if not ip_info:
                    ips_not_in_db.append(ip)

            # 不足しているIPを一括取得（WHOISなし - WHOISは詳細モーダルが開かれたときに取得されます）
            if ips_not_in_db:
                print(f"Fetching {len(ips_not_in_db)} IPs not in DB...")
                get_ip_info_batch(ips_not_in_db)

            # すべてのIPに対してDBからgeo情報を取得
            geo_info_map = {}
            for ip in unique_ips:
                try:
                    ip_info = get_ip_info_from_db(ip)
                    if ip_info:
                        geo_info_map[ip] = {
                            "country": ip_info.get("country"),
                            "country_code": ip_info.get("countryCode"),
                            "city": ip_info.get("city"),
                        }
                except Exception:
                    # geo情報取得が失敗した場合はスキップ
                    pass

            agg_result["geo_info"] = agg_result["value"].apply(
                lambda ip: geo_info_map.get(ip)
            )

        # 各集約にsample_log、mark_stats、mark_typeを追加
        from api.endpoints.log_marks.services import get_log_marks_for_logs

        sample_logs = []
        mark_stats_per_item = []
        mark_types = []

        for value in agg_result["value"]:
            # サンプルログを取得
            sample_df = combined_df[combined_df[group_column] == value].tail(1)
            if not sample_df.empty:
                sample_row = sample_df.iloc[0]
                # datetimeをJSTに変換
                sample_datetime_jst = sample_row["datetime"].tz_convert(jst)
                sample_logs.append(
                    {
                        "date": sample_datetime_jst.strftime("%Y-%m-%d"),
                        "time": sample_datetime_jst.strftime("%H:%M:%S"),
                        "uri": sample_row.get("cs-uri-stem", ""),
                        "status": int(sample_row.get("sc-status", 0)),
                    }
                )
            else:
                sample_logs.append(None)

            # この集計アイテムに関連するログのマーク統計を計算
            item_df = combined_df[combined_df[group_column] == value]
            item_logs_for_marks = item_df[["cs-user-agent"]].rename(
                columns={"cs-user-agent": "userAgent"}
            ).to_dict("records")
            item_marks = get_log_marks_for_logs(item_logs_for_marks, distribution_id)

            # マークタイプ別にカウント
            item_mark_stats = {"bot": 0, "suspicious": 0, "legitimate": 0, "unmarked": 0}
            for log in item_logs_for_marks:
                user_agent = log.get("userAgent", "")
                if user_agent and user_agent in item_marks:
                    mark_type = item_marks[user_agent]["mark_type"]
                    item_mark_stats[mark_type] = item_mark_stats.get(mark_type, 0) + 1
                else:
                    item_mark_stats["unmarked"] += 1

            mark_stats_per_item.append(item_mark_stats)

            # この集計値自体のマークタイプを取得
            mark_type = None
            if group_by == "user_agent":
                # このUser-Agentのマークを取得
                test_log = [{"userAgent": value}]
                value_marks = get_log_marks_for_logs(test_log, distribution_id)
                if value and value in value_marks:
                    mark_type = value_marks[value]["mark_type"]
            elif group_by == "ip":
                # IPアドレスの場合、まず組織情報からボット判定
                from api.endpoints.log_marks.services import check_ip_is_bot

                # valueが数値型の場合もあるので文字列に変換
                ip_str = str(value) if value is not None else None
                ip_bot_mark = check_ip_is_bot(ip_str) if ip_str else None
                if ip_bot_mark:
                    mark_type = ip_bot_mark["mark_type"]
                else:
                    # 組織ベースで判定できない場合、mark_statsから判定
                    # ボットの割合が50%以上の場合は"bot"とマーク
                    total_marked = sum(item_mark_stats.values())
                    if total_marked > 0:
                        bot_percentage = item_mark_stats["bot"] / total_marked
                        suspicious_percentage = item_mark_stats["suspicious"] / total_marked

                        if bot_percentage >= 0.5:
                            mark_type = "bot"
                        elif suspicious_percentage >= 0.5:
                            mark_type = "suspicious"
                        elif item_mark_stats["legitimate"] / total_marked >= 0.5:
                            mark_type = "legitimate"
            else:
                # referrer、query_stringなどの場合、mark_statsから判定
                total_marked = sum(item_mark_stats.values())
                if total_marked > 0:
                    bot_percentage = item_mark_stats["bot"] / total_marked
                    suspicious_percentage = item_mark_stats["suspicious"] / total_marked

                    if bot_percentage >= 0.5:
                        mark_type = "bot"
                    elif suspicious_percentage >= 0.5:
                        mark_type = "suspicious"
                    elif item_mark_stats["legitimate"] / total_marked >= 0.5:
                        mark_type = "legitimate"
            mark_types.append(mark_type)

        agg_result["sample_log"] = sample_logs
        agg_result["mark_stats"] = mark_stats_per_item
        agg_result["mark_type"] = mark_types

        # datetime列をJSTに変換
        agg_result["first_seen"] = pd.to_datetime(
            agg_result["first_seen"]
        ).dt.tz_convert(jst)
        agg_result["last_seen"] = pd.to_datetime(agg_result["last_seen"]).dt.tz_convert(
            jst
        )

        # Convert to list of dictionaries
        aggregations = agg_result.to_dict("records")

        # Calculate mark statistics
        from api.endpoints.log_marks.services import get_log_marks_for_logs

        # Convert DataFrame to list of dicts for mark checking
        logs_for_marks = combined_df[["cs-user-agent"]].rename(
            columns={"cs-user-agent": "userAgent"}
        ).to_dict("records")
        marks = get_log_marks_for_logs(logs_for_marks, distribution_id)

        # Count marks by type
        mark_stats = {"bot": 0, "suspicious": 0, "legitimate": 0, "unmarked": 0}
        for log in logs_for_marks:
            user_agent = log.get("userAgent", "")
            if user_agent and user_agent in marks:
                mark_type = marks[user_agent]["mark_type"]
                mark_stats[mark_type] = mark_stats.get(mark_type, 0) + 1
            else:
                mark_stats["unmarked"] += 1

        # レスポンスを構築
        response = {
            "distribution_id": distribution_id,
            "date_range": {
                "start": start_datetime.astimezone(jst),
                "end": end_datetime.astimezone(jst),
            },
            "group_by": group_by,
            "total_requests": total_requests,
            "unique_values": len(agg_result),
            "aggregations": aggregations,
            "mark_stats": mark_stats,
        }

        return response
