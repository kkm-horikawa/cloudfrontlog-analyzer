# テスト設計: Log Aggregation API

## エンドポイント情報

- **URL**: `/api/cloudfront/logs/aggregation/`
- **HTTPメソッド**: `GET`
- **説明**: CloudFrontのアクセスログをIPアドレス、User Agent、Referrer、Query Stringなどで集計し、統計情報を返却

## パラメータ仕様

### クエリパラメータ

| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |
| distributionId | string | ✓ | - | CloudFront ID形式 | CloudFront Distribution ID |
| startDate | date | ✓ | - | YYYY-MM-DD | 開始日 |
| endDate | date | ✓ | - | YYYY-MM-DD | 終了日 |
| groupBy | string | ✓ | - | ip/user_agent/referrer/query_string | 集計単位 |
| startTime | time | ✗ | "00:00:00" | HH:MM:SS | 開始時刻（JST） |
| endTime | time | ✗ | "23:59:59" | HH:MM:SS | 終了時刻（JST） |
| limit | integer | ✗ | 1000 | 1-10000 | 取得件数上限（Top N） |
| minCount | integer | ✗ | 1 | min=1 | 最小リクエスト数フィルタ |

## レスポンス構造

```json
{
  "distribution_id": "E1234567890ABC",
  "date_range": {
    "start": "2025-11-01T00:00:00+09:00",
    "end": "2025-11-17T23:59:59+09:00"
  },
  "group_by": "ip",
  "total_requests": 1234567,
  "unique_values": 1234,
  "aggregations": [
    {
      "value": "203.0.113.42",
      "request_count": 15234,
      "percentage": 1.23,
      "first_seen": "2025-11-01T10:30:00+09:00",
      "last_seen": "2025-11-17T14:20:00+09:00",
      "unique_paths": 120,
      "unique_user_agents": 2,
      "status_distribution": {
        "200": 15000,
        "404": 234
      },
      "method_distribution": {
        "GET": 15100,
        "POST": 134
      },
      "geo_info": {
        "country": "Japan",
        "country_code": "JP",
        "city": "Tokyo"
      },
      "sample_log": {
        "date": "2025-11-17",
        "time": "14:20:00",
        "uri": "/path/to/page",
        "status": 200
      }
    }
  ]
}
```

## テストケース設計

### 1. ユニットテスト (40ケース)

**テストファイル**: `api/tests/unit/test_log_aggregation_service.py`
**テスト対象**: `LogService.aggregate_logs()` メソッド

#### 1.1 基本集計機能

##### IPアドレス集計
- [ ] **AGG-U-001**: IPアドレスで基本集計 → 正しくグループ化され、カウントが正確
- [ ] **AGG-U-002**: 複数IPの集計 → 各IPごとに正しく集計される
- [ ] **AGG-U-003**: 単一IPの集計 → 1件のみ返却される
- [ ] **AGG-U-004**: IP集計時の地理情報 → geo_infoフィールドが含まれる

##### User Agent集計
- [ ] **AGG-U-011**: User Agentで基本集計 → UA文字列でグループ化される
- [ ] **AGG-U-012**: 複数UAの集計 → 各UAごとに正しく集計される
- [ ] **AGG-U-013**: 空UAの処理 → 空文字列も1つの値として集計
- [ ] **AGG-U-014**: URLエンコードされたUA → デコードされて集計される

##### Referrer集計
- [ ] **AGG-U-021**: Referrerで基本集計 → Referrer URLでグループ化される
- [ ] **AGG-U-022**: 複数Referrerの集計 → 各Referrerごとに正しく集計される
- [ ] **AGG-U-023**: "-"（なし）の処理 → "-"も1つの値として集計
- [ ] **AGG-U-024**: 空Referrerの処理 → 空文字列も1つの値として集計

##### Query String集計
- [ ] **AGG-U-031**: Query Stringで基本集計 → Query文字列でグループ化される
- [ ] **AGG-U-032**: 複数QueryStringの集計 → 各QueryStringごとに正しく集計される
- [ ] **AGG-U-033**: "-"（なし）の処理 → "-"も1つの値として集計
- [ ] **AGG-U-034**: 複雑なQueryStringの処理 → 正しくグループ化される

