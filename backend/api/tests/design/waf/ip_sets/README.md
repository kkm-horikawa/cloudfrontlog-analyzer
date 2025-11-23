# テスト設計: WAF IP Sets API

## エンドポイント情報

- **URL**: `/api/waf/ip-sets/`
- **HTTPメソッド**: `GET`
- **説明**: CloudFrontディストリビューションに関連付けられたWAF Web ACLのIPセット一覧を取得

## パラメータ仕様

### クエリパラメータ

| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |

## テストケース設計

### 1. 正常系テスト (50ケース)

#### 1.1 基本動作
- [ ] **WAF-IP-001**: 必須パラメータのみでIPセット一覧取得
- [ ] **WAF-IP-002**: デフォルトプロファイルで取得
- [ ] **WAF-IP-003**: 特定プロファイル指定で取得
- [ ] **WAF-IP-004**: IPセットが0件の場合 → 空配列
- [ ] **WAF-IP-005**: IPセットが1件の場合
- [ ] **WAF-IP-006**: IPセットが複数件（5件）の場合
- [ ] **WAF-IP-007**: レスポンスに`ipSets`配列が含まれる

#### 1.2 プロファイル指定
- [ ] **WAF-IP-010**: profile="default"
- [ ] **WAF-IP-011**: 有効なプロファイル名を指定
- [ ] **WAF-IP-012**: プロファイル名に特殊文字を含む場合
- [ ] **WAF-IP-013**: プロファイル名が日本語の場合（URLエンコード）
- [ ] **WAF-IP-014**: プロファイル名が非常に長い場合（255文字）
- [ ] **WAF-IP-015**: プロファイル省略時にデフォルト値使用

#### 1.3 レスポンス構造検証
- [ ] **WAF-IP-020**: 各IPセット要素に必須フィールド存在
- [ ] **WAF-IP-021**: id, name, arn, scope必須
- [ ] **WAF-IP-022**: addresses配列が含まれる
- [ ] **WAF-IP-023**: ipAddressVersion（IPv4/IPv6）が含まれる
- [ ] **WAF-IP-024**: description（説明）が含まれる
- [ ] **WAF-IP-025**: lockToken（更新トークン）が含まれる
- [ ] **WAF-IP-026**: scope値が"CLOUDFRONT"
- [ ] **WAF-IP-027**: addresses配列が空配列または文字列配列
- [ ] **WAF-IP-028**: レスポンスがJSON配列形式
- [ ] **WAF-IP-029**: レスポンスContent-Type: application/json
- [ ] **WAF-IP-030**: HTTPステータス200 OK

#### 1.4 Web ACL関連
- [ ] **WAF-IP-035**: Web ACLに関連付けられたIPセットのみ取得
- [ ] **WAF-IP-036**: Web ACLが存在しないディストリビューション → 空配列
- [ ] **WAF-IP-037**: Web ACLに複数のIPセット関連付け
- [ ] **WAF-IP-038**: Web ACL情報（webAclId, webAclName）が含まれる
- [ ] **WAF-IP-039**: 無効化されたWeb ACL → 適切なエラー

#### 1.5 データ整合性
- [ ] **WAF-IP-040**: 同じパラメータで複数回リクエスト → 同じ結果
- [ ] **WAF-IP-041**: IPセットの順序が一定（名前でソート）
- [ ] **WAF-IP-042**: 重複するIPセットが含まれない
- [ ] **WAF-IP-043**: 各IPセットのフィールドが正しい型
- [ ] **WAF-IP-044**: addresses配列内のIPが正しいCIDR形式
- [ ] **WAF-IP-045**: ARNがAWS ARN形式（arn:aws:wafv2:...）

#### 1.6 IPアドレスバージョン
- [ ] **WAF-IP-050**: IPv4のみのIPセット
- [ ] **WAF-IP-051**: IPv6のみのIPセット
- [ ] **WAF-IP-052**: IPv4とIPv6混在（別々のIPセット）
- [ ] **WAF-IP-053**: ipAddressVersion="IPV4"の検証
- [ ] **WAF-IP-054**: ipAddressVersion="IPV6"の検証

