# テスト設計: WAF Blocked IPs API

## エンドポイント情報

- **URL**: `/api/waf/blocked-ips/`
- **HTTPメソッド**: `GET`
- **説明**: WAF IPセットに登録されているブロック済みIPアドレスの一覧を取得

## 関連エンドポイント

- **詳細地理情報付きブロックIP一覧**: `/api/waf/blocked-ips/detail-geo/`
- **地理分布情報**: `/api/waf/blocked-ips/geo/`
- **Excel エクスポート**: `/api/waf/blocked-ips/export/`

## パラメータ仕様

### クエリパラメータ

| パラメータ名 | 型 | 必須 | デフォルト | 制約 | 説明 |
|------------|-----|------|----------|------|------|
| profile | string | ✗ | "default" | - | AWSプロファイル名 |
| distributionId | string | ✓ | - | CloudFront ID形式 | ディストリビューションID |

## テストケース設計

### 1. 正常系テスト (60ケース)

#### 1.1 基本動作
- [ ] **WAF-BIP-001**: 必須パラメータのみでブロックIP一覧取得
- [ ] **WAF-BIP-002**: デフォルトプロファイルで取得
- [ ] **WAF-BIP-003**: 特定プロファイル指定で取得
- [ ] **WAF-BIP-004**: ブロックIPが0件の場合 → 空配列
- [ ] **WAF-BIP-005**: ブロックIPが1件の場合
- [ ] **WAF-BIP-006**: ブロックIPが複数件（10件）の場合
- [ ] **WAF-BIP-007**: ブロックIPが大量（1000件）の場合
- [ ] **WAF-BIP-008**: レスポンスに`blockedIps`, `total`, `ipSets`フィールド存在

#### 1.2 プロファイル指定
- [ ] **WAF-BIP-010**: profile="default"
- [ ] **WAF-BIP-011**: 有効なプロファイル名を指定
- [ ] **WAF-BIP-012**: プロファイル名に特殊文字を含む場合
- [ ] **WAF-BIP-013**: プロファイル名が日本語の場合（URLエンコード）
- [ ] **WAF-BIP-014**: プロファイル省略時にデフォルト値使用

#### 1.3 レスポンス構造検証（基本）
- [ ] **WAF-BIP-020**: 各blockedIp要素に必須フィールド存在
- [ ] **WAF-BIP-021**: ip, cidr, ipSetId, ipSetName, ipSetArn必須
- [ ] **WAF-BIP-022**: ipフィールドが正しいIP形式
- [ ] **WAF-BIP-023**: cidrフィールドが正しいCIDR形式
- [ ] **WAF-BIP-024**: ipSetIdがUUID形式
- [ ] **WAF-BIP-025**: ipSetArnがAWS ARN形式
- [ ] **WAF-BIP-026**: total値とblockedIps配列の長さが一致
- [ ] **WAF-BIP-027**: レスポンスがJSON形式
- [ ] **WAF-BIP-028**: レスポンスContent-Type: application/json
- [ ] **WAF-BIP-029**: HTTPステータス200 OK

#### 1.4 IPアドレス形式
- [ ] **WAF-BIP-030**: IPv4単一IP（/32）
- [ ] **WAF-BIP-031**: IPv4サブネット（/24）
- [ ] **WAF-BIP-032**: IPv4サブネット（/16）
- [ ] **WAF-BIP-033**: IPv6単一IP（/128）
- [ ] **WAF-BIP-034**: IPv6サブネット（/64）
- [ ] **WAF-BIP-035**: IPv4とIPv6混在
- [ ] **WAF-BIP-036**: プライベートIPアドレス（10.0.0.0/8）
- [ ] **WAF-BIP-037**: ループバックIP（127.0.0.1/32）

