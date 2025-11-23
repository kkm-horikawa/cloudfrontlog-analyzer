"""IPアドレスユーティリティ関数"""

import ipaddress


def normalize_ip_address(ip_address: str) -> str:
    """IPアドレスをCIDR表記に正規化します。

    IPアドレスをCIDR表記に変換します。既にCIDR表記の場合はそのまま、
    単一IPアドレスの場合は適切なサフィックスを追加します。

    Args:
        ip_address (str): IPアドレス（CIDR表記あり・なし両方可）
            例: "192.168.1.1", "192.168.1.0/24", "2001:db8::1"

    Returns:
        str: CIDR表記のIPアドレス（IPv4は/32、IPv6は/128）

    Raises:
        ValueError: IPアドレスが無効な形式の場合

    Example:
        >>> normalize_ip_address("192.168.1.1")
        '192.168.1.1/32'
        >>> normalize_ip_address("192.168.1.0/24")
        '192.168.1.0/24'
        >>> normalize_ip_address("2001:db8::1")
        '2001:db8::1/128'
    """
    try:
        # ネットワーク（CIDR付き）としてパース試行
        network = ipaddress.ip_network(ip_address, strict=False)
        return str(network)
    except ValueError:
        # 単一アドレスとしてパース試行
        try:
            ip = ipaddress.ip_address(ip_address)
            # 適切なCIDRサフィックスを追加
            if ip.version == 4:
                return f"{ip_address}/32"
            else:  # IPv6
                return f"{ip_address}/128"
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip_address}")


def ip_in_network(ip_address: str, cidr: str) -> bool:
    """IPアドレスがCIDRネットワーク範囲内にあるかをチェックします。

    指定されたIPアドレスが、CIDRネットワークの範囲内に含まれるかを判定します。
    IPv4とIPv6の両方に対応しています。

    Args:
        ip_address (str): チェック対象のIPアドレス
            例: "192.168.1.100", "2001:db8::1"
        cidr (str): CIDR表記のネットワーク
            例: "192.168.1.0/24", "2001:db8::/32"

    Returns:
        bool: IPがネットワーク内にあればTrue、そうでなければFalse

    Example:
        >>> ip_in_network("192.168.1.100", "192.168.1.0/24")
        True
        >>> ip_in_network("192.168.2.100", "192.168.1.0/24")
        False
        >>> ip_in_network("10.0.0.1", "10.0.0.0/8")
        True
    """
    try:
        ip = ipaddress.ip_address(ip_address)
        network = ipaddress.ip_network(cidr, strict=False)
        return ip in network
    except ValueError:
        return False


def get_representative_ip_from_cidr(cidr: str, use_advanced: bool = False) -> str:
    """CIDRブロックからジオロケーション検索用の代表IPアドレスを抽出します。

    CIDRブロックから、そのネットワークを代表する単一のIPアドレスを取得します。
    高度な戦略を使用すると、ネットワークの実際に使用される可能性が高いIPを選択します。

    Args:
        cidr (str): CIDR表記のIPアドレス
            例: "203.0.113.0/24", "203.0.113.45/32", "2001:db8::/32"
        use_advanced (bool, optional): Trueの場合、より高精度なジオロケーション用の
            高度な戦略を使用します。デフォルトはFalse。

    Returns:
        str: 代表IPアドレス（文字列形式）

    Note:
        高度な戦略（use_advanced=True）の場合:
        - /32（単一IP）: IPをそのまま使用
        - /24以下: ネットワークアドレス + 1
        - /16以下: ネットワークアドレス + 256
        - /8以下: ネットワークアドレス + 65536
        - それより大きい: ネットワークアドレス + 1

    Example:
        >>> get_representative_ip_from_cidr("192.168.1.0/24")
        '192.168.1.0'
        >>> get_representative_ip_from_cidr("192.168.1.0/24", use_advanced=True)
        '192.168.1.1'
        >>> get_representative_ip_from_cidr("10.0.0.0/16", use_advanced=True)
        '10.0.1.0'
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)

        if not use_advanced:
            # シンプル戦略: ネットワークアドレスを使用
            return str(network.network_address)

        # より高精度なジオロケーション用の高度な戦略
        # 単一IP（IPv4の/32、IPv6の/128）の場合、直接使用
        if network.num_addresses == 1:
            return str(network.network_address)

        # 小～中規模の範囲では、ネットワークアドレス + オフセットを使用
        # これにより範囲内の使用可能なIPを取得を試みる
        if network.num_addresses <= 256:  # /24以下
            offset = 1
        elif network.num_addresses <= 65536:  # /16以下
            offset = 256
        elif network.num_addresses <= 16777216:  # /8以下
            offset = 65536
        else:
            # 非常に大きな範囲 - ネットワーク + 1のみ使用
            offset = 1

        # 代表IPを計算
        representative = network.network_address + offset

        # ネットワーク範囲を超えないことを確認
        if representative in network:
            return str(representative)
        else:
            # オフセットが範囲を超える場合、ネットワークアドレス + 1を使用
            return str(network.network_address + 1)

    except (ValueError, TypeError):
        # パース失敗時、ベースIPの抽出を試みる
        return cidr.split("/")[0]


def calculate_cidr_size_category(cidr: str) -> str:
    """CIDRブロックのサイズカテゴリを計算して精度レベルを示します。

    CIDRブロックに含まれるIPアドレスの数に基づいて、サイズカテゴリを判定します。
    これにより、ジオロケーションの精度レベルを推定できます。

    Args:
        cidr (str): CIDR表記のIPアドレス
            例: "192.168.1.0/24", "10.0.0.0/8"

    Returns:
        str: カテゴリ文字列
            - "single": 1個のIP（/32または/128）
            - "small": 256個以下
            - "medium": 65,536個以下
            - "large": 16,777,216個以下
            - "very_large": それ以上
            - "unknown": 解析失敗時

    Example:
        >>> calculate_cidr_size_category("192.168.1.100/32")
        'single'
        >>> calculate_cidr_size_category("192.168.1.0/24")
        'small'
        >>> calculate_cidr_size_category("10.0.0.0/16")
        'medium'
        >>> calculate_cidr_size_category("10.0.0.0/8")
        'large'
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        num_addresses = network.num_addresses

        if num_addresses == 1:
            return "single"
        elif num_addresses <= 256:
            return "small"
        elif num_addresses <= 65536:
            return "medium"
        elif num_addresses <= 16777216:
            return "large"
        else:
            return "very_large"
    except (ValueError, TypeError):
        return "unknown"
