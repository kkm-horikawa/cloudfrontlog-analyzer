"""
CloudFrontログの高度なセキュリティチェックエンドポイント
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CompanyInfoCheckRequestSerializer
from .serializers import FrequentIPCheckRequestSerializer
from .serializers import MultiDeviceCheckRequestSerializer
from .serializers import ResearchToolCheckRequestSerializer
from api.endpoints.logs.services import LogService
from .suspicious_check import BLOCKED_ARCHIVE_TOOLS_UA
from .suspicious_check import BLOCKED_MINOR_SEARCH_ENGINES_UA
from .suspicious_check import BLOCKED_OTHER_TOOLS_UA
from .suspicious_check import BLOCKED_REFERRER
from .suspicious_check import BLOCKED_SCRAPING_TOOLS_UA
from .suspicious_check import BLOCKED_SEO_TOOLS_UA
from .suspicious_check import SUSPICIOUS_UA
from .suspicious_check import detect_device_type


class CompanyInfoAccessCheckView(APIView):
    """企業情報ページがターゲットURLからのリファラーを持つかをチェックするAPIエンドポイント。

    特定のページを閲覧した後に企業情報ページにアクセスするパターンを検出します。
    過去3日間のログから、ターゲットURLをリファラーとして持つ企業情報ページへの
    アクセスを検索し、不審なアクセスパターンを分析します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            POST /api/security/check/company-info
            {
                "distributionId": "E1234567890ABC",
                "targetUrl": "/nattoku/special/",
                "companyInfoUrl": "/nattoku/about/"
            }

        レスポンス:
            {
                "checkType": "company_info_access",
                "criteria": {
                    "targetUrl": "/nattoku/special/",
                    "companyInfoUrl": "/nattoku/about/",
                    "period": "3 days"
                },
                "result": {
                    "isSuspicious": true,
                    "totalAccessCount": 100,
                    "suspiciousAccessCount": 5,
                    "description": "Found 5 accesses to company info page with referrer from target URL"
                },
                "details": [...]
            }
    """

    @extend_schema(
        summary="Company Info Page Access Check",
        description="Checks if the company info page (/nattoku/about/) has been accessed with a referrer from the target URL within the past 3 days",
        request=CompanyInfoCheckRequestSerializer,
        parameters=[
            OpenApiParameter(
                name="profile",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AWS profile name",
                default="default",
            ),
        ],
        examples=[
            OpenApiExample(
                "Example Request",
                value={
                    "distributionId": "E1234567890ABC",
                    "targetUrl": "/nattoku/special/",
                    "companyInfoUrl": "/nattoku/about/",
                },
            )
        ],
    )
    def post(self, request):
        """企業情報ページのアクセスパターンをチェックします。

        過去3日間のログから、ターゲットURLをリファラーとして持つ
        企業情報ページへのアクセスを検索し、不審なパターンを検出します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                リクエストボディ:
                - distributionId (str, required): CloudFrontディストリビューションID
                - targetUrl (str, required): ターゲットURLパス
                - companyInfoUrl (str, optional): 企業情報ページURLパス (デフォルト: '/nattoku/about/')

        Returns:
            Response: JSONレスポンス
                成功時(200): チェック結果を含む辞書
                    - checkType (str): チェックタイプ
                    - criteria (dict): チェック条件
                    - result (dict): チェック結果とサマリー
                    - details (list): 不審なアクセスの詳細リスト
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # POST /api/security/check/company-info
            >>> # Body: {"distributionId": "E1234567890ABC", "targetUrl": "/nattoku/special/"}
            >>> # Response: {"checkType": "company_info_access", "result": {...}}
        """
        profile = request.query_params.get("profile", "default")

        serializer = CompanyInfoCheckRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data

        try:
            service = LogService(profile_name=profile)

            # 過去3日間のログを取得
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=3)

            # 企業情報ページへのアクセスを検索
            company_info_logs = service.search_logs_by_path(
                distribution_id=validated_data["distributionId"],
                uri_path=validated_data["companyInfoUrl"],
                start_time=start_time,
                end_time=end_time,
            )

            # リファラーがターゲットURLに一致するログをフィルタ（クエリパラメータを含む）
            suspicious_accesses = []
            target_url = validated_data["targetUrl"]

            for log in company_info_logs:
                referrer = log.get("referrer", "-")
                if referrer == "-":
                    continue

                # リファラーからパスを抽出（プロトコルとドメインを除去）
                # 例: "https://defaulttech.co.jp/nattoku/special/91265/77164/?param=value"
                # -> "/nattoku/special/91265/77164/?param=value"
                try:
                    from urllib.parse import urlparse

                    parsed = urlparse(referrer)
                    referrer_path = parsed.path
                    if parsed.query:
                        referrer_path += "?" + parsed.query

                    # リファラーパスがターゲットURLで始まるかをチェック
                    # これにより、基本パスが一致することを確保しながらクエリパラメータの変動を許可
                    if referrer_path.startswith(target_url):
                        suspicious_accesses.append(
                            {
                                "date": log.get("date"),
                                "time": log.get("time"),
                                "clientIp": log.get("clientIp"),
                                "referrer": referrer,
                                "userAgent": log.get("userAgent"),
                                "statusCode": log.get("statusCode"),
                            }
                        )
                except Exception:
                    # パースに失敗した場合、このエントリをスキップ
                    continue

            return Response(
                {
                    "checkType": "company_info_access",
                    "criteria": {
                        "targetUrl": target_url,
                        "companyInfoUrl": validated_data["companyInfoUrl"],
                        "period": "3 days",
                    },
                    "result": {
                        "isSuspicious": len(suspicious_accesses) > 0,
                        "totalAccessCount": len(company_info_logs),
                        "suspiciousAccessCount": len(suspicious_accesses),
                        "description": f"Found {len(suspicious_accesses)} accesses to company info page with referrer from target URL",
                    },
                    "details": suspicious_accesses,
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FrequentIPAccessCheckView(APIView):
    """同一IPからの頻繁なアクセスをチェックするAPIエンドポイント。

    特定のIPアドレスからの過去N日間のアクセスパターンを分析します。
    静的ファイルを除外して、実際のページアクセスのみを対象とし、
    URLごとのアクセス頻度を集計して不審なパターンを検出します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            POST /api/security/check/frequent-ip
            {
                "distributionId": "E1234567890ABC",
                "clientIp": "1.2.3.4",
                "days": 3
            }

        レスポンス:
            {
                "checkType": "frequent_ip_access",
                "criteria": {
                    "clientIp": "1.2.3.4",
                    "period": "3 days",
                    "threshold": "Multiple accesses to same URLs"
                },
                "result": {
                    "isSuspicious": true,
                    "totalAccessCount": 500,
                    "uniqueUrlsAccessed": 50,
                    "description": "IP accessed 50 unique URLs 500 times in the past 3 days"
                },
                "details": [...]
            }
    """

    @extend_schema(
        summary="Frequent IP Access Check",
        description="Analyzes access patterns from a specific IP address over the past N days (default: 3 days). Excludes static files.",
        request=FrequentIPCheckRequestSerializer,
        parameters=[
            OpenApiParameter(
                name="profile",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AWS profile name",
                default="default",
            ),
        ],
        examples=[
            OpenApiExample(
                "Example Request",
                value={
                    "distributionId": "E1234567890ABC",
                    "clientIp": "1.2.3.4",
                    "days": 3,
                },
            )
        ],
    )
    def post(self, request):
        """頻繁なIPアクセスパターンをチェックします。

        特定のIPアドレスからの過去N日間のアクセスを分析し、
        URLごとのアクセス頻度を集計して不審なパターンを検出します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                リクエストボディ:
                - distributionId (str, required): CloudFrontディストリビューションID
                - clientIp (str, required): チェックするIPアドレス
                - days (int, optional): 検索期間（日数）（デフォルト: 3、範囲: 1-30）

        Returns:
            Response: JSONレスポンス
                成功時(200): チェック結果を含む辞書
                    - checkType (str): チェックタイプ
                    - criteria (dict): チェック条件
                    - result (dict): チェック結果とサマリー
                    - details (list): URLごとのアクセス詳細（上位20件）
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # POST /api/security/check/frequent-ip
            >>> # Body: {"distributionId": "E1234567890ABC", "clientIp": "1.2.3.4", "days": 3}
            >>> # Response: {"checkType": "frequent_ip_access", "result": {...}}
        """
        profile = request.query_params.get("profile", "default")

        serializer = FrequentIPCheckRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data

        try:
            service = LogService(profile_name=profile)

            # 過去N日間のログを取得
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=validated_data["days"])

            # このIPからの全アクセスを検索
            ip_logs = service.search_logs_by_ip(
                distribution_id=validated_data["distributionId"],
                client_ip=validated_data["clientIp"],
                start_time=start_time,
                end_time=end_time,
            )

            # URLごとにグループ化してカウント（静的ファイルを除く）
            url_counts = {}
            for log in ip_logs:
                uri = log.get("uriStem", "")
                # 静的ファイル（/media/、/static/、/assets/など）をスキップ
                if (
                    "/media/" in uri
                    or "/static/" in uri
                    or "/assets/" in uri
                    or uri.endswith(
                        (
                            ".css",
                            ".js",
                            ".jpg",
                            ".jpeg",
                            ".png",
                            ".gif",
                            ".svg",
                            ".ico",
                            ".woff",
                            ".woff2",
                            ".ttf",
                            ".eot",
                            ".webp",
                            ".avif",
                        )
                    )
                ):
                    continue
                if uri not in url_counts:
                    url_counts[uri] = []
                url_counts[uri].append(
                    {
                        "date": log.get("date"),
                        "time": log.get("time"),
                        "statusCode": log.get("statusCode"),
                        "userAgent": log.get("userAgent"),
                    }
                )

            # 頻度でソート
            sorted_urls = sorted(
                url_counts.items(), key=lambda x: len(x[1]), reverse=True
            )

            return Response(
                {
                    "checkType": "frequent_ip_access",
                    "criteria": {
                        "clientIp": validated_data["clientIp"],
                        "period": f"{validated_data['days']} days",
                        "threshold": "Multiple accesses to same URLs",
                    },
                    "result": {
                        "isSuspicious": len(ip_logs) > 10,
                        "totalAccessCount": len(ip_logs),
                        "uniqueUrlsAccessed": len(url_counts),
                        "description": f"IP accessed {len(url_counts)} unique URLs {len(ip_logs)} times in the past {validated_data['days']} days",
                    },
                    "details": [
                        {
                            "url": url,
                            "accessCount": len(accesses),
                            "accesses": accesses[:10],  # Limit to first 10 for display
                        }
                        for url, accesses in sorted_urls[:20]  # Top 20 URLs
                    ],
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MultiDeviceAccessCheckView(APIView):
    """同一IPが複数のデバイスタイプを使用しているかをチェックするAPIエンドポイント。

    同一IPアドレスから複数のデバイスタイプ（モバイル、デスクトップ等）で
    アクセスしているパターンを検出します。過去N日間のUser Agentを解析し、
    デバイスタイプごとのアクセスを集計します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            POST /api/security/check/multi-device
            {
                "distributionId": "E1234567890ABC",
                "clientIp": "1.2.3.4",
                "days": 3
            }

        レスポンス:
            {
                "checkType": "multi_device_access",
                "criteria": {
                    "clientIp": "1.2.3.4",
                    "period": "3 days",
                    "threshold": "Accesses from multiple device types (mobile, desktop)"
                },
                "result": {
                    "isSuspicious": true,
                    "totalAccessCount": 200,
                    "deviceTypesDetected": ["mobile", "desktop"],
                    "realDeviceTypes": ["mobile", "desktop"],
                    "description": "IP accessed from 2 different device types: mobile, desktop"
                },
                "details": {...}
            }
    """

    @extend_schema(
        summary="Multi-Device Access Check",
        description="Detects if the same IP address has been used to access from multiple device types (mobile + desktop) within the past N days (default: 3 days)",
        request=MultiDeviceCheckRequestSerializer,
        parameters=[
            OpenApiParameter(
                name="profile",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AWS profile name",
                default="default",
            ),
        ],
        examples=[
            OpenApiExample(
                "Example Request",
                value={
                    "distributionId": "E1234567890ABC",
                    "clientIp": "1.2.3.4",
                    "days": 3,
                },
            )
        ],
    )
    def post(self, request):
        """マルチデバイスアクセスパターンをチェックします。

        同一IPアドレスから複数のデバイスタイプでアクセスしている
        パターンを検出し、不審なアクティビティを分析します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                リクエストボディ:
                - distributionId (str, required): CloudFrontディストリビューションID
                - clientIp (str, required): チェックするIPアドレス
                - days (int, optional): 検索期間（日数）（デフォルト: 3、範囲: 1-30）

        Returns:
            Response: JSONレスポンス
                成功時(200): チェック結果を含む辞書
                    - checkType (str): チェックタイプ
                    - criteria (dict): チェック条件
                    - result (dict): チェック結果とサマリー
                    - details (dict): デバイスタイプごとのアクセス詳細
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # POST /api/security/check/multi-device
            >>> # Body: {"distributionId": "E1234567890ABC", "clientIp": "1.2.3.4", "days": 3}
            >>> # Response: {"checkType": "multi_device_access", "result": {...}}
        """
        profile = request.query_params.get("profile", "default")

        serializer = MultiDeviceCheckRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data

        try:
            service = LogService(profile_name=profile)

            # 過去N日間のログを取得
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=validated_data["days"])

            # このIPからの全アクセスを検索
            ip_logs = service.search_logs_by_ip(
                distribution_id=validated_data["distributionId"],
                client_ip=validated_data["clientIp"],
                start_time=start_time,
                end_time=end_time,
            )

            # デバイスタイプごとにグループ化
            device_types = {}
            for log in ip_logs:
                user_agent = log.get("userAgent", "")
                device_type = detect_device_type(user_agent)

                if device_type not in device_types:
                    device_types[device_type] = []

                device_types[device_type].append(
                    {
                        "date": log.get("date"),
                        "time": log.get("time"),
                        "userAgent": user_agent,
                        "uriStem": log.get("uriStem"),
                        "statusCode": log.get("statusCode"),
                    }
                )

            # 複数の実デバイスタイプがあるかをチェック（botとunknownを除く）
            real_devices = {
                k: v for k, v in device_types.items() if k not in ["bot", "unknown"]
            }
            is_suspicious = len(real_devices) > 1

            return Response(
                {
                    "checkType": "multi_device_access",
                    "criteria": {
                        "clientIp": validated_data["clientIp"],
                        "period": f"{validated_data['days']} days",
                        "threshold": "Accesses from multiple device types (mobile, desktop)",
                    },
                    "result": {
                        "isSuspicious": is_suspicious,
                        "totalAccessCount": len(ip_logs),
                        "deviceTypesDetected": list(device_types.keys()),
                        "realDeviceTypes": list(real_devices.keys()),
                        "description": f"IP accessed from {len(real_devices)} different device types: {', '.join(real_devices.keys())}"
                        if is_suspicious
                        else "Single device type detected",
                    },
                    "details": {
                        device_type: {
                            "count": len(accesses),
                            "samples": accesses[:5],  # First 5 samples
                        }
                        for device_type, accesses in device_types.items()
                    },
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ResearchToolDetectionCheckView(APIView):
    """User AgentまたはReferrerに調査ツールの署名が含まれているかをチェックするAPIエンドポイント。

    User AgentとReferrerヘッダーから、アーカイブツール、スクレイピングツール、
    SEOボット、その他の調査ツールの署名を検出します。既知のパターンと
    照合して不審なアクセスを識別します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            POST /api/security/check/research-tool
            {
                "userAgent": "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
                "referrer": "https://www.google.com/"
            }

        レスポンス:
            {
                "checkType": "research_tool_detection",
                "criteria": {
                    "patterns": [
                        "Archive tools (archive.org, Megalodon, PagePeeker)",
                        "Scraping tools (Python, Java, Scrapy, etc.)",
                        "SEO tools (SemrushBot, AhrefsBot, etc.)",
                        "Other tools (MTRobot, PostmanRuntime, etc.)",
                        "Minor search engines (PetalBot, YandexBot, etc.)",
                        "Suspicious patterns (Line, PhantomJS, Excel)",
                        "Blocked referrer domains"
                    ]
                },
                "result": {
                    "isSuspicious": true,
                    "matchedPatternCount": 1,
                    "description": "Research tool or suspicious pattern detected"
                },
                "details": {
                    "userAgent": "Mozilla/5.0 (compatible; SemrushBot/7~bl; ...)",
                    "referrer": "https://www.google.com/",
                    "matchedPatterns": ["SEO Tool detected in User Agent"]
                }
            }
    """

    @extend_schema(
        summary="Research Tool Detection Check",
        description="Detects research tools, scrapers, SEO bots, and other suspicious tools in User-Agent and Referrer headers",
        request=ResearchToolCheckRequestSerializer,
        examples=[
            OpenApiExample(
                "Example Request",
                value={
                    "userAgent": "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
                    "referrer": "https://www.google.com/",
                },
            )
        ],
    )
    def post(self, request):
        """調査ツールの署名をチェックします。

        User AgentとReferrerヘッダーから既知の調査ツールや
        不審なパターンを検出します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                リクエストボディ:
                - userAgent (str, required): チェックするUser Agent文字列
                - referrer (str, optional): チェックするReferrer URL

        Returns:
            Response: JSONレスポンス
                成功時(200): チェック結果を含む辞書
                    - checkType (str): チェックタイプ
                    - criteria (dict): チェックパターンのリスト
                    - result (dict): チェック結果とサマリー
                    - details (dict): 一致したパターンの詳細
                エラー時(400): バリデーションエラーメッセージ

        Example:
            >>> # POST /api/security/check/research-tool
            >>> # Body: {"userAgent": "Mozilla/5.0 (compatible; SemrushBot/...)", "referrer": "..."}
            >>> # Response: {"checkType": "research_tool_detection", "result": {...}}
        """
        serializer = ResearchToolCheckRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        user_agent = validated_data["userAgent"]
        referrer = validated_data.get("referrer", "")

        matched_patterns = []

        # User Agentのパターンをチェック
        if BLOCKED_ARCHIVE_TOOLS_UA.search(user_agent):
            matched_patterns.append("Archive Tool detected in User Agent")

        if BLOCKED_SCRAPING_TOOLS_UA.search(user_agent):
            matched_patterns.append("Scraping Tool detected in User Agent")

        if BLOCKED_SEO_TOOLS_UA.search(user_agent):
            matched_patterns.append("SEO Tool detected in User Agent")

        if BLOCKED_OTHER_TOOLS_UA.search(user_agent):
            matched_patterns.append("Other suspicious tool detected in User Agent")

        if BLOCKED_MINOR_SEARCH_ENGINES_UA.search(user_agent):
            matched_patterns.append("Minor search engine bot detected in User Agent")

        if SUSPICIOUS_UA.search(user_agent):
            matched_patterns.append("Suspicious pattern detected in User Agent")

        # Referrerのパターンをチェック
        if referrer and BLOCKED_REFERRER.search(referrer):
            matched_patterns.append("Blocked domain detected in Referrer")

        is_suspicious = len(matched_patterns) > 0

        return Response(
            {
                "checkType": "research_tool_detection",
                "criteria": {
                    "patterns": [
                        "Archive tools (archive.org, Megalodon, PagePeeker)",
                        "Scraping tools (Python, Java, Scrapy, etc.)",
                        "SEO tools (SemrushBot, AhrefsBot, etc.)",
                        "Other tools (MTRobot, PostmanRuntime, etc.)",
                        "Minor search engines (PetalBot, YandexBot, etc.)",
                        "Suspicious patterns (Line, PhantomJS, Excel)",
                        "Blocked referrer domains",
                    ],
                },
                "result": {
                    "isSuspicious": is_suspicious,
                    "matchedPatternCount": len(matched_patterns),
                    "description": "Research tool or suspicious pattern detected"
                    if is_suspicious
                    else "No suspicious patterns detected",
                },
                "details": {
                    "userAgent": user_agent,
                    "referrer": referrer if referrer else "N/A",
                    "matchedPatterns": matched_patterns,
                },
            }
        )