#### 1.5 複数IPセット処理
- [ ] **WAF-BIP-040**: 単一IPセットのみ
- [ ] **WAF-BIP-041**: 複数IPセット（2個）
- [ ] **WAF-BIP-042**: 複数IPセット（5個）
- [ ] **WAF-BIP-043**: 各IPセットに異なるIPが含まれる
- [ ] **WAF-BIP-044**: 空のIPセットは結果に含まれない
- [ ] **WAF-BIP-045**: ipSets配列に全IPセット情報が含まれる

#### 1.6 データ整合性
- [ ] **WAF-BIP-050**: 同じパラメータで複数回リクエスト → 同じ結果
- [ ] **WAF-BIP-051**: IPアドレスの順序が一定（辞書順）
- [ ] **WAF-BIP-052**: 重複するIPアドレスが含まれない
- [ ] **WAF-BIP-053**: 各IPが正しいIPセットに属している
- [ ] **WAF-BIP-054**: total値の正確性
- [ ] **WAF-BIP-055**: ipSets配列の情報がAPI_WAF_IP_SETSと一致

#### 1.7 詳細地理情報付きエンドポイント（/detail-geo/）
- [ ] **WAF-BIP-060**: 地理情報付きブロックIP一覧取得
- [ ] **WAF-BIP-061**: 各IPに`geolocation`オブジェクト含む
- [ ] **WAF-BIP-062**: geolocation: lat, lon, country, countryCode, city含む
- [ ] **WAF-BIP-063**: geolocation: isp, org, asn含む
- [ ] **WAF-BIP-064**: `representativeIp`（代表IP）含む
- [ ] **WAF-BIP-065**: `cidrCategory`（単一IP/サブネット）含む

#### 1.8 地理分布エンドポイント（/geo/）
- [ ] **WAF-BIP-070**: 地理分布情報取得
- [ ] **WAF-BIP-071**: `locations`配列含む
- [ ] **WAF-BIP-072**: 各location: lat, lon, city, country, count含む
- [ ] **WAF-BIP-073**: `cidrs`配列（その地域のCIDR一覧）含む
- [ ] **WAF-BIP-074**: `ipSetNames`配列含む
- [ ] **WAF-BIP-075**: count降順でソート

### 2. 異常系テスト (30ケース)

#### 2.1 必須パラメータ欠如
- [ ] **WAF-BIP-ERR-001**: distributionId欠如 → 400 Bad Request
- [ ] **WAF-BIP-ERR-002**: すべてのパラメータ欠如 → 400 Bad Request

#### 2.2 不正なパラメータ値
- [ ] **WAF-BIP-ERR-010**: distributionId不正な形式 → 400 Bad Request
- [ ] **WAF-BIP-ERR-011**: distributionId空文字列 → 400 Bad Request
- [ ] **WAF-BIP-ERR-012**: distributionIdにSQL Injection文字列 → エスケープ
- [ ] **WAF-BIP-ERR-013**: distributionIdにXSS文字列 → エスケープ
- [ ] **WAF-BIP-ERR-014**: プロファイル名に制御文字 → 400またはエスケープ

#### 2.3 AWS関連エラー
- [ ] **WAF-BIP-ERR-020**: 存在しないdistributionId → 404または500
- [ ] **WAF-BIP-ERR-021**: AWS認証エラー → 500
- [ ] **WAF-BIP-ERR-022**: IAM権限不足（wafv2:GetIPSet無し） → 403
- [ ] **WAF-BIP-ERR-023**: IAM権限不足（wafv2:ListIPSets無し） → 403
- [ ] **WAF-BIP-ERR-024**: IAM権限不足（cloudfront:GetDistribution無し） → 403
- [ ] **WAF-BIP-ERR-025**: Web ACL未関連付け → 空配列または適切なメッセージ
- [ ] **WAF-BIP-ERR-026**: Web ACL削除済み → 適切なエラー
- [ ] **WAF-BIP-ERR-027**: IPセット削除済み → 適切な処理（スキップまたはエラー）
- [ ] **WAF-BIP-ERR-028**: AWS API Rate Limit超過 → 適切なリトライまたはエラー

