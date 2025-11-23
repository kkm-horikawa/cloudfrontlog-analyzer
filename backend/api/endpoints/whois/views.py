"""WHOISバッチフェッチAPIビュー"""

import threading

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class WHOISBatchFetchView(APIView):
    """WHOIS情報を持たないすべてのIPに対してWHOIS情報を取得するAPIエンドポイント。

    データベース内のIPGeolocationテーブルから、WHOIS情報が未取得の
    IPアドレスを検索し、バックグラウンドでWHOIS情報を一括取得します。
    大量のIPに対して非同期で処理を実行します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            POST /api/whois/batch-fetch

        レスポンス:
            {
                "message": "WHOIS batch fetch started for 100 IPs",
                "pending_count": 100,
                "status": "running"
            }
    """

    @extend_schema(
        summary="不足しているWHOIS情報を取得",
        description="データベース内のWHOIS情報を持たないすべてのIPに対して、WHOIS情報を取得するバックグラウンドタスクを開始",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "pending_count": {"type": "integer"},
                    "status": {"type": "string"},
                },
            }
        },
    )
    def post(self, request):
        """バックグラウンドでWHOISフェッチタスクを開始します。

        WHOIS情報が未取得のIPアドレスを検索し、
        バックグラウンドスレッドで一括取得を開始します。

        Args:
            request (Request): HTTPリクエストオブジェクト

        Returns:
            Response: JSONレスポンス
                成功時(200): タスク開始結果を含む辞書
                    - message (str): 結果メッセージ
                    - pending_count (int): 未取得IP数
                    - status (str): タスクステータス（running/completed）
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # POST /api/whois/batch-fetch
            >>> # Response: {"message": "WHOIS batch fetch started for 100 IPs", "pending_count": 100, "status": "running"}
        """
        try:
            from .models import IPGeolocation

            # WHOIS情報を持たないIPをカウント
            ips_without_whois = IPGeolocation.objects.filter(
                whois_raw__isnull=True
            ) | IPGeolocation.objects.filter(whois_raw="")
            pending_count = ips_without_whois.count()

            if pending_count == 0:
                return Response(
                    {
                        "message": "All IPs already have WHOIS info",
                        "pending_count": 0,
                        "status": "completed",
                    }
                )

            # バックグラウンドスレッドを開始
            def run_whois_batch():
                from .ip_info import fetch_missing_whois_batch

                try:
                    fetch_missing_whois_batch()
                except Exception as e:
                    print(f"Error in WHOIS batch fetch: {str(e)}")

            thread = threading.Thread(target=run_whois_batch, daemon=True)
            thread.start()

            return Response(
                {
                    "message": f"WHOIS batch fetch started for {pending_count} IPs",
                    "pending_count": pending_count,
                    "status": "running",
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WHOISBatchStatusView(APIView):
    """WHOISバッチフェッチのステータスを確認するAPIエンドポイント。

    データベース内の全IPアドレスに対するWHOIS情報の取得状況を
    確認します。総IP数、取得済み数、未取得数、完了率を返します。

    Attributes:
        なし（ステートレスなAPIView）

    Example:
        リクエスト:
            GET /api/whois/batch-status

        レスポンス:
            {
                "total_ips": 1000,
                "with_whois": 800,
                "without_whois": 200,
                "percentage_complete": 80.0
            }
    """

    @extend_schema(
        summary="WHOISバッチステータスを取得",
        description="データベース内のWHOIS情報の現在のステータスを取得",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "total_ips": {"type": "integer"},
                    "with_whois": {"type": "integer"},
                    "without_whois": {"type": "integer"},
                    "percentage_complete": {"type": "number"},
                },
            }
        },
    )
    def get(self, request):
        """WHOISバッチフェッチのステータスを取得します。

        データベース内の全IPアドレスに対するWHOIS情報の
        取得状況を確認し、統計情報を返します。

        Args:
            request (Request): HTTPリクエストオブジェクト

        Returns:
            Response: JSONレスポンス
                成功時(200): WHOIS取得状況を含む辞書
                    - total_ips (int): 総IP数
                    - with_whois (int): WHOIS情報取得済みIP数
                    - without_whois (int): WHOIS情報未取得IP数
                    - percentage_complete (float): 完了率（%）
                エラー時(500): 内部サーバーエラーメッセージ

        Example:
            >>> # GET /api/whois/batch-status
            >>> # Response: {"total_ips": 1000, "with_whois": 800, "without_whois": 200, "percentage_complete": 80.0}
        """
        try:
            from .models import IPGeolocation

            total_ips = IPGeolocation.objects.count()
            with_whois = (
                IPGeolocation.objects.exclude(whois_raw__isnull=True)
                .exclude(whois_raw="")
                .count()
            )
            without_whois = total_ips - with_whois
            percentage_complete = (with_whois / total_ips * 100) if total_ips > 0 else 0

            return Response(
                {
                    "total_ips": total_ips,
                    "with_whois": with_whois,
                    "without_whois": without_whois,
                    "percentage_complete": round(percentage_complete, 2),
                }
            )

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
