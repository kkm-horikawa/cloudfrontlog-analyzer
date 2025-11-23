from django.db import models
from django.utils import timezone


class GeoLogCache(models.Model):
    """アクセスログの地理情報集約キャッシュモデル。

    CloudFrontアクセスログから集約した地理的分布情報をキャッシュします。
    日付範囲と時刻範囲による部分一致検索をサポートし、
    頻繁な集約処理を回避してパフォーマンスを向上させます。

    Attributes:
        distribution_id (str): CloudFront Distribution ID
        start_date (date): 検索開始日
        end_date (date): 検索終了日
        start_time (time): ユーザー指定の開始時刻（オプション）
        end_time (time): ユーザー指定の終了時刻（オプション）
        actual_start_datetime (datetime): キャッシュに含まれる実際のデータ開始時刻
        actual_end_datetime (datetime): キャッシュに含まれる実際のデータ終了時刻
        locations_data (JSON): 地理情報の集約データ
        total_count (int): 総アクセス数
        created_at (datetime): キャッシュ作成日時
        expires_at (datetime): キャッシュ有効期限（Noneの場合は永続）

    Note:
        actual_start_datetime/actual_end_datetimeは、キャッシュの部分一致検索に使用されます。
        クエリの日時範囲がこの範囲内に完全に含まれる場合、キャッシュヒットとなります。

    Example:
        >>> cache = GeoLogCache.objects.filter(
        ...     distribution_id="E1234567890ABC",
        ...     start_date="2024-01-01"
        ... ).first()
        >>> cache.total_count
        125678
        >>> cache.is_expired()
        False
    """

    distribution_id = models.CharField(max_length=100, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    start_time = models.TimeField(null=True, blank=True)  # ユーザー指定の開始時刻
    end_time = models.TimeField(null=True, blank=True)  # ユーザー指定の終了時刻

    # 実際のデータ範囲（キャッシュに含まれる実データの範囲）
    actual_start_datetime = models.DateTimeField(
        db_index=True, null=True, blank=True
    )  # 実際のデータ開始時刻
    actual_end_datetime = models.DateTimeField(
        db_index=True, null=True, blank=True
    )  # 実際のデータ終了時刻

    # 集約データ（JSON形式）
    locations_data = models.JSONField()  # GeoLogsResponseのlocations
    total_count = models.IntegerField(default=0)

    # メタデータ
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(
        db_index=True, null=True, blank=True
    )  # キャッシュの有効期限（永続的な場合はNone）

    class Meta:
        db_table = "geo_log_cache"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["distribution_id", "start_date", "end_date", "expires_at"]
            ),
            models.Index(
                fields=[
                    "distribution_id",
                    "actual_start_datetime",
                    "actual_end_datetime",
                ]
            ),
        ]

    def is_expired(self):
        """キャッシュが有効期限切れかを判定します。

        Returns:
            bool: 有効期限が設定されており、かつ現在時刻が有効期限を過ぎている場合True。
                有効期限が設定されていない（永続キャッシュ）場合はFalse。

        Example:
            >>> cache = GeoLogCache.objects.first()
            >>> cache.is_expired()
            False
        """
        return timezone.now() > self.expires_at if self.expires_at else False

    def __str__(self):
        return f"{self.distribution_id} - {self.start_date} to {self.end_date}"
