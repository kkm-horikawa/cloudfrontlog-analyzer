# テストディレクトリ構造

## 概要

CloudFront Analyzerのテストは、目的別に明確に分離された構造になっています。

## ディレクトリ構成

```
api/tests/
├── __init__.py                         # パッケージ初期化
├── conftest.py                         # pytest設定・共通フィクスチャ
├── README.md                           # テスト全体の概要
├── README_SNAPSHOT_TESTING.md          # スナップショットテスト使用方法
├── STRUCTURE.md                        # このファイル
│
├── design/                             # テスト設計書（2,188ケース）
│   ├── README.md                       # 設計書の読み方・使い方
│   ├── TEST_SUMMARY.md                 # 全テストケース要約
│   ├── TEST_DESIGN_COMPREHENSIVE.md    # 総合テスト設計（旧版）
│   ├── distributions/
│   │   └── API_DISTRIBUTIONS.md        # 66ケース
│   ├── logs/
│   │   ├── API_RAW_LOGS.md             # 192ケース
│   │   └── API_LOG_SEARCH.md           # 140ケース
│   ├── geo/
│   │   └── API_GEO_LOGS.md             # 172ケース
│   ├── ip_info/
│   │   └── API_IP_INFO.md              # 143ケース
│   ├── waf/
│   │   ├── API_WAF_IP_SETS.md          # 131ケース
│   │   ├── API_WAF_BLOCKED_IPS.md      # 150ケース
│   │   └── API_WAF_BLOCKLIST_OPS.md    # 192ケース
│   ├── security/
│   │   └── API_SECURITY_CHECKS.md      # 192ケース
│   ├── whois/
│   │   └── API_WHOIS.md                # 125ケース
│   ├── models/
│   │   └── MODELS_TEST_DESIGN.md       # 138ケース
│   ├── serializers/
│   │   └── SERIALIZERS_TEST_DESIGN.md  # 172ケース
│   ├── services/
│   │   └── SERVICES_TEST_DESIGN.md     # 225ケース
│   └── utils/
│       └── UTILS_TEST_DESIGN.md        # 150ケース
│
├── fixtures/                           # テストユーティリティ
│   ├── __init__.py
│   └── snapshot_helpers.py             # スナップショット比較ヘルパー
│
├── scripts/                            # テスト支援スクリプト
│   ├── __init__.py
│   └── collect_golden_data.py          # ゴールデンデータ収集スクリプト
│
├── data/                               # テストデータ
│   └── golden/                         # ゴールデンデータ（Parquet形式）
│       └── .gitkeep
│
├── unit/                               # ユニットテスト
│   ├── __init__.py
│   ├── test_models.py                  # (未実装) Djangoモデルのテスト
│   ├── test_serializers.py             # (未実装) DRF Serializerのテスト
│   ├── test_services.py                # (未実装) ビジネスロジックのテスト
│   └── test_utils.py                   # (未実装) ユーティリティ関数のテスト
│
├── integration/                        # 統合テスト
│   ├── __init__.py
│   ├── test_api_distributions.py       # (未実装) Distributions API統合テスト
│   ├── test_api_logs.py                # (未実装) Logs API統合テスト
│   ├── test_api_geo.py                 # (未実装) Geo API統合テスト
│   ├── test_api_ip_info.py             # (未実装) IP Info API統合テスト
│   ├── test_api_waf.py                 # (未実装) WAF API統合テスト
│   ├── test_api_security.py            # (未実装) Security API統合テスト
│   └── test_api_whois.py               # (未実装) WHOIS API統合テスト
│
└── snapshot/                           # スナップショットテスト（実装済み）
    ├── __init__.py
    ├── test_raw_logs.py                # ✓ Raw Logs API (12テスト)
    ├── test_geo_logs.py                # ✓ Geo Logs API (10テスト)
    └── test_waf.py                     # ✓ WAF API (8テスト)
```

## ディレクトリの役割

### `design/` - テスト設計書
- **目的**: 実装すべきテストケースの完全な設計書
- **内容**: 2,188テストケースの詳細仕様
- **対象者**: テスト実装者、レビュアー
- **更新頻度**: 機能追加時のみ

### `fixtures/` - テストユーティリティ
- **目的**: テスト実装で共通利用するヘルパー関数
- **内容**: スナップショット比較、モックデータ生成等
- **対象者**: テスト実装者
- **更新頻度**: ユーティリティ追加時

### `scripts/` - テスト支援スクリプト
- **目的**: テスト準備・メンテナンス用のスクリプト
- **内容**: ゴールデンデータ収集、テストデータ生成等
- **対象者**: テスト管理者
- **更新頻度**: テストデータ更新時

