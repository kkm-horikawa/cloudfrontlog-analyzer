"""
Log Marking Models

LogMarkPattern モデルは、User-Agent パターンに基づいてログにマークを付けるためのパターンを保存します。
"""

from django.db import models


class LogMarkPattern(models.Model):
    """複数条件でログにマークを付けるパターン設定。

    Attributes:
        distribution_id: 対象のDistribution ID（省略時は全Distribution対象）
        user_agent_pattern: マッチング対象のUser-Agentパターン（省略可）
        ip_pattern: マッチング対象のIPアドレスパターン（省略可）
        path_pattern: マッチング対象のパスパターン（省略可）
        query_string_pattern: マッチング対象のクエリストリングパターン（省略可）
        referrer_pattern: マッチング対象のリファラパターン（省略可）
        match_type: マッチング方法（exact/partial）
        mark_type: マークの種類（bot/suspicious/legitimate）
        note: メモ・説明
        is_active: アクティブフラグ
        created_at: 作成日時
        updated_at: 更新日時
    """

    MATCH_TYPE_CHOICES = [
        ("exact", "Exact Match"),
        ("partial", "Partial Match"),
    ]

    MARK_TYPE_CHOICES = [
        ("bot", "Bot"),
        ("suspicious", "Suspicious"),
        ("legitimate", "Legitimate"),
    ]

    distribution_id = models.CharField(
        max_length=100,
        db_index=True,
        null=True,
        blank=True,
        help_text="対象のDistribution ID（省略時は全Distribution対象）",
    )
    user_agent_pattern = models.CharField(
        max_length=500,
        db_index=True,
        null=True,
        blank=True,
        help_text="マッチング対象のUser-Agentパターン",
    )
    ip_pattern = models.CharField(
        max_length=100,
        db_index=True,
        null=True,
        blank=True,
        help_text="マッチング対象のIPアドレスパターン",
    )
    path_pattern = models.CharField(
        max_length=500,
        db_index=True,
        null=True,
        blank=True,
        help_text="マッチング対象のパスパターン",
    )
    query_string_pattern = models.CharField(
        max_length=500,
        db_index=True,
        null=True,
        blank=True,
        help_text="マッチング対象のクエリストリングパターン",
    )
    referrer_pattern = models.CharField(
        max_length=500,
        db_index=True,
        null=True,
        blank=True,
        help_text="マッチング対象のリファラパターン",
    )
    org_pattern = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        help_text="マッチング対象の組織名パターン（IPGeolocationのorg/isp/asnameと照合）",
    )
    match_type = models.CharField(
        max_length=10,
        choices=MATCH_TYPE_CHOICES,
        default="partial",
        help_text="マッチング方法",
    )
    mark_type = models.CharField(
        max_length=20, choices=MARK_TYPE_CHOICES, db_index=True, help_text="マークの種類"
    )
    note = models.TextField(null=True, blank=True, help_text="メモ・説明")
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="アクティブフラグ"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "log_mark_patterns"
        ordering = ["-created_at"]
        verbose_name = "Log Mark Pattern"
        verbose_name_plural = "Log Mark Patterns"

    def __str__(self):
        patterns = []
        if self.user_agent_pattern:
            patterns.append(f"UA:{self.user_agent_pattern[:20]}")
        if self.ip_pattern:
            patterns.append(f"IP:{self.ip_pattern}")
        if self.path_pattern:
            patterns.append(f"Path:{self.path_pattern[:20]}")
        if self.query_string_pattern:
            patterns.append(f"QS:{self.query_string_pattern[:20]}")
        if self.referrer_pattern:
            patterns.append(f"Ref:{self.referrer_pattern[:20]}")
        if self.org_pattern:
            patterns.append(f"Org:{self.org_pattern[:20]}")
        pattern_str = " & ".join(patterns) if patterns else "No pattern"
        return f"{self.mark_type}: {pattern_str} ({self.match_type})"

    def matches(
        self,
        user_agent: str = None,
        ip_address: str = None,
        path: str = None,
        query_string: str = None,
        referrer: str = None,
        org_info: dict = None,
    ) -> bool:
        """指定された条件がこのパターンにマッチするかをチェック。

        すべての指定されたパターン条件にマッチする必要があります（AND条件）。

        Args:
            user_agent: チェック対象のUser-Agent文字列
            ip_address: チェック対象のIPアドレス
            path: チェック対象のパス
            query_string: チェック対象のクエリストリング
            referrer: チェック対象のリファラ
            org_info: チェック対象の組織情報（org, isp, asnameを含む辞書）

        Returns:
            bool: すべての条件にマッチする場合True、しない場合False
        """
        if not self.is_active:
            return False

        # 少なくとも1つの条件が設定されている必要がある
        if (
            not self.user_agent_pattern
            and not self.ip_pattern
            and not self.path_pattern
            and not self.query_string_pattern
            and not self.referrer_pattern
            and not self.org_pattern
        ):
            return False

        # User-Agentチェック
        if self.user_agent_pattern:
            if not user_agent:
                return False
            if self.match_type == "exact":
                if user_agent != self.user_agent_pattern:
                    return False
            else:  # partial
                if self.user_agent_pattern.lower() not in user_agent.lower():
                    return False

        # IPアドレスチェック
        if self.ip_pattern:
            if not ip_address:
                return False
            if self.match_type == "exact":
                if ip_address != self.ip_pattern:
                    return False
            else:  # partial
                if self.ip_pattern.lower() not in ip_address.lower():
                    return False

        # パスチェック
        if self.path_pattern:
            if not path:
                return False
            if self.match_type == "exact":
                if path != self.path_pattern:
                    return False
            else:  # partial
                if self.path_pattern.lower() not in path.lower():
                    return False

        # クエリストリングチェック
        if self.query_string_pattern:
            if not query_string:
                return False
            if self.match_type == "exact":
                if query_string != self.query_string_pattern:
                    return False
            else:  # partial
                if self.query_string_pattern.lower() not in query_string.lower():
                    return False

        # リファラチェック
        if self.referrer_pattern:
            if not referrer:
                return False
            if self.match_type == "exact":
                if referrer != self.referrer_pattern:
                    return False
            else:  # partial
                if self.referrer_pattern.lower() not in referrer.lower():
                    return False

        # 組織名チェック
        if self.org_pattern:
            if not org_info:
                return False

            # org, isp, asnameのいずれかにマッチするかチェック
            org_fields = [
                org_info.get("org", ""),
                org_info.get("isp", ""),
                org_info.get("asname", ""),
            ]

            matched = False
            for field_value in org_fields:
                if not field_value:
                    continue

                # field_valueを文字列に変換（数値型の可能性に対応）
                field_value_str = str(field_value) if field_value is not None else ""
                if not field_value_str:
                    continue

                if self.match_type == "exact":
                    if field_value_str == self.org_pattern:
                        matched = True
                        break
                else:  # partial
                    if self.org_pattern.lower() in field_value_str.lower():
                        matched = True
                        break

            if not matched:
                return False

        return True
