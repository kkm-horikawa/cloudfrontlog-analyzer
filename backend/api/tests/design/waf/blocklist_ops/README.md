# テスト設計: WAF Blocklist Operations API

## エンドポイント情報

### 1. ブロックリストチェック
- **URL**: `/api/waf/blocklist/check/`
- **HTTPメソッド**: `GET`
- **説明**: 指定IPアドレスがWAFブロックリストに登録されているか確認

### 2. ブロックリスト追加
- **URL**: `/api/waf/blocklist/add/`
- **HTTPメソッド**: `POST`
- **説明**: 指定IPアドレスをWAF IPセットに追加してブロック

### 3. ブロックリスト削除
- **URL**: `/api/waf/blocklist/remove/`
- **HTTPメソッド**: `POST`
- **説明**: 指定IPアドレスをWAF IPセットから削除してブロック解除

## パラメータ仕様

### 1. ブロックリストチェック (`/check/`)

#### クエリパラメータ
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |
| ipAddress | string | ✓ | - | IP形式 | チェック対象IPアドレス |

### 2. ブロックリスト追加 (`/add/`)

#### クエリパラメータ
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |

#### リクエストボディ（JSON）
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |
| ipAddress | string | ✓ | - | IP形式 | 追加するIPアドレス |
| ipSetId | string | ✗ | null | UUID形式 | 追加先IPセットID（省略時は自動選択） |

### 3. ブロックリスト削除 (`/remove/`)

#### クエリパラメータ
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |

#### リクエストボディ（JSON）
| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |
| ipAddress | string | ✓ | - | IP形式 | 削除するIPアドレス |
| ipSetId | string | ✗ | null | UUID形式 | 削除元IPセットID（省略時は自動検索） |

## テストケース設計

### 1. 正常系テスト (80ケース)

#### 1.1 ブロックリストチェック - 基本動作
- [ ] **WAF-BLK-001**: 登録済みIPをチェック → isBlocked=true
- [ ] **WAF-BLK-002**: 未登録IPをチェック → isBlocked=false
- [ ] **WAF-BLK-003**: IPv4アドレスチェック
- [ ] **WAF-BLK-004**: IPv6アドレスチェック
- [ ] **WAF-BLK-005**: プライベートIPアドレスチェック
- [ ] **WAF-BLK-006**: ループバックIPチェック
- [ ] **WAF-BLK-007**: レスポンスに`isBlocked`, `ipAddress`フィールド存在
- [ ] **WAF-BLK-008**: isBlocked=trueの場合、`ipSetId`, `ipSetName`含む
- [ ] **WAF-BLK-009**: isBlocked=falseの場合、IPセット情報なし

#### 1.2 ブロックリストチェック - レスポンス検証
- [ ] **WAF-BLK-010**: HTTPステータス200 OK
- [ ] **WAF-BLK-011**: Content-Type: application/json
- [ ] **WAF-BLK-012**: isBlockedがboolean型
- [ ] **WAF-BLK-013**: ipAddressが入力値と一致
- [ ] **WAF-BLK-014**: 複数IPセットに同じIPが存在する場合、最初のIPセット情報を返す

#### 1.3 ブロックリスト追加 - 基本動作
- [ ] **WAF-BLK-020**: 新規IPを追加 → success=true
- [ ] **WAF-BLK-021**: IPv4アドレスを追加
- [ ] **WAF-BLK-022**: IPv6アドレスを追加
- [ ] **WAF-BLK-023**: ipSetId指定で特定IPセットに追加
- [ ] **WAF-BLK-024**: ipSetId省略で自動選択されたIPセットに追加
- [ ] **WAF-BLK-025**: 追加後にチェック → isBlocked=true
- [ ] **WAF-BLK-026**: レスポンスに`success`, `ipAddress`, `ipSetId`含む
- [ ] **WAF-BLK-027**: レスポンスに`message`含む
- [ ] **WAF-BLK-028**: 追加後のIPセット更新トークン（lockToken）更新確認

#### 1.4 ブロックリスト追加 - レスポンス検証
- [ ] **WAF-BLK-030**: HTTPステータス200 OK
- [ ] **WAF-BLK-031**: Content-Type: application/json
- [ ] **WAF-BLK-032**: successがboolean型
- [ ] **WAF-BLK-033**: ipAddressが入力値と一致
- [ ] **WAF-BLK-034**: ipSetIdがUUID形式
- [ ] **WAF-BLK-035**: messageが適切な成功メッセージ