### `data/golden/` - ゴールデンデータ
- **目的**: スナップショットテストの基準データ
- **形式**: Parquet (zstd最大圧縮)
- **対象者**: スナップショットテスト
- **更新頻度**: 意図的なAPI変更時

### `unit/` - ユニットテスト
- **目的**: 個々のコンポーネント（モデル、Serializer、Service、Utils）の単体テスト
- **実装状況**: 未実装（設計書のみ）
- **設計**: `design/models/`, `design/serializers/`, `design/services/`, `design/utils/`
- **テスト数**: 685ケース（予定）

### `integration/` - 統合テスト
- **目的**: APIエンドポイントの統合テスト（DB、外部API含む）
- **実装状況**: 未実装（設計書のみ）
- **設計**: `design/distributions/`, `design/logs/`, `design/geo/`, 等
- **テスト数**: 1,503ケース（予定）

### `snapshot/` - スナップショットテスト
- **目的**: APIレスポンスのレグレッション検出
- **実装状況**: 実装済み（29テスト）
- **依存**: `data/golden/` のゴールデンデータ
- **実行**: `pytest -m snapshot`

## テスト実行方法

### すべてのテスト
```bash
docker compose exec backend sh -c "cd /app && uv run pytest -v"
```

### カテゴリ別

#### スナップショットテストのみ
```bash
docker compose exec backend sh -c "cd /app && uv run pytest -v -m snapshot"
```

#### ユニットテストのみ
```bash
docker compose exec backend sh -c "cd /app && uv run pytest -v api/tests/unit/"
```

#### 統合テストのみ
```bash
docker compose exec backend sh -c "cd /app && uv run pytest -v api/tests/integration/"
```

#### 特定のファイル
```bash
docker compose exec backend sh -c "cd /app && uv run pytest -v api/tests/snapshot/test_raw_logs.py"
```

### カバレッジ測定
```bash
docker compose exec backend sh -c "cd /app && uv run pytest --cov=api --cov-report=html"
```

## 実装ステータス

| カテゴリ | 設計 | 実装 | 実装率 |
|---------|------|------|--------|
| **スナップショット** | 100ケース | 29ケース | 29% |
| **ユニット** | 685ケース | 0ケース | 0% |
| **統合** | 1,503ケース | 0ケース | 0% |
| **合計** | **2,188ケース** | **29ケース** | **1.3%** |

## 実装優先順位

### フェーズ1: 基盤テスト（Week 1-2）
1. `unit/test_models.py` (138ケース)
2. `unit/test_serializers.py` (172ケース)
3. `unit/test_utils.py` (150ケース)

### フェーズ2: コアAPI（Week 3-4）
4. `integration/test_api_distributions.py` (66ケース)
5. `integration/test_api_logs.py` (332ケース)
6. `integration/test_api_geo.py` (172ケース)
7. `integration/test_api_ip_info.py` (143ケース)

### フェーズ3: WAFとセキュリティ（Week 5-6）
8. `integration/test_api_waf.py` (473ケース)
9. `integration/test_api_security.py` (192ケース)

### フェーズ4: サービスと残り（Week 7-8）
10. `unit/test_services.py` (225ケース)
11. `integration/test_api_whois.py` (125ケース)

## 命名規則

### ファイル名
- ユニットテスト: `test_{対象}.py` (例: `test_models.py`)
- 統合テスト: `test_api_{エンドポイント}.py` (例: `test_api_logs.py`)
- スナップショット: `test_{エンドポイント}.py` (例: `test_raw_logs.py`)

### テストクラス名
- `Test{対象}` (例: `TestIPGeolocationModel`, `TestRawLogsAPI`)

### テストメソッド名
- `test_{ケースID}_{説明}` (例: `test_RAW_001_basic_request`)
- または `test_{説明}` (例: `test_basic_request`)

## 依存関係

```
design/          →  (設計書のみ、実装に依存なし)
  ↓
unit/            →  models, serializers, services, utils
  ↓
integration/     →  unit/ + API views + DB + 外部API
  ↓
snapshot/        →  integration/ + data/golden/
```

## ベストプラクティス

1. **設計書を先に読む**: 実装前に必ず対応する設計書を確認
2. **小さく始める**: 1ファイルずつ段階的に実装
3. **モックを活用**: 外部API依存を最小化
4. **カバレッジを確認**: 各ファイル実装後にカバレッジ測定
5. **CIで自動実行**: PR毎にすべてのテストを実行

## 参考資料

- [テスト設計書総合README](design/README.md)
- [テストケース要約](design/TEST_SUMMARY.md)
- [スナップショットテスト使用方法](README_SNAPSHOT_TESTING.md)
- [pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/5.2/topics/testing/)
