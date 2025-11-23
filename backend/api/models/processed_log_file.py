from django.db import models


class ProcessedLogFile(models.Model):
    """処理済みログファイル管理モデル。

    S3から取得して処理したCloudFrontログファイルを追跡管理します。
    重複処理を防ぎ、処理済みファイルの情報を記録します。

    Attributes:
        distribution_id (str): CloudFront Distribution ID
        log_file_key (str): S3オブジェクトキー（ユニーク）
        file_size (int): ファイルサイズ（バイト）
        record_count (int): 含まれるログレコード数
        log_start_time (datetime): ログの最も古いエントリの時刻
        log_end_time (datetime): ログの最も新しいエントリの時刻
        processed_at (datetime): 処理完了日時

    Example:
        >>> log_file = ProcessedLogFile.objects.filter(
        ...     distribution_id="E1234567890ABC"
        ... ).first()
        >>> log_file.record_count
        15234
        >>> log_file.logs.count()
        15234
    """

    distribution_id = models.CharField(max_length=100, db_index=True)
    log_file_key = models.CharField(
        max_length=500, unique=True, db_index=True
    )  # S3オブジェクトキー
    file_size = models.BigIntegerField(default=0)  # ファイルサイズ（バイト）
    record_count = models.IntegerField(default=0)  # レコード数
    log_start_time = models.DateTimeField(null=True, blank=True)  # ログの開始時刻
    log_end_time = models.DateTimeField(null=True, blank=True)  # ログの終了時刻

    # メタデータ
    processed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "processed_log_files"
        ordering = ["-processed_at"]
        indexes = [
            models.Index(fields=["distribution_id", "log_start_time", "log_end_time"]),
        ]

    def __str__(self):
        return f"{self.distribution_id} - {self.log_file_key}"
