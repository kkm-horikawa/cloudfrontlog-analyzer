"""CloudFrontログの地理的集約サービスモジュール。

このモジュールは、CloudFrontアクセスログを地理情報（国、都市、座標）で集約し、
マップビジュアライゼーション用のデータを提供します。日次キャッシュ戦略により
高速なレスポンスと効率的なデータベース使用を実現します。

主な機能:
    - IPベースの地理情報集約
    - 複数フィルタ条件サポート（URI、User-Agent、Referer等）
    - 日次キャッシュによるパフォーマンス最適化
    - 部分一致検索とキャッシュマージ
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Dict
from typing import Optional

import pandas as pd

from api.utils.aws_base import AWSServiceBase


class GeoService(AWSServiceBase):
    """CloudFrontログの地理的集約操作サービス。

    CloudFrontアクセスログをIPアドレスベースで地理情報に変換し、
    位置ごとにアクセス数を集約します。キャッシュ戦略により、
    頻繁なクエリでも高速なレスポンスを提供します。

    Attributes:
        profile_name (str): AWS CLIプロファイル名（親クラスから継承）
        session (boto3.Session): Boto3セッション（親クラスから継承）

    Note:
        - 過去の日のデータは永続キャッシュ（expires_at=None）として保存されます
        - 当日のデータは1時間TTLの一時キャッシュとして保存されます
        - フィルタ条件付きのクエリはキャッシュされません

    Example:
        >>> from api.endpoints.geo.services import GeoService
        >>> geo_service = GeoService(profile_name="default")
        >>> result = geo_service.get_geo_aggregated_logs(
        ...     distribution_id="E1234567890ABC",
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 31)
        ... )
        >>> len(result["locations"])
        42
        >>> result["total"]
        125678
    """

    def get_geo_aggregated_logs(
        self,
        distribution_id: str,
        start_date: datetime,
        end_date: datetime,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        uri_filter: Optional[str] = None,
        user_agent_filter: Optional[str] = None,
        referer_filter: Optional[str] = None,
        query_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        method_filter: Optional[str] = None,
        exclude_static_files: bool = False,
    ) -> Dict:
        """IPアドレスを地理情報に変換して位置ごとに集約されたログを取得します。

        CloudFrontログファイルをS3から読み込み、各IPアドレスの地理情報を取得して、
        位置（緯度・経度）ごとにアクセス数を集約します。フィルタ条件を指定して
        特定のリクエストのみを対象にすることも可能です。

        キャッシュ戦略:
            - フィルタなし: 日次キャッシュを使用（過去の日は永続、当日は1時間TTL）
            - フィルタあり: キャッシュをバイパスして常に最新データを取得

        Args:
            distribution_id (str): CloudFront Distribution ID
            start_date (datetime): 検索開始日（dateまたはdatetimeオブジェクト）
            end_date (datetime): 検索終了日（dateまたはdatetimeオブジェクト）
            start_time (Optional[str]): 開始時刻 HH:MM:SS形式（JST）。
                指定しない場合は00:00:00。
            end_time (Optional[str]): 終了時刻 HH:MM:SS形式（JST）。
                指定しない場合は23:59:59。
            uri_filter (Optional[str]): URIパスの部分一致フィルタ。
                例: "/api/" で /api/users などがマッチ
            user_agent_filter (Optional[str]): User-Agentの部分一致フィルタ。
                例: "Mozilla" でMozillaを含むUAがマッチ
            referer_filter (Optional[str]): Refererの部分一致フィルタ
            query_filter (Optional[str]): クエリ文字列の部分一致フィルタ
            status_filter (Optional[str]): HTTPステータスコードの完全一致フィルタ。
                例: "404" で404エラーのみ
            method_filter (Optional[str]): HTTPメソッドの完全一致フィルタ。
                例: "GET", "POST" など
            exclude_static_files (bool): 静的ファイル（js, css, 画像等）を除外するか。
                デフォルトはFalse

        Returns:
            Dict: 地理的に集約された結果。以下のキーを含む:
                - locations (List[Dict]): 位置情報のリスト。各要素は:
                    - lat (float): 緯度
                    - lon (float): 経度
                    - city (str): 都市名
                    - country (str): 国名
                    - countryCode (str): 国コード（ISO 3166-1）
                    - count (int): アクセス数
                    - ips (List[str]): この位置からアクセスしたIPアドレスリスト
                - total (int): 総アクセス数

        Raises:
            ValueError: 指定されたDistributionでログが有効化されていない場合

        Note:
            - 近接する位置（緯度・経度が0.01度以内）は自動的にマージされます
            - IP情報はip-api.comから取得され、DBにキャッシュされます
            - 未処理のログファイルは自動的にDBに保存されます
            - 日次Parquetキャッシュにより、過去の日のログは高速に読み込まれます

        Example:
            >>> from datetime import datetime
            >>> geo_service = GeoService(profile_name="default")
            >>> # 基本的な使用例
            >>> result = geo_service.get_geo_aggregated_logs(
            ...     distribution_id="E1234567890ABC",
            ...     start_date=datetime(2024, 1, 1),
            ...     end_date=datetime(2024, 1, 31)
            ... )
            >>> print(f"Total: {result['total']} accesses")
            Total: 125678 accesses
            >>> print(f"Locations: {len(result['locations'])}")
            Locations: 42
            >>> # トップアクセス位置を表示
            >>> top_location = result['locations'][0]
            >>> print(f"{top_location['city']}, {top_location['country']}: {top_location['count']}")
            Tokyo, Japan: 45678
            >>>
            >>> # フィルタを使用した例
            >>> result_filtered = geo_service.get_geo_aggregated_logs(
            ...     distribution_id="E1234567890ABC",
            ...     start_date=datetime(2024, 1, 1),
            ...     end_date=datetime(2024, 1, 1),
            ...     start_time="09:00:00",
            ...     end_time="17:00:00",
            ...     uri_filter="/api/",
            ...     status_filter="200"
            ... )
            >>> print(f"API成功リクエスト: {result_filtered['total']}")
            API成功リクエスト: 8432
        """
        from api.endpoints.distributions.services import DistributionService
        from api.endpoints.ip_info.services import get_ip_info_batch
        from api.endpoints.logs.services import LogService

        # 注意: フィルタはキャッシュされません - フィルタが適用された場合は常に新しいデータを取得
        has_filters = any(
            [
                uri_filter,
                referer_filter,
                query_filter,
                status_filter,
                method_filter,
                exclude_static_files,
            ]
        )

        # 最初にキャッシュをチェック（フィルタがない場合のみ）
        if not has_filters:
            cached_result = self._get_cached_geo_logs(
                distribution_id, start_date, end_date, start_time, end_time
            )
            if cached_result:
                print("✓ Using cached geo-aggregated log data")
                return cached_result

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

        # 日付範囲のログファイルリストを取得
        log_service = LogService(self.profile_name)
        log_files = log_service._list_log_files(
            bucket=log_bucket_info["bucket"],
            prefix=log_bucket_info["prefix"],
            distribution_id=distribution_id,
            start_time=start_datetime,
            end_time=end_datetime,
        )

        print(f"Found {len(log_files)} log files for the date range")

        # どのファイルが処理済みかをチェック
        processed_files, unprocessed_files = log_service._get_processed_log_files(
            distribution_id, log_files
        )

        print(
            f"DB cache status: {len(processed_files)} already processed, {len(unprocessed_files)} new files"
        )

        # 日次統合キャッシュを使用してすべてのログを読み込み（生ログAPIと同じ戦略）
        all_dfs = []

        # 日次キャッシュの最適化のためログファイルを日付でグループ化
        from collections import defaultdict

        files_by_date = defaultdict(list)
        for log_file_key in log_files:
            try:
                # ログファイル名から日付を抽出
                parts = log_file_key.split(".")
                for part in parts:
                    if len(part) >= 10 and part[4] == "-" and part[7] == "-":
                        date_str = part[:10]
                        file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        files_by_date[file_date].append(log_file_key)
                        break
            except (ValueError, IndexError):
                pass

        # 各日付のログを読み込み（過去の日付には日次キャッシュを使用）
        today = datetime.now(timezone.utc).date()
        all_unique_ips = set()
        # DB保存用に日次DataFrameを追跡（再ダウンロードを避けるため）
        daily_dfs_by_date = {}

        for file_date, date_log_files in files_by_date.items():
            is_today = file_date == today

            df = log_service._load_daily_logs(
                bucket=log_bucket_info["bucket"],
                distribution_id=distribution_id,
                target_date=file_date,
                log_files=date_log_files,
                is_current_day=is_today,
            )

            if not df.empty:
                all_dfs.append(df)
                # 後でDB保存するために日次dfを保存（再ダウンロードを回避）
                daily_dfs_by_date[file_date] = df

                # ユニークなIPを収集
                unique_ips_in_file = df["c-ip"].unique()
                all_unique_ips.update(unique_ips_in_file)

        # ステップ2: すべてのユニークなIPの位置情報を一度に取得（未処理ファイルがある場合）
        if all_unique_ips:
            print(
                f"Fetching geo info for {len(all_unique_ips)} unique IPs from all new log files..."
            )
            get_ip_info_batch(list(all_unique_ips))
            print("✓ Completed geo info fetching for all unique IPs")

        # ステップ3: 日次dfデータを使用して未処理ログファイルをデータベースに保存（再ダウンロードなし）
        # 重複する日次df保存を避けるため、未処理ファイルを日付でグループ化
        unprocessed_by_date = defaultdict(list)
        for log_file_key in unprocessed_files:
            try:
                parts = log_file_key.split(".")
                for part in parts:
                    if len(part) >= 10 and part[4] == "-" and part[7] == "-":
                        date_str = part[:10]
                        file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        unprocessed_by_date[file_date].append(log_file_key)
                        break
            except (ValueError, IndexError) as e:
                print(
                    f"Warning: Could not extract date from log file key {log_file_key}: {str(e)}"
                )

        # 各日付について、日次dfを一度だけ保存（最初のファイルのため）
        # 他のすべてのファイルは処理済みとしてマーク
        for file_date, date_unprocessed_files in unprocessed_by_date.items():
            if file_date in daily_dfs_by_date:
                daily_df = daily_dfs_by_date[file_date]

                # 最初のファイルのみ日次dfを保存
                first_file = date_unprocessed_files[0]
                log_service._save_log_file_to_db(distribution_id, first_file, daily_df)
                print(
                    f"✓ Saved {len(daily_df)} logs to DB from daily cache for: {first_file}"
                )

                # 重複データを保存せずに残りのファイルを処理済みとしてマーク
                for remaining_file in date_unprocessed_files[1:]:
                    log_service._mark_log_file_as_processed(
                        distribution_id, remaining_file
                    )
                    print(
                        f"✓ Marked as processed (no duplicate save): {remaining_file}"
                    )

        if not all_dfs:
            return {
                "locations": [],
                "total": 0,
            }

        # すべてのDataFrameを結合
        print(f"Combining {len(all_dfs)} DataFrames...")
        combined_df = pd.concat(all_dfs, ignore_index=True)
        print(f"✓ Combined into {len(combined_df)} total rows")

        # 時間範囲でフィルタ
        combined_df = combined_df[
            (combined_df["datetime"] >= start_datetime)
            & (combined_df["datetime"] <= end_datetime)
        ]

        # 提供された場合はユーザーフィルタを適用
        filter_messages = []
        initial_count = len(combined_df)

        if uri_filter:
            combined_df = combined_df[
                combined_df["cs-uri-stem"].str.contains(
                    uri_filter, case=False, na=False
                )
            ]
            filter_messages.append(f"URI contains '{uri_filter}'")

        if user_agent_filter:
            combined_df = combined_df[
                combined_df["cs-user-agent"].str.contains(
                    user_agent_filter, case=False, na=False
                )
            ]
            filter_messages.append(f"User Agent contains '{user_agent_filter}'")

        if referer_filter:
            combined_df = combined_df[
                combined_df["cs-referer"].str.contains(
                    referer_filter, case=False, na=False
                )
            ]
            filter_messages.append(f"Referer contains '{referer_filter}'")

        if query_filter:
            combined_df = combined_df[
                combined_df["cs-uri-query"].str.contains(
                    query_filter, case=False, na=False
                )
            ]
            filter_messages.append(f"Query contains '{query_filter}'")

        if status_filter:
            combined_df = combined_df[
                combined_df["sc-status"].astype(str) == status_filter
            ]
            filter_messages.append(f"Status = {status_filter}")

        if method_filter:
            combined_df = combined_df[combined_df["cs-method"] == method_filter]
            filter_messages.append(f"Method = {method_filter}")

        if exclude_static_files:
            from api.utils.cloudfront_constants import is_static_file

            combined_df = combined_df[~combined_df["cs-uri-stem"].apply(is_static_file)]
            filter_messages.append("Excluding static files")

        if filter_messages:
            filtered_count = len(combined_df)
            print(
                f"Applied filters: {', '.join(filter_messages)} "
                f"({initial_count} → {filtered_count} logs)"
            )

        # Get unique IPs and their counts
        print("Calculating unique IPs...")
        ip_counts = combined_df["c-ip"].value_counts().to_dict()

        print(f"Fetching geo info for {len(ip_counts)} unique IPs using batch API...")

        # バッチAPIを使用してすべてのIP情報を一度に取得
        ip_infos = get_ip_info_batch(list(ip_counts.keys()))

        print(f"Successfully fetched geo info for {len(ip_infos)} IPs")

        # 各ユニークなIPの地理情報を取得
        locations = []
        processed_coords = {}  # Map coordinate keys to location indices

        for ip, count in ip_counts.items():
            ip_info = ip_infos.get(ip)
            if ip_info and ip_info.get("lat") and ip_info.get("lon"):
                # 近接する位置をグループ化するための座標キーを作成
                coord_key = f"{round(ip_info['lat'], 2)},{round(ip_info['lon'], 2)}"

                if coord_key in processed_coords:
                    # 既存の位置に追加
                    idx = processed_coords[coord_key]
                    locations[idx]["count"] += count
                    locations[idx]["ips"].append(ip)
                else:
                    # 新しい位置を作成
                    idx = len(locations)
                    locations.append(
                        {
                            "lat": ip_info["lat"],
                            "lon": ip_info["lon"],
                            "city": ip_info.get("city", "Unknown"),
                            "country": ip_info.get("country", "Unknown"),
                            "countryCode": ip_info.get("countryCode", ""),
                            "count": count,
                            "ips": [ip],
                        }
                    )
                    processed_coords[coord_key] = idx

        # カウントで降順にソート
        locations.sort(key=lambda x: x["count"], reverse=True)

        result = {
            "locations": locations,
            "total": len(combined_df),
        }

        # キャッシュに保存 - 再利用性を高めるため日ごとに分割
        self._save_cached_geo_logs_by_day(
            distribution_id, combined_df, start_datetime, end_datetime
        )

        return result

    def _get_cached_geo_logs(
        self,
        distribution_id: str,
        start_date: datetime,
        end_date: datetime,
        start_time: Optional[str],
        end_time: Optional[str],
    ) -> Optional[Dict]:
        """データベースからキャッシュされた地理的集約ログを取得します。

        GeoLogCacheモデルから該当するキャッシュエントリを検索し、
        リクエストされた日時範囲を完全にカバーしている場合にキャッシュヒットとします。
        複数のキャッシュエントリをマージして部分一致検索もサポートします。

        キャッシュヒット条件:
            1. リクエスト範囲と重複するキャッシュエントリが存在する
            2. キャッシュエントリが有効期限内（expires_atがNullまたは未来）
            3. キャッシュエントリの実際の範囲がリクエスト範囲を完全にカバー

        Args:
            distribution_id (str): CloudFront Distribution ID
            start_date (datetime): 検索開始日
            end_date (datetime): 検索終了日
            start_time (Optional[str]): 開始時刻 HH:MM:SS形式（JST）
            end_time (Optional[str]): 終了時刻 HH:MM:SS形式（JST）

        Returns:
            Optional[Dict]: キャッシュヒットした場合は結果辞書、
                キャッシュミスまたはエラーの場合はNone。
                結果辞書の形式:
                    - locations (List[Dict]): 位置情報リスト
                    - total (int): 総アクセス数

        Note:
            - 複数のキャッシュエントリを自動的にマージします
            - 同じ座標の位置情報は自動的に統合されます
            - 部分的なカバレッジの場合はNoneを返します（完全カバレッジのみヒット）

        Example:
            >>> # 2024/1/1の完全な日がキャッシュされている場合
            >>> result = geo_service._get_cached_geo_logs(
            ...     distribution_id="E1234567890ABC",
            ...     start_date=datetime(2024, 1, 1),
            ...     end_date=datetime(2024, 1, 1),
            ...     start_time=None,
            ...     end_time=None
            ... )
            >>> result is not None  # キャッシュヒット
            True
            >>> # 2024/1/1 10:00-12:00がキャッシュにない場合
            >>> result = geo_service._get_cached_geo_logs(
            ...     distribution_id="E1234567890ABC",
            ...     start_date=datetime(2024, 1, 1),
            ...     end_date=datetime(2024, 1, 1),
            ...     start_time="10:00:00",
            ...     end_time="12:00:00"
            ... )
            >>> result is None  # キャッシュミス
            True
        """
        try:
            from django.utils import timezone as django_timezone

            from api.models import GeoLogCache

            # リクエストされた日時範囲を計算
            jst = timezone(timedelta(hours=9))

            if start_time:
                time_parts = [int(p) for p in start_time.split(":")]
                requested_start = (
                    datetime.combine(
                        start_date.date()
                        if hasattr(start_date, "date")
                        else start_date,
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
                requested_start = datetime.combine(
                    start_date.date() if hasattr(start_date, "date") else start_date,
                    datetime.min.time(),
                ).replace(tzinfo=timezone.utc)

            if end_time:
                time_parts = [int(p) for p in end_time.split(":")]
                requested_end = (
                    datetime.combine(
                        end_date.date() if hasattr(end_date, "date") else end_date,
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
                requested_end = datetime.combine(
                    end_date.date() if hasattr(end_date, "date") else end_date,
                    datetime.max.time(),
                ).replace(tzinfo=timezone.utc)

            # リクエストされた範囲と重複するキャッシュエントリを検索
            cache_entries = (
                GeoLogCache.objects.filter(
                    distribution_id=distribution_id,
                    actual_start_datetime__isnull=False,  # 実際の時刻を持つエントリのみ使用
                    actual_end_datetime__isnull=False,
                    actual_start_datetime__lte=requested_end,
                    actual_end_datetime__gte=requested_start,
                )
                .exclude(
                    expires_at__isnull=False, expires_at__lte=django_timezone.now()
                )
                .order_by("actual_start_datetime")
            )

            if not cache_entries:
                return None

            # Check if we have complete coverage
            cache_entries_list = list(cache_entries)

            # 開始時刻でソート
            cache_entries_list.sort(key=lambda x: x.actual_start_datetime)

            # カバレッジをチェック
            covered_start = cache_entries_list[0].actual_start_datetime
            covered_end = cache_entries_list[0].actual_end_datetime

            # Noneチェック - キャッシュエントリが無効な場合はスキップ
            if covered_start is None or covered_end is None:
                print("⚠️ Cache entry has invalid datetime, bypassing cache")
            else:
                for entry in cache_entries_list[1:]:
                    if (
                        entry.actual_start_datetime is None
                        or entry.actual_end_datetime is None
                    ):
                        continue
                    if entry.actual_start_datetime <= covered_end:
                        # 重複または隣接、カバレッジを拡張
                        covered_end = max(covered_end, entry.actual_end_datetime)
                    else:
                        # ギャップを検出
                        break

                # Check if we have complete coverage
                if covered_start <= requested_start and covered_end >= requested_end:
                    print(
                        f"✓ Cache hit: {len(cache_entries_list)} cache entries cover the requested range"
                    )

                    # キャッシュエントリを結合
                    combined_locations = {}
                    total_count = 0

                    for entry in cache_entries_list:
                        # リクエストされた時間範囲で位置をフィルタ
                        for location in entry.locations_data:
                            coord_key = f"{location['lat']},{location['lon']}"
                            if coord_key in combined_locations:
                                combined_locations[coord_key]["count"] += location[
                                    "count"
                                ]
                                combined_locations[coord_key]["ips"].extend(
                                    location["ips"]
                                )
                            else:
                                combined_locations[coord_key] = location.copy()

                        total_count += entry.total_count

                    return {
                        "locations": list(combined_locations.values()),
                        "total": total_count,
                    }
                else:
                    print(
                        f"Partial cache coverage: {covered_start} to {covered_end} (requested: {requested_start} to {requested_end})"
                    )
                return None

        except Exception as e:
            print(f"Error fetching geo log cache: {str(e)}")
            import traceback

            traceback.print_exc()
            return None

    def _save_cached_geo_logs(
        self,
        distribution_id: str,
        start_date: datetime,
        end_date: datetime,
        start_time: Optional[str],
        end_time: Optional[str],
        result: Dict,
    ) -> None:
        """地理的集約ログをGeoLogCacheモデルに保存します。

        集約結果をデータベースにキャッシュとして保存します。過去の日は永続キャッシュ、
        当日は1時間TTLの一時キャッシュとして保存されます。

        キャッシュ保存戦略:
            - 過去の日（end_date < today）:
                - actual_end_datetime = 23:59:59
                - expires_at = None（永続）
            - 当日（end_date == today）:
                - actual_end_datetime = 現在時刻
                - expires_at = 現在時刻 + 1時間
            - 未来の日（発生すべきでない）:
                - actual_end_datetime = 23:59:59
                - expires_at = 現在時刻 + 1時間

        Args:
            distribution_id (str): CloudFront Distribution ID
            start_date (datetime): 検索開始日
            end_date (datetime): 検索終了日
            start_time (Optional[str]): 開始時刻 HH:MM:SS形式（JST）
            end_time (Optional[str]): 終了時刻 HH:MM:SS形式（JST）
            result (Dict): 保存する集約結果。以下のキーを含む:
                - locations (List[Dict]): 位置情報リスト
                - total (int): 総アクセス数

        Returns:
            None

        Note:
            - 過去の日のデータは永続的に保存され、手動削除されるまで残ります
            - 当日のデータは1時間後に自動的に期限切れになります
            - actual_start_datetime/actual_end_datetimeはキャッシュヒット判定に使用されます
            - エラーが発生した場合はトレースバックを出力しますが、例外は発生させません

        Example:
            >>> # 過去の日のキャッシュを保存（永続）
            >>> geo_service._save_cached_geo_logs(
            ...     distribution_id="E1234567890ABC",
            ...     start_date=datetime(2024, 1, 1),
            ...     end_date=datetime(2024, 1, 1),
            ...     start_time=None,
            ...     end_time=None,
            ...     result={"locations": [...], "total": 12345}
            ... )
            Saving complete day cache (永久): 2024-01-01 to 2024-01-01
            ✓ Saved geo log cache (永久 - complete day)
            >>> # 当日のキャッシュを保存（1時間TTL）
            >>> geo_service._save_cached_geo_logs(
            ...     distribution_id="E1234567890ABC",
            ...     start_date=datetime.now(),
            ...     end_date=datetime.now(),
            ...     start_time=None,
            ...     end_time=None,
            ...     result={"locations": [...], "total": 456}
            ... )
            Saving incremental cache (1時間): up to 2024-11-18 15:30:45+00:00
            ✓ Saved geo log cache (expires in 1 hour - incremental)
        """
        try:
            from django.utils import timezone as django_timezone

            from api.models import GeoLogCache

            # 実際のdatetime範囲を計算
            jst = timezone(timedelta(hours=9))
            now = django_timezone.now()
            today_jst = now.astimezone(jst).date()

            # 実際の開始日時を決定
            if start_time:
                time_parts = [int(p) for p in start_time.split(":")]
                actual_start = (
                    datetime.combine(
                        start_date.date()
                        if hasattr(start_date, "date")
                        else start_date,
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
                actual_start = datetime.combine(
                    start_date.date() if hasattr(start_date, "date") else start_date,
                    datetime.min.time(),
                ).replace(tzinfo=timezone.utc)

            # 実際の終了日時を決定
            end_date_obj = end_date.date() if hasattr(end_date, "date") else end_date

            if end_date_obj < today_jst:
                # 前日: 完全な日（永久保存）
                actual_end = datetime.combine(
                    end_date_obj, datetime.max.time()
                ).replace(tzinfo=timezone.utc)
                expires_at = None  # 完全な日には有効期限なし
                print(f"Saving complete day cache (永久): {start_date} to {end_date}")
            elif end_date_obj == today_jst:
                # 当日: 現在時刻まで（1時間期限）
                if end_time:
                    time_parts = [int(p) for p in end_time.split(":")]
                    actual_end = (
                        datetime.combine(
                            end_date_obj,
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
                    actual_end = now
                expires_at = now + timedelta(hours=1)
                print(f"Saving incremental cache (1時間): up to {actual_end}")
            else:
                # Future day (should not happen): use max time
                actual_end = datetime.combine(
                    end_date_obj, datetime.max.time()
                ).replace(tzinfo=timezone.utc)
                expires_at = now + timedelta(hours=1)

            GeoLogCache.objects.create(
                distribution_id=distribution_id,
                start_date=start_date.date()
                if hasattr(start_date, "date")
                else start_date,
                end_date=end_date_obj,
                start_time=start_time,
                end_time=end_time,
                actual_start_datetime=actual_start,
                actual_end_datetime=actual_end,
                locations_data=result.get("locations", []),
                total_count=result.get("total", 0),
                expires_at=expires_at,
            )

            if expires_at:
                print("✓ Saved geo log cache (expires in 1 hour - incremental)")
            else:
                print("✓ Saved geo log cache (永久 - complete day)")

        except Exception as e:
            print(f"Error saving geo log cache: {str(e)}")
            import traceback

            traceback.print_exc()

    def _save_cached_geo_logs_by_day(
        self,
        distribution_id: str,
        combined_df: pd.DataFrame,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> None:
        """日ごとに分割して地理的集約ログをGeoLogCacheに保存します。

        複数日にまたがる検索結果を日ごとに分割してキャッシュに保存します。
        これにより、異なる日付範囲の検索でもキャッシュを再利用できるようになります。

        保存戦略の例:
            - 2024/1/11 ~ 2024/1/13 の検索 → 3つのキャッシュエントリを作成:
                1. 2024/1/11のデータ（永続）
                2. 2024/1/12のデータ（永続）
                3. 2024/1/13のデータ（過去なら永続、当日なら1時間TTL）

        各日のキャッシュエントリには以下が含まれます:
            - distribution_id: Distribution ID
            - start_date/end_date: 同じ日付（日ごとに保存）
            - start_time/end_time: None（完全な日）
            - actual_start_datetime: その日の00:00:00 UTC
            - actual_end_datetime: 過去の日なら23:59:59、当日なら現在時刻
            - locations_data: その日の位置情報集約データ
            - total_count: その日の総アクセス数
            - expires_at: 過去の日ならNone、当日なら現在時刻+1時間

        Args:
            distribution_id (str): CloudFront Distribution ID
            combined_df (pd.DataFrame): すべてのログを含む結合されたDataFrame。
                "datetime"列と"c-ip"列を含む必要があります。
            start_datetime (datetime): 検索開始日時（使用されません、情報目的）
            end_datetime (datetime): 検索終了日時（使用されません、情報目的）

        Returns:
            None

        Note:
            - DataFrameが空の場合は何もしません
            - 各日のIPアドレスに対してget_ip_info_batchを呼び出します（キャッシュ使用）
            - 近接する位置（緯度・経度が0.01度以内）は自動的にマージされます
            - エラーが発生した場合はトレースバックを出力しますが、例外は発生させません

        Example:
            >>> import pandas as pd
            >>> from datetime import datetime, timezone
            >>> # 2024/1/1~1/3のログデータ
            >>> df = pd.DataFrame({
            ...     "datetime": [
            ...         datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            ...         datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc),
            ...         datetime(2024, 1, 3, 14, 0, tzinfo=timezone.utc)
            ...     ],
            ...     "c-ip": ["8.8.8.8", "1.1.1.1", "8.8.8.8"]
            ... })
            >>> geo_service._save_cached_geo_logs_by_day(
            ...     distribution_id="E1234567890ABC",
            ...     combined_df=df,
            ...     start_datetime=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ...     end_datetime=datetime(2024, 1, 3, tzinfo=timezone.utc)
            ... )
            Splitting cache by day: 3 days
              2024-01-01: 1 logs, 1 locations (永久)
              2024-01-02: 1 logs, 1 locations (永久)
              2024-01-03: 1 logs, 1 locations (永久)
            ✓ Saved day-by-day cache entries
        """
        try:
            from django.utils import timezone as django_timezone

            from api.endpoints.ip_info.services import get_ip_info_batch

            jst = timezone(timedelta(hours=9))
            now = django_timezone.now()
            today_jst = now.astimezone(jst).date()

            # 日付でグループ化
            if combined_df.empty:
                return

            # datetime列が存在することを確認
            if "datetime" not in combined_df.columns:
                print("Warning: datetime column not found in DataFrame")
                return

            # グループ化のためdateに変換
            combined_df["date"] = combined_df["datetime"].dt.date

            # 範囲内のユニークな日付を取得
            unique_dates = sorted(combined_df["date"].unique())

            print(f"Splitting cache by day: {len(unique_dates)} days")

            for date_obj in unique_dates:
                # この日のログをフィルタ
                day_df = combined_df[combined_df["date"] == date_obj]

                # この日のユニークなIPとそのカウントを取得
                ip_counts = day_df["c-ip"].value_counts().to_dict()

                # すべてのIP情報を取得するためバッチAPIを使用（キャッシュを使用）
                ip_infos = get_ip_info_batch(list(ip_counts.keys()))

                # この日の位置ごとに集約
                locations = []
                processed_coords = {}

                for ip, count in ip_counts.items():
                    ip_info = ip_infos.get(ip)
                    if ip_info and ip_info.get("lat") and ip_info.get("lon"):
                        coord_key = (
                            f"{round(ip_info['lat'], 2)},{round(ip_info['lon'], 2)}"
                        )

                        if coord_key in processed_coords:
                            idx = processed_coords[coord_key]
                            locations[idx]["count"] += count
                            locations[idx]["ips"].append(ip)
                        else:
                            idx = len(locations)
                            locations.append(
                                {
                                    "lat": ip_info["lat"],
                                    "lon": ip_info["lon"],
                                    "city": ip_info.get("city", "Unknown"),
                                    "country": ip_info.get("country", "Unknown"),
                                    "countryCode": ip_info.get("countryCode", ""),
                                    "count": count,
                                    "ips": [ip],
                                }
                            )
                            processed_coords[coord_key] = idx

                locations.sort(key=lambda x: x["count"], reverse=True)

                # この日の実際の開始/終了時刻を決定
                actual_start = datetime.combine(date_obj, datetime.min.time()).replace(
                    tzinfo=timezone.utc
                )

                # これが過去の日か当日かチェック
                if date_obj < today_jst:
                    # 過去の日: 完全な日（永久保存）
                    actual_end = datetime.combine(
                        date_obj, datetime.max.time()
                    ).replace(tzinfo=timezone.utc)
                    expires_at = None
                    print(
                        f"  {date_obj}: {len(day_df)} logs, {len(locations)} locations (永久)"
                    )
                elif date_obj == today_jst:
                    # 当日: 現在まで（1時間期限）
                    actual_end = now
                    expires_at = now + timedelta(hours=1)
                    print(
                        f"  {date_obj}: {len(day_df)} logs, {len(locations)} locations (1時間TTL)"
                    )
                else:
                    # 未来の日（発生すべきでない）: 最大時刻を使用
                    actual_end = datetime.combine(
                        date_obj, datetime.max.time()
                    ).replace(tzinfo=timezone.utc)
                    expires_at = now + timedelta(hours=1)
                    print(
                        f"  {date_obj}: {len(day_df)} logs, {len(locations)} locations (1時間TTL)"
                    )

                # この日のキャッシュを保存
                from api.models import GeoLogCache

                GeoLogCache.objects.create(
                    distribution_id=distribution_id,
                    start_date=date_obj,
                    end_date=date_obj,
                    start_time=None,
                    end_time=None,
                    actual_start_datetime=actual_start,
                    actual_end_datetime=actual_end,
                    locations_data=locations,
                    total_count=len(day_df),
                    expires_at=expires_at,
                )

            print("✓ Saved day-by-day cache entries")

        except Exception as e:
            print(f"Error saving day-by-day cache: {str(e)}")
            import traceback

            traceback.print_exc()