### 2. 異常系テスト (30ケース)

#### 2.1 必須パラメータ欠如
- [ ] **WAF-IP-ERR-001**: distributionId欠如 → 400 Bad Request
- [ ] **WAF-IP-ERR-002**: すべてのパラメータ欠如 → 400 Bad Request

#### 2.2 不正なパラメータ値
- [ ] **WAF-IP-ERR-010**: distributionId不正な形式 → 400 Bad Request
- [ ] **WAF-IP-ERR-011**: distributionId空文字列 → 400 Bad Request
- [ ] **WAF-IP-ERR-012**: distributionIdにSQL Injection文字列 → エスケープ
- [ ] **WAF-IP-ERR-013**: distributionIdにXSS文字列 → エスケープ
- [ ] **WAF-IP-ERR-014**: distributionIdに制御文字 → 400 Bad Request
- [ ] **WAF-IP-ERR-015**: プロファイル名が空文字列 → デフォルト使用
- [ ] **WAF-IP-ERR-016**: プロファイル名に制御文字 → 400またはエスケープ

#### 2.3 AWS関連エラー
- [ ] **WAF-IP-ERR-020**: 存在しないdistributionId → 404または500
- [ ] **WAF-IP-ERR-021**: AWS認証エラー → 500
- [ ] **WAF-IP-ERR-022**: IAM権限不足（wafv2:ListIPSets無し） → 403
- [ ] **WAF-IP-ERR-023**: IAM権限不足（cloudfront:GetDistribution無し） → 403
- [ ] **WAF-IP-ERR-024**: IAM権限不足（wafv2:GetWebACL無し） → 403
- [ ] **WAF-IP-ERR-025**: AWS API Rate Limit超過 → 適切なリトライまたはエラー
- [ ] **WAF-IP-ERR-026**: CloudFrontにWeb ACL未関連付け → 空配列または適切なメッセージ
- [ ] **WAF-IP-ERR-027**: Web ACL削除済み → 適切なエラー
- [ ] **WAF-IP-ERR-028**: リージョン不一致（CloudFrontはus-east-1必須） → エラー

#### 2.4 HTTPメソッド不正
- [ ] **WAF-IP-ERR-030**: POSTメソッド → 405 Method Not Allowed
- [ ] **WAF-IP-ERR-031**: PUTメソッド → 405 Method Not Allowed
- [ ] **WAF-IP-ERR-032**: DELETEメソッド → 405 Method Not Allowed
- [ ] **WAF-IP-ERR-033**: PATCHメソッド → 405 Method Not Allowed

#### 2.5 その他
- [ ] **WAF-IP-ERR-040**: 不正なクエリパラメータ名 → 無視される
- [ ] **WAF-IP-ERR-041**: 重複パラメータ → 最後の値使用
- [ ] **WAF-IP-ERR-042**: URLエンコード不正 → 400
- [ ] **WAF-IP-ERR-043**: 存在しないプロファイル → 500またはエラー

### 3. 境界値テスト (15ケース)

#### 3.1 プロファイル名長さ
- [ ] **WAF-IP-EDGE-001**: プロファイル名1文字
- [ ] **WAF-IP-EDGE-002**: プロファイル名255文字（AWS最大長）
- [ ] **WAF-IP-EDGE-003**: プロファイル名256文字（AWS最大長+1） → エラー

#### 3.2 IPセット数
- [ ] **WAF-IP-EDGE-010**: IPセット0件
- [ ] **WAF-IP-EDGE-011**: IPセット1件
- [ ] **WAF-IP-EDGE-012**: IPセット10件
- [ ] **WAF-IP-EDGE-013**: IPセット100件（大量）

