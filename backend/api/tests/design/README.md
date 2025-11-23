# CloudFront Analyzer - 総合テスト設計書

## 概要

このディレクトリには、CloudFront Analyzerアプリケーションの**完全な**テスト設計書が含まれています。全APIエンドポイント、全モデル、全Serializer、全Service、全ユーティリティ関数の網羅的なテストケースを設計しています。

**合計テストケース数**: **2,100+ケース**

## テスト設計の方針

### 1. 網羅性
- **全APIエンドポイント** (18個) のテスト設計
- **全パラメータパターン** の組み合わせテスト
- **境界値テスト** (最小値、最大値、0件、1件、大量データ)
- **プロパティベーステスト** (ランダムテスト、一貫性テスト)
- **スナップショットテスト** (ゴールデンデータ比較)

### 2. テストピラミッド
```
        /\
       /  \  E2E (50)
      /____\
     /      \  統合テスト (200)
    /________\
   /          \  単体テスト (1200+)
  /__________\
 /            \  スナップショット (100)
/______________\
```

### 3. テストカテゴリ
各テスト設計書には以下のカテゴリが含まれます：

- **正常系テスト**: 基本動作、パラメータバリエーション、レスポンス検証
- **異常系テスト**: 不正な値、必須パラメータ欠如、外部API障害
- **境界値テスト**: 最小値、最大値、特殊ケース
- **パフォーマンステスト**: レスポンスタイム、スループット、メモリ使用量
- **セキュリティテスト**: インジェクション、XSS、認証、Rate Limiting
- **プロパティベーステスト**: ランダムテスト、一貫性テスト
- **スナップショットテスト**: ゴールデンデータ比較
- **統合テスト**: 複数コンポーネント連携

## ディレクトリ構造

```
design/
├── README.md                           # このファイル
├── TEST_SUMMARY.md                     # 全テストケースの要約
├── distributions/
│   └── API_DISTRIBUTIONS.md            # 66ケース
├── logs/
│   ├── API_RAW_LOGS.md                 # 192ケース
│   └── API_LOG_SEARCH.md               # 140ケース
├── geo/
│   └── API_GEO_LOGS.md                 # 172ケース
├── ip_info/
│   └── API_IP_INFO.md                  # 143ケース
├── waf/
│   ├── API_WAF_IP_SETS.md              # 131ケース
│   ├── API_WAF_BLOCKED_IPS.md          # 150ケース
│   └── API_WAF_BLOCKLIST_OPS.md        # 192ケース
├── security/
│   └── API_SECURITY_CHECKS.md          # 192ケース
├── whois/
│   └── API_WHOIS.md                    # 125ケース
├── models/
│   └── MODELS_TEST_DESIGN.md           # 138ケース
├── serializers/
│   └── SERIALIZERS_TEST_DESIGN.md      # 172ケース
├── services/
│   └── SERVICES_TEST_DESIGN.md         # 225ケース
└── utils/
    └── UTILS_TEST_DESIGN.md            # 150ケース
```

## テストケース総数

| カテゴリ | ドキュメント数 | テストケース数 | 行数 |
|---------|--------------|---------------|------|
| **API - Distributions** | 1 | 66 | 280 |
| **API - Logs** | 2 | 332 | 786 |
| **API - Geo** | 1 | 172 | 333 |
| **API - IP Info** | 1 | 143 | 355 |
| **API - WAF** | 3 | 473 | 1,033 |
| **API - Security** | 1 | 192 | 516 |
| **API - WHOIS** | 1 | 125 | 331 |
| **Models** | 1 | 138 | 365 |
| **Serializers** | 1 | 172 | 452 |
| **Services** | 1 | 225 | 573 |
| **Utils** | 1 | 150 | 425 |
| **合計** | **14** | **2,188** | **5,449** |

## APIエンドポイント一覧

### CloudFront Distributions (1エンドポイント)
1. `GET /api/cloudfront/distributions/` - ディストリビューション一覧

### CloudFront Logs (2エンドポイント)
2. `GET /api/cloudfront/logs/raw/` - 生ログ取得（ページネーション）
3. `POST /api/cloudfront/logs/search/` - ログ検索

### Geo Logs (1エンドポイント)
4. `GET /api/cloudfront/logs/geo/` - 地理情報集約ログ

### IP Info (1エンドポイント)
5. `GET /api/ip-info/{ip_address}/` - IP地理情報取得

