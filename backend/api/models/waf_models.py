from django.db import models
from django.utils import timezone

from .ip_geolocation import IPGeolocation


class WAFBlockedIPSnapshot(models.Model):
    """WAFブロックIPリストのスナップショットモデル。

    特定の時点でのWAF IP Setに登録されているブロック対象IPアドレスの
    スナップショットを保存します。時系列での変化を追跡できます。

    Attributes:
        distribution_id (str): CloudFront Distribution ID
        snapshot_time (datetime): スナップショット取得時刻
        total_ips (int): スナップショット内の総IP数
        created_at (datetime): レコード作成日時

    Example:
        >>> snapshot = WAFBlockedIPSnapshot.objects.filter(
        ...     distribution_id="E1234567890ABC"
        ... ).first()
        >>> snapshot.total_ips
        42
        >>> snapshot.blocked_ips.count()
        42
    """

    distribution_id = models.CharField(max_length=100, db_index=True)
    snapshot_time = models.DateTimeField(default=timezone.now, db_index=True)
    total_ips = models.IntegerField(default=0)

    # メタデータ
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "waf_blocked_ip_snapshots"
        ordering = ["-snapshot_time"]
        indexes = [
            models.Index(fields=["distribution_id", "snapshot_time"]),
        ]

    def __str__(self):
        return f"{self.distribution_id} - {self.snapshot_time} ({self.total_ips} IPs)"


class WAFBlockedIP(models.Model):
    """WAFブロックIPの詳細情報モデル。

    WAF IP Setに登録されている個別のブロック対象IPアドレスの詳細情報を保存します。
    スナップショットに紐づき、ジオロケーション情報も含みます。

    Attributes:
        snapshot (WAFBlockedIPSnapshot): 関連するスナップショット
        ip_address (str): 代表IPアドレス
        cidr (str): CIDR表記
        ip_set_id (str): WAF IP Set ID
        ip_set_name (str): WAF IP Set名
        ip_set_arn (str): WAF IP Set ARN
        geolocation (IPGeolocation): 関連するジオロケーション情報

    Example:
        >>> blocked = WAFBlockedIP.objects.filter(
        ...     ip_address="8.8.8.8"
        ... ).first()
        >>> blocked.cidr
        '8.8.8.8/32'
        >>> blocked.geolocation.country
        'United States'
    """

    snapshot = models.ForeignKey(
        WAFBlockedIPSnapshot, on_delete=models.CASCADE, related_name="blocked_ips"
    )
    ip_address = models.CharField(max_length=45, db_index=True)
    cidr = models.CharField(max_length=50)
    ip_set_id = models.CharField(max_length=100)
    ip_set_name = models.CharField(max_length=255)
    ip_set_arn = models.TextField()

    # キャッシュされた地理情報
    geolocation = models.ForeignKey(
        IPGeolocation, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "waf_blocked_ips"
        ordering = ["ip_address"]
        indexes = [
            models.Index(fields=["snapshot", "ip_address"]),
        ]

    def __str__(self):
        return f"{self.cidr} ({self.ip_set_name})"