#### 3.3 IPアドレス数
- [ ] **WAF-IP-EDGE-020**: addresses配列0件（空のIPセット）
- [ ] **WAF-IP-EDGE-021**: addresses配列1件
- [ ] **WAF-IP-EDGE-022**: addresses配列100件
- [ ] **WAF-IP-EDGE-023**: addresses配列10000件（AWS上限）

#### 3.4 特殊ケース
- [ ] **WAF-IP-EDGE-030**: IPセット名が非常に長い（128文字）
- [ ] **WAF-IP-EDGE-031**: 説明が非常に長い（256文字）
- [ ] **WAF-IP-EDGE-032**: IPv6アドレス（完全表記128ビット）

### 4. パフォーマンステスト (8ケース)

- [ ] **WAF-IP-PERF-001**: IPセット1件取得のレスポンスタイム < 500ms
- [ ] **WAF-IP-PERF-002**: IPセット10件取得のレスポンスタイム < 1000ms
- [ ] **WAF-IP-PERF-003**: IPセット100件取得のレスポンスタイム < 3000ms
- [ ] **WAF-IP-PERF-004**: addresses 10000件のIPセット取得 < 2000ms
- [ ] **WAF-IP-PERF-005**: 同時10リクエストの並行処理
- [ ] **WAF-IP-PERF-006**: 60秒間に100リクエスト（スループット）
- [ ] **WAF-IP-PERF-007**: メモリ使用量（100件取得） < 50MB
- [ ] **WAF-IP-PERF-008**: キャッシュ有効時のレスポンスタイム < 100ms

### 5. セキュリティテスト (10ケース)

- [ ] **WAF-IP-SEC-001**: CORS設定が正しい
- [ ] **WAF-IP-SEC-002**: 認証なし未認証ユーザーは拒否される（認証実装時）
- [ ] **WAF-IP-SEC-003**: distributionIdにパストラバーサル文字列 → エスケープ
- [ ] **WAF-IP-SEC-004**: distributionIdにコマンドインジェクション → エスケープ
- [ ] **WAF-IP-SEC-005**: HTTPSのみ許可（本番環境）
- [ ] **WAF-IP-SEC-006**: レスポンスヘッダーにセキュリティヘッダー設定
- [ ] **WAF-IP-SEC-007**: AWS認証情報がレスポンスに含まれないことを確認
- [ ] **WAF-IP-SEC-008**: エラーメッセージに機密情報が含まれない
- [ ] **WAF-IP-SEC-009**: Rate Limiting確認（1分間に100リクエスト制限）
- [ ] **WAF-IP-SEC-010**: lockToken（更新トークン）が適切に保護される

### 6. プロパティベーステスト (8ケース)

- [ ] **WAF-IP-PROP-001**: ランダムな有効distributionId 100パターン → すべて成功
- [ ] **WAF-IP-PROP-002**: 同じパラメータで複数回リクエスト → 常に同じ結果
- [ ] **WAF-IP-PROP-003**: レスポンスJSON構造の一貫性
- [ ] **WAF-IP-PROP-004**: すべてのケースでHTTPステータス2xx/4xx/5xx
- [ ] **WAF-IP-PROP-005**: IPセットのソート順の一貫性
- [ ] **WAF-IP-PROP-006**: ARN形式の一貫性
- [ ] **WAF-IP-PROP-007**: CIDR表記の妥当性（すべてのaddresses）
- [ ] **WAF-IP-PROP-008**: scope値が常に"CLOUDFRONT"

### 7. スナップショットテスト (10ケース)

