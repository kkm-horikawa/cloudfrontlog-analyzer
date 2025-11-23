# テスト設計: Log Search API

## エンドポイント情報

- **URL**: `/api/cloudfront/logs/search/`
- **HTTPメソッド**: `POST`
- **説明**: CloudFrontログを特定URL・時刻で検索し、該当するログエントリを返す

## パラメータ仕様

### クエリパラメータ

| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |

### リクエストボディ

| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |
| targetUrl | string | ✓ | - | - | 検索対象のURL（URI Stem） |
| dateTime | string (ISO8601) | ✓ | - | 有効な日時 | 検索基準となる日時 |
| timeWindowMinutes | integer | ✗ | 5 | 1-1440 | 検索時間幅（前後分） |

## テストケース設計

### 1. 正常系テスト (35ケース)

#### 1.1 基本動作
- [ ] **LOG-SEARCH-001**: デフォルトパラメータでログ検索が成功
- [ ] **LOG-SEARCH-002**: 検索結果が0件の場合、空配列を返す
- [ ] **LOG-SEARCH-003**: 検索結果が1件の場合、正しく返す
- [ ] **LOG-SEARCH-004**: 検索結果が複数件の場合、すべて返す
- [ ] **LOG-SEARCH-005**: 検索結果が時刻順にソートされている

#### 1.2 時間窓検証
- [ ] **LOG-SEARCH-006**: timeWindowMinutes=1で1分前後のログを検索
- [ ] **LOG-SEARCH-007**: timeWindowMinutes=5で5分前後のログを検索（デフォルト）
- [ ] **LOG-SEARCH-008**: timeWindowMinutes=30で30分前後のログを検索
- [ ] **LOG-SEARCH-009**: timeWindowMinutes=60で1時間前後のログを検索
- [ ] **LOG-SEARCH-010**: timeWindowMinutes=1440で24時間前後のログを検索

#### 1.3 日時形式検証
- [ ] **LOG-SEARCH-011**: ISO8601形式の日時（JST）で検索
- [ ] **LOG-SEARCH-012**: ISO8601形式の日時（UTC）で検索
- [ ] **LOG-SEARCH-013**: タイムゾーン+09:00（JST）で検索
- [ ] **LOG-SEARCH-014**: タイムゾーン+00:00（UTC）で検索
- [ ] **LOG-SEARCH-015**: タイムゾーン-07:00（PST）で検索
- [ ] **LOG-SEARCH-016**: ミリ秒を含む日時で検索
- [ ] **LOG-SEARCH-017**: UTCへの自動変換が正しく動作

#### 1.4 URL形式検証
- [ ] **LOG-SEARCH-018**: ルートパス"/"で検索
- [ ] **LOG-SEARCH-019**: 単純なパス"/index.html"で検索
- [ ] **LOG-SEARCH-020**: ネストされたパス"/path/to/file.html"で検索
- [ ] **LOG-SEARCH-021**: 特殊文字を含むパス（日本語URLエンコード済）
- [ ] **LOG-SEARCH-022**: クエリ文字列を含まないパスで検索
- [ ] **LOG-SEARCH-023**: 非常に長いパス（2000文字）で検索

#### 1.5 レスポンス構造検証
- [ ] **LOG-SEARCH-024**: レスポンスがJSON配列形式
- [ ] **LOG-SEARCH-025**: 各エントリに必須フィールドが含まれる（date, time, clientIp等）
- [ ] **LOG-SEARCH-026**: ipInfoフィールドが存在する（地理情報）
- [ ] **LOG-SEARCH-027**: suspiciousCheckフィールドが存在する（不審パターン検証）
- [ ] **LOG-SEARCH-028**: suspiciousCheckが正しく解析されている
- [ ] **LOG-SEARCH-029**: レスポンスのContent-Typeが"application/json"
- [ ] **LOG-SEARCH-030**: HTTPステータスコードが200 OK

#### 1.6 プロファイル指定
- [ ] **LOG-SEARCH-031**: 有効なプロファイル名を指定して検索
- [ ] **LOG-SEARCH-032**: プロファイル省略時、デフォルト値で動作
- [ ] **LOG-SEARCH-033**: 複数のプロファイルで同じ検索が可能

#### 1.7 ディストリビューションID検証
- [ ] **LOG-SEARCH-034**: 有効なディストリビューションID形式（E[A-Z0-9]{12}）で検索
- [ ] **LOG-SEARCH-035**: 異なるディストリビューションIDで異なる結果

### 2. 異常系テスト (30ケース)

#### 2.1 必須パラメータ欠如
- [ ] **LOG-SEARCH-ERR-001**: distributionId欠如 → 400エラー
- [ ] **LOG-SEARCH-ERR-002**: targetUrl欠如 → 400エラー
- [ ] **LOG-SEARCH-ERR-003**: dateTime欠如 → 400エラー
- [ ] **LOG-SEARCH-ERR-004**: リクエストボディが空 → 400エラー
- [ ] **LOG-SEARCH-ERR-005**: リクエストボディがnull → 400エラー