#### 2.4 HTTPメソッド不正
- [ ] **WAF-BIP-ERR-030**: POSTメソッド → 405 Method Not Allowed
- [ ] **WAF-BIP-ERR-031**: PUTメソッド → 405 Method Not Allowed
- [ ] **WAF-BIP-ERR-032**: DELETEメソッド → 405 Method Not Allowed

#### 2.5 地理情報関連エラー（/detail-geo/）
- [ ] **WAF-BIP-ERR-040**: IP地理情報API障害 → 地理情報なしで返却
- [ ] **WAF-BIP-ERR-041**: 地理情報取得タイムアウト → 地理情報なしで返却
- [ ] **WAF-BIP-ERR-042**: プライベートIPの地理情報 → 適切なデフォルト値

#### 2.6 その他
- [ ] **WAF-BIP-ERR-050**: 不正なクエリパラメータ名 → 無視される
- [ ] **WAF-BIP-ERR-051**: 重複パラメータ → 最後の値使用
- [ ] **WAF-BIP-ERR-052**: URLエンコード不正 → 400

### 3. 境界値テスト (20ケース)

#### 3.1 ブロックIP数
- [ ] **WAF-BIP-EDGE-001**: ブロックIP 0件
- [ ] **WAF-BIP-EDGE-002**: ブロックIP 1件
- [ ] **WAF-BIP-EDGE-003**: ブロックIP 10件
- [ ] **WAF-BIP-EDGE-004**: ブロックIP 100件
- [ ] **WAF-BIP-EDGE-005**: ブロックIP 1000件
- [ ] **WAF-BIP-EDGE-006**: ブロックIP 10000件（AWS上限）

#### 3.2 IPセット数
- [ ] **WAF-BIP-EDGE-010**: IPセット0個 → ブロックIP 0件
- [ ] **WAF-BIP-EDGE-011**: IPセット1個
- [ ] **WAF-BIP-EDGE-012**: IPセット10個
- [ ] **WAF-BIP-EDGE-013**: IPセット100個（大量）

#### 3.3 CIDR範囲
- [ ] **WAF-BIP-EDGE-020**: /32（単一IP）
- [ ] **WAF-BIP-EDGE-021**: /24（256アドレス）
- [ ] **WAF-BIP-EDGE-022**: /16（65536アドレス）
- [ ] **WAF-BIP-EDGE-023**: /8（大規模サブネット）
- [ ] **WAF-BIP-EDGE-024**: IPv6 /128（単一IP）
- [ ] **WAF-BIP-EDGE-025**: IPv6 /64（標準サブネット）

#### 3.4 特殊ケース
- [ ] **WAF-BIP-EDGE-030**: 全IPが同じIPセット
- [ ] **WAF-BIP-EDGE-031**: 各IPセットに1個ずつIP
- [ ] **WAF-BIP-EDGE-032**: IPセット名が非常に長い（128文字）

### 4. パフォーマンステスト (10ケース)

- [ ] **WAF-BIP-PERF-001**: 10件取得のレスポンスタイム < 500ms
- [ ] **WAF-BIP-PERF-002**: 100件取得のレスポンスタイム < 1000ms
- [ ] **WAF-BIP-PERF-003**: 1000件取得のレスポンスタイム < 2000ms
- [ ] **WAF-BIP-PERF-004**: 10000件取得のレスポンスタイム < 5000ms
- [ ] **WAF-BIP-PERF-005**: 地理情報付き100件取得 < 3000ms
- [ ] **WAF-BIP-PERF-006**: 地理分布集約100件 < 2000ms
- [ ] **WAF-BIP-PERF-007**: 同時10リクエストの並行処理
- [ ] **WAF-BIP-PERF-008**: 60秒間に100リクエスト（スループット）
- [ ] **WAF-BIP-PERF-009**: メモリ使用量（1000件取得） < 100MB
- [ ] **WAF-BIP-PERF-010**: Excel エクスポート1000件 < 3000ms

