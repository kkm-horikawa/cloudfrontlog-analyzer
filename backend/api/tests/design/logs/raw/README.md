# テスト設計: Raw Logs API

## エンドポイント情報

- **URL**: `/api/cloudfront/logs/raw/`
- **HTTPメソッド**: `GET`
- **説明**: CloudFront生ログをページネーション付きで取得、各種フィルタリング対応

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
| clientIp | string | ✗ | "" | IP形式 | クライアントIP（単一） |
| clientIps | array[string] | ✗ | [] | IP形式カンマ区切り | クライアントIP（複数） |
| uriPath | string | ✗ | "" | - | URIパス部分一致 |
| referrer | string | ✗ | "" | - | リファラー部分一致 |
| queryString | string | ✗ | "" | - | クエリ文字列部分一致 |
| page | integer | ✗ | 1 | min=1 | ページ番号 |
| perPage | integer | ✗ | 1000 | min=1, max=10000 | 1ページあたりのログ数 |

## テストケース設計

### 1. 正常系テスト (80ケース)

#### 1.1 基本動作（必須パラメータのみ）
- [ ] **RAW-001**: 必須パラメータのみでログ取得
- [ ] **RAW-002**: 1日分のログ取得（startDate = endDate）
- [ ] **RAW-003**: 複数日（7日間）のログ取得
- [ ] **RAW-004**: ログが0件の日付 → 空配列
- [ ] **RAW-005**: レスポンスに`logs`, `total`, `page`, `perPage`, `totalPages`フィールド

#### 1.2 日付・時刻フィルタ
- [ ] **RAW-010**: startTime指定（00:00:00〜12:00:00）
- [ ] **RAW-011**: endTime指定（12:00:00〜23:59:59）
- [ ] **RAW-012**: startTimeとendTime両方指定（狭い時間範囲）
- [ ] **RAW-013**: startTime = endTime（1分間のログ）
- [ ] **RAW-014**: 日付範囲30日間（最大範囲）
- [ ] **RAW-015**: 時刻フィルタなし（全時間帯）
- [ ] **RAW-016**: startDate = endDate = 今日
- [ ] **RAW-017**: startDate = endDate = 過去1年前

#### 1.3 IPフィルタ（単一IP）
- [ ] **RAW-020**: clientIp指定（有効なIPv4）
- [ ] **RAW-021**: clientIp指定（IPv6）
- [ ] **RAW-022**: clientIp指定（存在しないIP） → 0件
- [ ] **RAW-023**: clientIp指定（プライベートIP）
- [ ] **RAW-024**: clientIp指定（ループバックIP）

#### 1.4 IPフィルタ（複数IP）
- [ ] **RAW-030**: clientIps指定（2個のIP）
- [ ] **RAW-031**: clientIps指定（10個のIP）
- [ ] **RAW-032**: clientIps指定（100個のIP）
- [ ] **RAW-033**: clientIpsとclientIp両方指定 → 統合される
- [ ] **RAW-034**: clientIps空配列 → フィルタなし

#### 1.5 URIフィルタ
- [ ] **RAW-040**: uriPath完全一致（/nattoku/about/）
- [ ] **RAW-041**: uriPath前方一致（/nattoku/）
- [ ] **RAW-042**: uriPath部分一致（about）
- [ ] **RAW-043**: uriPath日本語パス（URLエンコード）
- [ ] **RAW-044**: uriPath空文字列 → フィルタなし
- [ ] **RAW-045**: uriPath特殊文字（%2F, %3F等）

#### 1.6 リファラーフィルタ
- [ ] **RAW-050**: referrer完全一致
- [ ] **RAW-051**: referrer部分一致（"google"）
- [ ] **RAW-052**: referrer部分一致（"facebook"）
- [ ] **RAW-053**: referrer空文字列 → フィルタなし
- [ ] **RAW-054**: referrer "-"（リファラーなし）

#### 1.7 クエリ文字列フィルタ
- [ ] **RAW-060**: queryString完全一致
- [ ] **RAW-061**: queryString部分一致（"utm_"）
- [ ] **RAW-062**: queryString部分一致（"source=google"）
- [ ] **RAW-063**: queryString空文字列 → フィルタなし
- [ ] **RAW-064**: queryString "-"（クエリなし）

