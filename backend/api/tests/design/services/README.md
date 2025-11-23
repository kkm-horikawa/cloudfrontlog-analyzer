# テスト設計: Service Classes

## 対象サービスクラス

1. DistributionService - CloudFrontディストリビューション操作
2. LogService - CloudFrontログ操作
3. GeoService - 地理情報集約操作
4. WAFService - WAF操作
5. IP Info関数群 - IP地理情報取得

## テストケース設計

---

## 1. DistributionService (35ケース)

### 1.1 list_distributions() - 正常系
- [ ] **DistSvc-001**: ディストリビューション一覧を正しく取得
- [ ] **DistSvc-002**: 複数のディストリビューションを正しく取得
- [ ] **DistSvc-003**: ディストリビューションが0件の場合、空リストを返す
- [ ] **DistSvc-004**: 各ディストリビューションにid, domain, aliasesが含まれる
- [ ] **DistSvc-005**: aliasesが存在しない場合、空リストを返す
- [ ] **DistSvc-006**: aliasesが複数ある場合、すべて取得

### 1.2 list_distributions() - 異常系
- [ ] **DistSvc-007**: AWS ClientError発生時にValueErrorをraiseする
- [ ] **DistSvc-008**: レスポンスにDistributionListが存在しない場合、空リストを返す
- [ ] **DistSvc-009**: レスポンスにItemsが存在しない場合、空リストを返す
- [ ] **DistSvc-010**: 認証エラー時に適切なエラーメッセージ

### 1.3 get_distribution_config() - 正常系
- [ ] **DistSvc-011**: 有効なディストリビューションIDで設定を取得
- [ ] **DistSvc-012**: DistributionConfigが正しく返される
- [ ] **DistSvc-013**: ログ設定が含まれる

### 1.4 get_distribution_config() - 異常系
- [ ] **DistSvc-014**: 存在しないディストリビューションIDでValueErrorをraise
- [ ] **DistSvc-015**: AWS ClientError発生時にValueErrorをraise
- [ ] **DistSvc-016**: 不正なディストリビューションID形式でエラー

### 1.5 get_log_bucket_info() - 正常系
- [ ] **DistSvc-017**: ログが有効な場合、bucket情報を取得
- [ ] **DistSvc-018**: bucketとprefixが正しく返される
- [ ] **DistSvc-019**: bucket名から.s3.amazonaws.com接尾辞が削除される
- [ ] **DistSvc-020**: prefixが空の場合も正しく処理

### 1.6 get_log_bucket_info() - 異常系
- [ ] **DistSvc-021**: ログが無効な場合、Noneを返す
- [ ] **DistSvc-022**: Logging設定が存在しない場合、Noneを返す
- [ ] **DistSvc-023**: Enabledがfalseの場合、Noneを返す

### 1.7 モック使用テスト
- [ ] **DistSvc-024**: CloudFrontクライアントをモック化してテスト
- [ ] **DistSvc-025**: list_distributionsのレスポンスをモック化
- [ ] **DistSvc-026**: get_distribution_configのレスポンスをモック化
- [ ] **DistSvc-027**: ClientErrorをシミュレート

### 1.8 統合テスト
- [ ] **DistSvc-028**: 実際のAWS APIを呼び出す統合テスト（任意）
- [ ] **DistSvc-029**: プロファイル指定が正しく動作
- [ ] **DistSvc-030**: AWSServiceBaseの継承が正しく動作

### 1.9 境界値テスト
- [ ] **DistSvc-031**: ディストリビューション数が100件以上の場合
- [ ] **DistSvc-032**: aliasesが20個の場合
- [ ] **DistSvc-033**: 非常に長いdomain名の処理
- [ ] **DistSvc-034**: 非常に長いprefixの処理
- [ ] **DistSvc-035**: bucket名に特殊文字が含まれる場合

---

## 2. LogService (55ケース)

### 2.1 search_logs() - 正常系
- [ ] **LogSvc-001**: 指定したURLのログを正しく検索
- [ ] **LogSvc-002**: 時間窓内のログをすべて取得
- [ ] **LogSvc-003**: 複数のログファイルにまたがる検索
- [ ] **LogSvc-004**: 検索結果が日時順にソートされる
- [ ] **LogSvc-005**: 検索結果が0件の場合、空リストを返す
- [ ] **LogSvc-006**: time_window_minutesが正しく適用される