#### 1.2 統計計算
- [ ] **AGG-U-041**: リクエスト数計算 → 正確なカウント
- [ ] **AGG-U-042**: パーセンテージ計算 → 正確な割合（合計100%）
- [ ] **AGG-U-043**: 最初のアクセス時刻 → 最も古い時刻が設定される
- [ ] **AGG-U-044**: 最後のアクセス時刻 → 最も新しい時刻が設定される
- [ ] **AGG-U-045**: ユニークパス数計算 → 正確なユニーク数
- [ ] **AGG-U-046**: ユニークUA数計算 → 正確なユニーク数

#### 1.3 ステータス・メソッド分布
- [ ] **AGG-U-051**: ステータスコード分布 → 各ステータスコードの件数が正確
- [ ] **AGG-U-052**: HTTPメソッド分布 → 各メソッドの件数が正確
- [ ] **AGG-U-053**: 複数ステータスコードの分布 → 全ステータスが含まれる
- [ ] **AGG-U-054**: 複数HTTPメソッドの分布 → 全メソッドが含まれる

#### 1.4 時刻フィルタ
- [ ] **AGG-U-061**: 開始時刻のみ指定 → 開始時刻以降のデータのみ集計
- [ ] **AGG-U-062**: 終了時刻のみ指定 → 終了時刻以前のデータのみ集計
- [ ] **AGG-U-063**: 開始・終了時刻両方指定 → 範囲内のデータのみ集計
- [ ] **AGG-U-064**: JST→UTC変換 → 正しくタイムゾーン変換される

#### 1.5 最小リクエスト数フィルタ
- [ ] **AGG-U-071**: 最小リクエスト数フィルタ → 閾値以上のデータのみ返却
- [ ] **AGG-U-072**: 閾値0 → 全データ返却
- [ ] **AGG-U-073**: 高い閾値 → 該当データのみ返却
- [ ] **AGG-U-074**: 全データ除外される閾値 → 空配列を返却

#### 1.6 Top N制限
- [ ] **AGG-U-081**: Top N制限 基本 → 指定件数のみ返却
- [ ] **AGG-U-082**: Top N ソート → リクエスト数降順でソート済み
- [ ] **AGG-U-083**: データ件数より大きいlimit → 全データ返却
- [ ] **AGG-U-084**: limit未指定 → デフォルト1000件

#### 1.7 エッジケース
- [ ] **AGG-U-091**: データなし → 空配列を返却
- [ ] **AGG-U-092**: ログ1件のみ → 正しく1件の集計結果
- [ ] **AGG-U-093**: 全て同じ値 → 1件の集計結果（100%）
- [ ] **AGG-U-094**: 大規模データセット → タイムアウトせず完了

#### 1.8 データ整合性
- [ ] **AGG-U-101**: 総リクエスト数一致 → 元データと一致
- [ ] **AGG-U-102**: パーセンテージ合計 → 約100%（丸め誤差許容）
- [ ] **AGG-U-103**: ユニーク値の数 → 正確なユニーク数
- [ ] **AGG-U-104**: サンプルログの妥当性 → 実在するログエントリ

### 2. 統合テスト (60ケース)

**テストファイル**: `api/tests/integration/test_log_aggregation_api.py`
**テスト対象**: `/api/cloudfront/logs/aggregation/` エンドポイント

#### 2.1 正常系 - 各集計単位

##### IPアドレス集計
- [ ] **AGG-I-001**: groupBy=ip, 日付範囲 → 200 OK, 正しいレスポンス構造
- [ ] **AGG-I-002**: groupBy=ip, 日付範囲 → geo_infoフィールドが含まれる
- [ ] **AGG-I-003**: groupBy=ip, 日付範囲 → リクエスト数降順でソート
- [ ] **AGG-I-004**: groupBy=ip, 時刻範囲指定 → 時刻フィルタが適用される

##### User Agent集計
- [ ] **AGG-I-011**: groupBy=user_agent, 日付範囲 → 200 OK, 正しいレスポンス構造
- [ ] **AGG-I-012**: groupBy=user_agent, 日付範囲 → geo_infoフィールドが含まれない
- [ ] **AGG-I-013**: groupBy=user_agent, 日付範囲 → unique_user_agentsが含まれる
- [ ] **AGG-I-014**: groupBy=user_agent, limit=10 → 最大10件返却