#### 1.5 ブロックリスト追加 - 既存IP処理
- [ ] **WAF-BLK-040**: 既に登録済みIPを再度追加 → success=false, 適切なメッセージ
- [ ] **WAF-BLK-041**: 既存IP追加時にエラーにならない
- [ ] **WAF-BLK-042**: 既存IP追加時のレスポンスに既存IPセット情報含む

#### 1.6 ブロックリスト追加 - 自動IPセット選択
- [ ] **WAF-BLK-045**: IPv4の場合、IPv4用IPセットに追加
- [ ] **WAF-BLK-046**: IPv6の場合、IPv6用IPセットに追加
- [ ] **WAF-BLK-047**: 複数の候補IPセットがある場合、最初のIPセットに追加
- [ ] **WAF-BLK-048**: IPセットが存在しない場合のエラー処理

#### 1.7 ブロックリスト削除 - 基本動作
- [ ] **WAF-BLK-050**: 登録済みIPを削除 → success=true
- [ ] **WAF-BLK-051**: IPv4アドレスを削除
- [ ] **WAF-BLK-052**: IPv6アドレスを削除
- [ ] **WAF-BLK-053**: ipSetId指定で特定IPセットから削除
- [ ] **WAF-BLK-054**: ipSetId省略で自動検索して削除
- [ ] **WAF-BLK-055**: 削除後にチェック → isBlocked=false
- [ ] **WAF-BLK-056**: レスポンスに`success`, `ipAddress`, `ipSetId`含む
- [ ] **WAF-BLK-057**: レスポンスに`message`含む
- [ ] **WAF-BLK-058**: 削除後のIPセット更新トークン（lockToken）更新確認

#### 1.8 ブロックリスト削除 - レスポンス検証
- [ ] **WAF-BLK-060**: HTTPステータス200 OK
- [ ] **WAF-BLK-061**: Content-Type: application/json
- [ ] **WAF-BLK-062**: successがboolean型
- [ ] **WAF-BLK-063**: ipAddressが入力値と一致
- [ ] **WAF-BLK-064**: ipSetIdがUUID形式
- [ ] **WAF-BLK-065**: messageが適切な成功メッセージ

#### 1.9 ブロックリスト削除 - 未登録IP処理
- [ ] **WAF-BLK-070**: 未登録IPを削除 → success=false, 適切なメッセージ
- [ ] **WAF-BLK-071**: 未登録IP削除時にエラーにならない
- [ ] **WAF-BLK-072**: 未登録IP削除時のレスポンスにメッセージ含む

#### 1.10 一連の操作フロー
- [ ] **WAF-BLK-080**: 追加 → チェック → 削除 → チェック（一連の流れ）
- [ ] **WAF-BLK-081**: 複数IP同時追加（5個）
- [ ] **WAF-BLK-082**: 複数IP同時削除（5個）
- [ ] **WAF-BLK-083**: 追加と削除を交互に実行（10回）
- [ ] **WAF-BLK-084**: 同じIPを追加→削除→追加（べき等性確認）

#### 1.11 データ整合性
- [ ] **WAF-BLK-090**: 追加後、/api/waf/blocked-ips/で確認可能
- [ ] **WAF-BLK-091**: 削除後、/api/waf/blocked-ips/から消えている
- [ ] **WAF-BLK-092**: lockTokenが正しく更新される
- [ ] **WAF-BLK-093**: 同時リクエストでの整合性（楽観的ロック）

### 2. 異常系テスト (40ケース)

#### 2.1 チェック - 必須パラメータ欠如
- [ ] **WAF-BLK-ERR-001**: distributionId欠如 → 400 Bad Request
- [ ] **WAF-BLK-ERR-002**: ipAddress欠如 → 400 Bad Request
- [ ] **WAF-BLK-ERR-003**: すべてのパラメータ欠如 → 400 Bad Request

#### 2.2 追加 - 必須パラメータ欠如
- [ ] **WAF-BLK-ERR-010**: distributionId欠如 → 400 Bad Request
- [ ] **WAF-BLK-ERR-011**: ipAddress欠如 → 400 Bad Request
- [ ] **WAF-BLK-ERR-012**: リクエストボディ空 → 400 Bad Request

