"""Web Application Firewall操作のためのWAFサービスモジュール。

このモジュールは、AWS WAFv2を使用したIP制御機能を提供します。
CloudFront DistributionのWAF設定管理、IP Setの操作、ブロックIPの管理などを行います。

主な機能:
- WAF Web ACLとIP Setの一覧取得
- IPアドレスのブロック・アンブロック
- ブロックIPのジオロケーション情報取得
- WAF設定状態のスナップショット保存

Example:
    >>> waf_service = WAFService(profile_name="production")
    >>> result = waf_service.add_ip_to_waf_blocklist("E1234567890ABC", "1.2.3.4")
    >>> result['success']
    True
"""

from typing import Dict, List, Optional

import ipaddress
from botocore.exceptions import ClientError

from api.utils.aws_base import AWSServiceBase
from api.utils.ip_utils import (
    calculate_cidr_size_category,
    get_representative_ip_from_cidr,
    ip_in_network,
    normalize_ip_address,
)


class WAFService(AWSServiceBase):
    """WAF操作のためのサービスクラス。

    AWS WAFv2を使用したIP制御とセキュリティ管理機能を提供します。
    CloudFront DistributionのWAF設定、IP Setの管理を行います。

    Example:
        >>> waf = WAFService(profile_name="production")
        >>> web_acl = waf.get_waf_web_acl_for_distribution("E1234567890ABC")
        >>> web_acl['name']
        'my-cloudfront-waf'
    """

    def get_waf_web_acl_for_distribution(self, distribution_id: str) -> Optional[Dict]:
        """CloudFront DistributionのWAF Web ACL情報を取得します。

        指定されたDistributionに関連付けられているWAF Web ACLの情報を取得します。
        WAFが関連付けられていない場合はNoneを返します。

        Args:
            distribution_id (str): CloudFront Distribution ID
                例: "E1234567890ABC"

        Returns:
            Optional[Dict]: Web ACL情報を含む辞書、またはNone。
                辞書には以下のキーが含まれます:
                - id (str): Web ACL ID
                - name (str): Web ACL名
                - arn (str): Web ACL ARN
                - lockToken (str): ロックトークン

        Raises:
            ValueError: Web ACL取得に失敗した場合

        Example:
            >>> waf = WAFService()
            >>> web_acl = waf.get_waf_web_acl_for_distribution("E1234567890ABC")
            >>> web_acl['name']
            'production-waf'
        """
        try:
            from api.endpoints.distributions.services import DistributionService

            distribution_service = DistributionService(self.profile_name)
            config = distribution_service.get_distribution_config(distribution_id)
            web_acl_id = config.get("WebACLId", "")

            if not web_acl_id:
                return None

            # Web ACLの詳細を取得
            # 注意: CloudFrontはCLOUDFRONTスコープでWAFv2を使用
            web_acls = self.wafv2_client.list_web_acls(Scope="CLOUDFRONT")

            for acl in web_acls.get("WebACLs", []):
                if acl["ARN"] == web_acl_id:
                    return {
                        "id": acl["Id"],
                        "name": acl["Name"],
                        "arn": acl["ARN"],
                        "lockToken": acl["LockToken"],
                    }

            return None
        except ClientError as e:
            raise ValueError(f"Failed to get WAF Web ACL: {str(e)}")

    def _extract_ip_set_references(self, statement: Dict) -> List[str]:
        """
        WAFステートメントからIP Set ARNを再帰的に抽出

        Args:
            statement: WAFルールステートメント

        Returns:
            IP Set ARNのリスト
        """
        arns = []

        # 直接的なIP Set参照
        if "IPSetReferenceStatement" in statement:
            arns.append(statement["IPSetReferenceStatement"].get("ARN", ""))

        # OrStatementは複数のステートメントを含む
        if "OrStatement" in statement:
            for sub_statement in statement["OrStatement"].get("Statements", []):
                arns.extend(self._extract_ip_set_references(sub_statement))

        # AndStatementは複数のステートメントを含む
        if "AndStatement" in statement:
            for sub_statement in statement["AndStatement"].get("Statements", []):
                arns.extend(self._extract_ip_set_references(sub_statement))

        # NotStatementは単一のステートメントを含む
        if "NotStatement" in statement:
            arns.extend(
                self._extract_ip_set_references(
                    statement["NotStatement"].get("Statement", {})
                )
            )

        return arns

    def list_waf_ip_sets(self, distribution_id: str) -> Dict:
        """WAF Web ACLで利用可能な全IP Setを一覧表示します。

        指定されたDistributionのWAF Web ACLに関連付けられている全てのIP Setを取得します。
        ネストされたステートメント内のIP Setも含めて再帰的に検索します。

        Args:
            distribution_id (str): CloudFront Distribution ID
                例: "E1234567890ABC"

        Returns:
            Dict: IP Set情報を含む辞書。以下のキーが含まれます:
                - hasWAF (bool): WAFが設定されているか
                - webAcl (Dict): Web ACL情報
                - ipSets (List[Dict]): IP Setのリスト

        Raises:
            ValueError: IP Set一覧取得に失敗した場合

        Example:
            >>> waf = WAFService()
            >>> result = waf.list_waf_ip_sets("E1234567890ABC")
            >>> result['hasWAF']
            True
            >>> len(result['ipSets'])
            2
        """
        try:
            web_acl = self.get_waf_web_acl_for_distribution(distribution_id)

            if not web_acl:
                return {
                    "hasWAF": False,
                    "ipSets": [],
                    "message": "No WAF Web ACL associated with this distribution",
                }

            # ルールを含むWeb ACLの詳細を取得
            acl_details = self.wafv2_client.get_web_acl(
                Scope="CLOUDFRONT",
                Id=web_acl["id"],
                Name=web_acl["name"],
            )

            # ルールからIP Setを収集（ネストされたステートメントを含む）
            ip_sets = []
            seen_ip_sets = set()

            for rule in acl_details["WebACL"].get("Rules", []):
                statement = rule.get("Statement", {})

                # ステートメントからすべてのIP Set ARNを抽出（ネストされたものを含む）
                ip_set_arns = self._extract_ip_set_references(statement)

                for ip_set_arn in ip_set_arns:
                    if not ip_set_arn or ip_set_arn in seen_ip_sets:
                        continue
                    seen_ip_sets.add(ip_set_arn)

                    # IP Setの詳細を取得
                    ip_set_id = ip_set_arn.split("/")[-1]
                    ip_set_name = ip_set_arn.split("/")[-2]

                    ip_set = self.wafv2_client.get_ip_set(
                        Scope="CLOUDFRONT",
                        Id=ip_set_id,
                        Name=ip_set_name,
                    )

                    ip_sets.append(
                        {
                            "name": ip_set["IPSet"]["Name"],
                            "id": ip_set["IPSet"]["Id"],
                            "arn": ip_set["IPSet"]["ARN"],
                            "addressCount": len(ip_set["IPSet"].get("Addresses", [])),
                            "ipAddressVersion": ip_set["IPSet"].get(
                                "IPAddressVersion", "IPV4"
                            ),
                            "description": ip_set["IPSet"].get("Description", ""),
                        }
                    )

            return {
                "hasWAF": True,
                "webAcl": {
                    "name": web_acl["name"],
                    "id": web_acl["id"],
                },
                "ipSets": ip_sets,
            }

        except ClientError as e:
            raise ValueError(f"Failed to list WAF IP Sets: {str(e)}")

    def check_ip_in_waf_blocklist(
        self, distribution_id: str, ip_address: str
    ) -> Dict:
        """IPアドレスがWAFブロックリストに含まれているかを確認します。

        指定されたIPアドレスが、WAF IP Setのいずれかに登録されているかを確認します。
        CIDR範囲内に含まれる場合もブロック対象として検出します。

        Args:
            distribution_id (str): CloudFront Distribution ID
                例: "E1234567890ABC"
            ip_address (str): 確認するIPアドレス
                例: "1.2.3.4", "2001:db8::1"

        Returns:
            Dict: 確認結果を含む辞書。以下のキーが含まれます:
                - hasWAF (bool): WAFが設定されているか
                - isBlocked (bool): ブロック対象か
                - blockingRule (str): ブロックしているルール名
                - matchedCidr (str): マッチしたCIDR
                - matchedIpSetId (str): マッチしたIP Set ID
                - matchedIpSetName (str): マッチしたIP Set名

        Raises:
            ValueError: 確認処理に失敗した場合

        Example:
            >>> waf = WAFService()
            >>> result = waf.check_ip_in_waf_blocklist("E1234567890ABC", "1.2.3.4")
            >>> result['isBlocked']
            True
            >>> result['matchedCidr']
            '1.2.3.0/24'
        """
        try:
            web_acl = self.get_waf_web_acl_for_distribution(distribution_id)

            if not web_acl:
                return {
                    "hasWAF": False,
                    "isBlocked": False,
                    "message": "No WAF Web ACL associated with this distribution",
                }

            # ルールを含むWeb ACLの詳細を取得
            acl_details = self.wafv2_client.get_web_acl(
                Scope="CLOUDFRONT",
                Id=web_acl["id"],
                Name=web_acl["name"],
            )

            # ルール内のIP Setを確認
            ip_sets_checked = []
            is_blocked = False
            blocking_rule = None
            matched_cidr = None
            matched_ip_set_id = None
            matched_ip_set_name = None

            for rule in acl_details["WebACL"].get("Rules", []):
                statement = rule.get("Statement", {})

                # ステートメントからすべてのIP Set ARNを抽出（ネストされたものを含む）
                ip_set_arns = self._extract_ip_set_references(statement)

                for ip_set_arn in ip_set_arns:
                    if not ip_set_arn:
                        continue

                    # IP Setの詳細を取得
                    ip_set_id = ip_set_arn.split("/")[-1]
                    ip_set_name = ip_set_arn.split("/")[-2]

                    ip_set = self.wafv2_client.get_ip_set(
                        Scope="CLOUDFRONT",
                        Id=ip_set_id,
                        Name=ip_set_name,
                    )

                    ip_sets_checked.append(
                        {
                            "name": ip_set["IPSet"]["Name"],
                            "id": ip_set["IPSet"]["Id"],
                            "arn": ip_set["IPSet"]["ARN"],
                        }
                    )

                    # IPがセットに含まれているかを確認
                    addresses = ip_set["IPSet"].get("Addresses", [])
                    for cidr in addresses:
                        if ip_in_network(ip_address, cidr):
                            is_blocked = True
                            blocking_rule = rule["Name"]
                            matched_cidr = cidr
                            matched_ip_set_id = ip_set_id
                            matched_ip_set_name = ip_set_name
                            break

                    if is_blocked:
                        break

            return {
                "hasWAF": True,
                "isBlocked": is_blocked,
                "webAcl": {
                    "name": web_acl["name"],
                    "id": web_acl["id"],
                },
                "blockingRule": blocking_rule,
                "ipSetsChecked": ip_sets_checked,
                "matchedCidr": matched_cidr,
                "matchedIpSetId": matched_ip_set_id,
                "matchedIpSetName": matched_ip_set_name,
            }

        except ClientError as e:
            raise ValueError(f"Failed to check IP in WAF: {str(e)}")

    def add_ip_to_waf_blocklist(
        self, distribution_id: str, ip_address: str, ip_set_id: str = None
    ) -> Dict:
        """
        WAFブロックリストにIPアドレスを追加

        Args:
            distribution_id: CloudFrontディストリビューションID
            ip_address: ブロックするIPアドレス
            ip_set_id: 追加先のIP Set ID（オプション、指定しない場合は最初に見つかったものを使用）

        Returns:
            操作結果を含むDict
        """
        try:
            web_acl = self.get_waf_web_acl_for_distribution(distribution_id)

            if not web_acl:
                return {
                    "success": False,
                    "message": "No WAF Web ACL associated with this distribution",
                }

            # ルールを含むWeb ACLの詳細を取得
            acl_details = self.wafv2_client.get_web_acl(
                Scope="CLOUDFRONT",
                Id=web_acl["id"],
                Name=web_acl["name"],
            )

            # 追加先のIP Setを検索
            target_ip_set = None

            # 特定のIP Set IDが指定されている場合は、それを使用
            if ip_set_id:
                # Web ACLルールからIP Set名を検索（ネストされたステートメントを含む）
                ip_set_name_found = None
                for rule in acl_details["WebACL"].get("Rules", []):
                    statement = rule.get("Statement", {})
                    ip_set_arns = self._extract_ip_set_references(statement)

                    for ip_set_arn in ip_set_arns:
                        if not ip_set_arn:
                            continue

                        ip_set_id_from_arn = ip_set_arn.split("/")[-1]

                        if ip_set_id_from_arn == ip_set_id:
                            ip_set_name_found = ip_set_arn.split("/")[-2]
                            break

                    if ip_set_name_found:
                        break

                if ip_set_name_found:
                    ip_set_response = self.wafv2_client.get_ip_set(
                        Scope="CLOUDFRONT",
                        Id=ip_set_id,
                        Name=ip_set_name_found,
                    )
                    target_ip_set = ip_set_response["IPSet"]
                    target_ip_set["LockToken"] = ip_set_response["LockToken"]
                else:
                    return {
                        "success": False,
                        "message": f"IP Set with ID {ip_set_id} not found in WAF Web ACL",
                    }
            else:
                # 最初に見つかったIP Setを使用（ネストされたステートメントを含む）
                for rule in acl_details["WebACL"].get("Rules", []):
                    statement = rule.get("Statement", {})
                    ip_set_arns = self._extract_ip_set_references(statement)

                    for ip_set_arn in ip_set_arns:
                        if not ip_set_arn:
                            continue

                        ip_set_id_from_arn = ip_set_arn.split("/")[-1]
                        ip_set_name_from_arn = ip_set_arn.split("/")[-2]

                        ip_set_response = self.wafv2_client.get_ip_set(
                            Scope="CLOUDFRONT",
                            Id=ip_set_id_from_arn,
                            Name=ip_set_name_from_arn,
                        )
                        target_ip_set = ip_set_response["IPSet"]
                        target_ip_set["LockToken"] = ip_set_response["LockToken"]
                        break

                    if target_ip_set:
                        break

            if not target_ip_set:
                return {
                    "success": False,
                    "message": "No suitable IP set found in WAF Web ACL rules",
                }

            # IPアドレスをCIDR表記に正規化
            try:
                ip_cidr = normalize_ip_address(ip_address)
            except ValueError as e:
                return {
                    "success": False,
                    "message": str(e),
                }

            # IPが既にセットに含まれているかを確認
            addresses = set(target_ip_set.get("Addresses", []))

            # 完全に一致するCIDRが既にセットに含まれているかを確認
            if ip_cidr in addresses:
                return {
                    "success": True,
                    "message": f"IP {ip_cidr} is already in the block list",
                    "ipSet": {
                        "name": target_ip_set["Name"],
                        "id": target_ip_set["Id"],
                    },
                    "alreadyBlocked": True,
                }

            # IPが既存のCIDR範囲でカバーされているかを確認
            try:
                ip_obj = ipaddress.ip_address(ip_address.split("/")[0])
                for existing_cidr in addresses:
                    try:
                        network = ipaddress.ip_network(existing_cidr, strict=False)
                        if ip_obj in network:
                            return {
                                "success": True,
                                "message": f"IP {ip_address} is already covered by {existing_cidr} in the block list",
                                "ipSet": {
                                    "name": target_ip_set["Name"],
                                    "id": target_ip_set["Id"],
                                },
                                "alreadyBlocked": True,
                                "coveredBy": existing_cidr,
                            }
                    except ValueError:
                        continue
            except ValueError:
                pass

            # IPをセットに追加
            addresses.add(ip_cidr)

            self.wafv2_client.update_ip_set(
                Scope="CLOUDFRONT",
                Id=target_ip_set["Id"],
                Name=target_ip_set["Name"],
                Addresses=list(addresses),
                LockToken=target_ip_set["LockToken"],
            )

            return {
                "success": True,
                "message": f"IP {ip_cidr} added to block list",
                "ipSet": {
                    "name": target_ip_set["Name"],
                    "id": target_ip_set["Id"],
                },
                "alreadyBlocked": False,
                "cidr": ip_cidr,
            }

        except ClientError as e:
            raise ValueError(f"Failed to add IP to WAF: {str(e)}")

    def remove_from_waf_blocklist(
        self, distribution_id: str, ip_address: str, ip_set_id: Optional[str] = None
    ) -> Dict:
        """
        WAF IP SetからIPアドレスを削除（ブロック解除）

        Args:
            distribution_id: CloudFrontディストリビューションID
            ip_address: 削除するIPアドレス（IPv4とIPv6の両方に対応）
            ip_set_id: 削除元の特定のIP Set ID（オプション）

        Returns:
            削除結果を含むDictionary
        """
        try:
            # ディストリビューションからWAF WebACL ARNを取得
            distribution_config = self.cloudfront_client.get_distribution_config(
                Id=distribution_id
            )
            web_acl_id = distribution_config["DistributionConfig"].get("WebACLId")

            if not web_acl_id:
                return {
                    "success": False,
                    "message": "No WAF WebACL associated with this distribution",
                }

            # CIDR表記を処理
            if "/" in ip_address:
                # 既にCIDR表記がある
                ip_cidr = ip_address
            else:
                # IPv4かIPv6かを判定し、デフォルトのCIDRを追加
                is_ipv6 = ":" in ip_address
                ip_cidr = f"{ip_address}/128" if is_ipv6 else f"{ip_address}/32"

            # IP Setを取得
            ip_sets_response = self.wafv2_client.list_ip_sets(Scope="CLOUDFRONT")
            ip_sets = ip_sets_response.get("IPSets", [])

            if not ip_sets:
                return {
                    "success": False,
                    "message": "No IP Sets found",
                }

            # このIPを含むIP Setを検索
            target_ip_set = None
            if ip_set_id:
                # 指定されたIP Setを使用
                for ip_set in ip_sets:
                    if ip_set["Id"] == ip_set_id:
                        target_ip_set = ip_set
                        break
            else:
                # このIPを含むIP Setを検索
                for ip_set in ip_sets:
                    ip_set_detail = self.wafv2_client.get_ip_set(
                        Name=ip_set["Name"], Scope="CLOUDFRONT", Id=ip_set["Id"]
                    )
                    addresses = ip_set_detail["IPSet"].get("Addresses", [])
                    if ip_cidr in addresses:
                        target_ip_set = ip_set
                        break

            if not target_ip_set:
                return {
                    "success": False,
                    "message": f"IP address {ip_address} not found in any IP Set",
                }

            # 現在のIP Setの詳細を取得
            ip_set_detail = self.wafv2_client.get_ip_set(
                Name=target_ip_set["Name"],
                Scope="CLOUDFRONT",
                Id=target_ip_set["Id"],
            )

            current_addresses = ip_set_detail["IPSet"].get("Addresses", [])

            if ip_cidr not in current_addresses:
                return {
                    "success": False,
                    "message": f"IP address {ip_address} not found in IP Set {target_ip_set['Name']}",
                }

            # IPアドレスを削除
            updated_addresses = [addr for addr in current_addresses if addr != ip_cidr]

            # IP Setを更新
            self.wafv2_client.update_ip_set(
                Name=target_ip_set["Name"],
                Scope="CLOUDFRONT",
                Id=target_ip_set["Id"],
                Addresses=updated_addresses,
                LockToken=ip_set_detail["LockToken"],
            )

            return {
                "success": True,
                "ipAddress": ip_address,
                "ipSetId": target_ip_set["Id"],
                "ipSetName": target_ip_set["Name"],
                "message": f"Successfully removed {ip_address} from {target_ip_set['Name']}",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to remove IP from blocklist: {str(e)}",
            }

    def get_waf_blocked_ips(self, distribution_id: str) -> Dict:
        """
        WAF IP SetからすべてのブロックされたIPアドレスを取得

        Args:
            distribution_id: CloudFrontディストリビューションID

        Returns:
            ブロックされたIP情報を含むDictionary
        """
        try:
            # ディストリビューションからWAF WebACL ARNを取得
            distribution_config = self.cloudfront_client.get_distribution_config(
                Id=distribution_id
            )
            web_acl_id = distribution_config["DistributionConfig"].get("WebACLId")

            if not web_acl_id:
                return {
                    "blockedIps": [],
                    "total": 0,
                    "message": "No WAF WebACL associated with this distribution",
                }

            # IP Setを取得
            ip_sets_response = self.wafv2_client.list_ip_sets(Scope="CLOUDFRONT")
            ip_sets = ip_sets_response.get("IPSets", [])

            blocked_ips = []
            for ip_set in ip_sets:
                # 詳細なIP Set情報を取得
                ip_set_detail = self.wafv2_client.get_ip_set(
                    Name=ip_set["Name"], Scope="CLOUDFRONT", Id=ip_set["Id"]
                )

                addresses = ip_set_detail["IPSet"].get("Addresses", [])
                for address in addresses:
                    # 表示用にCIDR表記を削除
                    ip = address.split("/")[0]
                    blocked_ips.append(
                        {
                            "ip": ip,
                            "cidr": address,
                            "ipSetId": ip_set["Id"],
                            "ipSetName": ip_set["Name"],
                            "ipSetArn": ip_set["ARN"],
                        }
                    )

            return {
                "blockedIps": blocked_ips,
                "total": len(blocked_ips),
                "ipSets": [
                    {"id": ip_set["Id"], "name": ip_set["Name"], "arn": ip_set["ARN"]}
                    for ip_set in ip_sets
                ],
            }

        except Exception as e:
            return {
                "blockedIps": [],
                "total": 0,
                "error": f"Failed to get blocked IPs: {str(e)}",
            }

    def get_waf_blocked_ips_geo(self, distribution_id: str) -> Dict:
        """
        WAF IP SetからブロックされたIPアドレスの地理的分布を取得

        Args:
            distribution_id: CloudFrontディストリビューションID

        Returns:
            ロケーションとブロックされたIP情報を含むDictionary
        """
        from api.endpoints.ip_info.services import get_ip_info_batch

        try:
            # ブロックされたIPを取得
            blocked_ips_data = self.get_waf_blocked_ips(distribution_id)

            if "error" in blocked_ips_data or not blocked_ips_data.get("blockedIps"):
                return {
                    "locations": [],
                    "total": 0,
                    "message": blocked_ips_data.get("message", "No blocked IPs found"),
                }

            blocked_ips = blocked_ips_data["blockedIps"]

            # ジオロケーション検索用にCIDRから代表IPを抽出
            ip_to_cidr_map = {}  # 代表IPを元のCIDR情報にマッピング
            representative_ips = []

            for blocked_ip in blocked_ips:
                cidr = blocked_ip["cidr"]
                rep_ip = get_representative_ip_from_cidr(cidr, use_advanced=True)
                representative_ips.append(rep_ip)
                ip_to_cidr_map[rep_ip] = blocked_ip

            # すべてのIPのジオロケーション情報を取得
            ip_infos = get_ip_info_batch(representative_ips)

            # ロケーションごとに集約
            locations = []
            processed_coords = {}  # 座標キーをロケーションインデックスにマッピング

            for rep_ip, ip_info in ip_infos.items():
                if ip_info and ip_info.get("lat") and ip_info.get("lon"):
                    # 近くのロケーションをグループ化するための座標キーを作成
                    coord_key = f"{round(ip_info['lat'], 2)},{round(ip_info['lon'], 2)}"

                    original_cidr_info = ip_to_cidr_map[rep_ip]

                    if coord_key in processed_coords:
                        # 既存のロケーションに追加
                        idx = processed_coords[coord_key]
                        locations[idx]["count"] += 1
                        locations[idx]["cidrs"].append(original_cidr_info["cidr"])
                        locations[idx]["ipSetNames"].add(
                            original_cidr_info["ipSetName"]
                        )
                    else:
                        # 新しいロケーションを作成
                        idx = len(locations)
                        locations.append(
                            {
                                "lat": ip_info["lat"],
                                "lon": ip_info["lon"],
                                "city": ip_info.get("city", "Unknown"),
                                "country": ip_info.get("country", "Unknown"),
                                "countryCode": ip_info.get("countryCode", ""),
                                "count": 1,
                                "cidrs": [original_cidr_info["cidr"]],
                                "ipSetNames": {original_cidr_info["ipSetName"]},
                            }
                        )
                        processed_coords[coord_key] = idx

            # JSONシリアライゼーション用にセットをリストに変換
            for location in locations:
                location["ipSetNames"] = list(location["ipSetNames"])

            # カウントの降順でソート
            locations.sort(key=lambda x: x["count"], reverse=True)

            return {
                "locations": locations,
                "total": len(blocked_ips),
            }

        except Exception as e:
            return {
                "locations": [],
                "total": 0,
                "error": f"Failed to get geographic distribution of blocked IPs: {str(e)}",
            }

    def get_waf_blocked_ips_with_geolocation(self, distribution_id: str) -> Dict:
        """
        WAF IP SetからすべてのブロックされたIPアドレスを詳細なジオロケーション情報とともに取得

        Args:
            distribution_id: CloudFrontディストリビューションID

        Returns:
            ブロックされたIPと詳細なジオロケーション情報を含むDictionary
        """
        from api.endpoints.ip_info.services import get_ip_info_batch

        try:
            # まず、すべてのブロックされたIPを取得
            blocked_ips_result = self.get_waf_blocked_ips(distribution_id)

            if "error" in blocked_ips_result or not blocked_ips_result.get(
                "blockedIps"
            ):
                return blocked_ips_result

            blocked_ips = blocked_ips_result["blockedIps"]

            print(
                f"Processing {len(blocked_ips)} blocked IPs for detailed geolocation..."
            )

            # ジオロケーション検索用にCIDRから代表IPを抽出
            # より高い精度のために高度な戦略を使用
            ips_to_lookup = []
            ip_to_blocked_data = {}

            for blocked_ip_data in blocked_ips:
                cidr = blocked_ip_data["cidr"]
                representative_ip = get_representative_ip_from_cidr(
                    cidr, use_advanced=True
                )

                ips_to_lookup.append(representative_ip)
                ip_to_blocked_data[representative_ip] = blocked_ip_data

            print(
                f"Fetching geolocation for {len(ips_to_lookup)} IPs using batch API..."
            )
            print(
                f"Estimated time: ~{len(ips_to_lookup) / 100 * 4.5:.1f} seconds (rate limit: 15 req/min)"
            )

            # ジオロケーション情報をバッチフェッチ
            geo_info_map = get_ip_info_batch(ips_to_lookup)

            print(f"Successfully fetched geo info for {len(geo_info_map)} IPs")

            # ジオロケーション情報をブロックされたIPデータとマージ
            blocked_ips_with_geo = []

            for representative_ip, blocked_data in ip_to_blocked_data.items():
                geo_info = geo_info_map.get(representative_ip)

                if geo_info:
                    # 精度表示のためにCIDRサイズカテゴリを計算
                    cidr_category = calculate_cidr_size_category(blocked_data["cidr"])

                    blocked_ips_with_geo.append(
                        {
                            **blocked_data,
                            "representativeIp": representative_ip,
                            "cidrCategory": cidr_category,
                            "geolocation": {
                                "lat": geo_info.get("lat"),
                                "lon": geo_info.get("lon"),
                                "country": geo_info.get("country"),
                                "countryCode": geo_info.get("countryCode"),
                                "region": geo_info.get("region"),
                                "city": geo_info.get("city"),
                                "isp": geo_info.get("isp"),
                                "org": geo_info.get("org"),
                                "asn": geo_info.get("asn"),
                            },
                        }
                    )
                else:
                    # ジオロケーション検索が失敗した場合でも、ジオなしでIPを含める
                    cidr_category = calculate_cidr_size_category(blocked_data["cidr"])
                    blocked_ips_with_geo.append(
                        {
                            **blocked_data,
                            "representativeIp": representative_ip,
                            "cidrCategory": cidr_category,
                            "geolocation": None,
                        }
                    )

            # 有効なジオロケーションを持たないエントリを除外
            blocked_ips_with_valid_geo = [
                item
                for item in blocked_ips_with_geo
                if item.get("geolocation")
                and item["geolocation"].get("lat") is not None
                and item["geolocation"].get("lon") is not None
            ]

            # スナップショットをデータベースに保存
            self._save_waf_blocked_ip_snapshot(
                distribution_id,
                blocked_ips_with_geo,
                blocked_ips_result.get("ipSets", []),
            )

            return {
                "blockedIps": blocked_ips_with_valid_geo,
                "total": len(blocked_ips_with_valid_geo),
                "totalWithoutGeo": len(blocked_ips_with_geo)
                - len(blocked_ips_with_valid_geo),
                "ipSets": blocked_ips_result.get("ipSets", []),
            }

        except Exception as e:
            return {
                "blockedIps": [],
                "total": 0,
                "error": f"Failed to get blocked IPs with geolocation: {str(e)}",
            }

    def _save_waf_blocked_ip_snapshot(
        self,
        distribution_id: str,
        blocked_ips_with_geo: List[Dict],
        ip_sets: List[Dict],
    ) -> None:
        """
        WAFブロックされたIPのスナップショットをデータベースに保存

        Args:
            distribution_id: CloudFrontディストリビューションID
            blocked_ips_with_geo: ジオロケーションデータを含むブロックされたIPのリスト
            ip_sets: IP Set情報のリスト
        """
        try:
            from api.models import IPGeolocation, WAFBlockedIP, WAFBlockedIPSnapshot

            print(f"Saving WAF blocked IP snapshot for {distribution_id}...")

            # スナップショットを作成
            snapshot = WAFBlockedIPSnapshot.objects.create(
                distribution_id=distribution_id, total_ips=len(blocked_ips_with_geo)
            )

            # すべてのIPGeolocationオブジェクトを一度にバルクフェッチ（N+1を回避）
            representative_ips = [
                ip_data.get("representativeIp")
                for ip_data in blocked_ips_with_geo
                if ip_data.get("representativeIp")
            ]

            # IP -> IPGeolocationオブジェクトのマップを作成
            geo_objects = {
                geo.ip_address: geo
                for geo in IPGeolocation.objects.filter(
                    ip_address__in=representative_ips
                )
            }

            print(f"Loaded {len(geo_objects)} geolocation objects from DB")

            # バルク作成リストを準備
            blocked_ip_objects = []
            for blocked_ip_data in blocked_ips_with_geo:
                representative_ip = blocked_ip_data.get("representativeIp")

                # プリロードされたマップからジオロケーションオブジェクトを取得（DBクエリなし！）
                geolocation_obj = None
                if representative_ip and blocked_ip_data.get("geolocation"):
                    geolocation_obj = geo_objects.get(representative_ip)

                blocked_ip_objects.append(
                    WAFBlockedIP(
                        snapshot=snapshot,
                        ip_address=representative_ip
                        or blocked_ip_data.get("cidr", "").split("/")[0],
                        cidr=blocked_ip_data.get("cidr", ""),
                        ip_set_id=blocked_ip_data.get("ipSetId", ""),
                        ip_set_name=blocked_ip_data.get("ipSetName", ""),
                        ip_set_arn=blocked_ip_data.get("ipSetArn", ""),
                        geolocation=geolocation_obj,
                    )
                )

            # すべてを一度にバルク作成（単一のINSERT）
            WAFBlockedIP.objects.bulk_create(
                blocked_ip_objects, batch_size=1000, ignore_conflicts=True
            )

            print(
                f"✓ Saved snapshot {snapshot.id} with {len(blocked_ips_with_geo)} IPs (bulk insert)"
            )

        except Exception as e:
            print(f"Error saving WAF blocked IP snapshot: {str(e)}")