##### Referrer集計
- [ ] **AGG-I-021**: groupBy=referrer, 日付範囲 → 200 OK, 正しいレスポンス構造
- [ ] **AGG-I-022**: groupBy=referrer, 日付範囲 → "-"も1つの値として集計
- [ ] **AGG-I-023**: groupBy=referrer, 日付範囲 → ユニークIP数が含まれる
- [ ] **AGG-I-024**: groupBy=referrer, 日付範囲 → リクエスト数降順でソート

##### Query String集計
- [ ] **AGG-I-031**: groupBy=query_string, 日付範囲 → 200 OK, 正しいレスポンス構造
- [ ] **AGG-I-032**: groupBy=query_string, 日付範囲 → "-"も1つの値として集計
- [ ] **AGG-I-033**: groupBy=query_string, 日付範囲 → ユニークIP数が含まれる
- [ ] **AGG-I-034**: groupBy=query_string, 日付範囲 → 複雑なクエリストリングも正しく集計

#### 2.2 異常系 - パラメータバリデーション

##### 必須パラメータ
- [ ] **AGG-I-041**: distributionId未指定 → 400 Bad Request
- [ ] **AGG-I-042**: startDate未指定 → 400 Bad Request
- [ ] **AGG-I-043**: endDate未指定 → 400 Bad Request
- [ ] **AGG-I-044**: groupBy未指定 → 400 Bad Request

##### パラメータ値検証
- [ ] **AGG-I-051**: groupBy=invalid → 400 Bad Request
- [ ] **AGG-I-052**: startDate=invalid → 400 Bad Request
- [ ] **AGG-I-053**: startTime=invalid → 400 Bad Request
- [ ] **AGG-I-054**: limit=-1 → 400 Bad Request
- [ ] **AGG-I-055**: minCount=-1 → 400 Bad Request
- [ ] **AGG-I-056**: limit=100000 → 400 Bad Request or 上限値で制限

##### 日付範囲検証
- [ ] **AGG-I-061**: startDate > endDate → 400 Bad Request
- [ ] **AGG-I-062**: startTime > endTime (同日) → 400 Bad Request
- [ ] **AGG-I-063**: 日付範囲 > 90日 → 400 Bad Request or 警告
- [ ] **AGG-I-064**: startDate > 今日 → 400 Bad Request or 空結果

#### 2.3 レスポンス構造検証
- [ ] **AGG-I-071**: 全必須フィールド存在確認 → 全フィールドが存在
- [ ] **AGG-I-072**: distribution_idフィールド → リクエストと一致
- [ ] **AGG-I-073**: date_rangeフィールド → 正しい日付範囲
- [ ] **AGG-I-074**: group_byフィールド → リクエストと一致
- [ ] **AGG-I-075**: total_requestsフィールド → 数値型、非負
- [ ] **AGG-I-076**: unique_valuesフィールド → 数値型、非負
- [ ] **AGG-I-077**: aggregationsフィールド → 配列型

#### 2.4 集計結果検証
- [ ] **AGG-I-081**: valueフィールド → 文字列型、非null
- [ ] **AGG-I-082**: request_countフィールド → 数値型、正の整数
- [ ] **AGG-I-083**: percentageフィールド → 数値型、0-100の範囲
- [ ] **AGG-I-084**: first_seenフィールド → ISO8601形式の日時
- [ ] **AGG-I-085**: last_seenフィールド → ISO8601形式の日時
- [ ] **AGG-I-086**: unique_pathsフィールド → 数値型、非負
- [ ] **AGG-I-087**: status_distributionフィールド → オブジェクト型、数値
- [ ] **AGG-I-088**: method_distributionフィールド → オブジェクト型、数値
- [ ] **AGG-I-089**: sample_logフィールド → オブジェクト型、ログ構造

#### 2.5 フィルタ機能

