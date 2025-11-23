"""AWS サービスの基底クラス。

このモジュールは、AWS CloudFront、S3、WAFv2などのAWSサービスとの
共通的なインタラクションを提供する基底クラスを定義します。
"""

import os
from pathlib import Path

import boto3


class AWSServiceBase:
    """AWSサービス操作の基底クラス。

    CloudFront、S3、WAFv2などのAWSサービスとの共通的な設定とクライアント初期化を提供します。
    すべてのAWSサービスクラスはこのクラスを継承して使用します。

    Attributes:
        CACHE_DIR (str): CloudFrontログのローカルキャッシュディレクトリパス
        profile_name (str): 使用するAWS CLIプロファイル名
        session (boto3.Session): Boto3セッションオブジェクト
        s3_client: Boto3 S3クライアント
        cloudfront_client: Boto3 CloudFrontクライアント
        wafv2_client: Boto3 WAFv2クライアント（us-east-1リージョン）

    Example:
        >>> service = AWSServiceBase(profile_name="my-profile")
        >>> distributions = service.cloudfront_client.list_distributions()
    """

    # Local cache directory for CloudFront logs
    # Use environment variable if set, otherwise calculate from repository root
    CACHE_DIR = os.environ.get(
        "CLOUDFRONT_LOG_CACHE_DIR",
        str(Path(__file__).resolve().parent.parent.parent.parent / ".cache" / "cloudfront_logs"),
    )

    def __init__(self, profile_name: str = "default"):
        """AWSサービスを指定されたプロファイルで初期化します。

        指定されたAWS CLIプロファイルを使用してBoto3セッションを作成し、
        必要なAWSサービスクライアント（S3、CloudFront、WAFv2）を初期化します。
        また、ログキャッシュ用のディレクトリを作成します。

        Args:
            profile_name (str, optional): 使用するAWS CLIプロファイル名。
                デフォルトは "default"。

        Example:
            >>> service = AWSServiceBase(profile_name="production")
            >>> service.profile_name
            'production'
        """
        self.profile_name = profile_name
        self.session = boto3.Session(profile_name=profile_name)

        # Initialize AWS clients
        self.s3_client = self.session.client("s3")
        self.cloudfront_client = self.session.client("cloudfront")
        self.wafv2_client = self.session.client("wafv2", region_name="us-east-1")

        # Ensure cache directory exists
        os.makedirs(self.CACHE_DIR, exist_ok=True)
