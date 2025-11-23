from rest_framework import serializers


class IPInfoSerializer(serializers.Serializer):
    """IP位置情報のシリアライザ。

    ip-api.comから取得したIPアドレスの詳細な位置情報と
    ネットワーク情報をシリアライズします。大陸、国、都市などの
    地理的情報に加え、ISP、組織、ASN情報、モバイル/プロキシ/
    ホスティングのフラグも含まれます。

    Attributes:
        ip (CharField): IPアドレス
        continent (CharField): 大陸名（任意）
        continentCode (CharField): 大陸コード（任意）
        country (CharField): 国名（任意）
        countryCode (CharField): 国コード（任意）
        region (CharField): 地域名（任意）
        city (CharField): 都市名（任意）
        district (CharField): 地区名（任意）
        zip (CharField): 郵便番号（任意）
        lat (FloatField): 緯度（任意）
        lon (FloatField): 経度（任意）
        timezone (CharField): タイムゾーン（任意）
        offset (IntegerField): UTCオフセット（任意）
        currency (CharField): 通貨（任意）
        isp (CharField): ISP名（任意）
        org (CharField): 組織名（任意）
        asn (CharField): AS番号（任意）
        asname (CharField): AS名（任意）
        mobile (BooleanField): モバイル接続フラグ（任意）
        proxy (BooleanField): プロキシフラグ（任意）
        hosting (BooleanField): ホスティングフラグ（任意）

    Example:
        シリアライズ対象データ:
            {
                "ip": "1.2.3.4",
                "continent": "Asia",
                "country": "Japan",
                "city": "Tokyo",
                "lat": 35.6895,
                "lon": 139.6917,
                "isp": "Example ISP",
                "mobile": false,
                "proxy": false,
                "hosting": false
            }

        使用例:
            >>> serializer = IPInfoSerializer(data=ip_data)
            >>> if serializer.is_valid():
            >>>     return Response(serializer.data)
    """

    ip = serializers.CharField()
    continent = serializers.CharField(required=False, allow_null=True)
    continentCode = serializers.CharField(required=False, allow_null=True)
    country = serializers.CharField(required=False, allow_null=True)
    countryCode = serializers.CharField(required=False, allow_null=True)
    region = serializers.CharField(required=False, allow_null=True)
    city = serializers.CharField(required=False, allow_null=True)
    district = serializers.CharField(required=False, allow_null=True)
    zip = serializers.CharField(required=False, allow_null=True)
    lat = serializers.FloatField(required=False, allow_null=True)
    lon = serializers.FloatField(required=False, allow_null=True)
    timezone = serializers.CharField(required=False, allow_null=True)
    offset = serializers.IntegerField(required=False, allow_null=True)
    currency = serializers.CharField(required=False, allow_null=True)
    isp = serializers.CharField(required=False, allow_null=True)
    org = serializers.CharField(required=False, allow_null=True)
    asn = serializers.CharField(required=False, allow_null=True)
    asname = serializers.CharField(required=False, allow_null=True)
    mobile = serializers.BooleanField(required=False, allow_null=True)
    proxy = serializers.BooleanField(required=False, allow_null=True)
    hosting = serializers.BooleanField(required=False, allow_null=True)
