"""不審なアクセス検出モジュール。

このモジュールは、リサーチツール、スクレイパー、SEOボット、その他の不審なアクセスパターンを
検出するためのパターンマッチング機能を提供します。

主な機能:
- ユーザーエージェントによる不審なボット検出
- リファラーチェック
- リクエストパスの分析
- デバイスタイプの判定
- 複数のログエントリにわたる分析

Example:
    >>> ua_check = check_user_agent_suspicious("Python-urllib/3.8")
    >>> ua_check['is_blocked']
    True
    >>> ua_check['severity']
    'danger'
"""

import re
from typing import Any
from typing import Dict
from typing import List


# 不審なアクティビティ検出用の正規表現パターン
POTENTIAL_BOTS_UA = re.compile(r"bot|Bot|BOT|spider|Spider|SPIDER")
ALLOWED_TOP_LEVEL = re.compile(
    r"^Down/5\.1\.1$|^Mozilla/5\.0 \(X11; Linux x86_64\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/104\.0\.0\.0 Safari/537\.36"
)
ALLOWED_GOOGLE_UR_1 = re.compile(
    r"APIs-Google|Mediapartners-Google|AdsBot-Google-Mobile|AdsBot-Google|Googlebot|AdsBot-Google-Mobile-Apps|FeedFetcher-Google|Google-Read-Aloud|DuplexWeb-Google|Google Favicon|googleweblight"
)
ALLOWED_GOOGLE_UR_2 = re.compile(r"Google-Ads-Creatives-Assistant|Google-Adwords")
ALLOWED_BOTS_UA = re.compile(
    r"bingbot|Applebot|facebookexternalhit|Twitterbot|Slack-ImgProxy|DuckDuckGo-Favicons-Bot|Slackbot|HatenaBlog-bot|MsnBot|Linespider|Hatena|AdsBot-LINE|Stripe"
)
BLOCKED_ARCHIVE_TOOLS_UA = re.compile(r"archive\.org_bot|Megalodon|PagePeeker")
BLOCKED_SCRAPING_TOOLS_UA = re.compile(
    r"GoogleDocs|Google-Apps-Script|Python|python|Java/1\.8\.0_261|dcrawl/1\.0|newspaper/|okhttp/2\.|dcrawl/1|Java/|fscrawler|Scrapy|Go http package|Chrome Safari Firefox \(Bot\)|loli_tentacle"
)
BLOCKED_SEO_TOOLS_UA = re.compile(
    r"linkfluence\.com|SemrushBot|SEOkicks|Cincraw|MJ12bot|DotBot|CCBot|AhrefsBot|AhrefsSiteAudit|SurdotlyBot|BLEXBot|proximic|Screaming Frog|Updownerbot|adbeat_bot|Nimbostratus-Bot|seostar|DataForSeoBot"
)
BLOCKED_OTHER_TOOLS_UA = re.compile(
    r"MTRobot|Re-re Studio|NetSystemsResearch|intelx\.io_bot|SMTBot|PostmanRuntime|Y!J-"
)
BLOCKED_MINOR_SEARCH_ENGINES_UA = re.compile(
    r"PetalBot|SeznamBot|coccocbot|YandexBot|YandexImages|Baiduspider|YisouSpider|\(compatible; Adsbot/3\.1\)|Barkrowler|MauiBot|ZoominfoBot|Keybot Translation-Search-Machine|SeekportBot"
)
SUSPICIOUS_UA = re.compile(
    r"Line(?<!spider)$|LINE|line|Chatwork|chatwork|Slack|slack|PhantomJS|Excel"
)
SUSPICIOUS_REQ_PATH = re.compile(r"\/wiseloan\/about\/")
BLOCKED_REFERRER = re.compile(
    r"anonymousfox|binance|videoi\.co\.jp|cybozu\.com|dpro-tools\.vercel\.app"
)