### 5. セキュリティテスト (10ケース)

- [ ] **WAF-BIP-SEC-001**: CORS設定が正しい
- [ ] **WAF-BIP-SEC-002**: 認証なし未認証ユーザーは拒否される（認証実装時）
- [ ] **WAF-BIP-SEC-003**: distributionIdにパストラバーサル文字列 → エスケープ
- [ ] **WAF-BIP-SEC-004**: distributionIdにコマンドインジェクション → エスケープ
- [ ] **WAF-BIP-SEC-005**: HTTPSのみ許可（本番環境）
- [ ] **WAF-BIP-SEC-006**: レスポンスヘッダーにセキュリティヘッダー設定
- [ ] **WAF-BIP-SEC-007**: AWS認証情報がレスポンスに含まれない
- [ ] **WAF-BIP-SEC-008**: エラーメッセージに機密情報が含まれない
- [ ] **WAF-BIP-SEC-009**: Rate Limiting確認（1分間に100リクエスト制限）
- [ ] **WAF-BIP-SEC-010**: ブロックIP情報の機密性保護

### 6. プロパティベーステスト (8ケース)

- [ ] **WAF-BIP-PROP-001**: 同じパラメータで複数回リクエスト → 常に同じ結果
- [ ] **WAF-BIP-PROP-002**: レスポンスJSON構造の一貫性
- [ ] **WAF-BIP-PROP-003**: すべてのケースでHTTPステータス2xx/4xx/5xx
- [ ] **WAF-BIP-PROP-004**: total値とblockedIps配列長の一貫性
- [ ] **WAF-BIP-PROP-005**: IPアドレスのソート順の一貫性
- [ ] **WAF-BIP-PROP-006**: CIDR形式の妥当性（すべてのIP）
- [ ] **WAF-BIP-PROP-007**: 地理情報の緯度経度範囲制約
- [ ] **WAF-BIP-PROP-008**: 国コードISO 3166-1形式の一貫性

### 7. スナップショットテスト (12ケース)

- [ ] **WAF-BIP-SNAP-001**: デフォルトプロファイルのレスポンス → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-002**: ブロックIP一覧（基本） → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-003**: ブロックIP一覧（IPv4） → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-004**: ブロックIP一覧（IPv6） → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-005**: ブロックIP一覧（混在） → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-006**: 詳細地理情報付き → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-007**: 地理分布情報 → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-008**: 複数IPセット → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-009**: 0件レスポンス → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-010**: エラーレスポンス（400） → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-011**: エラーレスポンス（403） → ゴールデンデータ一致
- [ ] **WAF-BIP-SNAP-012**: Excel エクスポート形式 → ゴールデンデータ一致

## 合計テストケース数: 150ケース

## テスト実装優先度

1. **高**: 正常系1.1-1.3, 1.6, 異常系2.1-2.3, スナップショット
2. **中**: 正常系1.4-1.5, 1.7-1.8, 異常系2.4-2.6, 境界値
3. **低**: パフォーマンス, セキュリティ, プロパティベース

## 自動化対象

- すべてのテストケースを自動化
- 正常系、異常系、スナップショットはCIで毎回実行
- パフォーマンステストはNightly実行
- Excel エクスポートは手動テストも併用

## テストデータ

### ゴールデンデータ
- 参照日: 2025-11-15
- ディストリビューションID: 環境変数から取得
- Web ACL ARN: 環境変数から取得
- ブロックIP数: 実環境による

