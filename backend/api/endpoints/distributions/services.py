"""CloudFront Distribution操作のためのサービスモジュール。

このモジュールは、CloudFront Distributionの一覧取得、設定取得、
ログバケット情報の取得などの操作を提供します。
"""

from typing import Dict
from typing import List
from typing import Optional

from botocore.exceptions import ClientError

from api.utils.aws_base import AWSServiceBase


class DistributionService(AWSServiceBase):
    """CloudFront Distribution操作用のサービスクラス。

    CloudFront Distributionの一覧表示、設定情報の取得、ログ設定の取得などを提供します。
    AWSServiceBaseクラスを継承し、CloudFrontクライアントを使用します。

    Example:
        >>> service = DistributionService(profile_name="production")
        >>> distributions = service.list_distributions()
        >>> len(distributions)
        3
    """

    def list_distributions(self) -> List[Dict[str, str]]:
        """すべてのCloudFront Distributionをリスト表示します。

        アカウント内のすべてのCloudFront Distributionを取得し、
        ID、ドメイン名、エイリアスの情報をリストで返します。

        Returns:
            List[Dict[str, str]]: Distributionの情報を含む辞書のリスト。
                各辞書には以下のキーが含まれます:
                - id (str): Distribution ID
                - domain (str): CloudFrontドメイン名
                - aliases (List[str]): カスタムドメインのリスト

        Raises:
            ValueError: CloudFront Distributionの取得に失敗した場合

        Example:
            >>> service = DistributionService()
            >>> distributions = service.list_distributions()
            >>> distributions[0]['id']
            'E1234567890ABC'
            >>> distributions[0]['domain']
            'd111111abcdef8.cloudfront.net'
        """
        try:
            response = self.cloudfront_client.list_distributions()

            if (
                "DistributionList" not in response
                or "Items" not in response["DistributionList"]
            ):
                return []

            distributions = []
            for dist in response["DistributionList"]["Items"]:
                distributions.append(
                    {
                        "id": dist["Id"],
                        "domain": dist["DomainName"],
                        "aliases": dist.get("Aliases", {}).get("Items", []),
                    }
                )

            return distributions
        except ClientError as e:
            raise ValueError(f"Failed to list CloudFront distributions: {str(e)}")

    def get_distribution_config(self, distribution_id: str) -> Dict:
        """CloudFront Distributionの設定情報を取得します。

        指定されたDistribution IDの詳細な設定情報を取得します。

        Args:
            distribution_id (str): CloudFront Distribution ID
                例: "E1234567890ABC"

        Returns:
            Dict: Distributionの設定情報を含む辞書

        Raises:
            ValueError: Distribution設定の取得に失敗した場合

        Example:
            >>> service = DistributionService()
            >>> config = service.get_distribution_config("E1234567890ABC")
            >>> config['Logging']['Enabled']
            True
        """
        try:
            response = self.cloudfront_client.get_distribution_config(
                Id=distribution_id
            )
            return response["DistributionConfig"]
        except ClientError as e:
            raise ValueError(f"Failed to get distribution config: {str(e)}")

    def get_log_bucket_info(self, distribution_id: str) -> Optional[Dict[str, str]]:
        """CloudFrontログ用のS3バケット情報を取得します。

        指定されたDistributionのログ設定からS3バケット名とprefixを取得します。
        ログが無効になっている場合はNoneを返します。

        Args:
            distribution_id (str): CloudFront Distribution ID
                例: "E1234567890ABC"

        Returns:
            Optional[Dict[str, str]]: ログ設定情報を含む辞書、またはNone。
                辞書には以下のキーが含まれます:
                - bucket (str): S3バケット名
                - prefix (str): ログファイルのprefix

        Example:
            >>> service = DistributionService()
            >>> log_info = service.get_log_bucket_info("E1234567890ABC")
            >>> log_info
            {'bucket': 'my-cloudfront-logs', 'prefix': 'cdn/'}
            >>> # ログが無効の場合
            >>> log_info = service.get_log_bucket_info("E9999999999ZZZ")
            >>> log_info is None
            True
        """
        try:
            config = self.get_distribution_config(distribution_id)
        except ValueError:
            # Distribution が存在しない場合は None を返す
            return None

        logging_config = config.get("Logging", {})

        if not logging_config.get("Enabled", False):
            return None

        bucket = logging_config.get("Bucket", "")
        # .s3.amazonaws.comサフィックスがあれば削除
        bucket = bucket.replace(".s3.amazonaws.com", "")

        return {
            "bucket": bucket,
            "prefix": logging_config.get("Prefix", ""),
        }
