# テスト設計: Security Checks API

## エンドポイント情報

### 1. 会社情報ページアクセスチェック
- **URL**: `/api/checks/company-info-access/`
- **HTTPメソッド**: `POST`
- **説明**: ターゲットURLからのリファラーで会社情報ページにアクセスがあるか確認（過去3日間）

### 2. 頻繁なIPアクセスチェック
- **URL**: `/api/checks/frequent-ip-access/`
- **HTTPメソッド**: `POST`
- **説明**: 特定IPからの頻繁なアクセスパターンを分析（過去N日間、デフォルト3日）

### 3. マルチデバイスアクセスチェック
- **URL**: `/api/checks/multi-device-access/`
- **HTTPメソッド**: `POST`
- **説明**: 同一IPから複数デバイスタイプ（モバイル＋デスクトップ）のアクセスを検出

### 4. リサーチツール検出チェック
- **URL**: `/api/checks/research-tool-detection/`
- **HTTPメソッド**: `POST`
- **説明**: User-AgentとReferrerからリサーチツール、スクレイパー、SEOボットを検出

## パラメータ仕様

### 1. 会社情報ページアクセスチェック

#### クエリパラメータ
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |

#### リクエストボディ（JSON）
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |
| targetUrl | string | ✓ | - | URLパス形式 | ターゲットURL |
| companyInfoUrl | string | ✗ | "/nattoku/about/" | URLパス形式 | 会社情報ページURL |

### 2. 頻繁なIPアクセスチェック

#### クエリパラメータ
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |

#### リクエストボディ（JSON）
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |
| clientIp | string | ✓ | - | IP形式 | 対象IPアドレス |
| days | integer | ✗ | 3 | min=1, max=30 | 分析対象期間（日数） |

### 3. マルチデバイスアクセスチェック

#### クエリパラメータ
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |

#### リクエストボディ（JSON）
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |
| clientIp | string | ✓ | - | IP形式 | 対象IPアドレス |
| days | integer | ✗ | 3 | min=1, max=30 | 分析対象期間（日数） |

### 4. リサーチツール検出チェック

#### リクエストボディ（JSON）
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| userAgent | string | ✓ | - | - | User-Agent文字列 |
| referrer | string | ✗ | "" | - | Referrer文字列 |

## テストケース設計

### 1. 正常系テスト (90ケース)

#### 1.1 会社情報ページアクセスチェック - 基本動作
- [ ] **SEC-CPA-001**: ターゲットURLからのアクセスあり → isSuspicious=true
- [ ] **SEC-CPA-002**: ターゲットURLからのアクセスなし → isSuspicious=false
- [ ] **SEC-CPA-003**: 必須パラメータのみで実行
- [ ] **SEC-CPA-004**: companyInfoUrl指定あり
- [ ] **SEC-CPA-005**: companyInfoUrl省略（デフォルト値使用）
- [ ] **SEC-CPA-006**: レスポンスに`checkType`, `criteria`, `result`, `details`含む
- [ ] **SEC-CPA-007**: result.isSuspicious boolean型
- [ ] **SEC-CPA-008**: result.totalAccessCount integer型
- [ ] **SEC-CPA-009**: result.suspiciousAccessCount integer型
- [ ] **SEC-CPA-010**: details配列に該当アクセスの詳細

#### 1.2 会社情報ページアクセスチェック - リファラーマッチング
- [ ] **SEC-CPA-020**: リファラー完全一致
- [ ] **SEC-CPA-021**: リファラー前方一致（クエリパラメータ異なる）
- [ ] **SEC-CPA-022**: リファラーにクエリパラメータあり
- [ ] **SEC-CPA-023**: リファラーに日本語パス（URLエンコード）
- [ ] **SEC-CPA-024**: リファラー "-"（なし）は該当しない
- [ ] **SEC-CPA-025**: 複数の該当アクセス（5件）

#### 1.3 頻繁なIPアクセスチェック - 基本動作
- [ ] **SEC-FIP-001**: 頻繁なアクセスあり → isSuspicious=true
- [ ] **SEC-FIP-002**: アクセス少ない → isSuspicious=false
- [ ] **SEC-FIP-003**: days=3（デフォルト）
- [ ] **SEC-FIP-004**: days=7
- [ ] **SEC-FIP-005**: days=30（最大）
- [ ] **SEC-FIP-006**: days=1（最小）
- [ ] **SEC-FIP-007**: レスポンスに`checkType`, `criteria`, `result`, `details`含む
- [ ] **SEC-FIP-008**: result.totalAccessCount integer型
- [ ] **SEC-FIP-009**: result.uniqueUrlsAccessed integer型
- [ ] **SEC-FIP-010**: details配列にURL別アクセス数

