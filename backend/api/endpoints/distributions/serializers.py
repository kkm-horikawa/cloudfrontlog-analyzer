from rest_framework import serializers


class DistributionSerializer(serializers.Serializer):
    """CloudFront Distribution情報のシリアライザ。

    CloudFront Distributionの基本情報をシリアライズ/デシリアライズします。

    Attributes:
        id (str): Distribution ID（例: "E1234567890ABC"）
        domain (str): CloudFrontドメイン名（例: "d111111abcdef8.cloudfront.net"）
        aliases (List[str]): カスタムドメインエイリアスのリスト（オプション）

    Example:
        >>> data = {
        ...     "id": "E1234567890ABC",
        ...     "domain": "d111111abcdef8.cloudfront.net",
        ...     "aliases": ["example.com", "www.example.com"]
        ... }
        >>> serializer = DistributionSerializer(data=data)
        >>> serializer.is_valid()
        True
    """

    id = serializers.CharField()
    domain = serializers.CharField()
    aliases = serializers.ListField(child=serializers.CharField(), required=False)
