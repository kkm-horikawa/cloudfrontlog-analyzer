# ゴールデンデータ

スナップショットテスト用の基準データ（Parquet形式、zstd最大圧縮）

## データ内容

- **distributions_list.parquet**: CloudFrontディストリビューション一覧
- **raw_logs_*.parquet**: 生ログ（フィルタパターン別8種類）
- **geo_logs_*.parquet**: 地理情報集約ログ（4種類）
- **waf_*.parquet**: WAF関連データ（IPセット、ブロック済みIP、地理分布）

## 収集方法

```bash
cd /app && uv run python api/tests/scripts/collect_golden_data.py \
    --base-url http://localhost:8000 \
    --profile default \
    --distribution-id E3K6JPV795PQRV \
    --date 2025-11-13
```

## 使用方法

スナップショットテストが自動的にこのデータと実APIレスポンスを比較します。

```bash
uv run pytest -m snapshot
```
