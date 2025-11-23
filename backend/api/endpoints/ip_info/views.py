from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_ip_info


class IPInfoView(APIView):
    """IP位置情報を取得するAPIエンドポイント。

    指定されたIPアドレスの詳細な地理的位置情報を
    ip-api.comから取得します。国、都市、ISP、組織、
    ASN情報に加え、モバイル/プロキシ/ホスティングの
    フラグも提供します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/ip-info/1.2.3.4

        レスポンス:
            {
                "ip": "1.2.3.4",
                "continent": "Asia",
                "continentCode": "AS",
                "country": "Japan",
                "countryCode": "JP",
                "region": "Tokyo",
                "city": "Tokyo",
                "lat": 35.6895,
                "lon": 139.6917,
                "isp": "Example ISP",
                "org": "Example Organization",
                "asn": "AS1234",
                "mobile": false,
                "proxy": false,
                "hosting": false
            }
    """

    @extend_schema(
        summary="Get IP Geolocation Info",
        description="Retrieves geolocation information for a specific IP address using ip-api.com. Includes continent, country, city, ISP, and flags for mobile/proxy/hosting.",
        parameters=[
            OpenApiParameter(
                name="ip_address",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="IP address to lookup (e.g., 1.2.3.4)",
                required=True,
            ),
        ],
    )
    def get(self, request, ip_address):
        """特定のIPアドレスのIP位置情報を取得します。

        ip-api.comを使用して、指定されたIPアドレスの詳細な
        地理的位置情報とネットワーク情報を取得します。

        Args:
            request (Request): HTTPリクエストオブジェクト
            ip_address (str): 検索するIPアドレス（パスパラメータ）

        Returns:
            Response: JSONレスポンス
                成功時(200): IP位置情報を含む辞書
                    - ip (str): IPアドレス
                    - continent (str): 大陸名
                    - country (str): 国名
                    - city (str): 都市名
                    - lat (float): 緯度
                    - lon (float): 経度
                    - isp (str): ISP名
                    - org (str): 組織名
                    - asn (str): AS番号
                    - mobile (bool): モバイル接続フラグ
                    - proxy (bool): プロキシフラグ
                    - hosting (bool): ホスティングフラグ
                エラー時(404): IP情報取得失敗
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # GET /api/ip-info/1.2.3.4
            >>> # Response: {"ip": "1.2.3.4", "country": "Japan", "city": "Tokyo", ...}
        """
        # profile = request.query_params.get("profile", "default")
        # 注: IP位置情報はプロファイルに依存しないため、実際には使用しない

        try:
            ip_info = get_ip_info(ip_address)

            if ip_info:
                return Response(ip_info)
            else:
                return Response(
                    {"error": "Failed to fetch IP information"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
