# テスト設計: Utility Functions

## 対象ユーティリティ

1. AWSServiceBase - AWS基底クラス
2. CloudFront Constants - CloudFrontログフォーマット定数
3. IP Utils - IP関連ユーティリティ関数
4. Suspicious Check - 不審アクセス検出パターン

## テストケース設計

---

## 1. AWSServiceBase (25ケース)

### 1.1 初期化
- [ ] **AWSBase-001**: デフォルトプロファイルで初期化
- [ ] **AWSBase-002**: カスタムプロファイル名で初期化
- [ ] **AWSBase-003**: profile_nameが正しく設定される
- [ ] **AWSBase-004**: sessionが正しく作成される

### 1.2 AWSクライアント初期化
- [ ] **AWSBase-005**: s3_clientが正しく初期化される
- [ ] **AWSBase-006**: cloudfront_clientが正しく初期化される
- [ ] **AWSBase-007**: wafv2_clientが正しく初期化される
- [ ] **AWSBase-008**: wafv2_clientのregionがus-east-1
- [ ] **AWSBase-009**: すべてのクライアントが利用可能

### 1.3 キャッシュディレクトリ
- [ ] **AWSBase-010**: CACHE_DIRが正しく設定される
- [ ] **AWSBase-011**: 環境変数CLOUDFRONT_LOG_CACHE_DIRが優先される
- [ ] **AWSBase-012**: デフォルトパスが正しく計算される
- [ ] **AWSBase-013**: キャッシュディレクトリが自動作成される
- [ ] **AWSBase-014**: 既存のキャッシュディレクトリが保持される

### 1.4 異常系
- [ ] **AWSBase-015**: 存在しないプロファイル名でエラー
- [ ] **AWSBase-016**: AWS認証情報が無効な場合のエラー
- [ ] **AWSBase-017**: 環境変数に不正なパスが設定された場合

### 1.5 継承テスト
- [ ] **AWSBase-018**: ServiceクラスがAWSServiceBaseを継承
- [ ] **AWSBase-019**: 継承先でクライアントが利用可能
- [ ] **AWSBase-020**: 継承先でCACHE_DIRが利用可能

### 1.6 モックテスト
- [ ] **AWSBase-021**: boto3.Sessionをモック化してテスト
- [ ] **AWSBase-022**: 各クライアントをモック化してテスト

### 1.7 環境テスト
- [ ] **AWSBase-023**: 異なる環境変数設定でのテスト
- [ ] **AWSBase-024**: パス計算の正確性テスト
- [ ] **AWSBase-025**: ディレクトリ作成権限のテスト

---

## 2. CloudFront Constants (20ケース)

### 2.1 CLOUDFRONT_LOG_COLUMNS
- [ ] **CFConst-001**: すべてのカラム名が定義されている
- [ ] **CFConst-002**: カラム数が正しい（33カラム）
- [ ] **CFConst-003**: 各カラムの順序が正しい
- [ ] **CFConst-004**: dateが0番目のカラム
- [ ] **CFConst-005**: timeが1番目のカラム
- [ ] **CFConst-006**: c-ipが4番目のカラム
- [ ] **CFConst-007**: 新しいフィールド（c-port以降）が含まれる

### 2.2 FIELD_NAME_MAPPING
- [ ] **CFConst-008**: すべてのカラムがマッピングされている
- [ ] **CFConst-009**: date → dateのマッピング
- [ ] **CFConst-010**: c-ip → clientIpのマッピング
- [ ] **CFConst-011**: cs-uri-stem → uriStemのマッピング
- [ ] **CFConst-012**: sc-status → statusCodeのマッピング
- [ ] **CFConst-013**: time-taken → timeTakenのマッピング（キャメルケース）

### 2.3 完全性チェック
- [ ] **CFConst-014**: CLOUDFRONT_LOG_COLUMNSのすべてのカラムがFIELD_NAME_MAPPINGに存在
- [ ] **CFConst-015**: マッピング後のフィールド名が一意
- [ ] **CFConst-016**: マッピング後のフィールド名にハイフンが含まれない

### 2.4 CloudFront公式ドキュメントとの整合性
- [ ] **CFConst-017**: AWS公式のログフォーマットと一致
- [ ] **CFConst-018**: 拡張フィールドが含まれる
- [ ] **CFConst-019**: Field-Level Encryptionフィールドが含まれる
- [ ] **CFConst-020**: 最新のCloudFrontログフォーマットに対応

---

## 3. IP Utils (50ケース)