def check_user_agent_suspicious(user_agent: str) -> Dict[str, Any]:
    """ユーザーエージェント文字列が不審かどうかを確認します。

    定義された正規表現パターンに基づいて、ユーザーエージェントが不審または
    ブロックすべきものかを判定します。許可されたボット、ブロックすべきツール、
    不審なパターンを階層的にチェックします。

    Args:
        user_agent (str): チェックするユーザーエージェント文字列
            例: "Mozilla/5.0...", "Python-urllib/3.8", "Googlebot"

    Returns:
        Dict[str, Any]: 確認結果を含む辞書。以下のキーが含まれます:
            - is_suspicious (bool): 不審なパターンに一致した場合True
            - is_blocked (bool): ブロックすべきパターンに一致した場合True
            - is_allowed_bot (bool): 許可されたボットの場合True
            - matched_patterns (List[str]): マッチしたパターンのリスト
            - severity (str): 深刻度 ("safe", "warning", "danger")

    Example:
        >>> check_user_agent_suspicious("Googlebot")
        {'is_suspicious': False, 'is_blocked': False, 'is_allowed_bot': True,
         'matched_patterns': ['Allowed: Google bot'], 'severity': 'safe'}
        >>> check_user_agent_suspicious("Python-urllib/3.8")
        {'is_suspicious': True, 'is_blocked': True, 'is_allowed_bot': False,
         'matched_patterns': ['Blocked: Scraping tool'], 'severity': 'danger'}
    """
    results = {
        "is_suspicious": False,
        "is_blocked": False,
        "is_allowed_bot": False,
        "matched_patterns": [],
        "severity": "safe",  # safe, warning, danger
    }

    if not user_agent or user_agent == "-":
        return results

    # まず許可されたボットを確認（これらはOK）
    if ALLOWED_TOP_LEVEL.search(user_agent):
        results["is_allowed_bot"] = True
        results["matched_patterns"].append("Allowed: Top level bot")
        return results

    if ALLOWED_GOOGLE_UR_1.search(user_agent) or ALLOWED_GOOGLE_UR_2.search(user_agent):
        results["is_allowed_bot"] = True
        results["matched_patterns"].append("Allowed: Google bot")
        return results

    if ALLOWED_BOTS_UA.search(user_agent):
        results["is_allowed_bot"] = True
        results["matched_patterns"].append("Allowed: Known bot")
        return results

    # ブロックされたパターンを確認（これらは悪い）
    if BLOCKED_ARCHIVE_TOOLS_UA.search(user_agent):
        results["is_blocked"] = True
        results["is_suspicious"] = True
        results["severity"] = "danger"
        results["matched_patterns"].append("Blocked: Archive tool")

    if BLOCKED_SCRAPING_TOOLS_UA.search(user_agent):
        results["is_blocked"] = True
        results["is_suspicious"] = True
        results["severity"] = "danger"
        results["matched_patterns"].append("Blocked: Scraping tool")

    if BLOCKED_SEO_TOOLS_UA.search(user_agent):
        results["is_blocked"] = True
        results["is_suspicious"] = True
        results["severity"] = "danger"
        results["matched_patterns"].append("Blocked: SEO tool")

    if BLOCKED_OTHER_TOOLS_UA.search(user_agent):
        results["is_blocked"] = True
        results["is_suspicious"] = True
        results["severity"] = "danger"
        results["matched_patterns"].append("Blocked: Other tool")

    if BLOCKED_MINOR_SEARCH_ENGINES_UA.search(user_agent):
        results["is_blocked"] = True
        results["is_suspicious"] = True
        results["severity"] = "danger"
        results["matched_patterns"].append("Blocked: Minor search engine")

    # 不審なパターンを確認（これらは不審）
    if SUSPICIOUS_UA.search(user_agent):
        results["is_suspicious"] = True
        results["severity"] = (
            "warning" if results["severity"] == "safe" else results["severity"]
        )
        results["matched_patterns"].append("Suspicious: Unusual user agent")

    if POTENTIAL_BOTS_UA.search(user_agent) and not results["is_allowed_bot"]:
        results["is_suspicious"] = True
        results["severity"] = (
            "warning" if results["severity"] == "safe" else results["severity"]
        )
        results["matched_patterns"].append("Suspicious: Potential bot")

    return results


def check_referrer_suspicious(referrer: str) -> Dict[str, Any]:
    """
    リファラーが不審かどうかを確認

    Returns:
        確認結果とマッチしたパターンを含むDictionary
    """
    results = {
        "is_suspicious": False,
        "is_blocked": False,
        "matched_patterns": [],
        "severity": "safe",
    }

    if not referrer or referrer == "-":
        return results

    if BLOCKED_REFERRER.search(referrer):
        results["is_blocked"] = True
        results["is_suspicious"] = True
        results["severity"] = "danger"
        results["matched_patterns"].append("Blocked: Suspicious referrer")

    return results


def check_path_suspicious(uri_stem: str) -> Dict[str, Any]:
    """
    リクエストパスが不審かどうかを確認

    Returns:
        確認結果とマッチしたパターンを含むDictionary
    """
    results = {"is_suspicious": False, "matched_patterns": [], "severity": "safe"}

    if not uri_stem:
        return results

    if SUSPICIOUS_REQ_PATH.search(uri_stem):
        results["is_suspicious"] = True
        results["severity"] = "warning"
        results["matched_patterns"].append("Suspicious: Company info page access")

    return results


def detect_device_type(user_agent: str) -> str:
    """ユーザーエージェント文字列からデバイスタイプを検出します。

    ユーザーエージェント文字列を解析して、アクセス元のデバイスタイプを判定します。
    ボット、モバイル、デスクトップ、不明の4つのカテゴリに分類します。

    Args:
        user_agent (str): 解析するユーザーエージェント文字列
            例: "Mozilla/5.0 (iPhone; CPU iPhone OS...)"

    Returns:
        str: デバイスタイプ
            - 'bot': ボットまたはクローラー
            - 'mobile': モバイルデバイス
            - 'desktop': デスクトップPC
            - 'unknown': 判定不可能

    Example:
        >>> detect_device_type("Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)")
        'mobile'
        >>> detect_device_type("Googlebot/2.1")
        'bot'
        >>> detect_device_type("Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        'desktop'
    """
    if not user_agent or user_agent == "-":
        return "unknown"

    ua_lower = user_agent.lower()

    # まずボットかどうかを確認
    if "bot" in ua_lower or "spider" in ua_lower or "crawler" in ua_lower:
        return "bot"

    # モバイルデバイスを確認
    mobile_patterns = [
        "mobile",
        "android",
        "iphone",
        "ipad",
        "ipod",
        "blackberry",
        "windows phone",
    ]
    if any(pattern in ua_lower for pattern in mobile_patterns):
        return "mobile"

    # デスクトップインジケータを確認
    desktop_patterns = ["windows", "macintosh", "linux", "x11"]
    if any(pattern in ua_lower for pattern in desktop_patterns):
        return "desktop"

    return "unknown"