#### 2.3 削除 - 必須パラメータ欠如
- [ ] **WAF-BLK-ERR-020**: distributionId欠如 → 400 Bad Request
- [ ] **WAF-BLK-ERR-021**: ipAddress欠如 → 400 Bad Request
- [ ] **WAF-BLK-ERR-022**: リクエストボディ空 → 400 Bad Request

#### 2.4 不正なパラメータ値
- [ ] **WAF-BLK-ERR-030**: distributionId不正な形式 → 400 Bad Request
- [ ] **WAF-BLK-ERR-031**: ipAddress不正な形式（"999.999.999.999"） → 400
- [ ] **WAF-BLK-ERR-032**: ipAddress文字列（"invalid"） → 400
- [ ] **WAF-BLK-ERR-033**: ipAddress空文字列 → 400
- [ ] **WAF-BLK-ERR-034**: ipSetId不正な形式（UUID以外） → 400
- [ ] **WAF-BLK-ERR-035**: ipSetId存在しないID → 404または400
- [ ] **WAF-BLK-ERR-036**: ipAddressにSQL Injection文字列 → エスケープ
- [ ] **WAF-BLK-ERR-037**: ipAddressにXSS文字列 → エスケープ

#### 2.5 AWS関連エラー
- [ ] **WAF-BLK-ERR-040**: 存在しないdistributionId → 404または500
- [ ] **WAF-BLK-ERR-041**: AWS認証エラー → 500
- [ ] **WAF-BLK-ERR-042**: IAM権限不足（wafv2:UpdateIPSet無し） → 403
- [ ] **WAF-BLK-ERR-043**: IAM権限不足（wafv2:GetIPSet無し） → 403
- [ ] **WAF-BLK-ERR-044**: Web ACL未関連付け → 適切なエラー
- [ ] **WAF-BLK-ERR-045**: IPセット容量上限（10000件）到達 → 適切なエラー
- [ ] **WAF-BLK-ERR-046**: lockToken不一致（同時更新競合） → 適切なリトライまたはエラー
- [ ] **WAF-BLK-ERR-047**: AWS API Rate Limit超過 → 適切なリトライまたはエラー

#### 2.6 HTTPメソッド不正
- [ ] **WAF-BLK-ERR-050**: チェックでPOST → 405 Method Not Allowed
- [ ] **WAF-BLK-ERR-051**: 追加でGET → 405 Method Not Allowed
- [ ] **WAF-BLK-ERR-052**: 削除でGET → 405 Method Not Allowed
- [ ] **WAF-BLK-ERR-053**: 追加でDELETE → 405 Method Not Allowed

#### 2.7 その他
- [ ] **WAF-BLK-ERR-060**: 不正なJSON形式 → 400
- [ ] **WAF-BLK-ERR-061**: Content-Type不正 → 400
- [ ] **WAF-BLK-ERR-062**: リクエストボディが巨大（1MB超） → 413

### 3. 境界値テスト (25ケース)

#### 3.1 IPアドレス形式
- [ ] **WAF-BLK-EDGE-001**: IPv4最小値（0.0.0.0）
- [ ] **WAF-BLK-EDGE-002**: IPv4最大値（255.255.255.255）
- [ ] **WAF-BLK-EDGE-003**: IPv6最小値（::）
- [ ] **WAF-BLK-EDGE-004**: IPv6最大値（ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff）
- [ ] **WAF-BLK-EDGE-005**: IPv6短縮形（::1）
- [ ] **WAF-BLK-EDGE-006**: IPv6完全形

#### 3.2 IPセット容量
- [ ] **WAF-BLK-EDGE-010**: IPセット空（0件）に追加
- [ ] **WAF-BLK-EDGE-011**: IPセット1件に追加
- [ ] **WAF-BLK-EDGE-012**: IPセット9999件（上限-1）に追加
- [ ] **WAF-BLK-EDGE-013**: IPセット10000件（上限）に追加 → エラー
- [ ] **WAF-BLK-EDGE-014**: IPセット1件から削除 → 0件になる
- [ ] **WAF-BLK-EDGE-015**: IPセット10000件から削除

#### 3.3 連続操作
- [ ] **WAF-BLK-EDGE-020**: 1秒間に10回追加
- [ ] **WAF-BLK-EDGE-021**: 1秒間に10回削除
- [ ] **WAF-BLK-EDGE-022**: 同じIPを10回連続追加
- [ ] **WAF-BLK-EDGE-023**: 同じIPを10回連続削除