#### 2.2 不正な値
- [ ] **LOG-SEARCH-ERR-006**: distributionIdが不正な形式 → 400エラー
- [ ] **LOG-SEARCH-ERR-007**: distributionIdが空文字列 → 400エラー
- [ ] **LOG-SEARCH-ERR-008**: targetUrlが空文字列 → 400エラー
- [ ] **LOG-SEARCH-ERR-009**: dateTimeが不正な形式 → 400エラー
- [ ] **LOG-SEARCH-ERR-010**: dateTimeが未来の日時 → 警告または正常動作
- [ ] **LOG-SEARCH-ERR-011**: timeWindowMinutesが0 → 400エラー
- [ ] **LOG-SEARCH-ERR-012**: timeWindowMinutesが負の値 → 400エラー
- [ ] **LOG-SEARCH-ERR-013**: timeWindowMinutesが1440超過 → 400エラー
- [ ] **LOG-SEARCH-ERR-014**: timeWindowMinutesが文字列 → 400エラー

#### 2.3 型エラー
- [ ] **LOG-SEARCH-ERR-015**: distributionIdが数値 → 400エラー
- [ ] **LOG-SEARCH-ERR-016**: targetUrlが配列 → 400エラー
- [ ] **LOG-SEARCH-ERR-017**: dateTimeが数値 → 400エラー
- [ ] **LOG-SEARCH-ERR-018**: timeWindowMinutesが文字列 → 400エラー
- [ ] **LOG-SEARCH-ERR-019**: リクエストボディがJSON形式でない → 400エラー

#### 2.4 HTTPメソッド不正
- [ ] **LOG-SEARCH-ERR-020**: GETメソッド → 405 Method Not Allowed
- [ ] **LOG-SEARCH-ERR-021**: PUTメソッド → 405 Method Not Allowed
- [ ] **LOG-SEARCH-ERR-022**: DELETEメソッド → 405 Method Not Allowed
- [ ] **LOG-SEARCH-ERR-023**: PATCHメソッド → 405 Method Not Allowed

#### 2.5 AWS関連エラー
- [ ] **LOG-SEARCH-ERR-024**: 存在しないディストリビューションID → 適切なエラー
- [ ] **LOG-SEARCH-ERR-025**: AWS認証情報が無効 → 500エラー
- [ ] **LOG-SEARCH-ERR-026**: IAM権限不足 → 403または500エラー
- [ ] **LOG-SEARCH-ERR-027**: 存在しないプロファイル名 → 500エラー

#### 2.6 その他
- [ ] **LOG-SEARCH-ERR-028**: Content-Typeがapplication/jsonでない → 400エラー
- [ ] **LOG-SEARCH-ERR-029**: リクエストボディが巨大（10MB超） → 413エラー
- [ ] **LOG-SEARCH-ERR-030**: 不正なクエリパラメータ → 無視される

### 3. 境界値テスト (20ケース)

#### 3.1 時間窓の境界
- [ ] **LOG-SEARCH-EDGE-001**: timeWindowMinutes=1（最小値）
- [ ] **LOG-SEARCH-EDGE-002**: timeWindowMinutes=1440（最大値・24時間）
- [ ] **LOG-SEARCH-EDGE-003**: timeWindowMinutes=0 → エラー
- [ ] **LOG-SEARCH-EDGE-004**: timeWindowMinutes=1441 → エラー

#### 3.2 日時の境界
- [ ] **LOG-SEARCH-EDGE-005**: 過去1年前の日時で検索
- [ ] **LOG-SEARCH-EDGE-006**: 過去1日前の日時で検索
- [ ] **LOG-SEARCH-EDGE-007**: 現在時刻で検索
- [ ] **LOG-SEARCH-EDGE-008**: 1秒後の日時で検索（未来）
- [ ] **LOG-SEARCH-EDGE-009**: 1970-01-01T00:00:00Z（Epoch）で検索
- [ ] **LOG-SEARCH-EDGE-010**: 2099-12-31T23:59:59Z（未来）で検索

#### 3.3 URL長の境界
- [ ] **LOG-SEARCH-EDGE-011**: targetUrlが1文字
- [ ] **LOG-SEARCH-EDGE-012**: targetUrlが2000文字（最大想定）
- [ ] **LOG-SEARCH-EDGE-013**: targetUrlが2001文字 → エラーまたは切り捨て
- [ ] **LOG-SEARCH-EDGE-014**: targetUrlが空文字列 → エラー