##### 時刻フィルタ
- [ ] **AGG-I-091**: startTime指定 → 開始時刻以降のデータのみ
- [ ] **AGG-I-092**: endTime指定 → 終了時刻以前のデータのみ
- [ ] **AGG-I-093**: startTime, endTime両方 → 範囲内のデータのみ
- [ ] **AGG-I-094**: 00:00:00-23:59:59 → 全時刻のデータ

##### 最小リクエスト数フィルタ
- [ ] **AGG-I-101**: minCount=10 → 10件以上のエントリのみ
- [ ] **AGG-I-102**: minCount=100 → 100件以上のエントリのみ
- [ ] **AGG-I-103**: minCount=1 → 全エントリ（デフォルト）
- [ ] **AGG-I-104**: minCount=999999 → 空配列または該当なし

##### Top N制限
- [ ] **AGG-I-111**: limit=10 → 最大10件返却
- [ ] **AGG-I-112**: limit=100 → 最大100件返却
- [ ] **AGG-I-113**: limit未指定 → デフォルト1000件
- [ ] **AGG-I-114**: limit=10 → Top 10がリクエスト数順

#### 2.6 エラーハンドリング
- [ ] **AGG-I-121**: 存在しないDistribution ID → 400/404 エラー
- [ ] **AGG-I-122**: ログ記録無効のDistribution → 400 エラー
- [ ] **AGG-I-123**: 日付範囲にログなし → 200 OK, 空配列
- [ ] **AGG-I-124**: S3アクセス拒否 → 500 エラー or 適切なメッセージ
- [ ] **AGG-I-125**: 無効なAWSプロファイル → 400/500 エラー

#### 2.7 複合フィルタ
- [ ] **AGG-I-131**: 全フィルタ適用 → 全フィルタが正しく適用
- [ ] **AGG-I-132**: 時刻 + minCount → 両方のフィルタが適用
- [ ] **AGG-I-133**: limit + minCount → 両方のフィルタが適用
- [ ] **AGG-I-134**: フィルタで全除外 → 200 OK, 空配列

### 3. スナップショットテスト (20ケース)

**テストファイル**: `api/tests/snapshot/test_log_aggregation.py`
**ゴールデンデータ**: `api/tests/data/golden/2025-11-13/`

#### 3.1 基本集計スナップショット
- [ ] **AGG-S-001**: IP集計 → aggregation_by_ip.parquetと一致
- [ ] **AGG-S-002**: User Agent集計 → aggregation_by_user_agent.parquetと一致
- [ ] **AGG-S-003**: Referrer集計 → aggregation_by_referrer.parquetと一致
- [ ] **AGG-S-004**: Query String集計 → aggregation_by_query_string.parquetと一致

#### 3.2 時刻フィルタ付きスナップショット
- [ ] **AGG-S-011**: 00:00-12:00 → 午前中のデータのみ集計
- [ ] **AGG-S-012**: 12:00-23:59 → 午後のデータのみ集計
- [ ] **AGG-S-013**: 10:00-14:00 → ピーク時間のデータのみ集計

#### 3.3 フィルタ組み合わせスナップショット
- [ ] **AGG-S-021**: minCount=10 → 10件以上のIPのみ
- [ ] **AGG-S-022**: limit=100 → Top 100 IPのみ
- [ ] **AGG-S-023**: minCount=5, limit=50 → フィルタ適用済み結果

#### 3.4 IP集計詳細
- [ ] **AGG-S-031**: 地理情報が含まれる
- [ ] **AGG-S-032**: Top 10 IPが一致
- [ ] **AGG-S-033**: ステータス分布が一致

#### 3.5 User Agent集計詳細
- [ ] **AGG-S-041**: 主要ブラウザが一致
- [ ] **AGG-S-042**: ボットUAが一致
- [ ] **AGG-S-043**: ユニークIP数が一致

#### 3.6 Referrer集計詳細
- [ ] **AGG-S-051**: 主要流入元が一致
- [ ] **AGG-S-052**: 直アクセス（"-"）が含まれる
- [ ] **AGG-S-053**: 検索エンジンからの流入が一致

#### 3.7 Query String集計詳細
- [ ] **AGG-S-061**: UTMパラメータが一致
- [ ] **AGG-S-062**: クエリなし（"-"）が含まれる
- [ ] **AGG-S-063**: 複雑なクエリが一致

