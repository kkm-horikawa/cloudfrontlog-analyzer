"""CloudFrontログフォーマットの定数定義。

このモジュールは、CloudFrontアクセスログのフォーマット仕様に基づいた
カラム名とフィールド名のマッピングを定義します。

参照: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html

Attributes:
    CLOUDFRONT_LOG_COLUMNS (list[str]): CloudFrontログファイルのカラム名リスト
    FIELD_NAME_MAPPING (dict[str, str]): ログフィールド名からAPIレスポンス形式へのマッピング
    STATIC_FILE_EXTENSIONS (set[str]): 静的ファイルとして扱う拡張子のセット

Example:
    >>> len(CLOUDFRONT_LOG_COLUMNS)
    33
    >>> FIELD_NAME_MAPPING["c-ip"]
    'clientIp'
    >>> is_static_file("/images/logo.png")
    True
"""

from typing import Optional


# CloudFront Log Format - Extended Fields (with Field-Level Encryption)
# https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html
CLOUDFRONT_LOG_COLUMNS = [
    "date",  # 0
    "time",  # 1
    "x-edge-location",  # 2
    "sc-bytes",  # 3
    "c-ip",  # 4
    "cs-method",  # 5
    "cs-host",  # 6
    "cs-uri-stem",  # 7
    "sc-status",  # 8
    "cs-referer",  # 9
    "cs-user-agent",  # 10
    "cs-uri-query",  # 11
    "cs-cookie",  # 12
    "x-edge-result-type",  # 13
    "x-edge-request-id",  # 14
    "x-host-header",  # 15
    "cs-protocol",  # 16
    "cs-bytes",  # 17
    "time-taken",  # 18
    "x-forwarded-for",  # 19
    "ssl-protocol",  # 20
    "ssl-cipher",  # 21
    "x-edge-response-result-type",  # 22
    "cs-protocol-version",  # 23
    "fle-status",  # 24
    "fle-encrypted-fields",  # 25
    "c-port",  # 26
    "time-to-first-byte",  # 27
    "x-edge-detailed-result-type",  # 28
    "sc-content-type",  # 29
    "sc-content-len",  # 30
    "sc-range-start",  # 31
    "sc-range-end",  # 32
]

# Field names mapping (API response format -> DataFrame column)
FIELD_NAME_MAPPING = {
    "date": "date",
    "time": "time",
    "x-edge-location": "edgeLocation",
    "sc-bytes": "bytes",
    "c-ip": "clientIp",
    "cs-method": "method",
    "cs-host": "host",
    "cs-uri-stem": "uriStem",
    "sc-status": "statusCode",
    "cs-referer": "referrer",
    "cs-user-agent": "userAgent",
    "cs-uri-query": "queryString",
    "cs-cookie": "cookie",
    "x-edge-result-type": "edgeResultType",
    "x-edge-request-id": "edgeRequestId",
    "x-host-header": "hostHeader",
    "cs-protocol": "protocol",
    "cs-bytes": "bytes_sent",
    "time-taken": "timeTaken",
    "x-forwarded-for": "xForwardedFor",
    "ssl-protocol": "sslProtocol",
    "ssl-cipher": "sslCipher",
    "x-edge-response-result-type": "edgeResponseResultType",
    "cs-protocol-version": "protocolVersion",
    "fle-status": "fleStatus",
    "fle-encrypted-fields": "fleEncryptedFields",
    "c-port": "clientPort",
    "time-to-first-byte": "timeToFirstByte",
    "x-edge-detailed-result-type": "edgeDetailedResultType",
    "sc-content-type": "contentType",
    "sc-content-len": "contentLength",
    "sc-range-start": "rangeStart",
    "sc-range-end": "rangeEnd",
}

# 静的ファイルとして扱う拡張子
STATIC_FILE_EXTENSIONS = {
    ".js",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".bmp",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    ".mp4",
    ".webm",
    ".ogg",
    ".mp3",
    ".wav",
    ".pdf",
    ".zip",
    ".map",
    ".txt",
    ".xml",
    ".json",
    ".wasm",
    ".avif",
}


# CloudFront Standard Logs v2で追加されたフィールド
# リアルタイムログフィールドのサブセット
V2_ADDITIONAL_FIELDS = [
    "timestamp(ms)",  # ミリ秒精度のUnixタイムスタンプ
    "origin-fbl",  # Origin first-byte latency (秒)
    "origin-lbl",  # Origin last-byte latency (秒)
    "asn",  # 自律システム番号
    "c-country",  # 国コード (ISO 3166-1 alpha-2)
    "cache-behavior-path-pattern",  # マッチしたキャッシュ動作パターン
]

# v2フィールドのマッピング (API response format)
V2_FIELD_NAME_MAPPING = {
    "timestamp(ms)": "timestampMs",
    "origin-fbl": "originFirstByteLatency",
    "origin-lbl": "originLastByteLatency",
    "asn": "asn",
    "c-country": "country",
    "cache-behavior-path-pattern": "cacheBehaviorPathPattern",
}

# v1とv2のすべてのフィールドを統合したリスト
ALL_CLOUDFRONT_LOG_FIELDS = CLOUDFRONT_LOG_COLUMNS + V2_ADDITIONAL_FIELDS


def is_static_file(uri_stem: Optional[str]) -> bool:
    """
    URIが静的ファイルかどうかを判定

    Args:
        uri_stem: CloudFrontログのcs-uri-stem値（例: "/images/logo.png"）

    Returns:
        静的ファイルの場合True、そうでない場合False

    Example:
        >>> is_static_file("/images/logo.png")
        True
        >>> is_static_file("/api/users")
        False
        >>> is_static_file(None)
        False
    """
    if not uri_stem:
        return False
    uri_lower = str(uri_stem).lower()
    return any(uri_lower.endswith(ext) for ext in STATIC_FILE_EXTENSIONS)
