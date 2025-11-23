# テスト実行ガイド

## 概要

このプロジェクトでは、**pytest** と **Django Test Framework** の両方でテストを実行できます。

## テスト実行方法

### 方法1: Django標準の`manage.py test`（推奨）

```bash
# すべてのテストを実行
docker compose exec backend sh -c "cd /app && uv run python manage.py test"

# 特定のモジュールを実行
docker compose exec backend sh -c "cd /app && uv run python manage.py test api.tests.snapshot"
docker compose exec backend sh -c "cd /app && uv run python manage.py test api.tests.unit"
docker compose exec backend sh -c "cd /app && uv run python manage.py test api.tests.integration"

# 特定のテストファイルを実行
docker compose exec backend sh -c "cd /app && uv run python manage.py test api.tests.snapshot.test_raw_logs"

# 特定のテストクラスを実行
docker compose exec backend sh -c "cd /app && uv run python manage.py test api.tests.snapshot.test_raw_logs.TestRawLogsSnapshots"

# 特定のテストメソッドを実行
docker compose exec backend sh -c "cd /app && uv run python manage.py test api.tests.snapshot.test_raw_logs.TestRawLogsSnapshots.test_raw_logs_no_filter"
```

### 方法2: pytest直接実行

```bash
# すべてのテストを実行
docker compose exec backend sh -c "cd /app && uv run pytest -v"

# スナップショットテストのみ
docker compose exec backend sh -c "cd /app && uv run pytest -v -m snapshot"

# 特定のディレクトリ
docker compose exec backend sh -c "cd /app && uv run pytest -v api/tests/snapshot/"
docker compose exec backend sh -c "cd /app && uv run pytest -v api/tests/unit/"
docker compose exec backend sh -c "cd /app && uv run pytest -v api/tests/integration/"

# 特定のファイル
docker compose exec backend sh -c "cd /app && uv run pytest -v api/tests/snapshot/test_raw_logs.py"

# 特定のテストメソッド
docker compose exec backend sh -c "cd /app && uv run pytest -v api/tests/snapshot/test_raw_logs.py::TestRawLogsSnapshots::test_raw_logs_no_filter"

# キーワードフィルタリング
docker compose exec backend sh -c "cd /app && uv run pytest -v -k 'raw_logs'"
```

## カバレッジ測定

```bash
# カバレッジ測定（HTMLレポート）
docker compose exec backend sh -c "cd /app && uv run pytest --cov=api --cov-report=html"

# カバレッジ測定（ターミナル表示）
docker compose exec backend sh -c "cd /app && uv run pytest --cov=api --cov-report=term-missing"

# カバレッジ測定（JSON出力）
docker compose exec backend sh -c "cd /app && uv run pytest --cov=api --cov-report=json"
```

カバレッジレポートは `htmlcov/index.html` に生成されます。

## テストマーカー

pytestマーカーを使ってテストをフィルタリングできます：

```bash
# django_db マーカー（データベース使用テスト）
docker compose exec backend sh -c "cd /app && uv run pytest -v -m django_db"

# snapshot マーカー（スナップショットテスト）
docker compose exec backend sh -c "cd /app && uv run pytest -v -m snapshot"

# slow マーカー（遅いテスト）
docker compose exec backend sh -c "cd /app && uv run pytest -v -m slow"

# マーカーの除外
docker compose exec backend sh -c "cd /app && uv run pytest -v -m 'not slow'"
```

## テストオプション

### 詳細出力

```bash
# 詳細出力（-v）
docker compose exec backend sh -c "cd /app && uv run pytest -v"

# さらに詳細（-vv）
docker compose exec backend sh -c "cd /app && uv run pytest -vv"

# 最も詳細（-vvv）
docker compose exec backend sh -c "cd /app && uv run pytest -vvv"
```

### 失敗時の動作

```bash
# 最初の失敗で停止
docker compose exec backend sh -c "cd /app && uv run pytest -x"

# 指定回数失敗で停止
docker compose exec backend sh -c "cd /app && uv run pytest --maxfail=3"

# 失敗時にpdbデバッガ起動
docker compose exec backend sh -c "cd /app && uv run pytest --pdb"
```

