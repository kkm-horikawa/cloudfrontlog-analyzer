# テスト設計: Geo Logs API

## エンドポイント情報

- **URL**: `/api/cloudfront/logs/geo/`
- **HTTPメソッド**: `GET`
- **説明**: CloudFrontログを地理的位置で集約し、国・都市別のアクセス統計を取得

## パラメータ仕様

### クエリパラメータ

| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |
| startDate | date | ✓ | - | YYYY-MM-DD | 開始日 |
| endDate | date | ✓ | - | YYYY-MM-DD | 終了日 |
| startTime | time | ✗ | null | HH:MM:SS | 開始時刻（JST） |
| endTime | time | ✗ | null | HH:MM:SS | 終了時刻（JST） |
| uriFilter | string | ✗ | "" | - | URIパス部分一致フィルタ |
| refererFilter | string | ✗ | "" | - | リファラー部分一致フィルタ |
| queryFilter | string | ✗ | "" | - | クエリ文字列部分一致フィルタ |
| statusFilter | string | ✗ | "" | - | ステータスコード完全一致フィルタ |
| methodFilter | string | ✗ | "" | - | HTTPメソッド完全一致フィルタ |

## テストケース設計

### 1. 正常系テスト (70ケース)

#### 1.1 基本動作（必須パラメータのみ）
- [ ] **GEO-001**: 必須パラメータのみで地理集約ログ取得
- [ ] **GEO-002**: 1日分の地理集約ログ取得（startDate = endDate）
- [ ] **GEO-003**: 複数日（7日間）の地理集約ログ取得
- [ ] **GEO-004**: ログが0件の日付 → 空配列
- [ ] **GEO-005**: レスポンスに`locations`, `total`, `period`フィールド存在

#### 1.2 日付・時刻フィルタ
- [ ] **GEO-010**: startTime指定（00:00:00〜12:00:00）
- [ ] **GEO-011**: endTime指定（12:00:00〜23:59:59）
- [ ] **GEO-012**: startTimeとendTime両方指定（狭い時間範囲）
- [ ] **GEO-013**: startTime = endTime（1分間のログ）
- [ ] **GEO-014**: 日付範囲30日間（最大範囲）
- [ ] **GEO-015**: 時刻フィルタなし（全時間帯）
- [ ] **GEO-016**: startDate = endDate = 今日
- [ ] **GEO-017**: startDate = endDate = 過去1年前

#### 1.3 URIフィルタ
- [ ] **GEO-020**: uriFilter完全一致（/nattoku/about/）
- [ ] **GEO-021**: uriFilter前方一致（/nattoku/）
- [ ] **GEO-022**: uriFilter部分一致（about）
- [ ] **GEO-023**: uriFilter日本語パス（URLエンコード）
- [ ] **GEO-024**: uriFilter空文字列 → フィルタなし
- [ ] **GEO-025**: uriFilter特殊文字（%2F, %3F等）
- [ ] **GEO-026**: uriFilter適用で結果0件 → 空配列

#### 1.4 リファラーフィルタ
- [ ] **GEO-030**: refererFilter完全一致
- [ ] **GEO-031**: refererFilter部分一致（"google"）
- [ ] **GEO-032**: refererFilter部分一致（"facebook"）
- [ ] **GEO-033**: refererFilter空文字列 → フィルタなし
- [ ] **GEO-034**: refererFilter "-"（リファラーなし）
- [ ] **GEO-035**: refererFilter適用で結果0件 → 空配列

#### 1.5 クエリ文字列フィルタ
- [ ] **GEO-040**: queryFilter完全一致
- [ ] **GEO-041**: queryFilter部分一致（"utm_"）
- [ ] **GEO-042**: queryFilter部分一致（"source=google"）
- [ ] **GEO-043**: queryFilter空文字列 → フィルタなし
- [ ] **GEO-044**: queryFilter "-"（クエリなし）
- [ ] **GEO-045**: queryFilter適用で結果0件 → 空配列

#### 1.6 ステータスコードフィルタ
- [ ] **GEO-050**: statusFilter "200"
- [ ] **GEO-051**: statusFilter "404"
- [ ] **GEO-052**: statusFilter "500"
- [ ] **GEO-053**: statusFilter "301"
- [ ] **GEO-054**: statusFilter空文字列 → フィルタなし
- [ ] **GEO-055**: statusFilter存在しないコード "999" → 0件

#### 1.7 HTTPメソッドフィルタ
- [ ] **GEO-060**: methodFilter "GET"
- [ ] **GEO-061**: methodFilter "POST"
- [ ] **GEO-062**: methodFilter "HEAD"
- [ ] **GEO-063**: methodFilter "OPTIONS"
- [ ] **GEO-064**: methodFilter空文字列 → フィルタなし
- [ ] **GEO-065**: methodFilter存在しないメソッド "TRACE" → 0件