#### 3.8 統計値検証
- [ ] **AGG-S-071**: 総リクエスト数が一致
- [ ] **AGG-S-072**: ユニーク値の数が一致
- [ ] **AGG-S-073**: パーセンテージ合計が100%前後
- [ ] **AGG-S-074**: リクエスト数降順でソート

### 4. パフォーマンステスト (3ケース)

- [ ] **AGG-PERF-001**: 1日分のログ → 5秒以内に完了
- [ ] **AGG-PERF-002**: 7日分のログ → 30秒以内に完了
- [ ] **AGG-PERF-003**: 30日分のログ → 120秒以内に完了

## 合計テストケース数: 123ケース

- ユニットテスト: 40ケース
- 統合テスト: 60ケース
- スナップショットテスト: 20ケース
- パフォーマンステスト: 3ケース

## テスト実装優先度

1. **高（優先実装）**:
   - ユニットテスト 1.1-1.3（基本集計、統計計算、ステータス・メソッド分布）
   - 統合テスト 2.1-2.2（正常系、異常系）
   - スナップショットテスト 3.1（基本集計）
   - データ整合性テスト

2. **中（次期実装）**:
   - ユニットテスト 1.4-1.6（フィルタ機能、Top N制限）
   - 統合テスト 2.3-2.5（レスポンス構造、集計結果、フィルタ機能）
   - スナップショットテスト 3.2-3.8（詳細検証）

3. **低（後回し可）**:
   - ユニットテスト 1.7（エッジケース）
   - 統合テスト 2.6-2.7（エラーハンドリング、複合フィルタ）
   - パフォーマンステスト（Nightlyビルド用）

## 自動化対象

- すべてのテストケースを自動化
- CIパイプラインで優先度「高」「中」を実行
- Nightlyビルドでパフォーマンステスト実行
- スナップショットテストは変更時のリグレッション検証に使用

## テストデータ

### ゴールデンデータ

- **参照日**: 2025-11-13
- **Distribution ID**: E3K6JPV795PQRV
- **プロファイル**: default

#### ゴールデンデータ構造

```
api/tests/data/golden/2025-11-13/
├── raw_logs.parquet                    # 生ログデータ
├── aggregation_by_ip.parquet           # IP集計結果
├── aggregation_by_user_agent.parquet   # UA集計結果
├── aggregation_by_referrer.parquet     # Referrer集計結果
└── aggregation_by_query_string.parquet # QueryString集計結果
```

### ユニットテスト用モックデータ

```python
sample_logs = [
    {
        'date': '2025-11-13',
        'time': '10:00:00',
        'c-ip': '1.2.3.4',
        'cs-user-agent': 'Mozilla/5.0',
        'cs-referer': 'https://google.com',
        'cs-uri-query': 'utm_source=google',
        'cs-uri-stem': '/page1',
        'sc-status': '200',
        'cs-method': 'GET',
    },
    {
        'date': '2025-11-13',
        'time': '11:00:00',
        'c-ip': '1.2.3.4',
        'cs-user-agent': 'Mozilla/5.0',
        'cs-referer': 'https://google.com',
        'cs-uri-query': 'utm_source=google',
        'cs-uri-stem': '/page2',
        'sc-status': '200',
        'cs-method': 'GET',
    },
    {
        'date': '2025-11-13',
        'time': '12:00:00',
        'c-ip': '5.6.7.8',
        'cs-user-agent': 'Googlebot/2.1',
        'cs-referer': '-',
        'cs-uri-query': '-',
        'cs-uri-stem': '/page1',
        'sc-status': '404',
        'cs-method': 'GET',
    },
]
```

### 統合テスト用レスポンス例

```json
{
  "distribution_id": "E1234567890ABC",
  "date_range": {
    "start": "2025-11-13T00:00:00+09:00",
    "end": "2025-11-13T23:59:59+09:00"
  },
  "group_by": "ip",
  "total_requests": 3,
  "unique_values": 2,
  "aggregations": [
    {
      "value": "1.2.3.4",
      "request_count": 2,
      "percentage": 66.67,
      "first_seen": "2025-11-13T10:00:00+09:00",
      "last_seen": "2025-11-13T11:00:00+09:00",
      "unique_paths": 2,
      "unique_user_agents": 1,
      "status_distribution": {"200": 2},
      "method_distribution": {"GET": 2},
      "geo_info": {
        "country": "Japan",
        "country_code": "JP",
        "city": "Tokyo"
      }
    }
  ]
}
```