#### 3.4 特殊ケース
- [ ] **WAF-BLK-EDGE-030**: 複数IPセットに同じIP存在（削除は1つのみ）
- [ ] **WAF-BLK-EDGE-031**: IPv4とIPv6両方のIPセットが存在
- [ ] **WAF-BLK-EDGE-032**: IPセット名が非常に長い（128文字）
- [ ] **WAF-BLK-EDGE-033**: プロファイル名255文字
- [ ] **WAF-BLK-EDGE-034**: distributionId非常に長い

### 4. パフォーマンステスト (10ケース)

- [ ] **WAF-BLK-PERF-001**: チェックのレスポンスタイム < 500ms
- [ ] **WAF-BLK-PERF-002**: 追加のレスポンスタイム < 1000ms
- [ ] **WAF-BLK-PERF-003**: 削除のレスポンスタイム < 1000ms
- [ ] **WAF-BLK-PERF-004**: 10件連続追加の総時間 < 10000ms
- [ ] **WAF-BLK-PERF-005**: 10件連続削除の総時間 < 10000ms
- [ ] **WAF-BLK-PERF-006**: 大規模IPセット（9999件）への追加 < 1500ms
- [ ] **WAF-BLK-PERF-007**: 大規模IPセット（9999件）からの削除 < 1500ms
- [ ] **WAF-BLK-PERF-008**: 同時5リクエスト（追加）の並行処理
- [ ] **WAF-BLK-PERF-009**: 同時5リクエスト（削除）の並行処理
- [ ] **WAF-BLK-PERF-010**: メモリ使用量 < 50MB

### 5. セキュリティテスト (12ケース)

- [ ] **WAF-BLK-SEC-001**: CORS設定が正しい
- [ ] **WAF-BLK-SEC-002**: 認証なし未認証ユーザーは拒否される（認証実装時）
- [ ] **WAF-BLK-SEC-003**: ipAddressにパストラバーサル文字列 → エスケープ
- [ ] **WAF-BLK-SEC-004**: ipAddressにコマンドインジェクション → エスケープ
- [ ] **WAF-BLK-SEC-005**: distributionIdにSQL Injection → エスケープ
- [ ] **WAF-BLK-SEC-006**: HTTPSのみ許可（本番環境）
- [ ] **WAF-BLK-SEC-007**: レスポンスヘッダーにセキュリティヘッダー設定
- [ ] **WAF-BLK-SEC-008**: AWS認証情報がレスポンスに含まれない
- [ ] **WAF-BLK-SEC-009**: エラーメッセージに機密情報が含まれない
- [ ] **WAF-BLK-SEC-010**: Rate Limiting確認（1分間に100リクエスト制限）
- [ ] **WAF-BLK-SEC-011**: lockTokenがレスポンスに含まれない（セキュリティ）
- [ ] **WAF-BLK-SEC-012**: 悪意のあるIPアドレス追加の監査ログ

### 6. プロパティベーステスト (10ケース)

- [ ] **WAF-BLK-PROP-001**: 追加→削除→追加が常に成功（べき等性）
- [ ] **WAF-BLK-PROP-002**: チェック結果の一貫性
- [ ] **WAF-BLK-PROP-003**: ランダムなIPアドレス100個で追加→チェック→削除
- [ ] **WAF-BLK-PROP-004**: すべてのケースでHTTPステータス2xx/4xx/5xx
- [ ] **WAF-BLK-PROP-005**: successフィールドの型の一貫性
- [ ] **WAF-BLK-PROP-006**: 追加後は常にチェックでisBlocked=true
- [ ] **WAF-BLK-PROP-007**: 削除後は常にチェックでisBlocked=false
- [ ] **WAF-BLK-PROP-008**: レスポンスJSON構造の一貫性
- [ ] **WAF-BLK-PROP-009**: IPv4とIPv6で動作の一貫性
- [ ] **WAF-BLK-PROP-010**: 同じIPに対する操作の整合性

### 7. スナップショットテスト (15ケース)