### 3.1 normalize_ip_address() - IPv4
- [ ] **IPUtils-001**: 単一IPv4アドレス → /32 CIDRに変換
- [ ] **IPUtils-002**: IPv4 CIDR表記 → そのまま返す
- [ ] **IPUtils-003**: "192.0.2.1" → "192.0.2.1/32"
- [ ] **IPUtils-004**: "192.0.2.0/24" → "192.0.2.0/24"
- [ ] **IPUtils-005**: "10.0.0.0/8" → "10.0.0.0/8"

### 3.2 normalize_ip_address() - IPv6
- [ ] **IPUtils-006**: 単一IPv6アドレス → /128 CIDRに変換
- [ ] **IPUtils-007**: IPv6 CIDR表記 → そのまま返す
- [ ] **IPUtils-008**: "2001:db8::1" → "2001:db8::1/128"
- [ ] **IPUtils-009**: "2001:db8::/32" → "2001:db8::/32"

### 3.3 normalize_ip_address() - 異常系
- [ ] **IPUtils-010**: 不正なIPアドレスでValueErrorをraise
- [ ] **IPUtils-011**: 空文字列でValueErrorをraise
- [ ] **IPUtils-012**: 不正なCIDR表記でValueErrorをraise
- [ ] **IPUtils-013**: エラーメッセージが適切

### 3.4 ip_in_network() - 正常系
- [ ] **IPUtils-014**: IPがネットワーク内の場合True
- [ ] **IPUtils-015**: IPがネットワーク外の場合False
- [ ] **IPUtils-016**: "192.0.2.1"が"192.0.2.0/24"に含まれる
- [ ] **IPUtils-017**: "192.0.2.1"が"10.0.0.0/8"に含まれない
- [ ] **IPUtils-018**: ネットワークアドレスがネットワークに含まれる
- [ ] **IPUtils-019**: ブロードキャストアドレスがネットワークに含まれる

### 3.5 ip_in_network() - 異常系
- [ ] **IPUtils-020**: 不正なIPアドレスでFalse
- [ ] **IPUtils-021**: 不正なCIDRでFalse
- [ ] **IPUtils-022**: 例外が発生せずFalseを返す

### 3.6 get_representative_ip_from_cidr() - シンプル戦略
- [ ] **IPUtils-023**: use_advanced=Falseでネットワークアドレスを返す
- [ ] **IPUtils-024**: "192.0.2.0/24" → "192.0.2.0"
- [ ] **IPUtils-025**: "192.0.2.1/32" → "192.0.2.1"

### 3.7 get_representative_ip_from_cidr() - 高度な戦略
- [ ] **IPUtils-026**: use_advanced=Trueで適切なオフセットを使用
- [ ] **IPUtils-027**: /32（単一IP） → そのIPを返す
- [ ] **IPUtils-028**: /24（256アドレス） → ネットワークアドレス+1
- [ ] **IPUtils-029**: /16（65536アドレス） → ネットワークアドレス+256
- [ ] **IPUtils-030**: /8（16777216アドレス） → ネットワークアドレス+65536
- [ ] **IPUtils-031**: 代表IPがネットワーク範囲内

### 3.8 get_representative_ip_from_cidr() - 境界値
- [ ] **IPUtils-032**: /31ネットワーク → 正しく処理
- [ ] **IPUtils-033**: /0ネットワーク（全IP） → 正しく処理
- [ ] **IPUtils-034**: オフセットがネットワーク範囲を超える場合の処理

### 3.9 get_representative_ip_from_cidr() - 異常系
- [ ] **IPUtils-035**: 不正なCIDR → ベースIPを返す（エラーではない）
- [ ] **IPUtils-036**: 空文字列 → 適切に処理

### 3.10 calculate_cidr_size_category() - 正常系
- [ ] **IPUtils-037**: /32（1アドレス） → "single"
- [ ] **IPUtils-038**: /24（256アドレス） → "small"
- [ ] **IPUtils-039**: /16（65536アドレス） → "medium"
- [ ] **IPUtils-040**: /8（16777216アドレス） → "large"
- [ ] **IPUtils-041**: /0（全IP） → "very_large"
- [ ] **IPUtils-042**: すべてのカテゴリが網羅される

### 3.11 calculate_cidr_size_category() - 境界値
- [ ] **IPUtils-043**: 1アドレス → "single"
- [ ] **IPUtils-044**: 2アドレス → "small"
- [ ] **IPUtils-045**: 256アドレス（境界） → "small"
- [ ] **IPUtils-046**: 257アドレス → "medium"
- [ ] **IPUtils-047**: 65536アドレス（境界） → "medium"
- [ ] **IPUtils-048**: 16777216アドレス（境界） → "large"

### 3.12 calculate_cidr_size_category() - 異常系
- [ ] **IPUtils-049**: 不正なCIDR → "unknown"
- [ ] **IPUtils-050**: 空文字列 → "unknown"