## テスト実行コマンド

```bash
# ユニットテスト
docker compose exec backend sh -c "cd /app && uv run pytest api/tests/unit/test_log_aggregation_service.py -v"

# 統合テスト
docker compose exec backend sh -c "cd /app && uv run pytest api/tests/integration/test_log_aggregation_api.py -v"

# スナップショットテスト
docker compose exec backend sh -c "cd /app && uv run pytest api/tests/snapshot/test_log_aggregation.py -v -m snapshot"

# 全集計関連テスト
docker compose exec backend sh -c "cd /app && uv run pytest -k aggregation -v"

# カバレッジ測定
docker compose exec backend sh -c "cd /app && uv run pytest api/tests/unit/test_log_aggregation_service.py --cov=api.endpoints.logs.services --cov-report=html"
```

## ゴールデンデータ収集

```bash
# ゴールデンデータ収集
docker compose exec backend sh -c "cd /app && uv run python api/tests/scripts/collect_golden_data.py \
    --base-url http://localhost:8000 \
    --profile default \
    --distribution-id E3K6JPV795PQRV \
    --date 2025-11-13 \
    --include-aggregation"

# ゴールデンデータ更新（API仕様変更時）
docker compose exec backend sh -c "cd /app && uv run python api/tests/scripts/collect_golden_data.py \
    --base-url http://localhost:8000 \
    --profile default \
    --distribution-id E3K6JPV795PQRV \
    --date 2025-11-13 \
    --include-aggregation \
    --overwrite"
```

## 依存サービス

- AWS CloudFront API
- AWS S3 API
- AWS認証情報（~/.aws/credentials または環境変数）
- IAM権限: `cloudfront:GetDistribution`, `s3:GetObject`, `s3:ListBucket`
- PostgreSQL/SQLite データベース
- IP Geolocation API（ip-api.com）

## 期待カバレッジ

### ユニットテスト
- **行カバレッジ**: 95%以上
- **分岐カバレッジ**: 90%以上
- **関数カバレッジ**: 100%

### 統合テスト
- **エンドポイントカバレッジ**: 100%
- **正常系/異常系カバレッジ**: 各80%以上

### スナップショットテスト
- **集計単位カバレッジ**: 100% (IP/UA/Referrer/QueryString)
- **フィルタパターンカバレッジ**: 80%以上

## 備考

### 既知の制約

1. **Top N制限**
   - デフォルト1000件、最大10000件
   - フロントエンドでのページネーション前提

2. **地理情報**
   - IP集計時のみ付与
   - 他の集計単位では付与されない

3. **パフォーマンス**
   - 大規模データセットでは時間がかかる可能性
   - 日次キャッシュの活用を推奨

### スナップショット比較における注意事項

#### 除外すべきフィールド
以下のフィールドは実行ごとに変わる可能性があるため、比較から除外：
- `sample_log`: 最新ログのサンプル（時刻に依存）
- `first_seen`, `last_seen`: キャッシュ状態で変わる可能性
- 動的に変わる可能性のあるフィールド

#### 許容誤差
- パーセンテージ計算: 0.01% (tolerance=0.01)
- リクエスト数: 完全一致
- ユニーク値の数: 完全一致

### モック使用例

#### S3クライアント

```python
@patch('boto3.Session')
def test_aggregate_by_ip_basic(mock_session):
    mock_s3 = MagicMock()
    mock_session.return_value.client.return_value = mock_s3
    # ...
```

#### IP地理情報

```python
@patch('api.endpoints.ip_info.services.IPInfoService.get_ip_info')
def test_aggregate_by_ip_geo_info(mock_get_ip_info):
    mock_get_ip_info.return_value = {
        'country': 'Japan',
        'country_code': 'JP',
        'city': 'Tokyo'
    }
    # ...
```
