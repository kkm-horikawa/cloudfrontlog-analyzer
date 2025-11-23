from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DistributionSerializer
from .services import DistributionService


class DistributionListView(APIView):
    """CloudFront Distribution一覧取得APIエンドポイント。

    指定されたAWSプロファイルのCloudFront Distributionを全て取得します。
    Distribution ID、ドメイン名、カスタムドメインエイリアスを返します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/distributions?profile=production

        レスポンス:
            [
                {
                    "id": "E1234567890ABC",
                    "domain": "d111111abcdef8.cloudfront.net",
                    "aliases": ["example.com", "www.example.com"]
                }
            ]
    """

    @extend_schema(
        summary="List CloudFront Distributions",
        description="Retrieves all CloudFront distributions for the specified AWS profile",
        parameters=[
            OpenApiParameter(
                name="profile",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AWS profile name",
                default="default",
            ),
        ],
        responses={200: DistributionSerializer(many=True)},
    )
    def get(self, request):
        """CloudFront Distributionの一覧を取得します。

        指定されたAWSプロファイルの全CloudFront Distributionを取得し、
        ID、ドメイン名、エイリアスの情報を返します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str): AWS CLIプロファイル名（デフォルト: "default"）

        Returns:
            Response: Distribution情報のリストを含むJSONレスポンス
                成功時(200): Distribution情報の配列
                エラー時(400/500): エラーメッセージ

        Example:
            >>> # GET /api/distributions?profile=production
            >>> # Response: [{"id": "E123...", "domain": "d111...", "aliases": [...]}]
        """
        profile = request.query_params.get("profile", "default")

        try:
            service = DistributionService(profile_name=profile)
            distributions = service.list_distributions()
            serializer = DistributionSerializer(distributions, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
