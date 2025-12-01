"""ログマーキング機能のビュー。"""

from django.db import models as django_models
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import LogMarkPattern

from .serializers import LogMarkPatternCreateSerializer
from .serializers import LogMarkPatternSerializer


@api_view(["GET", "POST"])
def log_mark_patterns_list(request):
    """LogMarkPatternの一覧取得と作成。

    GET: すべてのアクティブなマーキングパターンを取得
    POST: 新しいマーキングパターンを作成

    Query Parameters (GET):
        distribution_id (str, optional): Distribution IDでフィルタ
        mark_type (str, optional): マーク種別でフィルタ (bot, suspicious, legitimate)
        is_active (bool, optional): アクティブ状態でフィルタ

    Request Body (POST):
        {
            "distribution_id": "E1234567890ABC",  // optional
            "user_agent_pattern": "Googlebot",
            "match_type": "partial",  // "exact" or "partial"
            "mark_type": "bot",  // "bot", "suspicious", or "legitimate"
            "note": "Google's crawler",  // optional
            "is_active": true
        }

    Returns:
        GET: List of LogMarkPattern objects
        POST: Created LogMarkPattern object
    """
    if request.method == "GET":
        patterns = LogMarkPattern.objects.all()

        # フィルタリング
        distribution_id = request.query_params.get("distribution_id")
        if distribution_id:
            patterns = patterns.filter(distribution_id=distribution_id)

        mark_type = request.query_params.get("mark_type")
        if mark_type:
            patterns = patterns.filter(mark_type=mark_type)

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            patterns = patterns.filter(is_active=is_active.lower() == "true")

        serializer = LogMarkPatternSerializer(patterns, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = LogMarkPatternCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def log_mark_pattern_detail(request, pk):
    """LogMarkPatternの詳細取得、更新、削除。

    GET: 特定のマーキングパターンを取得
    PUT: マーキングパターンを更新
    DELETE: マーキングパターンを削除

    Args:
        pk (int): LogMarkPattern ID

    Request Body (PUT):
        {
            "distribution_id": "E1234567890ABC",
            "user_agent_pattern": "Googlebot",
            "match_type": "partial",
            "mark_type": "bot",
            "note": "Updated note",
            "is_active": false
        }

    Returns:
        GET: LogMarkPattern object
        PUT: Updated LogMarkPattern object
        DELETE: 204 No Content
    """
    try:
        pattern = LogMarkPattern.objects.get(pk=pk)
    except LogMarkPattern.DoesNotExist:
        return Response(
            {"error": "Pattern not found"}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        serializer = LogMarkPatternSerializer(pattern)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = LogMarkPatternCreateSerializer(pattern, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        pattern.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def check_log_marks(request):
    """ログエントリのリストに対してマークをチェック。

    複数のログエントリに対して、登録されているパターンに
    マッチするかをチェックし、マーク情報を返します。

    Request Body:
        {
            "distribution_id": "E1234567890ABC",
            "logs": [
                {
                    "user_agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
                    "log_id": "unique_log_id_1"
                },
                ...
            ]
        }

    Returns:
        {
            "marks": {
                "unique_log_id_1": {
                    "mark_type": "bot",
                    "pattern": "Googlebot",
                    "note": "Google's crawler"
                },
                ...
            }
        }
    """
    distribution_id = request.data.get("distribution_id")
    logs = request.data.get("logs", [])

    if not logs:
        return Response({"marks": {}})

    # アクティブなパターンを取得
    patterns = LogMarkPattern.objects.filter(is_active=True)
    if distribution_id:
        # distribution_id指定のパターンと全Distribution対象のパターン
        patterns = patterns.filter(
            django_models.Q(distribution_id=distribution_id)
            | django_models.Q(distribution_id__isnull=True)
            | django_models.Q(distribution_id="")
        )

    marks = {}
    for log in logs:
        user_agent = log.get("user_agent", "")
        log_id = log.get("log_id")

        if not user_agent or not log_id:
            continue

        # パターンマッチング（優先度: distribution指定 > 全体）
        matched_pattern = None
        for pattern in patterns:
            if pattern.matches(user_agent):
                # distribution指定のパターンを優先
                if (
                    matched_pattern is None
                    or pattern.distribution_id
                    and not matched_pattern.distribution_id
                ):
                    matched_pattern = pattern

        if matched_pattern:
            marks[log_id] = {
                "mark_type": matched_pattern.mark_type,
                "pattern": matched_pattern.user_agent_pattern,
                "note": matched_pattern.note or "",
            }

    return Response({"marks": marks})
