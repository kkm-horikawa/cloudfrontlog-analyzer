"""
ログマーキング機能のシリアライザー。
"""

from rest_framework import serializers

from api.models import LogMarkCategory, LogMarkPattern


class LogMarkCategorySerializer(serializers.ModelSerializer):
    """LogMarkCategory のシリアライザー。

    Attributes:
        id: カテゴリID
        name: カテゴリ名
        slug: スラッグ
        color: 表示色
        description: 説明
        created_at: 作成日時
        updated_at: 更新日時
    """

    class Meta:
        model = LogMarkCategory
        fields = [
            "id",
            "name",
            "slug",
            "color",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LogMarkPatternSerializer(serializers.ModelSerializer):
    """LogMarkPattern のシリアライザー（読み取り用）。

    Attributes:
        id: パターンID
        distribution_id: Distribution ID
        user_agent_pattern: User-Agentパターン
        ip_pattern: IPアドレスパターン
        path_pattern: パスパターン
        query_string_pattern: クエリストリングパターン
        referrer_pattern: リファラパターン
        org_pattern: 組織名パターン
        match_type: マッチング方法
        category: カテゴリ情報
        note: メモ
        is_active: アクティブフラグ
        created_at: 作成日時
        updated_at: 更新日時
    """

    category = LogMarkCategorySerializer(read_only=True)

    class Meta:
        model = LogMarkPattern
        fields = [
            "id",
            "distribution_id",
            "user_agent_pattern",
            "ip_pattern",
            "path_pattern",
            "query_string_pattern",
            "referrer_pattern",
            "org_pattern",
            "match_type",
            "category",
            "note",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LogMarkPatternCreateSerializer(serializers.ModelSerializer):
    """LogMarkPattern のシリアライザー（作成・更新用）。

    作成・更新時のバリデーションを実施します。
    category_id でカテゴリを指定します。
    """

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=LogMarkCategory.objects.all(),
        source="category",
        write_only=True,
    )

    class Meta:
        model = LogMarkPattern
        fields = [
            "id",
            "distribution_id",
            "user_agent_pattern",
            "ip_pattern",
            "path_pattern",
            "query_string_pattern",
            "referrer_pattern",
            "org_pattern",
            "match_type",
            "category_id",
            "note",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """全体のバリデーション。

        Args:
            data: バリデーション対象のデータ

        Returns:
            dict: バリデーション済みのデータ

        Raises:
            serializers.ValidationError: パターンが1つも指定されていない場合
        """
        user_agent = data.get("user_agent_pattern", "").strip() if data.get("user_agent_pattern") else ""
        ip = data.get("ip_pattern", "").strip() if data.get("ip_pattern") else ""
        path = data.get("path_pattern", "").strip() if data.get("path_pattern") else ""
        query_string = data.get("query_string_pattern", "").strip() if data.get("query_string_pattern") else ""
        referrer = data.get("referrer_pattern", "").strip() if data.get("referrer_pattern") else ""
        org = data.get("org_pattern", "").strip() if data.get("org_pattern") else ""

        if not user_agent and not ip and not path and not query_string and not referrer and not org:
            raise serializers.ValidationError(
                "At least one pattern (user_agent_pattern, ip_pattern, path_pattern, query_string_pattern, referrer_pattern, or org_pattern) must be specified."
            )

        # Trim whitespace
        if user_agent:
            data["user_agent_pattern"] = user_agent
        if ip:
            data["ip_pattern"] = ip
        if path:
            data["path_pattern"] = path
        if query_string:
            data["query_string_pattern"] = query_string
        if referrer:
            data["referrer_pattern"] = referrer
        if org:
            data["org_pattern"] = org

        return data
