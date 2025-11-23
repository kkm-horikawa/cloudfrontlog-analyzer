from rest_framework import serializers


class LogSearchRequestSerializer(serializers.Serializer):
    """CloudFrontログ検索リクエストのシリアライザ。

    URLと時刻を指定してCloudFrontログを検索するためのリクエストパラメータを検証します。

    Attributes:
        distributionId (str): CloudFront Distribution ID（必須）
        targetUrl (str): 検索対象のURLパス（必須）
        dateTime (datetime): 検索対象の日時（必須）
        timeWindowMinutes (int): 検索時間枠（分）、デフォルト5分（オプション）

    Example:
        >>> data = {
        ...     "distributionId": "E1234567890ABC",
        ...     "targetUrl": "/api/users",
        ...     "dateTime": "2024-01-01T12:00:00Z",
        ...     "timeWindowMinutes": 10
        ... }
        >>> serializer = LogSearchRequestSerializer(data=data)
        >>> serializer.is_valid()
        True
    """

    distributionId = serializers.CharField(required=True)
    targetUrl = serializers.CharField(required=True)
    dateTime = serializers.DateTimeField(required=True)
    timeWindowMinutes = serializers.IntegerField(default=5, required=False)


class RawLogsListRequestSerializer(serializers.Serializer):
    """生ログ一覧リクエストのシリアライザ"""

    distributionId = serializers.CharField(required=True)
    startDate = serializers.DateField(required=True)
    endDate = serializers.DateField(required=True)
    startTime = serializers.TimeField(required=False, allow_null=True)
    endTime = serializers.TimeField(required=False, allow_null=True)
    clientIp = serializers.CharField(required=False, allow_blank=True)
    clientIps = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    uriPath = serializers.CharField(required=False, allow_blank=True)
    userAgent = serializers.CharField(required=False, allow_blank=True)
    referrer = serializers.CharField(required=False, allow_blank=True)
    queryString = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(default=1, min_value=1)
    perPage = serializers.IntegerField(default=1000, min_value=1, max_value=10000)


class IPInfoSerializer(serializers.Serializer):
    """IP位置情報のシリアライザ"""

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


class SuspiciousCheckSerializer(serializers.Serializer):
    """不審チェック結果のシリアライザ"""

    isSuspicious = serializers.BooleanField()
    isBlocked = serializers.BooleanField()
    isAllowedBot = serializers.BooleanField()
    severity = serializers.CharField()
    matchedPatterns = serializers.ListField(child=serializers.CharField())
    details = serializers.DictField(required=False)


class LogEntrySerializer(serializers.Serializer):
    """CloudFrontログエントリのシリアライザ。

    CloudFrontアクセスログの単一エントリをシリアライズします。
    基本的なログフィールドに加え、IP情報と不審チェック結果も含みます。

    Attributes:
        date (str): ログの日付
        time (str): ログの時刻
        edgeLocation (str): エッジロケーション
        bytes (int): 送信バイト数
        clientIp (str): クライアントIPアドレス
        method (str): HTTPメソッド
        host (str): ホスト名
        uriStem (str): URIパス
        statusCode (int): HTTPステータスコード
        referrer (str): リファラー
        userAgent (str): ユーザーエージェント
        queryString (str): クエリ文字列
        cookie (str): Cookie
        edgeResultType (str): エッジ結果タイプ
        ipInfo (IPInfoSerializer, optional): IP情報
        suspiciousCheck (SuspiciousCheckSerializer, optional): 不審チェック結果

    Example:
        >>> entry = {
        ...     "date": "2024-01-01",
        ...     "time": "12:00:00",
        ...     "clientIp": "8.8.8.8",
        ...     "statusCode": 200,
        ...     "uriStem": "/index.html"
        ... }
        >>> serializer = LogEntrySerializer(data=entry)
        >>> serializer.is_valid()
        True
    """

    date = serializers.CharField()
    time = serializers.CharField()
    edgeLocation = serializers.CharField()
    bytes = serializers.IntegerField()
    clientIp = serializers.CharField()
    method = serializers.CharField()
    host = serializers.CharField()
    uriStem = serializers.CharField()
    statusCode = serializers.IntegerField()
    referrer = serializers.CharField()
    userAgent = serializers.CharField()
    queryString = serializers.CharField()
    cookie = serializers.CharField()
    edgeResultType = serializers.CharField()
    edgeRequestId = serializers.CharField(required=False)
    hostHeader = serializers.CharField(required=False)
    protocol = serializers.CharField(required=False)
    bytes_sent = serializers.IntegerField(required=False)
    timeTaken = serializers.FloatField(required=False)
    xForwardedFor = serializers.CharField(required=False)
    sslProtocol = serializers.CharField(required=False)
    sslCipher = serializers.CharField(required=False)
    edgeResponseResultType = serializers.CharField(required=False)
    protocolVersion = serializers.CharField(required=False)
    ipInfo = IPInfoSerializer(required=False, allow_null=True)
    suspiciousCheck = SuspiciousCheckSerializer(required=False, allow_null=True)