#### 1.8 複合フィルタ
- [ ] **GEO-070**: 日付 + 時刻 + URI
- [ ] **GEO-071**: 日付 + リファラー + ステータス
- [ ] **GEO-072**: 日付 + クエリ + メソッド
- [ ] **GEO-073**: すべてのフィルタ同時指定
- [ ] **GEO-074**: フィルタ組み合わせで0件 → 空配列
- [ ] **GEO-075**: URI + リファラー + ステータス
- [ ] **GEO-076**: クエリ + メソッド + 時刻範囲

#### 1.9 レスポンス構造検証
- [ ] **GEO-080**: 各location要素に必須フィールド存在
- [ ] **GEO-081**: country, countryCode, city, count必須
- [ ] **GEO-082**: lat, lonが数値型
- [ ] **GEO-083**: ips配列が含まれる
- [ ] **GEO-084**: representativeIp（代表IP）が含まれる
- [ ] **GEO-085**: countryCode ISO 3166-1形式（2文字）
- [ ] **GEO-086**: count降順（アクセス数多い順）でソート
- [ ] **GEO-087**: レスポンスContent-Type: application/json
- [ ] **GEO-088**: HTTPステータス200 OK

#### 1.10 データ整合性
- [ ] **GEO-090**: total値と各location.countの合計が一致
- [ ] **GEO-091**: 同じパラメータで複数回リクエスト → 同じ結果
- [ ] **GEO-092**: ips配列内のIP重複なし
- [ ] **GEO-093**: 各locationのcountが正の整数
- [ ] **GEO-094**: 地理情報取得失敗IPは"Unknown"として集約
- [ ] **GEO-095**: 緯度経度の妥当性（lat: -90〜90, lon: -180〜180）

### 2. 異常系テスト (35ケース)

#### 2.1 必須パラメータ欠如
- [ ] **GEO-ERR-001**: distributionId欠如 → 400 Bad Request
- [ ] **GEO-ERR-002**: startDate欠如 → 400 Bad Request
- [ ] **GEO-ERR-003**: endDate欠如 → 400 Bad Request
- [ ] **GEO-ERR-004**: すべてのパラメータ欠如 → 400 Bad Request

#### 2.2 不正なパラメータ値
- [ ] **GEO-ERR-010**: distributionId不正な形式 → 400 Bad Request
- [ ] **GEO-ERR-011**: startDate不正な形式（"2025/11/13"） → 400
- [ ] **GEO-ERR-012**: startDate不正な形式（"11-13-2025"） → 400
- [ ] **GEO-ERR-013**: startDate存在しない日付（"2025-02-30"） → 400
- [ ] **GEO-ERR-014**: endDate < startDate（逆転） → 400
- [ ] **GEO-ERR-015**: startTime不正な形式（"25:00:00"） → 400
- [ ] **GEO-ERR-016**: endTime不正な形式（"12:60:00"） → 400
- [ ] **GEO-ERR-017**: endTime < startTime（同日で逆転） → 400
- [ ] **GEO-ERR-018**: statusFilter不正な形式（"abc"） → 無視またはエラー
- [ ] **GEO-ERR-019**: methodFilter不正な形式（"invalid"） → 無視またはエラー

#### 2.3 境界値超過
- [ ] **GEO-ERR-020**: 日付範囲365日（過大） → 400またはタイムアウト
- [ ] **GEO-ERR-021**: uriFilter 10000文字（過大） → 400
- [ ] **GEO-ERR-022**: refererFilter 10000文字（過大） → 400

#### 2.4 AWS関連エラー
- [ ] **GEO-ERR-030**: 存在しないdistributionId → 404または500
- [ ] **GEO-ERR-031**: AWS認証エラー → 500
- [ ] **GEO-ERR-032**: IAM権限不足 → 403
- [ ] **GEO-ERR-033**: S3バケット存在しない → 500
- [ ] **GEO-ERR-034**: S3アクセス権限なし → 500
- [ ] **GEO-ERR-035**: データベース接続エラー → 500

#### 2.5 HTTPメソッド不正
- [ ] **GEO-ERR-040**: POSTメソッド → 405 Method Not Allowed
- [ ] **GEO-ERR-041**: PUTメソッド → 405 Method Not Allowed
- [ ] **GEO-ERR-042**: DELETEメソッド → 405 Method Not Allowed