#### 1.4 頻繁なIPアクセスチェック - フィルタリング
- [ ] **SEC-FIP-020**: 静的ファイル（/media/）除外
- [ ] **SEC-FIP-021**: 静的ファイル（/static/）除外
- [ ] **SEC-FIP-022**: 画像ファイル（.jpg, .png）除外
- [ ] **SEC-FIP-023**: CSSファイル（.css）除外
- [ ] **SEC-FIP-024**: JSファイル（.js）除外
- [ ] **SEC-FIP-025**: フォントファイル（.woff, .woff2）除外
- [ ] **SEC-FIP-026**: 動的コンテンツのみカウント

#### 1.5 頻繁なIPアクセスチェック - URL集計
- [ ] **SEC-FIP-030**: 同一URLの複数アクセス正しくカウント
- [ ] **SEC-FIP-031**: アクセス数降順でソート
- [ ] **SEC-FIP-032**: 上位20URLのみ返却
- [ ] **SEC-FIP-033**: 各URLに最大10件のアクセス詳細
- [ ] **SEC-FIP-034**: suspiciousの閾値（10件超）

#### 1.6 マルチデバイスアクセスチェック - 基本動作
- [ ] **SEC-MDV-001**: モバイル＋デスクトップあり → isSuspicious=true
- [ ] **SEC-MDV-002**: モバイルのみ → isSuspicious=false
- [ ] **SEC-MDV-003**: デスクトップのみ → isSuspicious=false
- [ ] **SEC-MDV-004**: days=3（デフォルト）
- [ ] **SEC-MDV-005**: days=10
- [ ] **SEC-MDV-006**: レスポンスに`checkType`, `criteria`, `result`, `details`含む
- [ ] **SEC-MDV-007**: result.deviceTypesDetected配列
- [ ] **SEC-MDV-008**: result.realDeviceTypes配列（bot/unknown除外）
- [ ] **SEC-MDV-009**: details各デバイスタイプ別にサンプル

#### 1.7 マルチデバイスアクセスチェック - デバイス検出
- [ ] **SEC-MDV-020**: モバイルデバイス検出（iPhone）
- [ ] **SEC-MDV-021**: モバイルデバイス検出（Android）
- [ ] **SEC-MDV-022**: デスクトップデバイス検出（Windows）
- [ ] **SEC-MDV-023**: デスクトップデバイス検出（Mac）
- [ ] **SEC-MDV-024**: タブレットデバイス検出（iPad）
- [ ] **SEC-MDV-025**: ボット検出（Googlebot）
- [ ] **SEC-MDV-026**: 不明デバイス（unknown）
- [ ] **SEC-MDV-027**: bot/unknown除外して判定

#### 1.8 リサーチツール検出チェック - 基本動作
- [ ] **SEC-RTD-001**: ツール検出あり → isSuspicious=true
- [ ] **SEC-RTD-002**: ツール検出なし → isSuspicious=false
- [ ] **SEC-RTD-003**: userAgentのみ指定
- [ ] **SEC-RTD-004**: userAgent + referrer両方指定
- [ ] **SEC-RTD-005**: referrer省略
- [ ] **SEC-RTD-006**: レスポンスに`checkType`, `criteria`, `result`, `details`含む
- [ ] **SEC-RTD-007**: result.matchedPatternCount integer型
- [ ] **SEC-RTD-008**: details.matchedPatterns配列

#### 1.9 リサーチツール検出チェック - User-Agentパターン
- [ ] **SEC-RTD-020**: アーカイブツール検出（archive.org）
- [ ] **SEC-RTD-021**: スクレイピングツール検出（Python-urllib）
- [ ] **SEC-RTD-022**: SEOツール検出（SemrushBot）
- [ ] **SEC-RTD-023**: SEOツール検出（AhrefsBot）
- [ ] **SEC-RTD-024**: その他ツール検出（MTRobot）
- [ ] **SEC-RTD-025**: マイナーサーチエンジン検出（PetalBot）
- [ ] **SEC-RTD-026**: 疑わしいパターン検出（PhantomJS）
- [ ] **SEC-RTD-027**: 通常のブラウザ（Chrome） → 検出なし
- [ ] **SEC-RTD-028**: 通常のブラウザ（Safari） → 検出なし

