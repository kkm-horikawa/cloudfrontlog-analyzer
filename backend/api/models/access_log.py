from django.db import models

from .ip_geolocation import IPGeolocation
from .processed_log_file import ProcessedLogFile


class AccessLog(models.Model):
    """CloudFrontアクセスログの生データを格納するモデル。

    CloudFrontから取得したアクセスログの詳細情報を保存します。
    各ログエントリには、クライアント情報、リクエスト情報、レスポンス情報が含まれます。

    Attributes:
        distribution_id (str): CloudFront Distribution ID
        log_file (ProcessedLogFile): 関連するログファイル
        log_datetime (datetime): ログの日時（UTC）
        edge_location (str): エッジロケーション
        c_ip (GenericIPAddress): クライアントIPアドレス
        geolocation (IPGeolocation): 関連するジオロケーション情報
        cs_method (str): HTTPメソッド（GET, POST等）
        cs_host (str): リクエストホスト
        cs_uri_stem (str): URIパス
        cs_uri_query (str): クエリ文字列
        sc_status (int): HTTPステータスコード
        sc_bytes (int): レスポンスバイト数
        time_taken (float): 処理時間（秒）
        cs_user_agent (str): ユーザーエージェント
        cs_referer (str): リファラー
        x_edge_result_type (str): エッジ結果タイプ

    Example:
        >>> log = AccessLog.objects.filter(c_ip="8.8.8.8").first()
        >>> log.sc_status
        200
        >>> log.cs_uri_stem
        '/index.html'
    """

    distribution_id = models.CharField(max_length=100, db_index=True)
    log_file = models.ForeignKey(
        ProcessedLogFile, on_delete=models.CASCADE, related_name="logs"
    )

    # 基本情報
    log_datetime = models.DateTimeField(db_index=True)  # date + time を結合
    edge_location = models.CharField(max_length=50, null=True, blank=True)

    # クライアント情報
    c_ip = models.GenericIPAddressField(db_index=True)
    geolocation = models.ForeignKey(
        IPGeolocation, on_delete=models.SET_NULL, null=True, blank=True
    )

    # リクエスト情報
    cs_method = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    cs_host = models.CharField(max_length=255, null=True, blank=True)
    cs_uri_stem = models.CharField(
        max_length=2000, null=True, blank=True, db_index=True
    )
    cs_uri_query = models.TextField(null=True, blank=True)

    # レスポンス情報
    sc_status = models.IntegerField(null=True, blank=True, db_index=True)
    sc_bytes = models.BigIntegerField(null=True, blank=True)
    time_taken = models.FloatField(null=True, blank=True)

    # その他
    cs_user_agent = models.TextField(null=True, blank=True)
    cs_referer = models.TextField(null=True, blank=True)
    x_edge_result_type = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "access_logs"
        ordering = ["-log_datetime"]
        indexes = [
            models.Index(fields=["distribution_id", "log_datetime"]),
            models.Index(fields=["c_ip", "log_datetime"]),
            models.Index(fields=["log_file", "log_datetime"]),
            # フィルタ用の複合インデックス
            models.Index(fields=["distribution_id", "cs_method", "sc_status"]),
            models.Index(fields=["distribution_id", "log_datetime", "sc_status"]),
        ]

    def __str__(self):
        return f"{self.c_ip} - {self.log_datetime} - {self.cs_uri_stem}"