### 2.2 search_logs() - 異常系
- [ ] **LogSvc-007**: ログが無効なディストリビューションでValueErrorをraise
- [ ] **LogSvc-008**: 存在しないディストリビューションIDでエラー
- [ ] **LogSvc-009**: S3バケットへのアクセス権限がない場合のエラー
- [ ] **LogSvc-010**: ログファイルが見つからない場合のエラー処理

### 2.3 search_logs() - 時間窓テスト
- [ ] **LogSvc-011**: time_window_minutes=1で正しく検索
- [ ] **LogSvc-012**: time_window_minutes=60で正しく検索
- [ ] **LogSvc-013**: 時間窓の境界ちょうどのログが含まれる
- [ ] **LogSvc-014**: 時間窓外のログが除外される

### 2.4 list_raw_logs() - 正常系
- [ ] **LogSvc-015**: 日付範囲でログを取得
- [ ] **LogSvc-016**: ページネーションが正しく動作
- [ ] **LogSvc-017**: per_pageが正しく適用される
- [ ] **LogSvc-018**: client_ipフィルタが正しく動作
- [ ] **LogSvc-019**: uri_pathフィルタが正しく動作
- [ ] **LogSvc-020**: referrerフィルタが正しく動作（部分一致）
- [ ] **LogSvc-021**: query_stringフィルタが正しく動作（部分一致）
- [ ] **LogSvc-022**: client_ips（複数IP）フィルタが正しく動作
- [ ] **LogSvc-023**: start_time、end_time指定が正しく動作

### 2.5 list_raw_logs() - 異常系
- [ ] **LogSvc-024**: ログが無効なディストリビューションでValueErrorをraise
- [ ] **LogSvc-025**: 不正な日付範囲でエラー
- [ ] **LogSvc-026**: page=0でエラー
- [ ] **LogSvc-027**: per_page=0でエラー

### 2.6 list_raw_logs() - ページネーション
- [ ] **LogSvc-028**: page=1で最初のページを取得
- [ ] **LogSvc-029**: page=2で2ページ目を取得
- [ ] **LogSvc-030**: 最終ページの処理が正しい
- [ ] **LogSvc-031**: per_page=1000で正しく動作
- [ ] **LogSvc-032**: total_pagesが正しく計算される
- [ ] **LogSvc-033**: total_countが正しく返される

### 2.7 _list_log_files() - 内部メソッド
- [ ] **LogSvc-034**: S3からログファイル一覧を取得
- [ ] **LogSvc-035**: prefixが正しく適用される
- [ ] **LogSvc-036**: 日付範囲でフィルタリングされる
- [ ] **LogSvc-037**: 空のファイル一覧を正しく処理

### 2.8 _parse_log_file() - 内部メソッド
- [ ] **LogSvc-038**: gzip圧縮ファイルを正しく展開
- [ ] **LogSvc-039**: TSVフォーマットを正しくパース
- [ ] **LogSvc-040**: CloudFrontログのカラム名マッピングが正しい
- [ ] **LogSvc-041**: 不完全なログエントリを適切に処理
- [ ] **LogSvc-042**: コメント行（#で始まる行）をスキップ

### 2.9 フィールドマッピング
- [ ] **LogSvc-043**: CLOUDFRONT_LOG_COLUMNSが正しく使用される
- [ ] **LogSvc-044**: FIELD_NAME_MAPPINGが正しく適用される
- [ ] **LogSvc-045**: すべての必須フィールドがマッピングされる

### 2.10 モック使用テスト
- [ ] **LogSvc-046**: S3クライアントをモック化してテスト
- [ ] **LogSvc-047**: DistributionServiceをモック化してテスト
- [ ] **LogSvc-048**: ログファイルの内容をモック化

### 2.11 統合テスト
- [ ] **LogSvc-049**: 実際のS3からログファイルを取得（任意）
- [ ] **LogSvc-050**: 実際のログファイルをパース（任意）