### WAF Operations (8エンドポイント)
6. `GET /api/waf/ip-sets/` - IPセット一覧
7. `GET /api/waf/blocklist/check/` - ブロックリストチェック
8. `POST /api/waf/blocklist/add/` - IPブロック追加
9. `POST /api/waf/blocklist/remove/` - IPブロック削除
10. `GET /api/waf/blocked-ips/` - ブロック済みIP一覧
11. `GET /api/waf/blocked-ips/export/` - ブロック済みIPエクスポート
12. `GET /api/waf/blocked-ips/geo/` - ブロック済みIP地理分布
13. `GET /api/waf/blocked-ips/geo/detail/` - ブロック済みIP詳細地理情報

### Security Checks (4エンドポイント)
14. `POST /api/checks/company-info-access/` - 会社情報アクセスチェック
15. `POST /api/checks/frequent-ip-access/` - 頻繁IPアクセスチェック
16. `POST /api/checks/multi-device-access/` - マルチデバイスアクセスチェック
17. `POST /api/checks/research-tool-detection/` - リサーチツール検出

### WHOIS (2エンドポイント)
18. `POST /api/whois/batch/fetch/` - WHOISバッチ取得開始
19. `GET /api/whois/batch/status/` - WHOISバッチステータス

## テスト実装の優先順位

### フェーズ1: 基盤テスト（Week 1-2）
**優先度: 最高**
- [ ] Models (138ケース)
- [ ] Serializers (172ケース)
- [ ] Utils (150ケース)
- [ ] スナップショットテストフレームワーク構築

### フェーズ2: コアAPI（Week 3-4）
**優先度: 高**
- [ ] Raw Logs API (192ケース)
- [ ] Geo Logs API (172ケース)
- [ ] IP Info API (143ケース)
- [ ] Distributions API (66ケース)

### フェーズ3: WAFとセキュリティ（Week 5-6）
**優先度: 高**
- [ ] WAF IP Sets API (131ケース)
- [ ] WAF Blocked IPs API (150ケース)
- [ ] WAF Blocklist Operations (192ケース)
- [ ] Security Checks API (192ケース)

### フェーズ4: サービスレイヤー（Week 7）
**優先度: 中**
- [ ] Services (225ケース)
- [ ] Log Search API (140ケース)
- [ ] WHOIS API (125ケース)

### フェーズ5: 統合とパフォーマンス（Week 8）
**優先度: 中**
- [ ] 統合テスト（全エンドポイント連携）
- [ ] パフォーマンステスト（全API）
- [ ] E2Eテスト（ユーザーシナリオ）

### フェーズ6: 最終調整（Week 9）
**優先度: 低**
- [ ] カバレッジ90%達成
- [ ] プロパティベーステスト完全実装
- [ ] CI/CD統合
- [ ] ドキュメント最終化

## テスト実装ガイドライン

### 1. 各テスト設計書の読み方

各設計書には以下が含まれます：

```markdown
# テスト設計: {エンドポイント名}

## エンドポイント情報
- URL, HTTPメソッド, 説明

## パラメータ仕様
- 表形式でパラメータ一覧

## テストケース設計
- カテゴリ別チェックリスト
- 具体的なテストケースID

## 合計テストケース数
- カテゴリ別集計

## テスト実装優先度
- 高・中・低

## 自動化対象
- CI/CD統合方針

## テストデータ
- ゴールデンデータ
- モックデータ

## 依存サービス
- 外部API、AWS、DB
```

### 2. テストケースIDの命名規則

```
{カテゴリ略称}-{種別}-{連番}

例:
- RAW-001: Raw Logs API 正常系テスト #1
- RAW-ERR-001: Raw Logs API 異常系テスト #1
- RAW-EDGE-001: Raw Logs API 境界値テスト #1
- RAW-PERF-001: Raw Logs API パフォーマンステスト #1
- RAW-SEC-001: Raw Logs API セキュリティテスト #1
- RAW-PROP-001: Raw Logs API プロパティベーステスト #1
- RAW-SNAP-001: Raw Logs API スナップショットテスト #1
```

### 3. テスト実装テンプレート