#### 2.6 その他
- [ ] **GEO-ERR-050**: 不正なクエリパラメータ名 → 無視される
- [ ] **GEO-ERR-051**: 重複パラメータ → 最後の値使用
- [ ] **GEO-ERR-052**: URLエンコード不正 → 400
- [ ] **GEO-ERR-053**: 巨大なクエリ文字列（8KB超） → 400

### 3. 境界値テスト (20ケース)

#### 3.1 日付・時刻境界
- [ ] **GEO-EDGE-001**: startDate = 2000-01-01（過去）
- [ ] **GEO-EDGE-002**: endDate = 今日
- [ ] **GEO-EDGE-003**: startDate = endDate（1日のみ）
- [ ] **GEO-EDGE-004**: startTime = 00:00:00
- [ ] **GEO-EDGE-005**: endTime = 23:59:59
- [ ] **GEO-EDGE-006**: startTime = endTime
- [ ] **GEO-EDGE-007**: 日付範囲1日
- [ ] **GEO-EDGE-008**: 日付範囲30日（推奨最大）

#### 3.2 フィルタ境界
- [ ] **GEO-EDGE-010**: uriFilter 1文字
- [ ] **GEO-EDGE-011**: uriFilter 2048文字（最大URL長）
- [ ] **GEO-EDGE-012**: refererFilter 1文字
- [ ] **GEO-EDGE-013**: queryFilter 1文字
- [ ] **GEO-EDGE-014**: statusFilter 3文字（標準長）
- [ ] **GEO-EDGE-015**: methodFilter 3文字（"GET"）
- [ ] **GEO-EDGE-016**: methodFilter 7文字（"OPTIONS"）

#### 3.3 結果数境界
- [ ] **GEO-EDGE-020**: 集約結果0件
- [ ] **GEO-EDGE-021**: 集約結果1件（単一国のみ）
- [ ] **GEO-EDGE-022**: 集約結果100件（多数の国）
- [ ] **GEO-EDGE-023**: 単一国に10万アクセス

### 4. パフォーマンステスト (10ケース)

- [ ] **GEO-PERF-001**: 1日分の集約レスポンスタイム < 1000ms
- [ ] **GEO-PERF-002**: 7日分の集約レスポンスタイム < 2000ms
- [ ] **GEO-PERF-003**: 30日分の集約レスポンスタイム < 5000ms
- [ ] **GEO-PERF-004**: フィルタなし集約のレスポンスタイム < 3000ms
- [ ] **GEO-PERF-005**: フィルタ5個同時適用のレスポンスタイム < 4000ms
- [ ] **GEO-PERF-006**: 10万件のログ集約のレスポンスタイム < 3000ms
- [ ] **GEO-PERF-007**: 100万件のログ集約のレスポンスタイム < 10000ms
- [ ] **GEO-PERF-008**: 同時10リクエストの並行処理
- [ ] **GEO-PERF-009**: メモリ使用量（100万件集約） < 200MB
- [ ] **GEO-PERF-010**: スループット（60秒間に50リクエスト）

### 5. セキュリティテスト (12ケース)

- [ ] **GEO-SEC-001**: SQL Injection（distributionId） → エスケープ
- [ ] **GEO-SEC-002**: SQL Injection（uriFilter） → エスケープ
- [ ] **GEO-SEC-003**: XSS（refererFilter） → エスケープ
- [ ] **GEO-SEC-004**: XSS（queryFilter） → エスケープ
- [ ] **GEO-SEC-005**: パストラバーサル（uriFilter） → エスケープ
- [ ] **GEO-SEC-006**: コマンドインジェクション（methodFilter） → エスケープ
- [ ] **GEO-SEC-007**: CORS設定確認
- [ ] **GEO-SEC-008**: HTTPSのみ許可（本番）
- [ ] **GEO-SEC-009**: レスポンスにAWS認証情報含まれない
- [ ] **GEO-SEC-010**: エラーメッセージに機密情報含まれない
- [ ] **GEO-SEC-011**: Rate Limiting確認（1分間に100リクエスト制限）
- [ ] **GEO-SEC-012**: 認証なしユーザー拒否（認証実装時）

### 6. プロパティベーステスト (10ケース)

- [ ] **GEO-PROP-001**: ランダムな日付範囲100パターン → すべて成功
- [ ] **GEO-PROP-002**: ランダムなフィルタ組み合わせ100パターン → すべて適切に処理
- [ ] **GEO-PROP-003**: 同じパラメータで複数回リクエスト → 常に同じ結果
- [ ] **GEO-PROP-004**: total値と各location.countの合計が常に一致
- [ ] **GEO-PROP-005**: フィルタ適用前後のtotal値変化の一貫性
- [ ] **GEO-PROP-006**: レスポンスJSON構造の一貫性
- [ ] **GEO-PROP-007**: ソート順の一貫性（count降順）
- [ ] **GEO-PROP-008**: すべてのケースでHTTPステータス2xx/4xx/5xx
- [ ] **GEO-PROP-009**: 緯度経度の範囲制約の一貫性
- [ ] **GEO-PROP-010**: 国コードISO 3166-1形式の一貫性