### 2.12 パフォーマンステスト
- [ ] **LogSvc-051**: 大量ログファイル（100件）の処理時間
- [ ] **LogSvc-052**: 大きなログファイル（100MB）の処理時間
- [ ] **LogSvc-053**: ページネーションのパフォーマンス
- [ ] **LogSvc-054**: フィルタリングのパフォーマンス
- [ ] **LogSvc-055**: メモリ使用量の測定

---

## 3. GeoService (40ケース)

### 3.1 get_geo_aggregated_logs() - 正常系
- [ ] **GeoSvc-001**: 地理情報で集約されたログを取得
- [ ] **GeoSvc-002**: 国ごとにアクセス数が集計される
- [ ] **GeoSvc-003**: 代表IPが正しく選択される
- [ ] **GeoSvc-004**: サンプルログが取得される

### 3.2 get_geo_aggregated_logs() - キャッシュ
- [ ] **GeoSvc-005**: キャッシュが存在する場合、キャッシュから取得
- [ ] **GeoSvc-006**: キャッシュが存在しない場合、新規作成
- [ ] **GeoSvc-007**: キャッシュが期限切れの場合、再取得
- [ ] **GeoSvc-008**: フィルタ指定時はキャッシュを使用しない
- [ ] **GeoSvc-009**: キャッシュの有効期限が正しく設定される
- [ ] **GeoSvc-010**: 永続的キャッシュ（expires_at=None）が正しく動作

### 3.3 get_geo_aggregated_logs() - フィルタ
- [ ] **GeoSvc-011**: uri_filterが正しく動作（部分一致）
- [ ] **GeoSvc-012**: referer_filterが正しく動作（部分一致）
- [ ] **GeoSvc-013**: query_filterが正しく動作（部分一致）
- [ ] **GeoSvc-014**: status_filterが正しく動作（完全一致）
- [ ] **GeoSvc-015**: method_filterが正しく動作（完全一致）
- [ ] **GeoSvc-016**: 複数フィルタの組み合わせが正しく動作

### 3.4 get_geo_aggregated_logs() - 時刻指定
- [ ] **GeoSvc-017**: start_time、end_time指定が正しく動作
- [ ] **GeoSvc-018**: JSTからUTCへの変換が正しい
- [ ] **GeoSvc-019**: 時刻のみ指定した場合の範囲が正しい

### 3.5 get_geo_aggregated_logs() - 異常系
- [ ] **GeoSvc-020**: ログが無効なディストリビューションでValueErrorをraise
- [ ] **GeoSvc-021**: 不正な日付範囲でエラー
- [ ] **GeoSvc-022**: 不正な時刻形式でエラー

### 3.6 _get_cached_geo_logs() - 内部メソッド
- [ ] **GeoSvc-023**: データベースからキャッシュを検索
- [ ] **GeoSvc-024**: 部分一致するキャッシュを検索
- [ ] **GeoSvc-025**: 複数のキャッシュから最適なものを選択
- [ ] **GeoSvc-026**: キャッシュが見つからない場合Noneを返す

### 3.7 _save_geo_cache() - 内部メソッド
- [ ] **GeoSvc-027**: 集約データをデータベースに保存
- [ ] **GeoSvc-028**: actual_start_datetime、actual_end_datetimeが正しく設定される
- [ ] **GeoSvc-029**: locations_dataがJSON形式で保存される
- [ ] **GeoSvc-030**: total_countが正しく保存される

### 3.8 IP情報統合
- [ ] **GeoSvc-031**: get_ip_info_batchが正しく呼び出される
- [ ] **GeoSvc-032**: 代表IPの地理情報が取得される
- [ ] **GeoSvc-033**: IP情報がキャッシュされる

### 3.9 モック使用テスト
- [ ] **GeoSvc-034**: LogServiceをモック化してテスト
- [ ] **GeoSvc-035**: get_ip_info_batchをモック化してテスト
- [ ] **GeoSvc-036**: データベースキャッシュをモック化

### 3.10 統合テスト
- [ ] **GeoSvc-037**: 実際のログファイルから集約（任意）
- [ ] **GeoSvc-038**: データベースキャッシュの読み書き統合テスト

### 3.11 パフォーマンステスト
- [ ] **GeoSvc-039**: 大量ログ（10万件）の集約時間
- [ ] **GeoSvc-040**: キャッシュヒット時のレスポンス時間

---

## 4. WAFService (45ケース)