#### 1.8 複合フィルタ
- [ ] **RAW-070**: 日付 + 時刻 + IP
- [ ] **RAW-071**: 日付 + URI + リファラー
- [ ] **RAW-072**: 日付 + クエリ + IP
- [ ] **RAW-073**: すべてのフィルタ同時指定
- [ ] **RAW-074**: フィルタ組み合わせで0件 → 空配列

#### 1.9 ページネーション
- [ ] **RAW-080**: page=1, perPage=10
- [ ] **RAW-081**: page=1, perPage=100
- [ ] **RAW-082**: page=1, perPage=1000（デフォルト）
- [ ] **RAW-083**: page=1, perPage=10000（最大）
- [ ] **RAW-084**: page=2（2ページ目取得）
- [ ] **RAW-085**: page=最終ページ
- [ ] **RAW-086**: perPage変更時のtotal一貫性
- [ ] **RAW-087**: ページング計算（totalPages）正確性

#### 1.10 レスポンス構造検証
- [ ] **RAW-090**: 各ログエントリに必須フィールド存在
- [ ] **RAW-091**: date, time, clientIp, method, uriStem, statusCode必須
- [ ] **RAW-092**: ipInfo（地理情報）が含まれる
- [ ] **RAW-093**: suspiciousCheck（不審チェック）が含まれる
- [ ] **RAW-094**: referrerフィールドのデコード確認
- [ ] **RAW-095**: userAgentフィールドのデコード確認
- [ ] **RAW-096**: queryStringフィールドのデコード確認
- [ ] **RAW-097**: 日付が降順（新しい順）でソート
- [ ] **RAW-098**: レスポンスContent-Type: application/json
- [ ] **RAW-099**: HTTPステータス200 OK

### 2. 異常系テスト (40ケース)

#### 2.1 必須パラメータ欠如
- [ ] **RAW-ERR-001**: distributionId欠如 → 400 Bad Request
- [ ] **RAW-ERR-002**: startDate欠如 → 400 Bad Request
- [ ] **RAW-ERR-003**: endDate欠如 → 400 Bad Request
- [ ] **RAW-ERR-004**: すべてのパラメータ欠如 → 400 Bad Request

#### 2.2 不正なパラメータ値
- [ ] **RAW-ERR-010**: distributionId不正な形式 → 400 Bad Request
- [ ] **RAW-ERR-011**: startDate不正な形式（"2025/11/13"） → 400
- [ ] **RAW-ERR-012**: startDate不正な形式（"11-13-2025"） → 400
- [ ] **RAW-ERR-013**: startDate存在しない日付（"2025-02-30"） → 400
- [ ] **RAW-ERR-014**: endDate < startDate（逆転） → 400
- [ ] **RAW-ERR-015**: startTime不正な形式（"25:00:00"） → 400
- [ ] **RAW-ERR-016**: endTime不正な形式（"12:60:00"） → 400
- [ ] **RAW-ERR-017**: endTime < startTime（同日で逆転） → 400
- [ ] **RAW-ERR-018**: clientIp不正な形式（"999.999.999.999"） → 400
- [ ] **RAW-ERR-019**: clientIp文字列（"invalid"） → 400

#### 2.3 境界値超過
- [ ] **RAW-ERR-020**: page=0 → 400 Bad Request
- [ ] **RAW-ERR-021**: page=-1 → 400 Bad Request
- [ ] **RAW-ERR-022**: page=999999（存在しないページ） → 空配列
- [ ] **RAW-ERR-023**: perPage=0 → 400 Bad Request
- [ ] **RAW-ERR-024**: perPage=-1 → 400 Bad Request
- [ ] **RAW-ERR-025**: perPage=10001（最大値+1） → 400 Bad Request
- [ ] **RAW-ERR-026**: 日付範囲365日（過大） → 400またはタイムアウト

