"""S3パス操作のヘルパーユーティリティ。

このモジュールは、CloudFront logsのS3パス構造を操作するための
ヘルパー関数を提供します。v1とv2の異なるパス構造に対応します。

Example:
    >>> from api.utils.s3_path_helper import generate_v2_partition_paths
    >>> paths = generate_v2_partition_paths(
    ...     prefix="logs/",
    ...     start_date=date(2025, 11, 23),
    ...     end_date=date(2025, 11, 23),
    ...     partition_format="year={yyyy}/month={MM}/day={dd}/hour={HH}"
    ... )
"""

from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import List


def generate_v2_partition_paths(
    prefix: str,
    start_date: date,
    end_date: date,
    start_hour: int = 0,
    end_hour: int = 23,
    partition_format: str = "year={yyyy}/month={MM}/day={dd}/hour={HH}",
    distribution_id: str = None,
) -> List[str]:
    """v2パーティション形式のS3パスリストを生成します。

    指定された期間と時間範囲に基づいて、v2形式のパーティションパスを生成します。

    Args:
        prefix (str): S3プレフィックス（例: "logs/"）
        start_date (date): 開始日
        end_date (date): 終了日
        start_hour (int, optional): 開始時刻（0-23）。デフォルトは0。
        end_hour (int, optional): 終了時刻（0-23）。デフォルトは23。
        partition_format (str, optional): パーティション形式。
            サポート形式:
            - "year={yyyy}/month={MM}/day={dd}/hour={HH}" (Hive形式)
            - "{yyyy}/{MM}/{dd}/{HH}" (シンプル形式)
            - "distributionid={DistributionId}/year={yyyy}/..." (Distribution ID付き)
        distribution_id (str, optional): Distribution ID（partition_formatに含まれる場合）

    Returns:
        List[str]: 生成されたパーティションパスのリスト

    Example:
        >>> paths = generate_v2_partition_paths(
        ...     prefix="logs/",
        ...     start_date=date(2025, 11, 23),
        ...     end_date=date(2025, 11, 23),
        ...     start_hour=10,
        ...     end_hour=12
        ... )
        >>> len(paths)
        3
        >>> paths[0]
        'logs/year=2025/month=11/day=23/hour=10/'
    """
    paths = []
    current_date = start_date

    while current_date <= end_date:
        # 開始日と終了日の時刻範囲を調整
        hour_start = start_hour if current_date == start_date else 0
        hour_end = end_hour if current_date == end_date else 23

        for hour in range(hour_start, hour_end + 1):
            path = _format_partition_path(
                prefix=prefix,
                target_date=current_date,
                hour=hour,
                partition_format=partition_format,
                distribution_id=distribution_id,
            )
            paths.append(path)

        current_date += timedelta(days=1)

    return paths


def _format_partition_path(
    prefix: str,
    target_date: date,
    hour: int,
    partition_format: str,
    distribution_id: str = None,
) -> str:
    """パーティション形式に従ってパスをフォーマットします。

    Args:
        prefix (str): S3プレフィックス
        target_date (date): 対象日
        hour (int): 時刻（0-23）
        partition_format (str): パーティション形式
        distribution_id (str, optional): Distribution ID

    Returns:
        str: フォーマットされたパス
    """
    # フォーマット変数の置換
    formatted = partition_format
    formatted = formatted.replace("{yyyy}", f"{target_date.year:04d}")
    formatted = formatted.replace("{MM}", f"{target_date.month:02d}")
    formatted = formatted.replace("{dd}", f"{target_date.day:02d}")
    formatted = formatted.replace("{HH}", f"{hour:02d}")

    if distribution_id:
        formatted = formatted.replace("{DistributionId}", distribution_id)
        formatted = formatted.replace("{distributionid}", distribution_id)

    # プレフィックスと結合
    full_path = prefix + formatted

    # 末尾にスラッシュを追加（ディレクトリを示すため）
    if not full_path.endswith("/"):
        full_path += "/"

    return full_path


def generate_v1_log_file_patterns(
    prefix: str, distribution_id: str, start_date: date, end_date: date
) -> List[str]:
    """v1形式のログファイルプレフィックスパターンを生成します。

    Args:
        prefix (str): S3プレフィックス
        distribution_id (str): CloudFront Distribution ID
        start_date (date): 開始日
        end_date (date): 終了日

    Returns:
        List[str]: 日付ごとのファイルプレフィックスパターンのリスト

    Example:
        >>> patterns = generate_v1_log_file_patterns(
        ...     prefix="logs/",
        ...     distribution_id="E123ABC",
        ...     start_date=date(2025, 11, 23),
        ...     end_date=date(2025, 11, 24)
        ... )
        >>> patterns[0]
        'logs/E123ABC.2025-11-23'
    """
    patterns = []
    current_date = start_date

    while current_date <= end_date:
        pattern = f"{prefix}{distribution_id}.{current_date.strftime('%Y-%m-%d')}"
        patterns.append(pattern)
        current_date += timedelta(days=1)

    return patterns


def detect_log_version_from_s3_structure(
    s3_client, bucket: str, prefix: str, distribution_id: str = None
) -> str:
    """S3のディレクトリ構造からログバージョン（v1/v2）を検出します。

    Args:
        s3_client: boto3 S3クライアント
        bucket (str): S3バケット名
        prefix (str): S3プレフィックス
        distribution_id (str, optional): Distribution ID

    Returns:
        str: 'v1' または 'v2'

    Example:
        >>> version = detect_log_version_from_s3_structure(
        ...     s3_client, "my-bucket", "logs/", "E123ABC"
        ... )
        >>> version
        'v2'
    """
    from api.utils.log_format_detector import LogFormatDetector

    try:
        # プレフィックス配下のオブジェクトをサンプリング
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=10)

        if "Contents" not in response or len(response["Contents"]) == 0:
            # オブジェクトがない場合はv1と仮定（後方互換）
            return "v1"

        # 最初のいくつかのキーをチェック
        detector = LogFormatDetector()
        for obj in response["Contents"][:10]:
            key = obj["Key"]
            if detector.is_v2_partitioned_path(key):
                return "v2"

        # v2パーティション構造が見つからない場合はv1
        return "v1"

    except Exception:
        # エラー時はv1をデフォルトとする
        return "v1"