---

## 4. Suspicious Check (40ケース)

### 4.1 check_user_agent_suspicious() - 許可されたBot
- [ ] **SuspCheck-001**: Google botが許可される
- [ ] **SuspCheck-002**: Bingbotが許可される
- [ ] **SuspCheck-003**: Applebotが許可される
- [ ] **SuspCheck-004**: facebookexternalhitが許可される
- [ ] **SuspCheck-005**: is_allowed_bot=Trueが返される
- [ ] **SuspCheck-006**: matched_patternsに"Allowed"が含まれる

### 4.2 check_user_agent_suspicious() - ブロックされたツール
- [ ] **SuspCheck-007**: Pythonスクリプトがブロックされる
- [ ] **SuspCheck-008**: Scrapyがブロックされる
- [ ] **SuspCheck-009**: SEO toolがブロックされる
- [ ] **SuspCheck-010**: Archive toolがブロックされる
- [ ] **SuspCheck-011**: is_blocked=True、is_suspicious=Trueが返される
- [ ] **SuspCheck-012**: severity="danger"が返される
- [ ] **SuspCheck-013**: matched_patternsに"Blocked"が含まれる

### 4.3 check_user_agent_suspicious() - 不審なパターン
- [ ] **SuspCheck-014**: LINEアプリが不審と判定される
- [ ] **SuspCheck-015**: Chatworkが不審と判定される
- [ ] **SuspCheck-016**: PhantomJSが不審と判定される
- [ ] **SuspCheck-017**: is_suspicious=Trueが返される
- [ ] **SuspCheck-018**: severity="warning"が返される

### 4.4 check_user_agent_suspicious() - 正常なブラウザ
- [ ] **SuspCheck-019**: Chrome UAgentが安全と判定される
- [ ] **SuspCheck-020**: Firefox UAgentが安全と判定される
- [ ] **SuspCheck-021**: Safari UAgentが安全と判定される
- [ ] **SuspCheck-022**: is_suspicious=False、severity="safe"が返される

### 4.5 check_user_agent_suspicious() - 境界値
- [ ] **SuspCheck-023**: 空文字列の処理
- [ ] **SuspCheck-024**: "-"の処理（CloudFrontで未設定）
- [ ] **SuspCheck-025**: Noneの処理
- [ ] **SuspCheck-026**: 非常に長いUser-Agentの処理

### 4.6 check_referrer_suspicious() - 正常系（関数がある場合）
- [ ] **SuspCheck-027**: ブロックされたreferrerを検出
- [ ] **SuspCheck-028**: 正常なreferrerが安全と判定される

### 4.7 analyze_log_entries() - 統合テスト
- [ ] **SuspCheck-029**: ログエントリに不審チェック結果が付与される
- [ ] **SuspCheck-030**: 複数のログエントリが正しく処理される
- [ ] **SuspCheck-031**: suspiciousCheckフィールドが正しく設定される

### 4.8 正規表現パターンテスト
- [ ] **SuspCheck-032**: POTENTIAL_BOTS_UAパターンが正しく動作
- [ ] **SuspCheck-033**: ALLOWED_GOOGLE_UR_1パターンが正しく動作
- [ ] **SuspCheck-034**: BLOCKED_SCRAPING_TOOLS_UAパターンが正しく動作
- [ ] **SuspCheck-035**: BLOCKED_SEO_TOOLS_UAパターンが正しく動作
- [ ] **SuspCheck-036**: SUSPICIOUS_UAパターンが正しく動作
- [ ] **SuspCheck-037**: BLOCKED_REFERRERパターンが正しく動作

### 4.9 パターンの優先順位
- [ ] **SuspCheck-038**: 許可パターンがブロックパターンより優先される
- [ ] **SuspCheck-039**: 複数のパターンにマッチする場合、すべて記録される
- [ ] **SuspCheck-040**: マッチした順序が一貫している

---

## 5. 横断的テスト (15ケース)

### 5.1 パフォーマンステスト
- [ ] **Utils-Perf-001**: normalize_ip_addressの実行時間 < 1ms
- [ ] **Utils-Perf-002**: ip_in_networkの実行時間 < 1ms
- [ ] **Utils-Perf-003**: check_user_agent_suspiciousの実行時間 < 5ms
- [ ] **Utils-Perf-004**: 1000件のIP処理時間測定
- [ ] **Utils-Perf-005**: 1000件のUser-Agent処理時間測定

### 5.2 メモリ使用量
- [ ] **Utils-Mem-001**: 大量IP処理時のメモリ使用量測定
- [ ] **Utils-Mem-002**: 正規表現パターンのメモリ効率