#### 2.4 AWS関連エラー
- [ ] **RAW-ERR-030**: 存在しないdistributionId → 404または500
- [ ] **RAW-ERR-031**: AWS認証エラー → 500
- [ ] **RAW-ERR-032**: IAM権限不足 → 403
- [ ] **RAW-ERR-033**: S3バケット存在しない → 500
- [ ] **RAW-ERR-034**: S3アクセス権限なし → 500

#### 2.5 HTTPメソッド不正
- [ ] **RAW-ERR-040**: POSTメソッド → 405 Method Not Allowed
- [ ] **RAW-ERR-041**: PUTメソッド → 405 Method Not Allowed
- [ ] **RAW-ERR-042**: DELETEメソッド → 405 Method Not Allowed

#### 2.6 その他
- [ ] **RAW-ERR-050**: 不正なクエリパラメータ名 → 無視される
- [ ] **RAW-ERR-051**: 重複パラメータ → 最後の値使用
- [ ] **RAW-ERR-052**: URLエンコード不正 → 400
- [ ] **RAW-ERR-053**: 巨大なクエリ文字列（8KB超） → 400

### 3. 境界値テスト (25ケース)

#### 3.1 日付・時刻境界
- [ ] **RAW-EDGE-001**: startDate = 2000-01-01（過去）
- [ ] **RAW-EDGE-002**: endDate = 今日
- [ ] **RAW-EDGE-003**: startDate = endDate（1日のみ）
- [ ] **RAW-EDGE-004**: startTime = 00:00:00
- [ ] **RAW-EDGE-005**: endTime = 23:59:59
- [ ] **RAW-EDGE-006**: startTime = endTime
- [ ] **RAW-EDGE-007**: 日付範囲1日
- [ ] **RAW-EDGE-008**: 日付範囲30日（推奨最大）

#### 3.2 ページネーション境界
- [ ] **RAW-EDGE-010**: page=1, perPage=1（最小）
- [ ] **RAW-EDGE-011**: page=1, perPage=10000（最大）
- [ ] **RAW-EDGE-012**: total=0件、page=1 → 空配列
- [ ] **RAW-EDGE-013**: total=1件、page=1, perPage=1
- [ ] **RAW-EDGE-014**: total=9999件、page=1, perPage=10000
- [ ] **RAW-EDGE-015**: total=10000件、page=1, perPage=10000
- [ ] **RAW-EDGE-016**: total=10001件、page=2, perPage=10000

#### 3.3 フィルタ境界
- [ ] **RAW-EDGE-020**: uriPath 1文字
- [ ] **RAW-EDGE-021**: uriPath 2048文字（最大URL長）
- [ ] **RAW-EDGE-022**: clientIps 1個
- [ ] **RAW-EDGE-023**: clientIps 100個
- [ ] **RAW-EDGE-024**: referrer 1文字
- [ ] **RAW-EDGE-025**: queryString 8000文字（最大クエリ長）

### 4. パフォーマンステスト (10ケース)

- [ ] **RAW-PERF-001**: 10件取得のレスポンスタイム < 500ms
- [ ] **RAW-PERF-002**: 100件取得のレスポンスタイム < 1000ms
- [ ] **RAW-PERF-003**: 1000件取得のレスポンスタイム < 2000ms
- [ ] **RAW-PERF-004**: 10000件取得のレスポンスタイム < 5000ms
- [ ] **RAW-PERF-005**: フィルタなし1日分のレスポンスタイム < 3000ms
- [ ] **RAW-PERF-006**: フィルタ5個同時適用のレスポンスタイム < 3000ms
- [ ] **RAW-PERF-007**: 日付範囲30日のレスポンスタイム < 10000ms
- [ ] **RAW-PERF-008**: 同時10リクエストの並行処理
- [ ] **RAW-PERF-009**: メモリ使用量（10000件） < 100MB
- [ ] **RAW-PERF-010**: スループット（60秒間に100リクエスト）

### 5. セキュリティテスト (12ケース)