#### 1.10 リサーチツール検出チェック - Referrerパターン
- [ ] **SEC-RTD-030**: ブロック対象ドメイン検出
- [ ] **SEC-RTD-031**: 許可ドメイン → 検出なし
- [ ] **SEC-RTD-032**: referrer空文字列 → 検出なし

#### 1.11 レスポンス構造検証
- [ ] **SEC-RSP-001**: HTTPステータス200 OK
- [ ] **SEC-RSP-002**: Content-Type: application/json
- [ ] **SEC-RSP-003**: checkTypeフィールドが正しい値
- [ ] **SEC-RSP-004**: criteriaオブジェクトに検査条件含む
- [ ] **SEC-RSP-005**: resultオブジェクトに検査結果含む
- [ ] **SEC-RSP-006**: detailsに詳細情報含む

### 2. 異常系テスト (35ケース)

#### 2.1 会社情報ページアクセスチェック - エラー
- [ ] **SEC-CPA-ERR-001**: distributionId欠如 → 400 Bad Request
- [ ] **SEC-CPA-ERR-002**: targetUrl欠如 → 400 Bad Request
- [ ] **SEC-CPA-ERR-003**: リクエストボディ空 → 400 Bad Request
- [ ] **SEC-CPA-ERR-004**: distributionId不正な形式 → 400
- [ ] **SEC-CPA-ERR-005**: targetUrl不正な形式 → 400
- [ ] **SEC-CPA-ERR-006**: companyInfoUrl不正な形式 → 400

#### 2.2 頻繁なIPアクセスチェック - エラー
- [ ] **SEC-FIP-ERR-001**: distributionId欠如 → 400 Bad Request
- [ ] **SEC-FIP-ERR-002**: clientIp欠如 → 400 Bad Request
- [ ] **SEC-FIP-ERR-003**: clientIp不正な形式 → 400
- [ ] **SEC-FIP-ERR-004**: days=0 → 400（最小値未満）
- [ ] **SEC-FIP-ERR-005**: days=31 → 400（最大値超）
- [ ] **SEC-FIP-ERR-006**: days=-1 → 400（負数）
- [ ] **SEC-FIP-ERR-007**: days文字列 → 400

#### 2.3 マルチデバイスアクセスチェック - エラー
- [ ] **SEC-MDV-ERR-001**: distributionId欠如 → 400 Bad Request
- [ ] **SEC-MDV-ERR-002**: clientIp欠如 → 400 Bad Request
- [ ] **SEC-MDV-ERR-003**: clientIp不正な形式 → 400
- [ ] **SEC-MDV-ERR-004**: days=0 → 400
- [ ] **SEC-MDV-ERR-005**: days=31 → 400
- [ ] **SEC-MDV-ERR-006**: days=-1 → 400

#### 2.4 リサーチツール検出チェック - エラー
- [ ] **SEC-RTD-ERR-001**: userAgent欠如 → 400 Bad Request
- [ ] **SEC-RTD-ERR-002**: userAgent空文字列 → 400
- [ ] **SEC-RTD-ERR-003**: リクエストボディ空 → 400

#### 2.5 AWS関連エラー
- [ ] **SEC-AWS-ERR-001**: 存在しないdistributionId → 404または500
- [ ] **SEC-AWS-ERR-002**: AWS認証エラー → 500
- [ ] **SEC-AWS-ERR-003**: IAM権限不足 → 403
- [ ] **SEC-AWS-ERR-004**: データベース接続エラー → 500

#### 2.6 HTTPメソッド不正
- [ ] **SEC-MTD-ERR-001**: GETメソッド → 405 Method Not Allowed
- [ ] **SEC-MTD-ERR-002**: PUTメソッド → 405 Method Not Allowed
- [ ] **SEC-MTD-ERR-003**: DELETEメソッド → 405 Method Not Allowed

#### 2.7 その他
- [ ] **SEC-OTH-ERR-001**: 不正なJSON形式 → 400
- [ ] **SEC-OTH-ERR-002**: Content-Type不正 → 400
- [ ] **SEC-OTH-ERR-003**: リクエストボディ巨大（1MB超） → 413