### 7. スナップショットテスト (15ケース)

- [ ] **GEO-SNAP-001**: フィルタなし → ゴールデンデータ一致
- [ ] **GEO-SNAP-002**: 日付フィルタ → ゴールデンデータ一致
- [ ] **GEO-SNAP-003**: 時刻フィルタ → ゴールデンデータ一致
- [ ] **GEO-SNAP-004**: URIフィルタ → ゴールデンデータ一致
- [ ] **GEO-SNAP-005**: リファラーフィルタ → ゴールデンデータ一致
- [ ] **GEO-SNAP-006**: クエリフィルタ → ゴールデンデータ一致
- [ ] **GEO-SNAP-007**: ステータスフィルタ → ゴールデンデータ一致
- [ ] **GEO-SNAP-008**: メソッドフィルタ → ゴールデンデータ一致
- [ ] **GEO-SNAP-009**: 複合フィルタ → ゴールデンデータ一致
- [ ] **GEO-SNAP-010**: location構造 → ゴールデンデータ一致
- [ ] **GEO-SNAP-011**: ips配列構造 → ゴールデンデータ一致
- [ ] **GEO-SNAP-012**: 地理情報未取得（Unknown） → ゴールデンデータ一致
- [ ] **GEO-SNAP-013**: エラーレスポンス（400） → ゴールデンデータ一致
- [ ] **GEO-SNAP-014**: エラーレスポンス（404） → ゴールデンデータ一致
- [ ] **GEO-SNAP-015**: 0件レスポンス → ゴールデンデータ一致

## 合計テストケース数: 172ケース

## テスト実装優先度

1. **高**: 正常系1.1-1.3, 1.9, 異常系2.1-2.3, スナップショット
2. **中**: 正常系1.4-1.8, 1.10, 異常系2.4-2.6, 境界値
3. **低**: パフォーマンス, セキュリティ, プロパティベース

## 自動化対象

- すべてのテストケースを自動化
- 正常系、異常系、スナップショットはCIで毎回実行
- パフォーマンステストはNightly実行

## テストデータ

### ゴールデンデータ
- 参照日: 2025-11-15
- ディストリビューションID: 環境変数から取得
- 8パターンのフィルタ組み合わせを保存
- 国別集約結果のスナップショット

### モックデータ
```json
{
  "locations": [
    {
      "country": "Japan",
      "countryCode": "JP",
      "city": "Tokyo",
      "lat": 35.6895,
      "lon": 139.6917,
      "count": 1234,
      "ips": ["203.0.113.1", "203.0.113.2", "203.0.113.3"],
      "representativeIp": "203.0.113.1"
    },
    {
      "country": "United States",
      "countryCode": "US",
      "city": "New York",
      "lat": 40.7128,
      "lon": -74.0060,
      "count": 567,
      "ips": ["198.51.100.1", "198.51.100.2"],
      "representativeIp": "198.51.100.1"
    },
    {
      "country": "Unknown",
      "countryCode": "XX",
      "city": "Unknown",
      "lat": 0,
      "lon": 0,
      "count": 12,
      "ips": ["192.0.2.1"],
      "representativeIp": "192.0.2.1"
    }
  ],
  "total": 1813,
  "period": {
    "startDate": "2025-11-13",
    "endDate": "2025-11-15",
    "startTime": "00:00:00",
    "endTime": "23:59:59"
  }
}
```

## 依存サービス

- AWS CloudFront API
- AWS S3（ログファイル保管）
- PostgreSQLデータベース（アクセスログキャッシュ）
- IP Geolocation API（ip-api.com）
- AWS認証情報（~/.aws/credentials または環境変数）
- IAM権限: `cloudfront:GetDistribution`, `s3:GetObject`, `s3:ListBucket`

## 備考

### キャッシュ機能
- 地理情報集約結果はGeoLogCacheテーブルにキャッシュされる
- キャッシュ有効期限: 24時間
- 同一パラメータでのリクエストはキャッシュから返却
- フィルタパラメータの組み合わせでキャッシュキーを生成

### 代表IP選択ロジック
- 各地域の代表IPは最頻出IPを選択
- 同数の場合は辞書順で最小のIPを選択