- [ ] **WAF-IP-SNAP-001**: デフォルトプロファイルのレスポンス → ゴールデンデータ一致
- [ ] **WAF-IP-SNAP-002**: 特定ディストリビューションのレスポンス → ゴールデンデータ一致
- [ ] **WAF-IP-SNAP-003**: IPセット構造（IPv4） → ゴールデンデータ一致
- [ ] **WAF-IP-SNAP-004**: IPセット構造（IPv6） → ゴールデンデータ一致
- [ ] **WAF-IP-SNAP-005**: Web ACL情報含む → ゴールデンデータ一致
- [ ] **WAF-IP-SNAP-006**: 空のIPセット → ゴールデンデータ一致
- [ ] **WAF-IP-SNAP-007**: 複数IPセット → ゴールデンデータ一致
- [ ] **WAF-IP-SNAP-008**: エラーレスポンス（400） → ゴールデンデータ一致
- [ ] **WAF-IP-SNAP-009**: エラーレスポンス（403） → ゴールデンデータ一致
- [ ] **WAF-IP-SNAP-010**: 0件レスポンス → ゴールデンデータ一致

## 合計テストケース数: 131ケース

## テスト実装優先度

1. **高**: 正常系1.1-1.3, 異常系2.1-2.3, スナップショット
2. **中**: 正常系1.4-1.6, 異常系2.4-2.5, 境界値
3. **低**: パフォーマンス, セキュリティ, プロパティベース

## 自動化対象

- すべてのテストケースを自動化
- 正常系、異常系、スナップショットはCIで毎回実行
- パフォーマンステストはNightly実行

## テストデータ

### ゴールデンデータ
- 参照日: 2025-11-15
- ディストリビューションID: 環境変数から取得
- Web ACL ARN: 環境変数から取得
- IPセット数: 実環境による

### モックデータ
```json
{
  "ipSets": [
    {
      "id": "12345678-1234-1234-1234-123456789012",
      "name": "BlockedIPs",
      "arn": "arn:aws:wafv2:us-east-1:123456789012:global/ipset/BlockedIPs/12345678-1234-1234-1234-123456789012",
      "scope": "CLOUDFRONT",
      "description": "Manually blocked IP addresses",
      "ipAddressVersion": "IPV4",
      "addresses": [
        "203.0.113.0/32",
        "198.51.100.0/24",
        "192.0.2.1/32"
      ],
      "lockToken": "abcd1234-5678-90ef-ghij-klmnopqrstuv"
    },
    {
      "id": "87654321-4321-4321-4321-210987654321",
      "name": "SuspiciousIPs",
      "arn": "arn:aws:wafv2:us-east-1:123456789012:global/ipset/SuspiciousIPs/87654321-4321-4321-4321-210987654321",
      "scope": "CLOUDFRONT",
      "description": "Automatically detected suspicious IPs",
      "ipAddressVersion": "IPV4",
      "addresses": [
        "1.2.3.4/32",
        "5.6.7.8/32"
      ],
      "lockToken": "wxyz9876-5432-10ab-cdef-ghijklmnopqr"
    }
  ],
  "webAclId": "98765432-8765-8765-8765-987654321098",
  "webAclName": "CloudFront-WebACL",
  "webAclArn": "arn:aws:wafv2:us-east-1:123456789012:global/webacl/CloudFront-WebACL/98765432-8765-8765-8765-987654321098"
}
```

## 依存サービス

- AWS WAFv2 API
- AWS CloudFront API
- AWS認証情報（~/.aws/credentials または環境変数）
- IAM権限:
  - `wafv2:ListIPSets`
  - `wafv2:GetIPSet`
  - `wafv2:GetWebACL`
  - `cloudfront:GetDistribution`
  - `cloudfront:GetDistributionConfig`

## 備考

### WAFv2とWAF Classic
- このAPIはWAFv2（最新版）のみ対応
- WAF Classic（旧版）は非対応
- CloudFrontディストリビューションはus-east-1リージョンのWAFv2リソースのみ使用可能

### IPセットの制限
- 1つのIPセットに最大10,000個のIPアドレス（CIDR）
- 1つのWeb ACLに最大100個のIPセット参照可能
- IPアドレスはCIDR表記（例: 192.0.2.0/24 または 192.0.2.1/32）

### lockTokenの用途
- IPセット更新時に楽観的ロックとして使用
- 他のクライアントによる同時更新を防止
- 取得時のlockTokenを更新APIに渡す必要がある