### 3. 境界値テスト (20ケース)

#### 3.1 会社情報ページアクセスチェック
- [ ] **SEC-CPA-EDGE-001**: targetUrl 1文字
- [ ] **SEC-CPA-EDGE-002**: targetUrl 2048文字（最大URL長）
- [ ] **SEC-CPA-EDGE-003**: 該当アクセス0件
- [ ] **SEC-CPA-EDGE-004**: 該当アクセス1件
- [ ] **SEC-CPA-EDGE-005**: 該当アクセス100件

#### 3.2 頻繁なIPアクセスチェック
- [ ] **SEC-FIP-EDGE-001**: days=1（最小）
- [ ] **SEC-FIP-EDGE-002**: days=30（最大）
- [ ] **SEC-FIP-EDGE-003**: アクセス0件
- [ ] **SEC-FIP-EDGE-004**: アクセス1件
- [ ] **SEC-FIP-EDGE-005**: アクセス10件（閾値）
- [ ] **SEC-FIP-EDGE-006**: アクセス11件（閾値超）
- [ ] **SEC-FIP-EDGE-007**: アクセス10000件（大量）

#### 3.3 マルチデバイスアクセスチェック
- [ ] **SEC-MDV-EDGE-001**: days=1（最小）
- [ ] **SEC-MDV-EDGE-002**: days=30（最大）
- [ ] **SEC-MDV-EDGE-003**: デバイスタイプ0種類
- [ ] **SEC-MDV-EDGE-004**: デバイスタイプ1種類
- [ ] **SEC-MDV-EDGE-005**: デバイスタイプ2種類（suspicious）
- [ ] **SEC-MDV-EDGE-006**: デバイスタイプ5種類（大量）

#### 3.4 リサーチツール検出チェック
- [ ] **SEC-RTD-EDGE-001**: userAgent 1文字
- [ ] **SEC-RTD-EDGE-002**: userAgent 8000文字（最大）
- [ ] **SEC-RTD-EDGE-003**: referrer 8000文字（最大）

### 4. パフォーマンステスト (10ケース)

- [ ] **SEC-PERF-001**: 会社情報チェック（3日分） < 2000ms
- [ ] **SEC-PERF-002**: 頻繁IPチェック（3日分） < 2000ms
- [ ] **SEC-PERF-003**: 頻繁IPチェック（30日分） < 5000ms
- [ ] **SEC-PERF-004**: マルチデバイスチェック（3日分） < 2000ms
- [ ] **SEC-PERF-005**: マルチデバイスチェック（30日分） < 5000ms
- [ ] **SEC-PERF-006**: リサーチツール検出 < 100ms（ログ検索不要）
- [ ] **SEC-PERF-007**: 同時10リクエストの並行処理
- [ ] **SEC-PERF-008**: 60秒間に50リクエスト（スループット）
- [ ] **SEC-PERF-009**: メモリ使用量（30日分検索） < 200MB
- [ ] **SEC-PERF-010**: 10万件のログ検索 < 5000ms

### 5. セキュリティテスト (12ケース)

- [ ] **SEC-SEC-001**: CORS設定が正しい
- [ ] **SEC-SEC-002**: 認証なし未認証ユーザーは拒否される（認証実装時）
- [ ] **SEC-SEC-003**: targetUrlにSQL Injection → エスケープ
- [ ] **SEC-SEC-004**: targetUrlにXSS → エスケープ
- [ ] **SEC-SEC-005**: clientIpにコマンドインジェクション → エスケープ
- [ ] **SEC-SEC-006**: userAgentにXSS → エスケープ
- [ ] **SEC-SEC-007**: referrerにXSS → エスケープ
- [ ] **SEC-SEC-008**: HTTPSのみ許可（本番環境）
- [ ] **SEC-SEC-009**: レスポンスヘッダーにセキュリティヘッダー設定
- [ ] **SEC-SEC-010**: AWS認証情報がレスポンスに含まれない
- [ ] **SEC-SEC-011**: エラーメッセージに機密情報が含まれない
- [ ] **SEC-SEC-012**: Rate Limiting確認（1分間に100リクエスト制限）

### 6. プロパティベーステスト (10ケース)

