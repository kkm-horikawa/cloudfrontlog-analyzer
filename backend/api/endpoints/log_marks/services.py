"""ログマーキング機能のサービス層。"""

from typing import Dict, List, Optional

from django.db import models as django_models

from api.models import LogMarkPattern


def get_log_marks_for_logs(
    logs: List[Dict], distribution_id: Optional[str] = None
) -> Dict[str, Dict]:
    """ログエントリのリストに対してマーク情報を取得。

    Args:
        logs (List[Dict]): ログエントリのリスト
            各ログには 'userAgent' キーが必要
        distribution_id (Optional[str]): Distribution ID
            指定された場合、そのDistribution用のパターンを優先

    Returns:
        Dict[str, Dict]: User Agentをキーとしたマーク情報の辞書
            例: {
                "Mozilla/5.0 (compatible; Googlebot/2.1)": {
                    "mark_type": "bot",
                    "pattern": "Googlebot",
                    "note": "Google's crawler"
                }
            }

    Example:
        >>> logs = [{"userAgent": "Mozilla/5.0 (compatible; Googlebot/2.1)"}]
        >>> marks = get_log_marks_for_logs(logs, "E1234567890ABC")
        >>> marks["Mozilla/5.0 (compatible; Googlebot/2.1)"]["mark_type"]
        'bot'
    """
    if not logs:
        return {}

    # ユニークなUser Agentを抽出
    unique_user_agents = set()
    for log in logs:
        user_agent = log.get("userAgent") or log.get("user_agent") or ""
        if user_agent:
            unique_user_agents.add(user_agent)

    if not unique_user_agents:
        return {}

    # アクティブなパターンを取得
    patterns = LogMarkPattern.objects.filter(is_active=True)
    if distribution_id:
        # distribution_id指定のパターンと全Distribution対象のパターン
        patterns = patterns.filter(
            django_models.Q(distribution_id=distribution_id)
            | django_models.Q(distribution_id__isnull=True)
            | django_models.Q(distribution_id="")
        )

    # User Agentごとにマッチするパターンを検索
    marks = {}
    for user_agent in unique_user_agents:
        matched_pattern = None

        for pattern in patterns:
            if pattern.matches(user_agent):
                # distribution指定のパターンを優先
                if (
                    matched_pattern is None
                    or (
                        pattern.distribution_id
                        and not matched_pattern.distribution_id
                    )
                ):
                    matched_pattern = pattern

        if matched_pattern:
            marks[user_agent] = {
                "mark_type": matched_pattern.mark_type,
                "pattern": matched_pattern.user_agent_pattern,
                "note": matched_pattern.note or "",
            }

    return marks


def add_marks_to_logs(
    logs: List[Dict], distribution_id: Optional[str] = None
) -> List[Dict]:
    """ログエントリのリストにマーク情報を追加。

    Args:
        logs (List[Dict]): ログエントリのリスト
        distribution_id (Optional[str]): Distribution ID

    Returns:
        List[Dict]: マーク情報が追加されたログエントリのリスト
            各ログに 'mark' キーが追加される

    Example:
        >>> logs = [{"userAgent": "Googlebot/2.1", "clientIp": "1.2.3.4"}]
        >>> marked_logs = add_marks_to_logs(logs, "E1234567890ABC")
        >>> marked_logs[0]["mark"]
        {'mark_type': 'bot', 'pattern': 'Googlebot', 'note': '...'}
    """
    if not logs:
        return logs

    # マーク情報を取得
    marks = get_log_marks_for_logs(logs, distribution_id)

    # 各ログにマーク情報を追加
    for log in logs:
        user_agent = log.get("userAgent") or log.get("user_agent") or ""
        if user_agent and user_agent in marks:
            log["mark"] = marks[user_agent]
        else:
            log["mark"] = None

    return logs


def check_ip_is_bot(ip_address: str, distribution_id: Optional[str] = None) -> Optional[Dict]:
    """IPアドレスが既知のボット組織に属するかをチェック。

    登録されたorg_patternをチェックします。

    Args:
        ip_address (str): チェック対象のIPアドレス
        distribution_id (Optional[str]): Distribution ID（パターンフィルタ用）

    Returns:
        Optional[Dict]: ボットの場合はマーク情報、そうでない場合はNone
            例: {
                "mark_type": "bot",
                "pattern": "Anthropic",
                "note": "Anthropic AI (Claude)"
            }

    Example:
        >>> mark = check_ip_is_bot("1.2.3.4")
        >>> if mark:
        ...     print(f"Bot detected: {mark['note']}")
    """
    from api.models.ip_geolocation import IPGeolocation

    try:
        geo = IPGeolocation.objects.filter(ip_address=ip_address).first()
        if not geo:
            return None

        org_info = {
            "org": geo.org or "",
            "isp": geo.isp or "",
            "asname": geo.asname or "",
        }

        # 登録されたorg_patternをチェック
        patterns = LogMarkPattern.objects.filter(is_active=True, org_pattern__isnull=False)
        if distribution_id:
            patterns = patterns.filter(
                django_models.Q(distribution_id=distribution_id)
                | django_models.Q(distribution_id__isnull=True)
                | django_models.Q(distribution_id="")
            )

        for pattern in patterns:
            if pattern.matches(org_info=org_info):
                return {
                    "mark_type": pattern.mark_type,
                    "pattern": pattern.org_pattern,
                    "note": pattern.note or f"{pattern.org_pattern} (組織マッチ)",
                }

        return None
    except Exception:
        return None