### 並列実行

```bash
# 4プロセスで並列実行（pytest-xdistが必要）
docker compose exec backend sh -c "cd /app && uv run pytest -n 4"

# 自動並列数
docker compose exec backend sh -c "cd /app && uv run pytest -n auto"
```

### 出力制御

```bash
# print文の出力を表示
docker compose exec backend sh -c "cd /app && uv run pytest -s"

# ログ出力を表示
docker compose exec backend sh -c "cd /app && uv run pytest --log-cli-level=INFO"

# 警告を表示
docker compose exec backend sh -c "cd /app && uv run pytest -W default"
```

## テストデータベース

### テストDBの保持

```bash
# テストDB削除をスキップ（次回高速化）
docker compose exec backend sh -c "cd /app && uv run python manage.py test --keepdb"
docker compose exec backend sh -c "cd /app && uv run pytest --reuse-db"

# テストDB再作成
docker compose exec backend sh -c "cd /app && uv run pytest --create-db"
```

### テストDBの確認

```bash
# テスト時にDBの状態を確認
docker compose exec backend sh -c "cd /app && uv run python manage.py test --debug-sql"
```

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

      - name: Start services
        run: docker compose up -d

      - name: Run all tests
        run: |
          docker compose exec -T backend sh -c "cd /app && uv run python manage.py test"

      - name: Run with coverage
        run: |
          docker compose exec -T backend sh -c "cd /app && uv run pytest --cov=api --cov-report=xml"

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## トラブルシューティング

### Q: テストが見つからない

**A:** テストファイルが以下の規則に従っているか確認：
- ファイル名: `test_*.py`
- クラス名: `Test*`
- メソッド名: `test_*`

### Q: インポートエラー

**A:** Djangoの設定が正しいか確認：
```bash
docker compose exec backend sh -c "cd /app && uv run python manage.py check"
```

### Q: データベースエラー

**A:** マイグレーションを実行：
```bash
docker compose exec backend sh -c "cd /app && uv run python manage.py migrate"
```

### Q: スナップショットテスト失敗

**A:** ゴールデンデータを収集：
```bash
docker compose exec backend sh -c "cd /app && uv run python api/tests/scripts/collect_golden_data.py \
    --distribution-id YOUR_DISTRIBUTION_ID --date 2025-11-13"
```

### Q: カバレッジが低い

**A:** カバレッジレポートを確認して未テストコードを特定：
```bash
docker compose exec backend sh -c "cd /app && uv run pytest --cov=api --cov-report=html"
# htmlcov/index.html を開く
```

## ベストプラクティス

1. **テスト前にチェック**
   ```bash
   docker compose exec backend sh -c "cd /app && uv run python manage.py check"
   docker compose exec backend sh -c "cd /app && uv run python manage.py migrate --check"
   ```

2. **小さく頻繁に実行**
   - 変更したファイルのテストのみ実行
   - `pytest -k "test_name"` でフィルタリング

3. **カバレッジを確認**
   - PR毎にカバレッジ測定
   - 90%以上を目標

4. **並列実行で高速化**
   - `pytest -n auto` で並列実行
   - ただしDBトランザクションに注意

5. **失敗時はデバッグ**
   ```bash
   docker compose exec backend sh -c "cd /app && uv run pytest --pdb -x"
   ```

## テストの種類と実行時間の目安

| テスト種類 | テスト数 | 実行時間 | 実行頻度 |
|----------|--------|---------|---------|
| スナップショット | 29 | 10秒 | 毎PR |
| ユニット（予定） | 685 | 30秒 | 毎PR |
| 統合（予定） | 1,503 | 120秒 | 毎PR |
| パフォーマンス（予定） | 120 | 300秒 | Nightly |
| **合計** | **2,188** | **460秒** | - |

## 参考資料

- [pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/5.2/topics/testing/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [テスト設計書](design/README.md)
- [スナップショットテスト](README_SNAPSHOT_TESTING.md)