- [ ] **WAF-BLK-SNAP-001**: チェック（登録済み） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-002**: チェック（未登録） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-003**: 追加成功 → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-004**: 追加失敗（既存IP） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-005**: 削除成功 → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-006**: 削除失敗（未登録IP） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-007**: チェック（IPv4） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-008**: チェック（IPv6） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-009**: 追加（IPv4） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-010**: 追加（IPv6） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-011**: エラーレスポンス（400） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-012**: エラーレスポンス（403） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-013**: エラーレスポンス（405） → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-014**: IPセット容量上限エラー → ゴールデンデータ一致
- [ ] **WAF-BLK-SNAP-015**: lockToken競合エラー → ゴールデンデータ一致

## 合計テストケース数: 192ケース

## テスト実装優先度

1. **高**: 正常系1.1-1.4, 1.7-1.8, 1.10, 異常系2.1-2.3, 2.5, スナップショット
2. **中**: 正常系1.5-1.6, 1.9, 1.11, 異常系2.4, 2.6, 境界値
3. **低**: パフォーマンス, セキュリティ, プロパティベース

## 自動化対象

- すべてのテストケースを自動化
- 正常系、異常系、スナップショットはCIで毎回実行
- パフォーマンステストはNightly実行
- 実際のWAF更新を伴うテストはテスト専用環境で実行

## テストデータ

### ゴールデンデータ
- 参照日: 2025-11-15
- ディストリビューションID: 環境変数から取得
- テスト用IPアドレス: 192.0.2.0/24（TEST-NET-1）
- テスト用IPセットID: 環境変数から取得

### モックデータ（チェック - 登録済み）
```json
{
  "isBlocked": true,
  "ipAddress": "192.0.2.1",
  "ipSetId": "12345678-1234-1234-1234-123456789012",
  "ipSetName": "BlockedIPs",
  "cidr": "192.0.2.1/32"
}
```

### モックデータ（チェック - 未登録）
```json
{
  "isBlocked": false,
  "ipAddress": "198.51.100.1"
}
```

### モックデータ（追加成功）
```json
{
  "success": true,
  "ipAddress": "192.0.2.1",
  "ipSetId": "12345678-1234-1234-1234-123456789012",
  "ipSetName": "BlockedIPs",
  "message": "IP address 192.0.2.1 has been successfully added to the blocklist"
}
```

### モックデータ（追加失敗 - 既存IP）
```json
{
  "success": false,
  "ipAddress": "192.0.2.1",
  "ipSetId": "12345678-1234-1234-1234-123456789012",
  "ipSetName": "BlockedIPs",
  "message": "IP address 192.0.2.1 is already in the blocklist"
}
```

### モックデータ（削除成功）
```json
{
  "success": true,
  "ipAddress": "192.0.2.1",
  "ipSetId": "12345678-1234-1234-1234-123456789012",
  "ipSetName": "BlockedIPs",
  "message": "IP address 192.0.2.1 has been successfully removed from the blocklist"
}
```

### モックデータ（削除失敗 - 未登録IP）
```json
{
  "success": false,
  "ipAddress": "198.51.100.1",
  "message": "IP address 198.51.100.1 is not found in any blocklist"
}
```

## 依存サービス

- AWS WAFv2 API
- AWS CloudFront API
- AWS認証情報（~/.aws/credentials または環境変数）
- IAM権限:
  - `wafv2:GetIPSet`
  - `wafv2:UpdateIPSet`
  - `wafv2:ListIPSets`
  - `wafv2:GetWebACL`
  - `cloudfront:GetDistribution`

## 備考

### IPアドレスのCIDR変換
- 単一IPアドレス（例: 192.0.2.1）は自動的に /32（IPv4）または /128（IPv6）のCIDR形式に変換
- IPセットにはCIDR形式で保存される

### 楽観的ロック（Optimistic Locking）
- WAFv2のIPセット更新にはlockTokenが必要
- 同時更新を防ぐため、取得時のlockTokenを更新時に使用
- lockToken不一致の場合は自動リトライ（最大3回）

### 自動IPセット選択ロジック
- ipSetId省略時、以下の優先順位で選択：
  1. IPv4の場合は"BlockedIPs"（IPv4用）を優先
  2. IPv6の場合は"BlockedIPsV6"（IPv6用）を優先
  3. 存在しない場合は最初に見つかったIPセットを使用

### テスト時の注意事項
- 本番環境での追加/削除テストは避ける
- テスト用のIPアドレス範囲（192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24）を使用
- テスト後は追加したIPを必ず削除（クリーンアップ）