- [ ] **SEC-PROP-001**: 同じパラメータで複数回リクエスト → 常に同じ結果
- [ ] **SEC-PROP-002**: レスポンスJSON構造の一貫性
- [ ] **SEC-PROP-003**: すべてのケースでHTTPステータス2xx/4xx/5xx
- [ ] **SEC-PROP-004**: isSuspiciousフィールドの型の一貫性（boolean）
- [ ] **SEC-PROP-005**: checkTypeフィールドの値の一貫性
- [ ] **SEC-PROP-006**: ランダムなIPアドレス100個で各チェック実行
- [ ] **SEC-PROP-007**: ランダムなUser-Agent 100個でツール検出実行
- [ ] **SEC-PROP-008**: days範囲内のランダム値100パターン
- [ ] **SEC-PROP-009**: カウント系フィールドが非負整数
- [ ] **SEC-PROP-010**: details配列の整合性

### 7. スナップショットテスト (15ケース)

- [ ] **SEC-SNAP-001**: 会社情報チェック（該当あり） → ゴールデンデータ一致
- [ ] **SEC-SNAP-002**: 会社情報チェック（該当なし） → ゴールデンデータ一致
- [ ] **SEC-SNAP-003**: 頻繁IPチェック（suspicious） → ゴールデンデータ一致
- [ ] **SEC-SNAP-004**: 頻繁IPチェック（正常） → ゴールデンデータ一致
- [ ] **SEC-SNAP-005**: マルチデバイスチェック（suspicious） → ゴールデンデータ一致
- [ ] **SEC-SNAP-006**: マルチデバイスチェック（正常） → ゴールデンデータ一致
- [ ] **SEC-SNAP-007**: リサーチツール検出（ツールあり） → ゴールデンデータ一致
- [ ] **SEC-SNAP-008**: リサーチツール検出（ツールなし） → ゴールデンデータ一致
- [ ] **SEC-SNAP-009**: リサーチツール検出（SEOツール） → ゴールデンデータ一致
- [ ] **SEC-SNAP-010**: リサーチツール検出（スクレイパー） → ゴールデンデータ一致
- [ ] **SEC-SNAP-011**: リサーチツール検出（アーカイブツール） → ゴールデンデータ一致
- [ ] **SEC-SNAP-012**: エラーレスポンス（400） → ゴールデンデータ一致
- [ ] **SEC-SNAP-013**: エラーレスポンス（404） → ゴールデンデータ一致
- [ ] **SEC-SNAP-014**: エラーレスポンス（405） → ゴールデンデータ一致
- [ ] **SEC-SNAP-015**: 0件レスポンス → ゴールデンデータ一致

## 合計テストケース数: 192ケース

## テスト実装優先度

1. **高**: 正常系1.1, 1.3, 1.6, 1.8, 1.11, 異常系2.1-2.4, スナップショット
2. **中**: 正常系1.2, 1.4, 1.5, 1.7, 1.9, 1.10, 異常系2.5-2.7, 境界値
3. **低**: パフォーマンス, セキュリティ, プロパティベース

## 自動化対象

- すべてのテストケースを自動化
- 正常系、異常系、スナップショットはCIで毎回実行
- パフォーマンステストはNightly実行

## テストデータ

### ゴールデンデータ
- 参照日: 2025-11-15
- ディストリビューションID: 環境変数から取得
- テスト用IPアドレス: 192.0.2.0/24
- テスト用User-Agent: 各種ツールのUA文字列

### モックデータ（会社情報ページアクセスチェック）
```json
{
  "checkType": "company_info_access",
  "criteria": {
    "targetUrl": "/nattoku/special/",
    "companyInfoUrl": "/nattoku/about/",
    "period": "3 days"
  },
  "result": {
    "isSuspicious": true,
    "totalAccessCount": 50,
    "suspiciousAccessCount": 3,
    "description": "Found 3 accesses to company info page with referrer from target URL"
  },
  "details": [
    {
      "date": "2025-11-15",
      "time": "12:34:56",
      "clientIp": "203.0.113.1",
      "referrer": "https://defaulttech.co.jp/nattoku/special/12345/",
      "userAgent": "Mozilla/5.0 ...",
      "statusCode": 200
    }
  ]
}
```