### 4.1 get_waf_web_acl_for_distribution() - 正常系
- [ ] **WAFSvc-001**: ディストリビューションに関連付けられたWeb ACLを取得
- [ ] **WAFSvc-002**: Web ACLのid、name、arn、lockTokenが含まれる
- [ ] **WAFSvc-003**: 複数のWeb ACLから正しいものを選択

### 4.2 get_waf_web_acl_for_distribution() - 異常系
- [ ] **WAFSvc-004**: WAFが関連付けられていない場合Noneを返す
- [ ] **WAFSvc-005**: WebACLIdが空の場合Noneを返す
- [ ] **WAFSvc-006**: AWS ClientError発生時にValueErrorをraise

### 4.3 _extract_ip_set_references() - 内部メソッド
- [ ] **WAFSvc-007**: IPSetReferenceStatementからARNを抽出
- [ ] **WAFSvc-008**: OrStatementから再帰的に抽出
- [ ] **WAFSvc-009**: AndStatementから再帰的に抽出
- [ ] **WAFSvc-010**: NotStatementから再帰的に抽出
- [ ] **WAFSvc-011**: 複雑にネストされたStatementから抽出
- [ ] **WAFSvc-012**: 空のStatementで空リストを返す

### 4.4 list_waf_ip_sets() - 正常系
- [ ] **WAFSvc-013**: Web ACL内のすべてのIP Setを取得
- [ ] **WAFSvc-014**: IP Setのid、name、arnが含まれる
- [ ] **WAFSvc-015**: 複数のIP Setを正しく取得
- [ ] **WAFSvc-016**: IP Setが0件の場合、空リストを返す

### 4.5 list_waf_ip_sets() - 異常系
- [ ] **WAFSvc-017**: WAFが関連付けられていない場合エラー
- [ ] **WAFSvc-018**: AWS ClientError発生時にValueErrorをraise

### 4.6 get_waf_blocked_ips() - 正常系
- [ ] **WAFSvc-019**: ブロックされたIPのリストを取得
- [ ] **WAFSvc-020**: 各IPにCIDR、ip_set情報が含まれる
- [ ] **WAFSvc-021**: 複数のIP SetからすべてのIPを取得
- [ ] **WAFSvc-022**: IPv4とIPv6の両方を正しく処理
- [ ] **WAFSvc-023**: 代表IPが正しく計算される

### 4.7 get_waf_blocked_ips() - 集約
- [ ] **WAFSvc-024**: aggregateByCountryがTrueの場合、国ごとに集約
- [ ] **WAFSvc-025**: 各国のIP数が正しくカウントされる
- [ ] **WAFSvc-026**: 代表IPが各国ごとに選択される
- [ ] **WAFSvc-027**: 集約時にサンプルIPが含まれる

### 4.8 get_waf_blocked_ips() - 異常系
- [ ] **WAFSvc-028**: WAFが関連付けられていない場合エラー
- [ ] **WAFSvc-029**: IP Setが空の場合、空リストを返す
- [ ] **WAFSvc-030**: 不正なCIDR形式でエラー処理

### 4.9 データベース統合
- [ ] **WAFSvc-031**: WAFBlockedIPSnapshotを作成
- [ ] **WAFSvc-032**: WAFBlockedIPを一括作成
- [ ] **WAFSvc-033**: IPGeolocationとの関連付け
- [ ] **WAFSvc-034**: 既存のスナップショットとの重複防止

### 4.10 IP情報統合
- [ ] **WAFSvc-035**: get_ip_info_batchが正しく呼び出される
- [ ] **WAFSvc-036**: 代表IPの地理情報が取得される
- [ ] **WAFSvc-037**: IP情報がキャッシュされる

### 4.11 CIDR処理
- [ ] **WAFSvc-038**: calculate_cidr_size_categoryが正しく動作
- [ ] **WAFSvc-039**: get_representative_ip_from_cidrが正しく動作
- [ ] **WAFSvc-040**: normalize_ip_addressが正しく動作
- [ ] **WAFSvc-041**: ip_in_networkが正しく動作

### 4.12 モック使用テスト
- [ ] **WAFSvc-042**: WAFv2クライアントをモック化してテスト
- [ ] **WAFSvc-043**: DistributionServiceをモック化してテスト

