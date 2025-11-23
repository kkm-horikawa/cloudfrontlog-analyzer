from rest_framework import serializers


class CompanyInfoCheckRequestSerializer(serializers.Serializer):
    """企業情報ページチェックリクエストのシリアライザ。

    企業情報ページへのアクセスパターンをチェックするための
    リクエストパラメータをバリデーションします。

    Attributes:
        distributionId (CharField): CloudFrontディストリビューションID（必須）
        targetUrl (CharField): ターゲットURLパス（必須）
        companyInfoUrl (CharField): 企業情報ページURLパス（デフォルト: '/nattoku/about/'）

    Example:
        >>> data = {
        >>>     "distributionId": "E1234567890ABC",
        >>>     "targetUrl": "/nattoku/special/",
        >>>     "companyInfoUrl": "/nattoku/about/"
        >>> }
        >>> serializer = CompanyInfoCheckRequestSerializer(data=data)
        >>> serializer.is_valid()
    """

    distributionId = serializers.CharField(required=True)
    targetUrl = serializers.CharField(required=True)
    companyInfoUrl = serializers.CharField(default="/nattoku/about/")


class FrequentIPCheckRequestSerializer(serializers.Serializer):
    """頻繁なIPチェックリクエストのシリアライザ。

    特定のIPアドレスからの頻繁なアクセスをチェックするための
    リクエストパラメータをバリデーションします。

    Attributes:
        distributionId (CharField): CloudFrontディストリビューションID（必須）
        clientIp (CharField): チェックするIPアドレス（必須）
        days (IntegerField): 検索期間（日数）（デフォルト: 3、範囲: 1-30）

    Example:
        >>> data = {
        >>>     "distributionId": "E1234567890ABC",
        >>>     "clientIp": "1.2.3.4",
        >>>     "days": 3
        >>> }
        >>> serializer = FrequentIPCheckRequestSerializer(data=data)
        >>> serializer.is_valid()
    """

    distributionId = serializers.CharField(required=True)
    clientIp = serializers.CharField(required=True)
    days = serializers.IntegerField(default=3, min_value=1, max_value=30)


class MultiDeviceCheckRequestSerializer(serializers.Serializer):
    """マルチデバイスチェックリクエストのシリアライザ。

    同一IPアドレスからの複数デバイスタイプでのアクセスを
    チェックするためのリクエストパラメータをバリデーションします。

    Attributes:
        distributionId (CharField): CloudFrontディストリビューションID（必須）
        clientIp (CharField): チェックするIPアドレス（必須）
        days (IntegerField): 検索期間（日数）（デフォルト: 3、範囲: 1-30）

    Example:
        >>> data = {
        >>>     "distributionId": "E1234567890ABC",
        >>>     "clientIp": "1.2.3.4",
        >>>     "days": 10
        >>> }
        >>> serializer = MultiDeviceCheckRequestSerializer(data=data)
        >>> serializer.is_valid()
    """

    distributionId = serializers.CharField(required=True)
    clientIp = serializers.CharField(required=True)
    days = serializers.IntegerField(default=3, min_value=1, max_value=30)


class ResearchToolDetectionRequestSerializer(serializers.Serializer):
    """調査ツール検出リクエストのシリアライザ。

    ログから調査ツールのアクセスを検出するための
    リクエストパラメータをバリデーションします。

    Attributes:
        distributionId (CharField): CloudFrontディストリビューションID（必須）
        startDate (DateField): 開始日（必須、YYYY-MM-DD形式）
        endDate (DateField): 終了日（必須、YYYY-MM-DD形式）
        startTime (TimeField): 開始時刻（任意、HH:MM:SS形式）
        endTime (TimeField): 終了時刻（任意、HH:MM:SS形式）

    Example:
        >>> data = {
        >>>     "distributionId": "E1234567890ABC",
        >>>     "startDate": "2025-11-01",
        >>>     "endDate": "2025-11-18",
        >>>     "startTime": "00:00:00",
        >>>     "endTime": "23:59:59"
        >>> }
        >>> serializer = ResearchToolDetectionRequestSerializer(data=data)
        >>> serializer.is_valid()
    """

    distributionId = serializers.CharField(required=True)
    startDate = serializers.DateField(required=True)
    endDate = serializers.DateField(required=True)
    startTime = serializers.TimeField(required=False, allow_null=True)
    endTime = serializers.TimeField(required=False, allow_null=True)


class ResearchToolCheckRequestSerializer(serializers.Serializer):
    """調査ツールチェックリクエストのシリアライザ。

    User AgentとReferrerから調査ツールの署名を検出するための
    リクエストパラメータをバリデーションします。

    Attributes:
        userAgent (CharField): チェックするUser Agent文字列（必須）
        referrer (CharField): チェックするReferrer URL（任意）

    Example:
        >>> data = {
        >>>     "userAgent": "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
        >>>     "referrer": "https://www.google.com/"
        >>> }
        >>> serializer = ResearchToolCheckRequestSerializer(data=data)
        >>> serializer.is_valid()
    """

    userAgent = serializers.CharField(required=True)
    referrer = serializers.CharField(required=False, allow_blank=True)
