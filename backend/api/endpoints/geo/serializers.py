from rest_framework import serializers


class GeoLogsRequestSerializer(serializers.Serializer):
    """地理的ログ集計リクエストのシリアライザ。

    CloudFrontログを地理的に集計するためのリクエストパラメータを
    バリデーションします。日付と時刻の範囲を検証し、必須フィールドを
    確認します。

    Attributes:
        distributionId (CharField): CloudFrontディストリビューションID（必須）
        startDate (DateField): 開始日（必須、YYYY-MM-DD形式）
        endDate (DateField): 終了日（必須、YYYY-MM-DD形式）
        startTime (TimeField): 開始時刻（任意、HH:MM:SS形式）
        endTime (TimeField): 終了時刻（任意、HH:MM:SS形式）

    Example:
        バリデーション対象データ:
            {
                "distributionId": "E1234567890ABC",
                "startDate": "2025-11-01",
                "endDate": "2025-11-18",
                "startTime": "00:00:00",
                "endTime": "23:59:59"
            }

        使用例:
            >>> serializer = GeoLogsRequestSerializer(data=request_data)
            >>> if serializer.is_valid():
            >>>     validated_data = serializer.validated_data
    """

    distributionId = serializers.CharField(required=True)
    startDate = serializers.DateField(required=True)
    endDate = serializers.DateField(required=True)
    startTime = serializers.TimeField(required=False, allow_null=True)
    endTime = serializers.TimeField(required=False, allow_null=True)
