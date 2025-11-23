from django.db import models


class IPGeolocation(models.Model):
    """IPアドレスのジオロケーション情報キャッシュモデル。

    ip-api.comから取得したIPアドレスのジオロケーション情報とWHOIS情報を
    データベースにキャッシュして保存します。キャッシュヒット回数も記録されます。

    Attributes:
        ip_address (str): IPアドレス（ユニーク）
        continent (str): 大陸名
        continent_code (str): 大陸コード
        country (str): 国名
        country_code (str): 国コード（ISO 3166-1）
        region (str): 地域/州名
        city (str): 都市名
        district (str): 地区名
        zip_code (str): 郵便番号
        latitude (float): 緯度
        longitude (float): 経度
        timezone (str): タイムゾーン
        offset (int): UTCからのオフセット（秒）
        currency (str): 通貨コード
        isp (str): ISP名
        org (str): 組織名
        asn (str): AS番号
        asname (str): AS名
        mobile (bool): モバイル接続かどうか
        proxy (bool): プロキシかどうか
        hosting (bool): ホスティングサービスかどうか
        whois_raw (str): WHOIS生データ
        whois_netname (str): WHOISネットワーク名
        whois_org_name (str): WHOIS組織名
        whois_country (str): WHOIS国コード
        whois_net_range (str): WHOISネットワーク範囲
        created_at (datetime): 作成日時
        updated_at (datetime): 更新日時
        hit_count (int): キャッシュヒット回数

    Example:
        >>> geo = IPGeolocation.objects.get(ip_address="8.8.8.8")
        >>> geo.country
        'United States'
        >>> geo.city
        'Mountain View'
        >>> geo.latitude
        37.386
    """

    ip_address = models.CharField(max_length=45, unique=True, db_index=True)
    continent = models.CharField(max_length=100, null=True, blank=True)
    continent_code = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timezone = models.CharField(max_length=100, null=True, blank=True)
    offset = models.IntegerField(null=True, blank=True)
    currency = models.CharField(max_length=10, null=True, blank=True)
    isp = models.CharField(max_length=255, null=True, blank=True)
    org = models.CharField(max_length=255, null=True, blank=True)
    asn = models.CharField(max_length=100, null=True, blank=True)
    asname = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.BooleanField(null=True, blank=True)
    proxy = models.BooleanField(null=True, blank=True)
    hosting = models.BooleanField(null=True, blank=True)

    # WHOIS情報
    whois_raw = models.TextField(
        null=True, blank=True, db_index=True
    )  # WHOIS未取得IP検索用
    whois_netname = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    whois_org_name = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    whois_country = models.CharField(max_length=10, null=True, blank=True)
    whois_net_range = models.CharField(max_length=100, null=True, blank=True)

    # メタデータ
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    hit_count = models.IntegerField(
        default=0, db_index=True
    )  # キャッシュヒット回数（人気IP検索用）

    class Meta:
        db_table = "ip_geolocation_cache"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ip_address", "created_at"]),
        ]

    def __str__(self):
        return f"{self.ip_address} - {self.city}, {self.country}"