### 4.13 統合テスト
- [ ] **WAFSvc-044**: 実際のWAF APIを呼び出す（任意）

### 4.14 パフォーマンステスト
- [ ] **WAFSvc-045**: 大量IP（10000件）の処理時間

---

## 5. IP Info関数群 (50ケース)

### 5.1 get_ip_info_from_db() - 正常系
- [ ] **IPInfo-001**: データベースからIP情報を取得
- [ ] **IPInfo-002**: hit_countが増加する
- [ ] **IPInfo-003**: すべてのフィールドが正しく返される
- [ ] **IPInfo-004**: WHOIS情報が存在する場合、含めて返す
- [ ] **IPInfo-005**: WHOIS情報が存在しない場合、None

### 5.2 get_ip_info_from_db() - 異常系
- [ ] **IPInfo-006**: IP情報が存在しない場合、Noneを返す
- [ ] **IPInfo-007**: データベースエラー時の処理

### 5.3 save_ip_info_to_db() - 正常系
- [ ] **IPInfo-008**: 新規IP情報をデータベースに保存
- [ ] **IPInfo-009**: 既存IP情報を更新
- [ ] **IPInfo-010**: すべてのフィールドが正しく保存される
- [ ] **IPInfo-011**: WHOIS情報が含まれる場合、保存される

### 5.4 save_ip_info_to_db() - 異常系
- [ ] **IPInfo-012**: 不正なIP情報でエラー処理
- [ ] **IPInfo-013**: データベースエラー時の処理

### 5.5 get_ip_info() - 正常系
- [ ] **IPInfo-014**: データベースキャッシュが存在する場合、そこから取得
- [ ] **IPInfo-015**: キャッシュが存在しない場合、外部APIから取得
- [ ] **IPInfo-016**: 外部API取得後、データベースに保存
- [ ] **IPInfo-017**: メモリキャッシュが正しく動作

### 5.6 get_ip_info() - 外部API
- [ ] **IPInfo-018**: ip-api.comから正しくデータ取得
- [ ] **IPInfo-019**: レート制限を遵守（45req/min）
- [ ] **IPInfo-020**: API障害時にリトライ
- [ ] **IPInfo-021**: タイムアウト時の処理

### 5.7 get_ip_info() - 異常系
- [ ] **IPInfo-022**: 不正なIPアドレスでエラー
- [ ] **IPInfo-023**: 外部API障害時のフォールバック処理
- [ ] **IPInfo-024**: ネットワーク接続エラー時の処理

### 5.8 get_ip_info_batch() - 正常系
- [ ] **IPInfo-025**: 複数のIPを一括取得
- [ ] **IPInfo-026**: バッチサイズが正しく制御される
- [ ] **IPInfo-027**: レート制限を遵守
- [ ] **IPInfo-028**: すべてのIPが処理される

### 5.9 get_ip_info_batch() - 異常系
- [ ] **IPInfo-029**: 一部のIP取得失敗時も継続
- [ ] **IPInfo-030**: 空のIPリストで空ディクショナリを返す

### 5.10 fetch_whois() - 正常系
- [ ] **IPInfo-031**: WHOIS情報を外部APIから取得
- [ ] **IPInfo-032**: netname、org_name、country、net_rangeを抽出
- [ ] **IPInfo-033**: raw WHOIS情報を保存

### 5.11 fetch_whois() - 異常系
- [ ] **IPInfo-034**: 外部API障害時のエラー処理
- [ ] **IPInfo-035**: タイムアウト時の処理
- [ ] **IPInfo-036**: レート制限超過時の処理

### 5.12 fetch_missing_whois_batch() - 正常系
- [ ] **IPInfo-037**: WHOIS未取得IPをすべて取得
- [ ] **IPInfo-038**: バッチ処理が正しく動作
- [ ] **IPInfo-039**: 進捗状況がログ出力される

### 5.13 fetch_missing_whois_batch() - 異常系
- [ ] **IPInfo-040**: 一部のIP取得失敗時も継続
- [ ] **IPInfo-041**: データベースエラー時の処理

### 5.14 キャッシュ機能
- [ ] **IPInfo-042**: メモリキャッシュが正しく動作
- [ ] **IPInfo-043**: データベースキャッシュが正しく動作
- [ ] **IPInfo-044**: 二段階キャッシュが効率的に動作

