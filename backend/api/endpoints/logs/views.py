from datetime import timezone

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.endpoints.security.suspicious_check import analyze_log_entries

from .serializers import LogAggregationRequestSerializer
from .serializers import LogAggregationResponseSerializer
from .serializers import LogEntrySerializer
from .serializers import LogSearchRequestSerializer
from .serializers import RawLogsListRequestSerializer
from .services import LogService


class LogSearchView(APIView):
    """CloudFrontログを検索するAPIエンドポイント。

    特定のURLと時間範囲でCloudFrontのアクセスログを検索します。
    一致するログエントリを返し、不審なアクティビティの分析結果も
    含めます。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            POST /api/logs/search?profile=default
            {
                "distributionId": "E1234567890ABC",
                "targetUrl": "/nattoku/special/",
                "dateTime": "2025-11-12T13:42:00+09:00",
                "timeWindowMinutes": 5
            }

        レスポンス:
            [
                {
                    "date": "2025-11-12",
                    "time": "04:40:00",
                    "clientIp": "1.2.3.4",
                    "method": "GET",
                    "uriStem": "/nattoku/special/",
                    "statusCode": 200,
                    "userAgent": "Mozilla/5.0...",
                    "referrer": "https://example.com",
                    "isSuspicious": false
                }
            ]
    """

    @extend_schema(
        summary="Search CloudFront Logs",
        description="Searches CloudFront access logs for a specific URL and time range. Returns matching log entries with suspicious activity analysis.",
        request=LogSearchRequestSerializer,
        parameters=[
            OpenApiParameter(
                name="profile",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AWS profile name",
                default="default",
            ),
        ],
        responses={200: LogEntrySerializer(many=True)},
        examples=[
            OpenApiExample(
                "Example Request",
                value={
                    "distributionId": "E1234567890ABC",
                    "targetUrl": "/nattoku/special/",
                    "targetDatetime": "2025-11-12T12:00:00+09:00",
                    "timeWindowMinutes": 5,
                },
            )
        ],
    )
    def post(self, request):
        """特定のURLと時間でCloudFrontログを検索します。

        指定されたURLとタイムウィンドウでログを検索し、
        不審なアクティビティの分析結果を付加して返します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                リクエストボディ:
                - distributionId (str, required): CloudFrontディストリビューションID
                - targetUrl (str, required): 検索するURLパス
                - dateTime (str, required): ターゲット日時 (ISO 8601形式)
                - timeWindowMinutes (int, optional): 時間範囲（分）（デフォルト: 5）

        Returns:
            Response: JSONレスポンス
                成功時(200): ログエントリのリスト
                    各エントリには不審度フラグ（isSuspicious）が付加
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Raises:
            ValueError: パラメータが無効な場合

        Example:
            >>> # POST /api/logs/search
            >>> # Body: {"distributionId": "E1234567890ABC", "targetUrl": "/path", ...}
            >>> # Response: [{"date": "2025-11-12", "clientIp": "1.2.3.4", ...}]
        """
        profile = request.query_params.get("profile", "default")

        # リクエストデータのバリデーション
        request_serializer = LogSearchRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = request_serializer.validated_data

        try:
            service = LogService(profile_name=profile)

            # 日時をUTCに変換
            dt = validated_data["dateTime"]
            utc_datetime = dt.astimezone(timezone.utc)

            log_entries = service.search_logs(
                distribution_id=validated_data["distributionId"],
                target_url=validated_data["targetUrl"],
                target_datetime=utc_datetime,
                time_window_minutes=validated_data.get("timeWindowMinutes", 5),
            )

            # ログエントリの不審なパターンを分析（現時点ではIP情報なし）
            log_entries = analyze_log_entries(log_entries)

            serializer = LogEntrySerializer(log_entries, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RawLogsListView(APIView):
    """ページネーション付きでCloudFront生ログを一覧表示するAPIエンドポイント。

    CloudFrontの生ログをページネーション付きで取得します。
    IPアドレス、URIパス、User Agent、リファラー、クエリ文字列など
    多様なフィルタ条件で絞り込みが可能です。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/logs/raw?distributionId=E1234567890ABC&startDate=2025-11-01&endDate=2025-11-18&page=1&perPage=1000

        レスポンス:
            {
                "logs": [
                    {
                        "date": "2025-11-12",
                        "time": "04:40:00",
                        "clientIp": "1.2.3.4",
                        "method": "GET",
                        "uriStem": "/path/to/resource",
                        "statusCode": 200,
                        "userAgent": "Mozilla/5.0...",
                        "referrer": "https://example.com"
                    }
                ],
                "total": 5000,
                "page": 1,
                "perPage": 1000,
                "totalPages": 5
            }
    """

    @extend_schema(
        summary="List Raw CloudFront Logs",
        description="Retrieves raw CloudFront logs with pagination and optional filtering by IP address and URI path",
        parameters=[
            OpenApiParameter(
                name="profile",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AWS profile name",
                default="default",
            ),
            OpenApiParameter(
                name="distributionId",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="CloudFront distribution ID",
                required=True,
            ),
            OpenApiParameter(
                name="startDate",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date (YYYY-MM-DD)",
                required=True,
            ),
            OpenApiParameter(
                name="endDate",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date (YYYY-MM-DD)",
                required=True,
            ),
            OpenApiParameter(
                name="startTime",
                type=OpenApiTypes.TIME,
                location=OpenApiParameter.QUERY,
                description="Start time in JST (HH:MM:SS, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="endTime",
                type=OpenApiTypes.TIME,
                location=OpenApiParameter.QUERY,
                description="End time in JST (HH:MM:SS, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="clientIp",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by client IP address (optional)",
                required=False,
            ),
            OpenApiParameter(
                name="uriPath",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by URI path (optional)",
                required=False,
            ),
            OpenApiParameter(
                name="userAgent",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by User Agent (optional, exact match)",
                required=False,
            ),
            OpenApiParameter(
                name="referrer",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by referrer (optional, partial match)",
                required=False,
            ),
            OpenApiParameter(
                name="queryString",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by query string (optional, partial match)",
                required=False,
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number (default: 1)",
                default=1,
            ),
            OpenApiParameter(
                name="perPage",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of logs per page (default: 1000, max: 10000)",
                default=1000,
            ),
            OpenApiParameter(
                name="excludeStaticFiles",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Exclude static files (js, css, images, etc.) from results (default: false)",
                default=False,
                required=False,
            ),
        ],
        responses={200: LogEntrySerializer(many=True)},
    )
    def get(self, request):
        """ページネーション付きでCloudFront生ログを一覧表示します。

        指定された期間のCloudFront生ログをページネーション付きで取得します。
        多様なフィルタ条件で絞り込みが可能で、大量のログを効率的に参照できます。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                - distributionId (str, required): CloudFrontディストリビューションID
                - startDate (str, required): 開始日 YYYY-MM-DD形式
                - endDate (str, required): 終了日 YYYY-MM-DD形式
                - startTime (str, optional): 開始時刻 JST (HH:MM:SS)
                - endTime (str, optional): 終了時刻 JST (HH:MM:SS)
                - clientIp (str, optional): クライアントIPアドレスでフィルタ
                - uriPath (str, optional): URIパスでフィルタ
                - userAgent (str, optional): User Agentでフィルタ (完全一致)
                - referrer (str, optional): リファラーでフィルタ (部分一致)
                - queryString (str, optional): クエリ文字列でフィルタ (部分一致)
                - page (int, optional): ページ番号 (デフォルト: 1)
                - perPage (int, optional): 1ページあたりのログ数 (デフォルト: 1000、最大: 10000)
                - excludeStaticFiles (bool, optional): 静的ファイルを除外 (デフォルト: false)

        Returns:
            Response: JSONレスポンス
                成功時(200): ページネーション情報とログリストを含む辞書
                    - logs (list): ログエントリのリスト
                    - total (int): 総ログ数
                    - page (int): 現在のページ番号
                    - perPage (int): 1ページあたりのログ数
                    - totalPages (int): 総ページ数
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Raises:
            ValueError: パラメータが無効な場合

        Example:
            >>> # GET /api/logs/raw?distributionId=E1234567890ABC&startDate=2025-11-01&endDate=2025-11-18
            >>> # Response: {"logs": [...], "total": 5000, "page": 1, "perPage": 1000}
        """
        profile = request.query_params.get("profile", "default")

        # clientIpsパラメータ（カンマ区切りリスト）を処理
        client_ips_param = request.query_params.get("clientIps", "")
        client_ips = (
            [ip.strip() for ip in client_ips_param.split(",") if ip.strip()]
            if client_ips_param
            else []
        )

        # クエリパラメータからリクエストデータを構築
        request_data = {
            "distributionId": request.query_params.get("distributionId"),
            "startDate": request.query_params.get("startDate"),
            "endDate": request.query_params.get("endDate"),
            "startTime": request.query_params.get("startTime"),
            "endTime": request.query_params.get("endTime"),
            "clientIp": request.query_params.get("clientIp", ""),
            "clientIps": client_ips,
            "uriPath": request.query_params.get("uriPath", ""),
            "userAgent": request.query_params.get("userAgent", ""),
            "referrer": request.query_params.get("referrer", ""),
            "queryString": request.query_params.get("queryString", ""),
            "page": request.query_params.get("page", 1),
            "perPage": request.query_params.get("perPage", 1000),
        }

        exclude_static_files = (
            request.query_params.get("excludeStaticFiles", "false").lower() == "true"
        )

        # リクエストデータのバリデーション
        request_serializer = RawLogsListRequestSerializer(data=request_data)
        if not request_serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = request_serializer.validated_data

        try:
            service = LogService(profile_name=profile)

            result = service.list_raw_logs(
                distribution_id=validated_data["distributionId"],
                start_date=validated_data["startDate"],
                end_date=validated_data["endDate"],
                start_time=str(validated_data.get("startTime"))
                if validated_data.get("startTime")
                else None,
                end_time=str(validated_data.get("endTime"))
                if validated_data.get("endTime")
                else None,
                client_ip=validated_data.get("clientIp") or None,
                client_ips=validated_data.get("clientIps") or None,
                uri_path=validated_data.get("uriPath") or None,
                user_agent=validated_data.get("userAgent") or None,
                referrer=validated_data.get("referrer") or None,
                query_string=validated_data.get("queryString") or None,
                page=validated_data["page"],
                per_page=validated_data["perPage"],
                exclude_static_files=exclude_static_files,
            )

            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LogAggregationView(APIView):
    """様々なグルーピングキーでCloudFrontログを集計するAPIエンドポイント。

    CloudFrontログをIPアドレス、User Agent、リファラー、クエリ文字列など
    様々なキーでグループ化して集計します。上位N件の統計情報を返します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/logs/aggregate?distributionId=E1234567890ABC&startDate=2025-11-01&endDate=2025-11-18&groupBy=ip&limit=100

        レスポンス:
            {
                "aggregations": [
                    {
                        "key": "1.2.3.4",
                        "count": 500,
                        "percentage": 10.0
                    },
                    {
                        "key": "5.6.7.8",
                        "count": 300,
                        "percentage": 6.0
                    }
                ],
                "total": 5000,
                "groupBy": "ip",
                "uniqueCount": 100
            }
    """

    @extend_schema(
        summary="Aggregate CloudFront Logs",
        description="Aggregates CloudFront access logs by IP address, User Agent, Referrer, or Query String. Returns statistics and top N entries.",
        parameters=[
            OpenApiParameter(
                name="profile",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AWS profile name",
                default="default",
            ),
            OpenApiParameter(
                name="distributionId",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="CloudFront distribution ID",
                required=True,
            ),
            OpenApiParameter(
                name="startDate",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date (YYYY-MM-DD)",
                required=True,
            ),
            OpenApiParameter(
                name="endDate",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date (YYYY-MM-DD)",
                required=True,
            ),
            OpenApiParameter(
                name="groupBy",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Grouping key (ip, user_agent, referrer, query_string)",
                required=True,
                enum=["ip", "user_agent", "referrer", "query_string"],
            ),
            OpenApiParameter(
                name="startTime",
                type=OpenApiTypes.TIME,
                location=OpenApiParameter.QUERY,
                description="Start time in JST (HH:MM:SS, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="endTime",
                type=OpenApiTypes.TIME,
                location=OpenApiParameter.QUERY,
                description="End time in JST (HH:MM:SS, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Maximum number of aggregation results (default: 1000, max: 10000)",
                default=1000,
            ),
            OpenApiParameter(
                name="minCount",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Minimum request count filter (default: 1)",
                default=1,
            ),
            OpenApiParameter(
                name="excludeStaticFiles",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Exclude static files (js, css, images, etc.) from aggregation (default: false)",
                default=False,
                required=False,
            ),
            OpenApiParameter(
                name="clientIp",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by client IP address (optional)",
                required=False,
            ),
            OpenApiParameter(
                name="uriPath",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by URI path (optional, partial match)",
                required=False,
            ),
            OpenApiParameter(
                name="userAgent",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by User Agent (optional, exact match)",
                required=False,
            ),
            OpenApiParameter(
                name="referrer",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by referrer (optional, partial match)",
                required=False,
            ),
            OpenApiParameter(
                name="queryString",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by query string (optional, partial match)",
                required=False,
            ),
        ],
        responses={200: LogAggregationResponseSerializer},
    )
    def get(self, request):
        """CloudFrontログを集計します。

        指定されたグルーピングキーでログを集計し、
        上位N件の統計情報と全体の集計結果を返します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                - distributionId (str, required): CloudFrontディストリビューションID
                - startDate (str, required): 開始日 YYYY-MM-DD形式
                - endDate (str, required): 終了日 YYYY-MM-DD形式
                - groupBy (str, required): グルーピングキー (ip, user_agent, referrer, query_string)
                - startTime (str, optional): 開始時刻 JST (HH:MM:SS)
                - endTime (str, optional): 終了時刻 JST (HH:MM:SS)
                - limit (int, optional): 最大結果数 (デフォルト: 100000、最大: 1000000)
                - minCount (int, optional): 最小リクエスト数フィルタ (デフォルト: 1)
                - excludeStaticFiles (bool, optional): 静的ファイルを除外 (デフォルト: false)

        Returns:
            Response: JSONレスポンス
                成功時(200): 集計データを含む辞書
                    - aggregations (list): キーごとの集計結果リスト
                    - total (int): 総リクエスト数
                    - groupBy (str): 使用したグルーピングキー
                    - uniqueCount (int): ユニークなキーの数
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Raises:
            ValueError: パラメータが無効な場合

        Example:
            >>> # GET /api/logs/aggregate?distributionId=E1234567890ABC&startDate=2025-11-01&endDate=2025-11-18&groupBy=ip
            >>> # Response: {"aggregations": [...], "total": 5000, "groupBy": "ip"}
        """
        profile = request.query_params.get("profile", "default")

        # clientIpsパラメータ（カンマ区切りリスト）を処理
        client_ips_param = request.query_params.get("clientIps", "")
        client_ips = (
            [ip.strip() for ip in client_ips_param.split(",") if ip.strip()]
            if client_ips_param
            else []
        )

        # クエリパラメータからリクエストデータを構築
        request_data = {
            "distributionId": request.query_params.get("distributionId"),
            "startDate": request.query_params.get("startDate"),
            "endDate": request.query_params.get("endDate"),
            "groupBy": request.query_params.get("groupBy"),
            "startTime": request.query_params.get("startTime"),
            "endTime": request.query_params.get("endTime"),
            "limit": request.query_params.get("limit", 100000),
            "minCount": request.query_params.get("minCount", 1),
            "clientIp": request.query_params.get("clientIp", ""),
            "clientIps": client_ips,
            "uriPath": request.query_params.get("uriPath", ""),
            "userAgent": request.query_params.get("userAgent", ""),
            "referrer": request.query_params.get("referrer", ""),
            "queryString": request.query_params.get("queryString", ""),
        }

        # excludeStaticFilesは別途処理（Serializerに含めない）
        exclude_static_files = (
            request.query_params.get("excludeStaticFiles", "false").lower() == "true"
        )

        # リクエストデータのバリデーション
        request_serializer = LogAggregationRequestSerializer(data=request_data)
        if not request_serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = request_serializer.validated_data

        try:
            service = LogService(profile_name=profile)

            result = service.aggregate_logs(
                distribution_id=validated_data["distributionId"],
                start_date=validated_data["startDate"],
                end_date=validated_data["endDate"],
                group_by=validated_data["groupBy"],
                start_time=str(validated_data.get("startTime"))
                if validated_data.get("startTime")
                else None,
                end_time=str(validated_data.get("endTime"))
                if validated_data.get("endTime")
                else None,
                limit=validated_data["limit"],
                min_count=validated_data["minCount"],
                exclude_static_files=exclude_static_files,
                client_ip=validated_data.get("clientIp") or None,
                client_ips=validated_data.get("clientIps") or None,
                uri_path=validated_data.get("uriPath") or None,
                user_agent=validated_data.get("userAgent") or None,
                referrer=validated_data.get("referrer") or None,
                query_string=validated_data.get("queryString") or None,
            )

            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
