from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import WAFService


class WAFIPSetsListView(APIView):
    """WAFで利用可能なIPセットを一覧表示するAPIエンドポイント。

    CloudFrontディストリビューションに関連付けられたWAF WebACL内の
    すべてのIPセットを取得します。IPセットは、ブロックリストの管理に
    使用されます。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/waf/ip-sets?distributionId=E1234567890ABC&profile=default

        レスポンス:
            {
                "ipSets": [
                    {
                        "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                        "name": "BlockedIPs",
                        "arn": "arn:aws:wafv2:...",
                        "scope": "CLOUDFRONT",
                        "ipCount": 10
                    }
                ]
            }
    """

    @extend_schema(
        summary="List WAF IP Sets",
        description="List all IP Sets available in the WAF Web ACL for a CloudFront distribution",
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
        ],
    )
    def get(self, request):
        """WAF WebACL内のIPセットを一覧表示します。

        指定されたCloudFrontディストリビューションに関連付けられた
        WAF WebACL内のすべてのIPセット情報を取得します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                - distributionId (str, required): CloudFrontディストリビューションID

        Returns:
            Response: JSONレスポンス
                成功時(200): IPセットのリストを含む辞書
                    - ipSets (list): IPセット情報のリスト
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Raises:
            ValueError: distributionIdが無効な場合

        Example:
            >>> # GET /api/waf/ip-sets?distributionId=E1234567890ABC
            >>> # Response: {"ipSets": [...]}
        """
        profile = request.query_params.get("profile", "default")
        distribution_id = request.query_params.get("distributionId")

        if not distribution_id:
            return Response(
                {"error": "distributionId is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = WAFService(profile_name=profile)
            result = service.list_waf_ip_sets(distribution_id)
            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WAFBlocklistCheckView(APIView):
    """IPがWAFブロックリストに含まれているかをチェックするAPIエンドポイント。

    指定されたIPアドレスがCloudFrontディストリビューションのWAF
    ブロックリスト（IPセット）に登録されているかを確認します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/waf/blocklist/check?distributionId=E1234567890ABC&ipAddress=1.2.3.4

        レスポンス:
            {
                "isBlocked": true,
                "ipAddress": "1.2.3.4",
                "ipSets": [
                    {
                        "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                        "name": "BlockedIPs",
                        "cidr": "1.2.3.4/32"
                    }
                ]
            }
    """

    @extend_schema(
        summary="Check IP in WAF Block List",
        description="Check if an IP address is in the WAF block list for a CloudFront distribution",
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
                name="ipAddress",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="IP address to check",
                required=True,
            ),
        ],
    )
    def get(self, request):
        """IPアドレスがWAFブロックリストに含まれているかをチェックします。

        指定されたIPアドレスがWAF IPセット内に存在するかを確認し、
        含まれている場合はそのIPセット情報を返します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                - distributionId (str, required): CloudFrontディストリビューションID
                - ipAddress (str, required): チェックするIPアドレス

        Returns:
            Response: JSONレスポンス
                成功時(200): ブロック状態とIPセット情報を含む辞書
                    - isBlocked (bool): ブロックされているかどうか
                    - ipAddress (str): チェックしたIPアドレス
                    - ipSets (list): IPが含まれるIPセット情報
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Raises:
            ValueError: パラメータが無効な場合

        Example:
            >>> # GET /api/waf/blocklist/check?distributionId=E1234567890ABC&ipAddress=1.2.3.4
            >>> # Response: {"isBlocked": true, "ipAddress": "1.2.3.4", "ipSets": [...]}
        """
        profile = request.query_params.get("profile", "default")
        distribution_id = request.query_params.get("distributionId")
        ip_address = request.query_params.get("ipAddress")

        if not distribution_id or not ip_address:
            return Response(
                {"error": "distributionId and ipAddress are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = WAFService(profile_name=profile)
            result = service.check_ip_in_waf_blocklist(distribution_id, ip_address)
            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WAFBlocklistAddView(APIView):
    """WAFブロックリストにIPを追加するAPIエンドポイント。

    指定されたIPアドレスをCloudFrontディストリビューションのWAF
    ブロックリスト（IPセット）に追加します。IPセットIDが指定されない
    場合は、デフォルトのIPセットに追加されます。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            POST /api/waf/blocklist/add?profile=default
            {
                "distributionId": "E1234567890ABC",
                "ipAddress": "1.2.3.4",
                "ipSetId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            }

        レスポンス:
            {
                "success": true,
                "message": "IP address 1.2.3.4 added to blocklist",
                "ipSetId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "ipSetName": "BlockedIPs"
            }
    """

    @extend_schema(
        summary="Add IP to WAF Block List",
        description="Add an IP address to the WAF block list for a CloudFront distribution",
        parameters=[
            OpenApiParameter(
                name="profile",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AWS profile name",
                default="default",
            ),
        ],
    )
    def post(self, request):
        """WAFブロックリストにIPアドレスを追加します。

        指定されたIPアドレスをWAF IPセットに追加してブロックします。
        IPセットIDが指定されない場合は、自動的に適切なIPセットが選択されます。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                リクエストボディ:
                - distributionId (str, required): CloudFrontディストリビューションID
                - ipAddress (str, required): ブロックするIPアドレス
                - ipSetId (str, optional): IPセットID（指定しない場合はデフォルト使用）

        Returns:
            Response: JSONレスポンス
                成功時(200): 追加結果を含む辞書
                    - success (bool): 成功フラグ
                    - message (str): 結果メッセージ
                    - ipSetId (str): 使用されたIPセットID
                    - ipSetName (str): IPセット名
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Raises:
            ValueError: パラメータが無効な場合

        Example:
            >>> # POST /api/waf/blocklist/add
            >>> # Body: {"distributionId": "E1234567890ABC", "ipAddress": "1.2.3.4"}
            >>> # Response: {"success": true, "message": "IP address added"}
        """
        profile = request.query_params.get("profile", "default")
        distribution_id = request.data.get("distributionId")
        ip_address = request.data.get("ipAddress")
        ip_set_id = request.data.get("ipSetId")

        if not distribution_id or not ip_address:
            return Response(
                {"error": "distributionId and ipAddress are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = WAFService(profile_name=profile)
            result = service.add_ip_to_waf_blocklist(
                distribution_id, ip_address, ip_set_id
            )
            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WAFBlocklistRemoveView(APIView):
    """WAFブロックリストからIPを削除するAPIエンドポイント。

    指定されたIPアドレスをCloudFrontディストリビューションのWAF
    ブロックリスト（IPセット）から削除してアクセスを許可します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            POST /api/waf/blocklist/remove?profile=default
            {
                "distributionId": "E1234567890ABC",
                "ipAddress": "1.2.3.4",
                "ipSetId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            }

        レスポンス:
            {
                "success": true,
                "message": "IP address 1.2.3.4 removed from blocklist",
                "ipSetId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            }
    """

    @extend_schema(
        summary="Remove IP from WAF Blocklist",
        description="Remove an IP address from WAF IP Set (unblock)",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "distributionId": {"type": "string"},
                    "ipAddress": {"type": "string"},
                    "ipSetId": {"type": "string", "nullable": True},
                },
                "required": ["distributionId", "ipAddress"],
            }
        },
        parameters=[
            OpenApiParameter(
                name="profile",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="AWS profile name",
                default="default",
            ),
        ],
        responses={200: {"type": "object"}},
    )
    def post(self, request):
        """WAFブロックリストからIPアドレスを削除します。

        指定されたIPアドレスをWAF IPセットから削除してブロックを解除します。
        IPセットIDが指定されない場合は、全IPセットから検索して削除します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                リクエストボディ:
                - distributionId (str, required): CloudFrontディストリビューションID
                - ipAddress (str, required): 削除するIPアドレス
                - ipSetId (str, optional): IPセットID（指定しない場合は自動検索）

        Returns:
            Response: JSONレスポンス
                成功時(200): 削除結果を含む辞書
                    - success (bool): 成功フラグ
                    - message (str): 結果メッセージ
                    - ipSetId (str): 使用されたIPセットID
                エラー時(400): バリデーションエラーまたはIP未検出
                エラー時(500): 内部サーバーエラーメッセージ

        Raises:
            ValueError: パラメータが無効な場合

        Example:
            >>> # POST /api/waf/blocklist/remove
            >>> # Body: {"distributionId": "E1234567890ABC", "ipAddress": "1.2.3.4"}
            >>> # Response: {"success": true, "message": "IP address removed"}
        """
        profile = request.query_params.get("profile", "default")

        distribution_id = request.data.get("distributionId")
        ip_address = request.data.get("ipAddress")
        ip_set_id = request.data.get("ipSetId")

        if not distribution_id or not ip_address:
            return Response(
                {"error": "distributionId and ipAddress are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = WAFService(profile_name=profile)
            result = service.remove_from_waf_blocklist(
                distribution_id=distribution_id,
                ip_address=ip_address,
                ip_set_id=ip_set_id,
            )

            if result.get("success"):
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WAFBlockedIPsListView(APIView):
    """WAFでブロックされている全IPを一覧表示するAPIエンドポイント。

    CloudFrontディストリビューションのWAF IPセットに登録されている
    全てのブロック済みIPアドレスを取得します。IPセット情報も含まれます。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/waf/blocked-ips?distributionId=E1234567890ABC

        レスポンス:
            {
                "blockedIps": [
                    {
                        "ip": "1.2.3.4",
                        "cidr": "1.2.3.4/32",
                        "ipSetId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                        "ipSetName": "BlockedIPs",
                        "ipSetArn": "arn:aws:wafv2:..."
                    }
                ],
                "total": 1,
                "ipSets": [...]
            }
    """

    @extend_schema(
        summary="List All Blocked IPs",
        description="Get all IP addresses currently blocked in WAF IP Sets",
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
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "blockedIps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ip": {"type": "string"},
                                "cidr": {"type": "string"},
                                "ipSetId": {"type": "string"},
                                "ipSetName": {"type": "string"},
                                "ipSetArn": {"type": "string"},
                            },
                        },
                    },
                    "total": {"type": "integer"},
                    "ipSets": {"type": "array"},
                },
            }
        },
    )
    def get(self, request):
        """WAFでブロックされている全IPアドレスを一覧表示します。

        指定されたCloudFrontディストリビューションのWAF IPセットに
        登録されている全てのブロック済みIPアドレスを取得します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                - distributionId (str, required): CloudFrontディストリビューションID

        Returns:
            Response: JSONレスポンス
                成功時(200): ブロック済みIPのリストを含む辞書
                    - blockedIps (list): ブロック済みIP情報のリスト
                    - total (int): ブロック済みIPの総数
                    - ipSets (list): IPセット情報のリスト
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # GET /api/waf/blocked-ips?distributionId=E1234567890ABC
            >>> # Response: {"blockedIps": [...], "total": 10}
        """
        profile = request.query_params.get("profile", "default")
        distribution_id = request.query_params.get("distributionId")

        if not distribution_id:
            return Response(
                {"error": "distributionId is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = WAFService(profile_name=profile)
            result = service.get_waf_blocked_ips(distribution_id=distribution_id)
            return Response(result)

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WAFBlockedIPsExportView(APIView):
    """ブロックされたIPをExcelファイルとしてエクスポートするAPIエンドポイント。

    WAFでブロックされている全てのIPアドレスをExcel形式でダウンロード
    できます。各IPのCIDR、IPセット名、IPセットIDなどの情報が含まれます。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/waf/blocked-ips/export?distributionId=E1234567890ABC

        レスポンス:
            - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
            - ファイル名: waf_blocked_ips_E1234567890ABC_20251118_120000.xlsx
            - 内容: ブロック済みIPのExcelファイル
    """

    @extend_schema(
        summary="Export Blocked IPs to Excel",
        description="Download all blocked IP addresses as an Excel file",
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
        ],
        responses={200: OpenApiTypes.BINARY},
    )
    def get(self, request):
        """ブロックされたIPをExcelファイルとしてエクスポートします。

        WAFでブロックされている全てのIPアドレスをExcel形式で
        ダウンロード可能なファイルとして返します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                - distributionId (str, required): CloudFrontディストリビューションID

        Returns:
            FileResponse: Excelファイル
                成功時(200): タイムスタンプ付きExcelファイル
                    列: IP Address, CIDR, IP Set Name, IP Set ID, IP Set ARN
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # GET /api/waf/blocked-ips/export?distributionId=E1234567890ABC
            >>> # Response: Excelファイルのダウンロード
        """
        import io
        from datetime import datetime

        import pandas as pd
        from django.http import FileResponse

        profile = request.query_params.get("profile", "default")
        distribution_id = request.query_params.get("distributionId")

        if not distribution_id:
            return Response(
                {"error": "distributionId is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = WAFService(profile_name=profile)
            result = service.get_waf_blocked_ips(distribution_id=distribution_id)

            if not result["blockedIps"]:
                # メッセージ付きの空のExcelを返す
                df = pd.DataFrame([{"Message": "No blocked IPs found"}])
            else:
                # ブロックされたIPからDataFrameを作成
                blocked_ips_data = []
                for blocked_ip in result["blockedIps"]:
                    blocked_ips_data.append(
                        {
                            "IP Address": blocked_ip["ip"],
                            "CIDR": blocked_ip["cidr"],
                            "IP Set Name": blocked_ip["ipSetName"],
                            "IP Set ID": blocked_ip["ipSetId"],
                            "IP Set ARN": blocked_ip["ipSetArn"],
                        }
                    )
                df = pd.DataFrame(blocked_ips_data)

            # メモリ内にExcelファイルを作成
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Blocked IPs", index=False)

                # 列幅を自動調整
                worksheet = writer.sheets["Blocked IPs"]
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(), len(str(col))
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

            output.seek(0)

            # タイムスタンプ付きのファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"waf_blocked_ips_{distribution_id}_{timestamp}.xlsx"

            # ファイルダウンロードとして返す
            response = FileResponse(
                output,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WAFBlockedIPsGeoView(APIView):
    """ブロックされたIPの地理的分布を取得するAPIエンドポイント。

    WAFでブロックされているIPアドレスの地理的位置情報を集計して
    マップ表示用のデータを提供します。国、都市ごとにグループ化されます。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/waf/blocked-ips/geo?distributionId=E1234567890ABC

        レスポンス:
            {
                "locations": [
                    {
                        "lat": 35.6895,
                        "lon": 139.6917,
                        "city": "Tokyo",
                        "country": "Japan",
                        "countryCode": "JP",
                        "count": 5,
                        "cidrs": ["1.2.3.4/32", "5.6.7.8/32"],
                        "ipSetNames": ["BlockedIPs"]
                    }
                ],
                "total": 5
            }
    """

    @extend_schema(
        summary="Get Geographic Distribution of Blocked IPs",
        description="Get geographic distribution of blocked IP addresses in WAF IP Sets",
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
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "locations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "lat": {"type": "number"},
                                "lon": {"type": "number"},
                                "city": {"type": "string"},
                                "country": {"type": "string"},
                                "countryCode": {"type": "string"},
                                "count": {"type": "integer"},
                                "cidrs": {"type": "array", "items": {"type": "string"}},
                                "ipSetNames": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    },
                    "total": {"type": "integer"},
                },
            }
        },
    )
    def get(self, request):
        """ブロックされたIPの地理的分布を取得します。

        WAFでブロックされているIPアドレスの位置情報を集計し、
        地理的分布をマップ表示用の形式で返します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                - distributionId (str, required): CloudFrontディストリビューションID

        Returns:
            Response: JSONレスポンス
                成功時(200): 地理的分布データを含む辞書
                    - locations (list): 位置情報とカウントのリスト
                    - total (int): ブロック済みIPの総数
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # GET /api/waf/blocked-ips/geo?distributionId=E1234567890ABC
            >>> # Response: {"locations": [...], "total": 5}
        """
        profile = request.query_params.get("profile", "default")
        distribution_id = request.query_params.get("distributionId")

        if not distribution_id:
            return Response(
                {"error": "distributionId is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = WAFService(profile_name=profile)
            result = service.get_waf_blocked_ips_geo(distribution_id=distribution_id)
            return Response(result)

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WAFBlockedIPsDetailGeoView(APIView):
    """詳細な位置情報付きでブロックされた全IPを一覧表示するAPIエンドポイント。

    WAFでブロックされている各IPアドレスに対して、詳細な位置情報
    （国、都市、ISP、組織、ASN等）を付加して返します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/waf/blocked-ips/detail-geo?distributionId=E1234567890ABC

        レスポンス:
            {
                "blockedIps": [
                    {
                        "ip": "1.2.3.4",
                        "cidr": "1.2.3.4/32",
                        "representativeIp": "1.2.3.4",
                        "cidrCategory": "single",
                        "ipSetId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                        "ipSetName": "BlockedIPs",
                        "ipSetArn": "arn:aws:wafv2:...",
                        "geolocation": {
                            "lat": 35.6895,
                            "lon": 139.6917,
                            "country": "Japan",
                            "countryCode": "JP",
                            "city": "Tokyo",
                            "isp": "Example ISP",
                            "org": "Example Org",
                            "asn": "AS1234"
                        }
                    }
                ],
                "total": 1,
                "totalWithoutGeo": 0,
                "ipSets": [...]
            }
    """

    @extend_schema(
        summary="List All Blocked IPs with Detailed Geolocation",
        description="Get all IP addresses currently blocked in WAF IP Sets with detailed geolocation information",
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
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "blockedIps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ip": {"type": "string"},
                                "cidr": {"type": "string"},
                                "representativeIp": {"type": "string"},
                                "cidrCategory": {"type": "string"},
                                "ipSetId": {"type": "string"},
                                "ipSetName": {"type": "string"},
                                "ipSetArn": {"type": "string"},
                                "geolocation": {
                                    "type": "object",
                                    "properties": {
                                        "lat": {"type": "number"},
                                        "lon": {"type": "number"},
                                        "country": {"type": "string"},
                                        "countryCode": {"type": "string"},
                                        "region": {"type": "string"},
                                        "city": {"type": "string"},
                                        "isp": {"type": "string"},
                                        "org": {"type": "string"},
                                        "asn": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                    "total": {"type": "integer"},
                    "totalWithoutGeo": {"type": "integer"},
                    "ipSets": {"type": "array"},
                },
            }
        },
    )
    def get(self, request):
        """詳細な位置情報付きでブロックされた全IPを一覧表示します。

        WAFでブロックされている各IPアドレスに対して、ip-api.comから
        取得した詳細な位置情報を付加して返します。

        Args:
            request (Request): HTTPリクエストオブジェクト
                クエリパラメータ:
                - profile (str, optional): AWS CLIプロファイル名 (デフォルト: 'default')
                - distributionId (str, required): CloudFrontディストリビューションID

        Returns:
            Response: JSONレスポンス
                成功時(200): 詳細位置情報付きIPリストを含む辞書
                    - blockedIps (list): IP情報と位置情報のリスト
                    - total (int): ブロック済みIPの総数
                    - totalWithoutGeo (int): 位置情報が取得できなかったIP数
                    - ipSets (list): IPセット情報のリスト
                エラー時(400): バリデーションエラーメッセージ
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # GET /api/waf/blocked-ips/detail-geo?distributionId=E1234567890ABC
            >>> # Response: {"blockedIps": [...], "total": 1, "totalWithoutGeo": 0}
        """
        profile = request.query_params.get("profile", "default")
        distribution_id = request.query_params.get("distributionId")

        if not distribution_id:
            return Response(
                {"error": "distributionId is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = WAFService(profile_name=profile)
            result = service.get_waf_blocked_ips_with_geolocation(
                distribution_id=distribution_id
            )
            return Response(result)

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