- [ ] **RAW-SEC-001**: SQL Injection（distributionId） → エスケープ
- [ ] **RAW-SEC-002**: SQL Injection（uriPath） → エスケープ
- [ ] **RAW-SEC-003**: XSS（referrer） → エスケープ
- [ ] **RAW-SEC-004**: XSS（queryString） → エスケープ
- [ ] **RAW-SEC-005**: パストラバーサル（uriPath） → エスケープ
- [ ] **RAW-SEC-006**: コマンドインジェクション（clientIp） → エスケープ
- [ ] **RAW-SEC-007**: CORS設定確認
- [ ] **RAW-SEC-008**: HTTPSのみ許可（本番）
- [ ] **RAW-SEC-009**: レスポンスにAWS認証情報含まれない
- [ ] **RAW-SEC-010**: エラーメッセージに機密情報含まれない
- [ ] **RAW-SEC-011**: Rate Limiting確認（1分間に100リクエスト制限）
- [ ] **RAW-SEC-012**: 認証なしユーザー拒否（認証実装時）

### 6. プロパティベーステスト (10ケース)

- [ ] **RAW-PROP-001**: ランダムな日付範囲100パターン → すべて成功
- [ ] **RAW-PROP-002**: ランダムなページ番号100パターン → すべて適切に処理
- [ ] **RAW-PROP-003**: 同じパラメータで複数回リクエスト → 常に同じ結果
- [ ] **RAW-PROP-004**: total値の一貫性（ページ変更時）
- [ ] **RAW-PROP-005**: ページング計算の一貫性
- [ ] **RAW-PROP-006**: フィルタ適用前後のtotal値変化
- [ ] **RAW-PROP-007**: レスポンスJSON構造の一貫性
- [ ] **RAW-PROP-008**: ソート順の一貫性（日付降順）
- [ ] **RAW-PROP-009**: すべてのケースでHTTPステータス2xx/4xx/5xx
- [ ] **RAW-PROP-010**: レスポンスサイズとperPageの相関

### 7. スナップショットテスト (15ケース)

- [ ] **RAW-SNAP-001**: フィルタなし → ゴールデンデータ一致
- [ ] **RAW-SNAP-002**: 日付フィルタ → ゴールデンデータ一致
- [ ] **RAW-SNAP-003**: 時刻フィルタ → ゴールデンデータ一致
- [ ] **RAW-SNAP-004**: IPフィルタ → ゴールデンデータ一致
- [ ] **RAW-SNAP-005**: URIフィルタ → ゴールデンデータ一致
- [ ] **RAW-SNAP-006**: リファラーフィルタ → ゴールデンデータ一致
- [ ] **RAW-SNAP-007**: クエリフィルタ → ゴールデンデータ一致
- [ ] **RAW-SNAP-008**: 複合フィルタ → ゴールデンデータ一致
- [ ] **RAW-SNAP-009**: ページネーション（page=1） → ゴールデンデータ一致
- [ ] **RAW-SNAP-010**: ページネーション（perPage=10） → ゴールデンデータ一致
- [ ] **RAW-SNAP-011**: ipInfo構造 → ゴールデンデータ一致
- [ ] **RAW-SNAP-012**: suspiciousCheck構造 → ゴールデンデータ一致
- [ ] **RAW-SNAP-013**: エラーレスポンス（400） → ゴールデンデータ一致
- [ ] **RAW-SNAP-014**: エラーレスポンス（404） → ゴールデンデータ一致
- [ ] **RAW-SNAP-015**: 0件レスポンス → ゴールデンデータ一致

## 合計テストケース数: 192ケース

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
- 参照日: 2025-11-13
- ディストリビューションID: 環境変数から取得
- 8パターンのフィルタ組み合わせを保存

### モックデータ
```json
{
  "logs": [
    {
      "date": "2025-11-13",
      "time": "12:34:56",
      "clientIp": "203.0.113.1",
      "method": "GET",
      "uriStem": "/nattoku/about/",
      "statusCode": 200,
      "referrer": "https://www.google.com/",
      "userAgent": "Mozilla/5.0...",
      "queryString": "utm_source=google",
      "ipInfo": {...},
      "suspiciousCheck": {...}
    }
  ],
  "total": 1234,
  "page": 1,
  "perPage": 1000,
  "totalPages": 2
}
```