class LogAggregationRequestSerializer(serializers.Serializer):
    """ログ集計リクエストのシリアライザ"""

    distributionId = serializers.CharField(required=True)
    startDate = serializers.DateField(required=True)
    endDate = serializers.DateField(required=True)
    groupBy = serializers.ChoiceField(
        choices=["ip", "user_agent", "referrer", "query_string"], required=True
    )
    startTime = serializers.TimeField(required=False, allow_null=True)
    endTime = serializers.TimeField(required=False, allow_null=True)
    limit = serializers.IntegerField(default=1000, min_value=1, max_value=10000)
    minCount = serializers.IntegerField(default=1, min_value=1)
    excludeStaticFiles = serializers.BooleanField(default=False, required=False)
    # フィルタフィールド
    clientIp = serializers.CharField(required=False, allow_blank=True)
    clientIps = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    uriPath = serializers.CharField(required=False, allow_blank=True)
    userAgent = serializers.CharField(required=False, allow_blank=True)
    referrer = serializers.CharField(required=False, allow_blank=True)
    queryString = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """日付範囲のバリデーション"""
        if data["startDate"] > data["endDate"]:
            raise serializers.ValidationError(
                "startDate must be before or equal to endDate"
            )
        return data


class GeoInfoSerializer(serializers.Serializer):
    """集計結果の地理情報のシリアライザ"""

    country = serializers.CharField(required=False, allow_null=True)
    country_code = serializers.CharField(required=False, allow_null=True)
    city = serializers.CharField(required=False, allow_null=True)


class SampleLogSerializer(serializers.Serializer):
    """集計結果のサンプルログエントリのシリアライザ"""

    date = serializers.CharField()
    time = serializers.CharField()
    uri = serializers.CharField()
    status = serializers.IntegerField()


class AggregationItemSerializer(serializers.Serializer):
    """単一の集計結果アイテムのシリアライザ"""

    value = serializers.CharField()
    request_count = serializers.IntegerField()
    percentage = serializers.FloatField()
    first_seen = serializers.DateTimeField()
    last_seen = serializers.DateTimeField()
    unique_paths = serializers.IntegerField()
    unique_user_agents = serializers.IntegerField(required=False)
    status_distribution = serializers.DictField()
    method_distribution = serializers.DictField()
    geo_info = GeoInfoSerializer(required=False, allow_null=True)
    sample_log = SampleLogSerializer(required=False, allow_null=True)


class DateRangeSerializer(serializers.Serializer):
    """日付範囲のシリアライザ"""

    start = serializers.DateTimeField()
    end = serializers.DateTimeField()


class LogAggregationResponseSerializer(serializers.Serializer):
    """ログ集計レスポンスのシリアライザ"""

    distribution_id = serializers.CharField()
    date_range = DateRangeSerializer()
    group_by = serializers.CharField()
    total_requests = serializers.IntegerField()
    unique_values = serializers.IntegerField()
    aggregations = AggregationItemSerializer(many=True)
