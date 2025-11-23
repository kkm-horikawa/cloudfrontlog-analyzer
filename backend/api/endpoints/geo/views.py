from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import GeoLogsRequestSerializer
from .services import GeoService


class GeoLogsView(APIView):
    """地理的に集計されたログを取得するAPIエンドポイント。

    CloudFrontのアクセスログを地理的位置情報（国、都市）で
    グループ化して集計します。マップ表示用のデータを提供し、
    各地域からのアクセス数とユニークIPカウントを返します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/geo/logs?distributionId=E1234567890ABC&startDate=2025-11-01&endDate=2025-11-18

        レスポンス:
            {
                "locations": [
                    {
                        "lat": 35.6895,
                        "lon": 139.6917,
                        "country": "Japan",
                        "countryCode": "JP",
                        "city": "Tokyo",
                        "requestCount": 1000,
                        "uniqueIpCount": 50,
                        "ips": ["1.2.3.4", "5.6.7.8"]
                    }
                ],
                "totalRequests": 1000,
                "totalUniqueIps": 50
            }
    """

    @extend_schema(
        summary="Get Geo-Aggregated Logs",
        description="Retrieves CloudFront logs aggregated by geographic location with IP counts",
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
                name="uriFilter",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by URI path (partial match, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="userAgentFilter",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by user agent (partial match, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="refererFilter",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by referer (partial match, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="queryFilter",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by query string (partial match, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="statusFilter",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by status code (exact match, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="methodFilter",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by HTTP method (exact match, optional)",
                required=False,
            ),
            OpenApiParameter(
                name="excludeStaticFiles",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Exclude static files (js, css, images, etc.) from aggregation (default: false)",
                default=False,
                required=False,
            ),
        ],
    )
    def get(self, request):
        """地理的に集計されたCloudFrontログを取得します。

        指定された期間のCloudFrontログを地理的位置情報で集計し、
        各地域からのアクセス数とユニークIPカウントを返します。
        フィルタ条件を指定してログを絞り込むことも可能です。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                - distributionId (str, required): CloudFrontディストリビューションID
                - startDate (str, required): 開始日 YYYY-MM-DD形式
                - endDate (str, required): 終了日 YYYY-MM-DD形式
                - startTime (str, optional): 開始時刻 JST (HH:MM:SS)
                - endTime (str, optional): 終了時刻 JST (HH:MM:SS)
                - uriFilter (str, optional): URIパスでフィルタ (部分一致)
                - userAgentFilter (str, optional): User Agentでフィルタ (部分一致)
                - refererFilter (str, optional): リファラーでフィルタ (部分一致)
                - queryFilter (str, optional): クエリ文字列でフィルタ (部分一致)
                - statusFilter (str, optional): ステータスコードでフィルタ (完全一致)
                - methodFilter (str, optional): HTTPメソッドでフィルタ (完全一致)
                - excludeStaticFiles (bool, optional): 静的ファイルを除外 (デフォルト: false)

        Returns:
            Response: JSONレスポンス
                成功時(200): 地理的集計データを含む辞書
                    - locations (list): 位置情報とアクセス統計のリスト
                    - totalRequests (int): 総リクエスト数
                    - totalUniqueIps (int): ユニークIP数
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Raises:
            ValueError: パラメータが無効な場合

        Example:
            >>> # GET /api/geo/logs?distributionId=E1234567890ABC&startDate=2025-11-01&endDate=2025-11-18
            >>> # Response: {"locations": [...], "totalRequests": 1000}
        """
        profile = request.query_params.get("profile", "default")

        # クエリパラメータからリクエストデータを構築
        request_data = {
            "distributionId": request.query_params.get("distributionId"),
            "startDate": request.query_params.get("startDate"),
            "endDate": request.query_params.get("endDate"),
            "startTime": request.query_params.get("startTime"),
            "endTime": request.query_params.get("endTime"),
        }

        # フィルタパラメータを取得
        uri_filter = request.query_params.get("uriFilter")
        user_agent_filter = request.query_params.get("userAgentFilter")
        referer_filter = request.query_params.get("refererFilter")
        query_filter = request.query_params.get("queryFilter")
        status_filter = request.query_params.get("statusFilter")
        method_filter = request.query_params.get("methodFilter")
        exclude_static_files = (
            request.query_params.get("excludeStaticFiles", "false").lower() == "true"
        )

        # リクエストデータのバリデーション
        request_serializer = GeoLogsRequestSerializer(data=request_data)
        if not request_serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = request_serializer.validated_data

        try:
            service = GeoService(profile_name=profile)

            result = service.get_geo_aggregated_logs(
                distribution_id=validated_data["distributionId"],
                start_date=validated_data["startDate"],
                end_date=validated_data["endDate"],
                start_time=str(validated_data.get("startTime"))
                if validated_data.get("startTime")
                else None,
                end_time=str(validated_data.get("endTime"))
                if validated_data.get("endTime")
                else None,
                uri_filter=uri_filter,
                user_agent_filter=user_agent_filter,
                referer_filter=referer_filter,
                query_filter=query_filter,
                status_filter=status_filter,
                method_filter=method_filter,
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