#### 3.4 結果件数の境界
- [ ] **LOG-SEARCH-EDGE-015**: 検索結果0件
- [ ] **LOG-SEARCH-EDGE-016**: 検索結果1件
- [ ] **LOG-SEARCH-EDGE-017**: 検索結果100件
- [ ] **LOG-SEARCH-EDGE-018**: 検索結果1000件（大量）
- [ ] **LOG-SEARCH-EDGE-019**: 検索結果10000件（非常に大量）
- [ ] **LOG-SEARCH-EDGE-020**: 時間窓の境界ちょうどのログ（含まれるか確認）

### 4. パフォーマンステスト (10ケース)

- [ ] **LOG-SEARCH-PERF-001**: 1件検索のレスポンスタイム < 1000ms
- [ ] **LOG-SEARCH-PERF-002**: 100件検索のレスポンスタイム < 2000ms
- [ ] **LOG-SEARCH-PERF-003**: 1000件検索のレスポンスタイム < 5000ms
- [ ] **LOG-SEARCH-PERF-004**: timeWindowMinutes=1440（大きな時間窓）のレスポンスタイム < 10000ms
- [ ] **LOG-SEARCH-PERF-005**: 同時10リクエストの並行処理
- [ ] **LOG-SEARCH-PERF-006**: 60秒間に50リクエスト（スループット）
- [ ] **LOG-SEARCH-PERF-007**: キャッシュヒット時のレスポンスタイム < 500ms
- [ ] **LOG-SEARCH-PERF-008**: キャッシュミス時のレスポンスタイム測定
- [ ] **LOG-SEARCH-PERF-009**: 大きなログファイル（100MB）からの検索時間
- [ ] **LOG-SEARCH-PERF-010**: メモリ使用量が一定範囲内

### 5. セキュリティテスト (12ケース)

- [ ] **LOG-SEARCH-SEC-001**: CORS設定が正しい
- [ ] **LOG-SEARCH-SEC-002**: 認証なし未認証ユーザーは拒否される（認証実装時）
- [ ] **LOG-SEARCH-SEC-003**: SQLインジェクション対策（targetUrlにSQL文字列）
- [ ] **LOG-SEARCH-SEC-004**: XSS対策（targetUrlにスクリプトタグ）
- [ ] **LOG-SEARCH-SEC-005**: パストラバーサル対策（targetUrlに../）
- [ ] **LOG-SEARCH-SEC-006**: コマンドインジェクション対策（targetUrlにシェルコマンド）
- [ ] **LOG-SEARCH-SEC-007**: HTTPSのみ許可（本番環境）
- [ ] **LOG-SEARCH-SEC-008**: レスポンスヘッダーにセキュリティヘッダー設定
- [ ] **LOG-SEARCH-SEC-009**: AWS認証情報がレスポンスに含まれない
- [ ] **LOG-SEARCH-SEC-010**: エラーメッセージに機密情報が含まれない
- [ ] **LOG-SEARCH-SEC-011**: Rate Limiting実装（DDoS対策）
- [ ] **LOG-SEARCH-SEC-012**: 大量リクエストでのサービス拒否攻撃対策

### 6. 統合テスト (15ケース)

#### 6.1 suspicious_check統合
- [ ] **LOG-SEARCH-INT-001**: suspiciousCheckフィールドが正しく付与される
- [ ] **LOG-SEARCH-INT-002**: 不審なIPが正しく検出される
- [ ] **LOG-SEARCH-INT-003**: 許可されたボットが正しく識別される
- [ ] **LOG-SEARCH-INT-004**: ブロックされたIPが正しく識別される
- [ ] **LOG-SEARCH-INT-005**: severityレベルが正しく設定される

#### 6.2 IP情報統合
- [ ] **LOG-SEARCH-INT-006**: ipInfoフィールドに地理情報が含まれる
- [ ] **LOG-SEARCH-INT-007**: IP情報がキャッシュされる
- [ ] **LOG-SEARCH-INT-008**: キャッシュヒット時に外部API呼び出しなし
- [ ] **LOG-SEARCH-INT-009**: WHOIS情報が含まれる（取得済みの場合）

#### 6.3 S3統合
- [ ] **LOG-SEARCH-INT-010**: S3からログファイルを正しく取得
- [ ] **LOG-SEARCH-INT-011**: gzip圧縮ファイルを正しく展開
- [ ] **LOG-SEARCH-INT-012**: 複数のログファイルにまたがる検索

#### 6.4 データベース統合
- [ ] **LOG-SEARCH-INT-013**: データベースキャッシュから検索
- [ ] **LOG-SEARCH-INT-014**: データベースとS3のハイブリッド検索
- [ ] **LOG-SEARCH-INT-015**: ProcessedLogFileの記録が正しく行われる

### 7. エッジケーステスト (10ケース)

