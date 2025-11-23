# APIテスト

このディレクトリは、リファクタリング中のリグレッションを防ぐため、すべてのAPIエンドポイントの統合テストを含んでいます。

## テスト構造

```
tests/
├── unit/                         # ユニットテスト（サービス層、ユーティリティ）
├── integration/                  # 統合テスト（API エンドポイント）
├── snapshot/                     # スナップショット/ゴールデンデータテスト
│   ├── test_distributions.py    # ディストリビューション一覧スナップショット
│   ├── test_raw_logs.py         # 生ログ取得スナップショット
│   └── test_geo_logs.py         # 地理情報集約スナップショット
├── fixtures/                     # テスト用フィクスチャとヘルパー
│   ├── snapshot_helpers.py      # ゴールデンデータ比較ロジック
│   └── conftest.py              # 共有フィクスチャとテスト設定
├── data/                        # テストデータ
│   └── golden/                  # ゴールデンデータ（Parquet形式）
├── scripts/                     # テストユーティリティスクリプト
│   └── collect_golden_data.py  # ゴールデンデータ収集スクリプト
└── design/                      # テスト設計書
    ├── TEST_SUMMARY.md         # 全テストケースの要約（2,188ケース）
    ├── distributions/          # ディストリビューションAPI テスト設計
    ├── logs/                   # ログAPI テスト設計
    ├── geo/                    # 地理情報API テスト設計
    ├── ip_info/                # IP情報API テスト設計
    ├── waf/                    # WAF API テスト設計
    ├── security/               # セキュリティチェックAPI テスト設計
    └── whois/                  # WHOIS API テスト設計
```

## テスト実行方法

### すべてのテストを実行
```bash
# Django Test経由（推奨）
docker compose exec backend sh -c "cd /app && uv run python manage.py test"

# pytest直接実行
docker compose exec backend sh -c "cd /app && uv run pytest"
```

### 特定のテストファイルを実行
```bash
docker compose exec backend sh -c "cd /app && uv run pytest api/tests/snapshot/test_distributions.py"
```

### 特定のテストクラスを実行
```bash
docker compose exec backend sh -c "cd /app && uv run pytest api/tests/snapshot/test_raw_logs.py::TestRawLogsSnapshots"
```

### 特定のテスト関数を実行
```bash
docker compose exec backend sh -c "cd /app && uv run pytest api/tests/snapshot/test_raw_logs.py::TestRawLogsSnapshots::test_raw_logs_no_filter"
```

### 詳細出力で実行
```bash
docker compose exec backend sh -c "cd /app && uv run pytest -v"
```

### カバレッジ測定
```bash
docker compose exec backend sh -c "cd /app && uv run pytest --cov=api --cov-report=html"
```

## テストカテゴリ

### 1. ディストリビューションテスト (`snapshot/test_distributions.py`)
- CloudFrontディストリビューション一覧取得
- AWSエラーハンドリング
- レスポンス構造の検証

### 2. ログテスト (`snapshot/test_raw_logs.py`, `snapshot/test_geo_logs.py`)
- ログ検索機能
- フィルタ付き生ログ取得（時間、URI、ステータス、メソッド、リファラー、クエリ）
- 地理情報ログ集約
- ページネーション
- ストリーミングモード

### 3. IP情報テスト (`integration/test_ip_info.py`)
- IPジオロケーション検索
- データベースキャッシング
- WHOIS情報取得
- キャッシュヒット数追跡
- キャッシュ済みIPのオンデマンドWHOIS取得

### 4. WAFテスト (`integration/test_waf.py`)
- IPセット一覧取得
- IPブロック状態確認
- ブロックリストへのIP追加
- ブロックリストからのIP削除
- ブロック済みIP一覧取得
- ブロック済みIPの地理的分布
- ブロック済みIPのCSVエクスポート

### 5. セキュリティチェックテスト (`integration/test_security_checks.py`)
- 企業情報アクセス検出
- 頻繁なIPアクセス検出
- マルチデバイスアクセス検出
- 調査ツール検出

### 6. WHOISテスト (`integration/test_whois.py`)
- バッチWHOIS取得
- バッチ取得ステータス確認
- WHOISキャッシング動作

## フィクスチャ

### 利用可能なフィクスチャ（`fixtures/conftest.py`参照）

- `api_client`: API リクエスト用Django テストクライアント
- `mock_boto3_client`: AWS操作用モックboto3 クライアント
- `sample_distribution`: サンプルCloudFrontディストリビューションデータ
- `sample_log_entry`: サンプルCloudFrontログエントリ
- `sample_ip_info`: サンプルIPジオロケーション情報
- `sample_waf_ip_set`: サンプルWAF IPセットデータ

## 新しいテストの作成

新しいエンドポイントを追加したり、既存のものを変更する場合：

1. リファクタリング前にテストを追加
2. テストが以下をカバーしていることを確認：
   - 成功ケース
   - エラーケース
   - パラメータ欠如
   - レスポンス構造の検証
3. 外部依存関係（AWS、IP-API、WHOIS）にはモックを使用
4. データベーステストには`@pytest.mark.django_db`を付ける

## CI/CD 統合

これらのテストは以下のタイミングで自動実行すべきです：
- プルリクエストマージ前
- デプロイパイプライン中
- リファクタリング変更後

## 注意事項

- テストは実際のAWS API呼び出しや外部APIレート制限を避けるためモックを使用します
- データベーステストはDjangoのテストデータベースを使用します（自動作成・削除）
- WHOISテストはソケット接続のため遅くなる可能性があります（可能な限りモックを使用）

## スナップショットテスト

スナップショットテストは実際のAPIレスポンスとゴールデンデータ（Parquet形式）を比較します：

### ゴールデンデータの収集
```bash
docker compose exec backend sh -c "cd /app && uv run python api/tests/scripts/collect_golden_data.py \
    --base-url http://localhost:8000 \
    --profile default \
    --distribution-id E3K6JPV795PQRV \
    --date 2025-11-13"
```

### スナップショットテストの実行
```bash
docker compose exec backend sh -c "cd /app && uv run pytest -m snapshot"
```