def analyze_log_entries(log_entries: List[Dict]) -> List[Dict]:
    """複数のログエントリを横断的に分析して不審なパターンを検出します。

    単一ログのパターンマッチングに加えて、複数のログエントリを横断的に分析し、
    IPベースの不審な行動パターンを検出します。

    分析内容:
    - 同じIPからの複数回のアクセス
    - 同じIPから異なるデバイスタイプでのアクセス
    - ユーザーエージェント、リファラー、パスの個別パターン

    Args:
        log_entries (List[Dict]): 分析対象のログエントリのリスト
            各エントリには以下のキーが必要:
            - clientIp (str): クライアントIPアドレス
            - userAgent (str): ユーザーエージェント
            - referrer (str): リファラー
            - uriStem (str): リクエストパス

    Returns:
        List[Dict]: 不審性チェック結果が追加されたログエントリのリスト。
            各エントリに 'suspiciousCheck' キーが追加されます。

    Example:
        >>> logs = [
        ...     {'clientIp': '1.2.3.4', 'userAgent': 'Python', ...},
        ...     {'clientIp': '1.2.3.4', 'userAgent': 'Chrome', ...}
        ... ]
        >>> analyzed = analyze_log_entries(logs)
        >>> analyzed[0]['suspiciousCheck']['isSuspicious']
        True
    """
    # IPごとのアクセス数をカウントし、デバイスタイプを追跡
    ip_stats = {}

    for entry in log_entries:
        client_ip = entry.get("clientIp", "")
        user_agent = entry.get("userAgent", "")

        if client_ip not in ip_stats:
            ip_stats[client_ip] = {
                "count": 0,
                "device_types": set(),
                "user_agents": set(),
            }

        ip_stats[client_ip]["count"] += 1
        ip_stats[client_ip]["device_types"].add(detect_device_type(user_agent))
        ip_stats[client_ip]["user_agents"].add(user_agent)

    # 各エントリを分析
    for entry in log_entries:
        client_ip = entry.get("clientIp", "")
        user_agent = entry.get("userAgent", "")
        referrer = entry.get("referrer", "")
        uri_stem = entry.get("uriStem", "")

        # 個別のパターンを確認
        ua_check = check_user_agent_suspicious(user_agent)
        ref_check = check_referrer_suspicious(referrer)
        path_check = check_path_suspicious(uri_stem)

        # IPベースのパターンを確認
        ip_check = {"is_suspicious": False, "matched_patterns": [], "severity": "safe"}

        # 同じIPからの複数のアクセス
        if ip_stats[client_ip]["count"] >= 3:
            ip_check["is_suspicious"] = True
            ip_check["severity"] = "warning"
            ip_check["matched_patterns"].append(
                f"Multiple accesses from same IP ({ip_stats[client_ip]['count']} times)"
            )

        # 複数のデバイスタイプを持つ同じIP（'unknown'と'bot'を除く）
        device_types = ip_stats[client_ip]["device_types"] - {"unknown", "bot"}
        if len(device_types) > 1:
            ip_check["is_suspicious"] = True
            ip_check["severity"] = "warning"
            ip_check["matched_patterns"].append(
                f"Same IP with multiple device types: {', '.join(device_types)}"
            )

        # すべてのチェックを結合
        all_patterns = (
            ua_check["matched_patterns"]
            + ref_check["matched_patterns"]
            + path_check["matched_patterns"]
            + ip_check["matched_patterns"]
        )

        is_suspicious = (
            ua_check["is_suspicious"]
            or ref_check["is_suspicious"]
            or path_check["is_suspicious"]
            or ip_check["is_suspicious"]
        )

        is_blocked = ua_check["is_blocked"] or ref_check["is_blocked"]

        # 総合的な深刻度を判定
        severities = [
            ua_check["severity"],
            ref_check["severity"],
            path_check["severity"],
            ip_check["severity"],
        ]

        if "danger" in severities:
            overall_severity = "danger"
        elif "warning" in severities:
            overall_severity = "warning"
        else:
            overall_severity = "safe"

        # エントリに不審なチェック結果を追加
        entry["suspiciousCheck"] = {
            "isSuspicious": is_suspicious,
            "isBlocked": is_blocked,
            "isAllowedBot": ua_check["is_allowed_bot"],
            "severity": overall_severity,
            "matchedPatterns": all_patterns,
            "details": {
                "userAgent": ua_check,
                "referrer": ref_check,
                "path": path_check,
                "ip": ip_check,
            },
        }

    return log_entries