```python
import pytest
from django.test import Client

class TestRawLogsAPI:
    """Raw Logs APIのテスト"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.client = Client()
        self.base_url = "/api/cloudfront/logs/raw/"

    @pytest.mark.django_db
    def test_raw_001_basic_request(self):
        """RAW-001: 必須パラメータのみでログ取得"""
        response = self.client.get(self.base_url, {
            "distributionId": "E1234567890ABC",
            "startDate": "2025-11-13",
            "endDate": "2025-11-13",
        })

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data

    @pytest.mark.django_db
    def test_raw_err_001_missing_distribution_id(self):
        """RAW-ERR-001: distributionId欠如 → 400 Bad Request"""
        response = self.client.get(self.base_url, {
            "startDate": "2025-11-13",
            "endDate": "2025-11-13",
        })

        assert response.status_code == 400
```

### 4. スナップショットテストの実装

```python
from api.tests.fixtures.snapshot_helpers import snapshot_comparator

@pytest.mark.snapshot
def test_raw_snap_001_no_filter(self):
    """RAW-SNAP-001: フィルタなし → ゴールデンデータ一致"""
    response = self.client.get(self.base_url, {...})

    assert response.status_code == 200
    data = response.json()

    snapshot_comparator.assert_matches_snapshot(
        data.get("logs", []),
        "raw_logs_no_filter",
        exclude_fields=["cacheStatus"]
    )
```

### 5. モックの使用

外部API依存のテストではモックを使用：

```python
from unittest.mock import patch, MagicMock

@patch('api.endpoints.logs.services.LogService.search_logs')
def test_with_mock(self, mock_search):
    """外部API呼び出しをモック"""
    mock_search.return_value = {
        "logs": [...],
        "total": 100
    }

    response = self.client.get(...)
    assert response.status_code == 200
    mock_search.assert_called_once()
```

## カバレッジ目標

- **ライン カバレッジ**: 90%以上
- **ブランチ カバレッジ**: 85%以上
- **関数 カバレッジ**: 95%以上

## CI/CD統合

### GitHub Actions設定例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run unit tests
        run: |
          docker compose exec -T backend uv run pytest -v \
            api/tests/test_models.py \
            api/tests/test_serializers.py \
            api/tests/test_utils.py

      - name: Run API tests
        run: |
          docker compose exec -T backend uv run pytest -v \
            api/tests/test_api_*.py

      - name: Run snapshot tests
        run: |
          docker compose exec -T backend uv run pytest -v -m snapshot

      - name: Coverage report
        run: |
          docker compose exec -T backend uv run pytest \
            --cov=api \
            --cov-report=xml \
            --cov-report=html
```

## テストデータ管理

### ゴールデンデータ
- **場所**: `api/tests/data/golden/`
- **形式**: Parquet (zstd圧縮)
- **収集**: `api/tests/scripts/collect_golden_data.py`
- **参照日**: 2025-11-13

### モックデータ
- **場所**: 各テスト設計書内に記載
- **形式**: JSON
- **更新**: 実装時に適宜調整

## 依存サービス

テスト実装時に必要な外部サービス：

1. **AWS CloudFront** - ディストリビューション、ログ
2. **AWS S3** - ログストレージ
3. **AWS WAF** - IPセット、ブロックリスト
4. **ip-api.com** - IP地理情報 (45req/min制限)
5. **WHOISサーバー** - WHOIS情報取得
6. **PostgreSQL** - データベース

## トラブルシューティング

### Q: テストが遅い
A: 外部API呼び出しをモックに置き換えてください

### Q: スナップショットテストが失敗する
A: ゴールデンデータを再収集するか、除外フィールドを追加してください

### Q: AWS認証エラー
A: `~/.aws/credentials`を確認するか、環境変数を設定してください

### Q: カバレッジが低い
A: 各テスト設計書の「高」優先度テストを実装してください

## 参考資料

- [Django Testing Documentation](https://docs.djangoproject.com/en/5.2/topics/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [Property-Based Testing with Hypothesis](https://hypothesis.readthedocs.io/)
- [スナップショットテスト実装ガイド](../README_SNAPSHOT_TESTING.md)

## 貢献ガイドライン

新しいテストを追加する場合：

1. 該当するテスト設計書のチェックリストを確認
2. テストケースIDを使用してテストメソッド名を決定
3. テストを実装し、チェックリストにチェック
4. カバレッジを確認し、90%以上を維持
5. PRを作成し、レビュー依頼

## ライセンス

このテスト設計書はCloudFront Analyzerプロジェクトの一部です。