### モックデータ（頻繁なIPアクセスチェック）
```json
{
  "checkType": "frequent_ip_access",
  "criteria": {
    "clientIp": "203.0.113.1",
    "period": "3 days",
    "threshold": "Multiple accesses to same URLs"
  },
  "result": {
    "isSuspicious": true,
    "totalAccessCount": 125,
    "uniqueUrlsAccessed": 45,
    "description": "IP accessed 45 unique URLs 125 times in the past 3 days"
  },
  "details": [
    {
      "url": "/nattoku/special/12345/",
      "accessCount": 15,
      "accesses": [
        {
          "date": "2025-11-15",
          "time": "12:34:56",
          "statusCode": 200,
          "userAgent": "Mozilla/5.0 ..."
        }
      ]
    }
  ]
}
```

### モックデータ（マルチデバイスアクセスチェック）
```json
{
  "checkType": "multi_device_access",
  "criteria": {
    "clientIp": "203.0.113.1",
    "period": "3 days",
    "threshold": "Accesses from multiple device types (mobile, desktop)"
  },
  "result": {
    "isSuspicious": true,
    "totalAccessCount": 50,
    "deviceTypesDetected": ["mobile", "desktop", "bot"],
    "realDeviceTypes": ["mobile", "desktop"],
    "description": "IP accessed from 2 different device types: mobile, desktop"
  },
  "details": {
    "mobile": {
      "count": 20,
      "samples": [
        {
          "date": "2025-11-15",
          "time": "12:34:56",
          "userAgent": "Mozilla/5.0 (iPhone; ...)",
          "uriStem": "/nattoku/special/12345/",
          "statusCode": 200
        }
      ]
    },
    "desktop": {
      "count": 25,
      "samples": [
        {
          "date": "2025-11-15",
          "time": "14:00:00",
          "userAgent": "Mozilla/5.0 (Windows NT 10.0; ...)",
          "uriStem": "/nattoku/about/",
          "statusCode": 200
        }
      ]
    },
    "bot": {
      "count": 5,
      "samples": []
    }
  }
}
```

### モックデータ（リサーチツール検出チェック）
```json
{
  "checkType": "research_tool_detection",
  "criteria": {
    "patterns": [
      "Archive tools (archive.org, Megalodon, PagePeeker)",
      "Scraping tools (Python, Java, Scrapy, etc.)",
      "SEO tools (SemrushBot, AhrefsBot, etc.)",
      "Other tools (MTRobot, PostmanRuntime, etc.)",
      "Minor search engines (PetalBot, YandexBot, etc.)",
      "Suspicious patterns (Line, PhantomJS, Excel)",
      "Blocked referrer domains"
    ]
  },
  "result": {
    "isSuspicious": true,
    "matchedPatternCount": 1,
    "description": "Research tool or suspicious pattern detected"
  },
  "details": {
    "userAgent": "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
    "referrer": "https://www.google.com/",
    "matchedPatterns": [
      "SEO Tool detected in User Agent"
    ]
  }
}
```

## 依存サービス

- AWS CloudFront API
- AWS S3（ログファイル保管）
- PostgreSQLデータベース（アクセスログキャッシュ）
- AWS認証情報（~/.aws/credentials または環境変数）
- IAM権限: `cloudfront:GetDistribution`, `s3:GetObject`, `s3:ListBucket`

## 備考

### デバイスタイプ検出ロジック
- User-Agent文字列から以下のデバイスタイプを判定：
  - `mobile`: iPhone, Android, Mobile
  - `desktop`: Windows, Mac, Linux
  - `tablet`: iPad, Tablet
  - `bot`: bot, crawler, spider
  - `unknown`: 判定不可

### リサーチツールパターン（suspicious_check.py）
- **アーカイブツール**: archive.org, Megalodon, PagePeeker
- **スクレイピングツール**: Python-urllib, Java, Scrapy, curl, wget
- **SEOツール**: SemrushBot, AhrefsBot, MJ12bot, DotBot
- **その他ツール**: MTRobot, PostmanRuntime, HeadlessChrome
- **マイナーサーチエンジン**: PetalBot, YandexBot, Baiduspider
- **疑わしいパターン**: Line, PhantomJS, Excel, VBA

### 静的ファイル除外パターン
- パス: `/media/`, `/static/`, `/assets/`
- 拡張子: `.css`, `.js`, `.jpg`, `.jpeg`, `.png`, `.gif`, `.svg`, `.ico`, `.woff`, `.woff2`, `.ttf`, `.eot`, `.webp`, `.avif`

### 期間範囲
- デフォルト: 過去3日間
- 最小: 1日
- 最大: 30日