### 5.3 エッジケース
- [ ] **Utils-Edge-001**: Unicodeを含むIPアドレス（無効）
- [ ] **Utils-Edge-002**: 非常に長い文字列の処理
- [ ] **Utils-Edge-003**: null文字を含む文字列の処理
- [ ] **Utils-Edge-004**: 改行文字を含む文字列の処理

### 5.4 セキュリティ
- [ ] **Utils-Sec-001**: ReDoS（Regular expression Denial of Service）対策
- [ ] **Utils-Sec-002**: インジェクション文字列の安全な処理
- [ ] **Utils-Sec-003**: 正規表現パターンの安全性検証

### 5.5 互換性
- [ ] **Utils-Compat-001**: Python 3.8以降での動作確認
- [ ] **Utils-Compat-002**: 異なるOS（Windows, Linux, macOS）での動作確認

---

## 合計テストケース数: 150ケース

## テスト実装優先度

1. **高（優先実装）**:
   - IP Utils全関数の正常系テスト
   - Suspicious Check関数の正常系テスト
   - CloudFront Constantsの完全性チェック
   - AWSServiceBase初期化テスト

2. **中（次期実装）**:
   - IP Utils異常系テスト
   - Suspicious Check境界値テスト
   - AWSServiceBaseモックテスト
   - 正規表現パターンテスト

3. **低（後回し可）**:
   - パフォーマンステスト（Nightlyビルド用）
   - メモリ使用量テスト
   - セキュリティテスト（ReDoS等）
   - 互換性テスト

## 自動化対象

- すべてのテストケースを自動化
- CIパイプラインで優先度「高」「中」を実行
- Nightlyビルドでパフォーマンステスト実行

## テストデータ

### IP Utils テストデータ
```python
# IPv4
test_ipv4 = [
    ("192.0.2.1", "192.0.2.1/32"),
    ("192.0.2.0/24", "192.0.2.0/24"),
    ("10.0.0.0/8", "10.0.0.0/8"),
]

# IPv6
test_ipv6 = [
    ("2001:db8::1", "2001:db8::1/128"),
    ("2001:db8::/32", "2001:db8::/32"),
]

# 不正なIP
invalid_ips = [
    "invalid",
    "999.999.999.999",
    "",
    "192.0.2.1/33",  # 不正なCIDR
]
```

### Suspicious Check テストデータ
```python
# 許可されたBot
allowed_bots = [
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "facebookexternalhit/1.1",
]

# ブロックされたツール
blocked_tools = [
    "Python/3.8",
    "Scrapy/2.5.0",
    "SemrushBot",
    "archive.org_bot",
]

# 不審なパターン
suspicious_patterns = [
    "LINE/10.3.0",
    "Chatwork/1.0",
    "PhantomJS/2.1.1",
]

# 正常なブラウザ
normal_browsers = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]
```

## テスト実装方法

### 単純な関数テスト
```python
def test_normalize_ip_address():
    assert normalize_ip_address("192.0.2.1") == "192.0.2.1/32"
    assert normalize_ip_address("192.0.2.0/24") == "192.0.2.0/24"
```

### 異常系テスト
```python
def test_normalize_ip_address_invalid():
    with pytest.raises(ValueError) as exc_info:
        normalize_ip_address("invalid")
    assert "Invalid IP address" in str(exc_info.value)
```

### 正規表現パターンテスト
```python
def test_google_bot_pattern():
    result = check_user_agent_suspicious(
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    )
    assert result['is_allowed_bot'] is True
    assert result['is_suspicious'] is False
    assert "Google bot" in result['matched_patterns']
```

### パラメータ化テスト
```python
@pytest.mark.parametrize("ip,expected", [
    ("192.0.2.1", "192.0.2.1/32"),
    ("10.0.0.0/8", "10.0.0.0/8"),
    ("2001:db8::1", "2001:db8::1/128"),
])
def test_normalize_ip_address_parametrize(ip, expected):
    assert normalize_ip_address(ip) == expected
```

## 依存ライブラリ

- ipaddress (Python標準ライブラリ)
- re (Python標準ライブラリ)
- boto3 (AWS SDK)
- pytest
- pytest-benchmark（パフォーマンステスト用）

## 備考

- IP関連関数はPythonの標準ライブラリ`ipaddress`を使用しているため、信頼性が高い
- 正規表現パターンはReDoS攻撃に対する脆弱性チェックが必要
- CloudFront ConstantsはAWS公式ドキュメントとの整合性を定期的に確認
- AWSServiceBaseは実際のAWS呼び出しをモック化してテスト
- パフォーマンステストはベンチマークツール（pytest-benchmark）を使用