### モックデータ（基本）
```json
{
  "blockedIps": [
    {
      "ip": "1.2.3.4",
      "cidr": "1.2.3.4/32",
      "ipSetId": "12345678-1234-1234-1234-123456789012",
      "ipSetName": "BlockedIPs",
      "ipSetArn": "arn:aws:wafv2:us-east-1:123456789012:global/ipset/BlockedIPs/12345678-1234-1234-1234-123456789012"
    },
    {
      "ip": "198.51.100.0",
      "cidr": "198.51.100.0/24",
      "ipSetId": "12345678-1234-1234-1234-123456789012",
      "ipSetName": "BlockedIPs",
      "ipSetArn": "arn:aws:wafv2:us-east-1:123456789012:global/ipset/BlockedIPs/12345678-1234-1234-1234-123456789012"
    },
    {
      "ip": "203.0.113.1",
      "cidr": "203.0.113.1/32",
      "ipSetId": "87654321-4321-4321-4321-210987654321",
      "ipSetName": "SuspiciousIPs",
      "ipSetArn": "arn:aws:wafv2:us-east-1:123456789012:global/ipset/SuspiciousIPs/87654321-4321-4321-4321-210987654321"
    }
  ],
  "total": 3,
  "ipSets": [
    {
      "id": "12345678-1234-1234-1234-123456789012",
      "name": "BlockedIPs",
      "arn": "arn:aws:wafv2:us-east-1:123456789012:global/ipset/BlockedIPs/12345678-1234-1234-1234-123456789012"
    },
    {
      "id": "87654321-4321-4321-4321-210987654321",
      "name": "SuspiciousIPs",
      "arn": "arn:aws:wafv2:us-east-1:123456789012:global/ipset/SuspiciousIPs/87654321-4321-4321-4321-210987654321"
    }
  ]
}
```

### モックデータ（詳細地理情報付き）
```json
{
  "blockedIps": [
    {
      "ip": "1.2.3.4",
      "cidr": "1.2.3.4/32",
      "representativeIp": "1.2.3.4",
      "cidrCategory": "single",
      "ipSetId": "12345678-1234-1234-1234-123456789012",
      "ipSetName": "BlockedIPs",
      "ipSetArn": "arn:aws:wafv2:us-east-1:123456789012:global/ipset/BlockedIPs/12345678-1234-1234-1234-123456789012",
      "geolocation": {
        "lat": 35.6895,
        "lon": 139.6917,
        "country": "Japan",
        "countryCode": "JP",
        "region": "Tokyo",
        "city": "Tokyo",
        "isp": "Example ISP",
        "org": "Example Organization",
        "asn": "AS1234"
      }
    }
  ],
  "total": 1,
  "totalWithoutGeo": 0,
  "ipSets": [...]
}
```

### モックデータ（地理分布）
```json
{
  "locations": [
    {
      "lat": 35.6895,
      "lon": 139.6917,
      "city": "Tokyo",
      "country": "Japan",
      "countryCode": "JP",
      "count": 5,
      "cidrs": ["1.2.3.4/32", "5.6.7.8/32"],
      "ipSetNames": ["BlockedIPs", "SuspiciousIPs"]
    }
  ],
  "total": 5
}
```

## 依存サービス

- AWS WAFv2 API
- AWS CloudFront API
- IP Geolocation API（ip-api.com）（/detail-geo/, /geo/のみ）
- AWS認証情報（~/.aws/credentials または環境変数）
- IAM権限:
  - `wafv2:ListIPSets`
  - `wafv2:GetIPSet`
  - `wafv2:GetWebACL`
  - `cloudfront:GetDistribution`

## 備考

### 代表IP選択ロジック（/detail-geo/）
- CIDR範囲の場合、最初のIPアドレスを代表IPとして選択
- 例: 198.51.100.0/24 → 代表IP: 198.51.100.0

### cidrCategory
- "single": /32（IPv4）または /128（IPv6）の単一IP
- "subnet": それ以外のサブネット範囲

### Excel エクスポート形式
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- ファイル名: `waf_blocked_ips_{distributionId}_{timestamp}.xlsx`
- シート名: "Blocked IPs"
- カラム: IP Address, CIDR, IP Set Name, IP Set ID, IP Set ARN