### 5.15 モック使用テスト
- [ ] **IPInfo-045**: 外部API呼び出しをモック化
- [ ] **IPInfo-046**: データベース操作をモック化
- [ ] **IPInfo-047**: requests.getをモック化

### 5.16 統合テスト
- [ ] **IPInfo-048**: 実際の外部API呼び出し（制限あり）
- [ ] **IPInfo-049**: データベースとの統合テスト

### 5.17 パフォーマンステスト
- [ ] **IPInfo-050**: 100件のIP一括取得時間

---

## 合計テストケース数: 225ケース

## テスト実装優先度

1. **高（優先実装）**:
   - すべてのServiceクラスの正常系テスト
   - モック使用テスト（外部API呼び出しをモック化）
   - エラーハンドリングテスト

2. **中（次期実装）**:
   - 内部メソッドのテスト
   - 境界値テスト
   - データベース統合テスト
   - キャッシュ機能テスト

3. **低（後回し可）**:
   - 統合テスト（実際のAWS API呼び出し）
   - パフォーマンステスト（Nightlyビルド用）

## 自動化対象

- すべてのテストケースを自動化
- CIパイプラインで優先度「高」「中」を実行（モック使用）
- Nightlyビルドでパフォーマンステスト実行
- 実際のAWS API呼び出しテストは手動または週次実行

## テストデータ

### DistributionService モックデータ
```python
mock_distributions = {
    "DistributionList": {
        "Items": [
            {
                "Id": "E1234567890ABC",
                "DomainName": "d111111abcdef8.cloudfront.net",
                "Aliases": {"Items": ["example.com"]}
            }
        ]
    }
}
```

### LogService モックデータ
```python
mock_log_content = """#Version: 1.0
#Fields: date time x-edge-location sc-bytes c-ip cs-method cs(Host) cs-uri-stem sc-status cs(Referer) cs(User-Agent) cs-uri-query cs(Cookie) x-edge-result-type x-edge-request-id x-host-header cs-protocol cs-bytes time-taken x-forwarded-for ssl-protocol ssl-cipher x-edge-response-result-type cs-protocol-version fle-status fle-encrypted-fields
2025-11-15\t12:00:00\tNRT51-C1\t1234\t192.0.2.1\tGET\td111111abcdef8.cloudfront.net\t/test/path\t200\t-\tMozilla/5.0\t-\t-\tHit\trequest-id\texample.com\thttps\t500\t0.123\t-\tTLSv1.3\tTLS_AES_128_GCM_SHA256\tHit\tHTTP/2.0\t-\t-
"""
```

### GeoService モックデータ
```python
mock_geo_cache = {
    "distribution_id": "E1234567890ABC",
    "start_date": "2025-11-01",
    "end_date": "2025-11-30",
    "locations_data": {
        "JP": {"count": 100, "ips": ["192.0.2.1"]}
    },
    "total_count": 100
}
```

## テスト実装方法

### モックの使用
```python
from unittest.mock import Mock, patch

def test_list_distributions():
    with patch('boto3.client') as mock_client:
        mock_client.return_value.list_distributions.return_value = mock_distributions
        service = DistributionService()
        result = service.list_distributions()
        assert len(result) == 1
        assert result[0]['id'] == "E1234567890ABC"
```

### 外部API呼び出しのモック
```python
def test_get_ip_info():
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            "status": "success",
            "country": "Japan",
            "countryCode": "JP"
        }
        result = get_ip_info("192.0.2.1")
        assert result['country'] == "Japan"
```

### データベース操作のモック
```python
@pytest.fixture
def mock_ip_geolocation(db):
    from api.models import IPGeolocation
    return IPGeolocation.objects.create(
        ip_address="192.0.2.1",
        country="Japan"
    )
```

## 依存ライブラリ

- boto3 (AWS SDK)
- requests (外部API呼び出し)
- pandas (ログファイル処理)
- pytest
- pytest-mock
- unittest.mock

## 備考

- 外部API呼び出しは必ずモック化してテスト
- AWS API呼び出しも原則モック化（統合テストを除く）
- レート制限を考慮したテスト設計
- エラーハンドリングを重点的にテスト
- パフォーマンステストは別途実行（Nightly）