- [ ] **LOG-SEARCH-EDGE-021**: 日付変更時刻（00:00:00）での検索
- [ ] **LOG-SEARCH-EDGE-022**: 夏時間切り替え時の検索
- [ ] **LOG-SEARCH-EDGE-023**: うるう秒を含む日時での検索
- [ ] **LOG-SEARCH-EDGE-024**: 特殊文字を含むURL（スペース、&、=等）
- [ ] **LOG-SEARCH-EDGE-025**: URLエンコードされたパス
- [ ] **LOG-SEARCH-EDGE-026**: 重複するログエントリ
- [ ] **LOG-SEARCH-EDGE-027**: ログファイルが存在しない期間
- [ ] **LOG-SEARCH-EDGE-028**: 不完全なログエントリ（フィールド欠損）
- [ ] **LOG-SEARCH-EDGE-029**: 同一時刻に複数のリクエスト
- [ ] **LOG-SEARCH-EDGE-030**: タイムゾーン変換の境界値

### 8. データ整合性テスト (8ケース)

- [ ] **LOG-SEARCH-DATA-001**: 同じパラメータで複数回検索→同じ結果
- [ ] **LOG-SEARCH-DATA-002**: ログデータのフィールドが正しく変換される
- [ ] **LOG-SEARCH-DATA-003**: 日時フォーマットの一貫性
- [ ] **LOG-SEARCH-DATA-004**: IPアドレスフォーマットの一貫性
- [ ] **LOG-SEARCH-DATA-005**: ステータスコードが数値型
- [ ] **LOG-SEARCH-DATA-006**: バイト数が数値型
- [ ] **LOG-SEARCH-DATA-007**: 時間窓の計算が正確
- [ ] **LOG-SEARCH-DATA-008**: CloudFrontログフィールドマッピングの正確性

## 合計テストケース数: 140ケース

## テスト実装優先度

1. **高（優先実装）**:
   - 正常系1.1-1.5（基本動作、レスポンス構造）
   - 異常系2.1-2.2（必須パラメータ、不正な値）
   - 統合テスト6.1-6.4（suspicious_check, IP情報、S3、DB統合）

2. **中（次期実装）**:
   - 正常系1.6-1.7（プロファイル、ディストリビューションID）
   - 異常系2.3-2.5（型エラー、HTTPメソッド、AWS関連）
   - 境界値テスト3.1-3.4
   - データ整合性テスト

3. **低（後回し可）**:
   - 異常系2.6（その他）
   - パフォーマンステスト（Nightlyビルド用）
   - セキュリティテスト（セキュリティ監査時）
   - エッジケーステスト

## 自動化対象

- すべてのテストケースを自動化
- CIパイプラインで優先度「高」「中」を実行
- Nightlyビルドでパフォーマンステスト実行
- セキュリティテストは週次実行

## テストデータ

### ゴールデンデータ
- 参照日: 2025-11-15
- Distribution ID: 実環境のディストリビューションID
- テスト対象URL: `/nattoku/special/`
- テスト日時: `2025-11-12T12:00:00+09:00`

### モックデータ（リクエスト）
```json
{
  "distributionId": "E1234567890ABC",
  "targetUrl": "/nattoku/special/",
  "dateTime": "2025-11-12T12:00:00+09:00",
  "timeWindowMinutes": 5
}
```

### モックデータ（レスポンス）
```json
[
  {
    "date": "2025-11-12",
    "time": "03:00:00",
    "edgeLocation": "NRT51-C1",
    "bytes": 1234,
    "clientIp": "192.0.2.1",
    "method": "GET",
    "host": "d111111abcdef8.cloudfront.net",
    "uriStem": "/nattoku/special/",
    "statusCode": 200,
    "referrer": "-",
    "userAgent": "Mozilla/5.0...",
    "queryString": "-",
    "cookie": "-",
    "edgeResultType": "Hit",
    "ipInfo": {
      "ip": "192.0.2.1",
      "country": "Japan",
      "countryCode": "JP",
      "city": "Tokyo"
    },
    "suspiciousCheck": {
      "isSuspicious": false,
      "isBlocked": false,
      "isAllowedBot": false,
      "severity": "low",
      "matchedPatterns": []
    }
  }
]
```

## 依存サービス

- AWS CloudFront API
- AWS S3 API
- AWS認証情報（~/.aws/credentials または環境変数）
- IAM権限: `cloudfront:GetDistribution`, `s3:GetObject`, `s3:ListBucket`
- PostgreSQL/SQLite データベース
- IP Geolocation API（ip-api.com）
- WHOIS API（ipwhois.app）

## 備考

- ログ検索は時間がかかる可能性があるため、タイムアウト設定を適切に設定
- S3からの大量ログファイル取得はコストがかかるため、テスト時は制限を設ける
- suspicious_checkの解析ロジックは別途テストが必要
- キャッシュ機能のテストは別途設計が必要
