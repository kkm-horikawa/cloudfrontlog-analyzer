# テスト設計: Django Models

## 対象モデル

1. IPGeolocation - IP地理情報キャッシュ
2. AccessLog - CloudFrontアクセスログ
3. WAFBlockedIP - WAFブロックIP詳細
4. WAFBlockedIPSnapshot - WAFブロックIPスナップショット
5. GeoLogCache - 地理情報集約キャッシュ
6. ProcessedLogFile - 処理済みログファイル管理

## テストケース設計

---

## 1. IPGeolocation モデル (20ケース)

### 1.1 フィールドバリデーション
- [ ] **IPGeo-001**: ip_addressが必須フィールド
- [ ] **IPGeo-002**: ip_addressがunique制約
- [ ] **IPGeo-003**: ip_addressの最大長が45文字（IPv6対応）
- [ ] **IPGeo-004**: ip_addressにインデックスが設定されている
- [ ] **IPGeo-005**: continentがnull許可、blank許可
- [ ] **IPGeo-006**: countryがnull許可、blank許可
- [ ] **IPGeo-007**: latitudeがFloatFieldでnull許可
- [ ] **IPGeo-008**: longitudeがFloatFieldでnull許可
- [ ] **IPGeo-009**: offsetがIntegerFieldでnull許可

### 1.2 WHOIS関連フィールド
- [ ] **IPGeo-010**: whois_rawがTextFieldでnull許可
- [ ] **IPGeo-011**: whois_rawにインデックスが設定されている
- [ ] **IPGeo-012**: whois_netnameがnull許可でインデックスあり
- [ ] **IPGeo-013**: whois_org_nameがnull許可でインデックスあり

### 1.3 メタデータフィールド
- [ ] **IPGeo-014**: created_atが自動設定される（auto_now_add=True）
- [ ] **IPGeo-015**: updated_atが自動更新される（auto_now=True）
- [ ] **IPGeo-016**: hit_countのデフォルト値が0
- [ ] **IPGeo-017**: hit_countにインデックスが設定されている

### 1.4 モデルメソッドとメタ
- [ ] **IPGeo-018**: __str__メソッドが正しい文字列を返す
- [ ] **IPGeo-019**: db_tableが"ip_geolocation_cache"
- [ ] **IPGeo-020**: orderingが["-created_at"]

---

## 2. AccessLog モデル (25ケース)

### 2.1 必須フィールド
- [ ] **AccessLog-001**: distribution_idが必須フィールド
- [ ] **AccessLog-002**: distribution_idにインデックスが設定されている
- [ ] **AccessLog-003**: log_datetimeが必須でインデックスあり
- [ ] **AccessLog-004**: c_ipがGenericIPAddressFieldでインデックスあり
- [ ] **AccessLog-005**: log_fileがForeignKeyで必須

### 2.2 リレーションシップ
- [ ] **AccessLog-006**: log_fileがProcessedLogFileへのForeignKey
- [ ] **AccessLog-007**: log_fileのon_deleteがCASCADE
- [ ] **AccessLog-008**: log_fileのrelated_nameが"logs"
- [ ] **AccessLog-009**: geolocationがIPGeolocationへのForeignKey
- [ ] **AccessLog-010**: geolocationのon_deleteがSET_NULL
- [ ] **AccessLog-011**: geolocationがnull許可

### 2.3 リクエスト情報フィールド
- [ ] **AccessLog-012**: cs_methodがnull許可でインデックスあり
- [ ] **AccessLog-013**: cs_uri_stemがnull許可でインデックスあり
- [ ] **AccessLog-014**: cs_uri_stemの最大長が2000文字
- [ ] **AccessLog-015**: cs_uri_queryがTextFieldでnull許可

### 2.4 レスポンス情報フィールド
- [ ] **AccessLog-016**: sc_statusがIntegerFieldでnull許可
- [ ] **AccessLog-017**: sc_statusにインデックスが設定されている
- [ ] **AccessLog-018**: sc_bytesがBigIntegerFieldでnull許可
- [ ] **AccessLog-019**: time_takenがFloatFieldでnull許可

### 2.5 複合インデックス
- [ ] **AccessLog-020**: (distribution_id, log_datetime)の複合インデックスあり
- [ ] **AccessLog-021**: (c_ip, log_datetime)の複合インデックスあり
- [ ] **AccessLog-022**: (log_file, log_datetime)の複合インデックスあり
- [ ] **AccessLog-023**: (distribution_id, cs_method, sc_status)の複合インデックスあり

### 2.6 モデルメソッドとメタ
- [ ] **AccessLog-024**: __str__メソッドが正しい文字列を返す
- [ ] **AccessLog-025**: db_tableが"access_logs"、orderingが["-log_datetime"]

---

## 3. WAFBlockedIPSnapshot モデル (15ケース)

### 3.1 基本フィールド
- [ ] **WAFSnapshot-001**: distribution_idが必須フィールド
- [ ] **WAFSnapshot-002**: distribution_idにインデックスが設定されている
- [ ] **WAFSnapshot-003**: snapshot_timeのデフォルト値がtimezone.now
- [ ] **WAFSnapshot-004**: snapshot_timeにインデックスが設定されている
- [ ] **WAFSnapshot-005**: total_ipsのデフォルト値が0

### 3.2 メタデータ
- [ ] **WAFSnapshot-006**: created_atが自動設定される（auto_now_add=True）

### 3.3 複合インデックス
- [ ] **WAFSnapshot-007**: (distribution_id, snapshot_time)の複合インデックスあり

### 3.4 モデルメソッドとメタ
- [ ] **WAFSnapshot-008**: __str__メソッドが正しい文字列を返す
- [ ] **WAFSnapshot-009**: db_tableが"waf_blocked_ip_snapshots"
- [ ] **WAFSnapshot-010**: orderingが["-snapshot_time"]

### 3.5 境界値テスト
- [ ] **WAFSnapshot-011**: total_ips=0の場合
- [ ] **WAFSnapshot-012**: total_ips=10000の場合（大量）
- [ ] **WAFSnapshot-013**: snapshot_timeが過去の日時
- [ ] **WAFSnapshot-014**: snapshot_timeが現在時刻
- [ ] **WAFSnapshot-015**: 同じdistribution_idで複数のスナップショット

---

## 4. WAFBlockedIP モデル (18ケース)

### 4.1 基本フィールド
- [ ] **WAFBlockedIP-001**: snapshotがForeignKeyで必須
- [ ] **WAFBlockedIP-002**: snapshotのon_deleteがCASCADE
- [ ] **WAFBlockedIP-003**: snapshotのrelated_nameが"blocked_ips"
- [ ] **WAFBlockedIP-004**: ip_addressが必須でインデックスあり
- [ ] **WAFBlockedIP-005**: cidrが必須フィールド
- [ ] **WAFBlockedIP-006**: ip_set_idが必須フィールド
- [ ] **WAFBlockedIP-007**: ip_set_nameが必須フィールド
- [ ] **WAFBlockedIP-008**: ip_set_arnがTextFieldで必須

### 4.2 リレーションシップ
- [ ] **WAFBlockedIP-009**: geolocationがIPGeolocationへのForeignKey
- [ ] **WAFBlockedIP-010**: geolocationのon_deleteがSET_NULL
- [ ] **WAFBlockedIP-011**: geolocationがnull許可

### 4.3 複合インデックス
- [ ] **WAFBlockedIP-012**: (snapshot, ip_address)の複合インデックスあり

### 4.4 モデルメソッドとメタ
- [ ] **WAFBlockedIP-013**: __str__メソッドが正しい文字列を返す（CIDR形式）
- [ ] **WAFBlockedIP-014**: db_tableが"waf_blocked_ips"
- [ ] **WAFBlockedIP-015**: orderingが["ip_address"]

### 4.5 データ整合性
- [ ] **WAFBlockedIP-016**: スナップショット削除時にカスケード削除される
- [ ] **WAFBlockedIP-017**: 同じスナップショット内で同じIPが重複しない
- [ ] **WAFBlockedIP-018**: geolocation削除時にnullになる

---

## 5. GeoLogCache モデル (22ケース)

### 5.1 基本フィールド
- [ ] **GeoCache-001**: distribution_idが必須でインデックスあり
- [ ] **GeoCache-002**: start_dateがDateFieldで必須、インデックスあり
- [ ] **GeoCache-003**: end_dateがDateFieldで必須、インデックスあり
- [ ] **GeoCache-004**: start_timeがTimeFieldでnull許可
- [ ] **GeoCache-005**: end_timeがTimeFieldでnull許可

### 5.2 実際のデータ範囲フィールド
- [ ] **GeoCache-006**: actual_start_datetimeがnull許可でインデックスあり
- [ ] **GeoCache-007**: actual_end_datetimeがnull許可でインデックスあり

### 5.3 集約データフィールド
- [ ] **GeoCache-008**: locations_dataがJSONField
- [ ] **GeoCache-009**: total_countのデフォルト値が0

### 5.4 メタデータフィールド
- [ ] **GeoCache-010**: created_atが自動設定される（auto_now_add=True）
- [ ] **GeoCache-011**: created_atにインデックスが設定されている
- [ ] **GeoCache-012**: expires_atがnull許可でインデックスあり

### 5.5 複合インデックス
- [ ] **GeoCache-013**: (distribution_id, start_date, end_date, expires_at)の複合インデックスあり
- [ ] **GeoCache-014**: (distribution_id, actual_start_datetime, actual_end_datetime)の複合インデックスあり

### 5.6 カスタムメソッド
- [ ] **GeoCache-015**: is_expired()メソッドが正しく動作（expires_atがnullの場合False）
- [ ] **GeoCache-016**: is_expired()メソッドが正しく動作（expires_at未来の場合False）
- [ ] **GeoCache-017**: is_expired()メソッドが正しく動作（expires_at過去の場合True）

### 5.7 モデルメソッドとメタ
- [ ] **GeoCache-018**: __str__メソッドが正しい文字列を返す
- [ ] **GeoCache-019**: db_tableが"geo_log_cache"
- [ ] **GeoCache-020**: orderingが["-created_at"]

### 5.8 JSONFieldテスト
- [ ] **GeoCache-021**: locations_dataに有効なJSON保存
- [ ] **GeoCache-022**: locations_dataから正しくデータ取得

---

## 6. ProcessedLogFile モデル (18ケース)

### 6.1 基本フィールド
- [ ] **ProcessedLog-001**: distribution_idが必須でインデックスあり
- [ ] **ProcessedLog-002**: log_file_keyが必須でunique制約
- [ ] **ProcessedLog-003**: log_file_keyにインデックスが設定されている
- [ ] **ProcessedLog-004**: log_file_keyの最大長が500文字
- [ ] **ProcessedLog-005**: file_sizeのデフォルト値が0
- [ ] **ProcessedLog-006**: file_sizeがBigIntegerField
- [ ] **ProcessedLog-007**: record_countのデフォルト値が0

### 6.2 時刻フィールド
- [ ] **ProcessedLog-008**: log_start_timeがnull許可
- [ ] **ProcessedLog-009**: log_end_timeがnull許可

### 6.3 メタデータ
- [ ] **ProcessedLog-010**: processed_atが自動設定される（auto_now_add=True）
- [ ] **ProcessedLog-011**: processed_atにインデックスが設定されている

### 6.4 複合インデックス
- [ ] **ProcessedLog-012**: (distribution_id, log_start_time, log_end_time)の複合インデックスあり

### 6.5 モデルメソッドとメタ
- [ ] **ProcessedLog-013**: __str__メソッドが正しい文字列を返す
- [ ] **ProcessedLog-014**: db_tableが"processed_log_files"
- [ ] **ProcessedLog-015**: orderingが["-processed_at"]

### 6.6 データ整合性
- [ ] **ProcessedLog-016**: 同じlog_file_keyを重複して保存できない（unique制約）
- [ ] **ProcessedLog-017**: file_sizeが負の値でないことを確認
- [ ] **ProcessedLog-018**: log_end_time >= log_start_timeの検証

---

## 7. モデル横断テスト (20ケース)

### 7.1 リレーションシップ
- [ ] **Model-Rel-001**: AccessLog削除時にIPGeolocationは削除されない（SET_NULL）
- [ ] **Model-Rel-002**: ProcessedLogFile削除時にAccessLogがカスケード削除
- [ ] **Model-Rel-003**: WAFBlockedIPSnapshot削除時にWAFBlockedIPがカスケード削除
- [ ] **Model-Rel-004**: IPGeolocation削除時にWAFBlockedIPはnullになる
- [ ] **Model-Rel-005**: 循環参照がない

### 7.2 インデックス効率
- [ ] **Model-Index-001**: IPGeolocationのip_addressインデックスが有効
- [ ] **Model-Index-002**: AccessLogの複合インデックスが有効
- [ ] **Model-Index-003**: クエリパフォーマンスが許容範囲内

### 7.3 データベース制約
- [ ] **Model-Constraint-001**: unique制約が正しく動作
- [ ] **Model-Constraint-002**: null制約が正しく動作
- [ ] **Model-Constraint-003**: ForeignKey制約が正しく動作
- [ ] **Model-Constraint-004**: データベースレベルの制約が正しく設定されている

### 7.4 マイグレーション
- [ ] **Model-Migration-001**: すべてのマイグレーションが適用可能
- [ ] **Model-Migration-002**: マイグレーションのロールバックが可能
- [ ] **Model-Migration-003**: マイグレーション間の依存関係が正しい
- [ ] **Model-Migration-004**: インデックス追加マイグレーションが正しく動作

### 7.5 クエリセット
- [ ] **Model-Query-001**: select_related/prefetch_relatedが正しく動作
- [ ] **Model-Query-002**: アノテーション/集約が正しく動作
- [ ] **Model-Query-003**: フィルタリングが正しく動作
- [ ] **Model-Query-004**: N+1問題が発生しない

---

## 合計テストケース数: 138ケース

## テスト実装優先度

1. **高（優先実装）**:
   - 各モデルの基本フィールドバリデーション
   - リレーションシップテスト
   - unique制約、null制約のテスト
   - __str__メソッドのテスト

2. **中（次期実装）**:
   - 複合インデックステスト
   - カスタムメソッドのテスト（is_expired等）
   - データ整合性テスト
   - マイグレーションテスト

3. **低（後回し可）**:
   - インデックス効率テスト
   - クエリセットパフォーマンステスト
   - 境界値テスト

## 自動化対象

- すべてのテストケースを自動化
- CIパイプラインで優先度「高」「中」を実行
- Nightlyビルドでインデックス効率テスト実行

## テストデータ

### IPGeolocation テストデータ
```python
{
    "ip_address": "192.0.2.1",
    "country": "Japan",
    "country_code": "JP",
    "city": "Tokyo",
    "latitude": 35.6895,
    "longitude": 139.6917,
    "whois_raw": "NetRange: 192.0.2.0 - 192.0.2.255",
    "whois_netname": "TEST-NET",
    "whois_org_name": "Test Organization",
    "hit_count": 10
}
```

### AccessLog テストデータ
```python
{
    "distribution_id": "E1234567890ABC",
    "log_datetime": "2025-11-15T12:00:00Z",
    "c_ip": "192.0.2.1",
    "cs_method": "GET",
    "cs_uri_stem": "/test/path",
    "sc_status": 200,
    "sc_bytes": 1234
}
```

### GeoLogCache テストデータ
```python
{
    "distribution_id": "E1234567890ABC",
    "start_date": "2025-11-01",
    "end_date": "2025-11-30",
    "locations_data": {"JP": {"count": 100, "ips": ["192.0.2.1"]}},
    "total_count": 100,
    "expires_at": None  # 永続的
}
```

## 依存サービス

- PostgreSQL/SQLite データベース
- Django ORM
- django.utils.timezone

## テスト実装方法

### Fixtureの使用
```python
@pytest.fixture
def ip_geo():
    return IPGeolocation.objects.create(
        ip_address="192.0.2.1",
        country="Japan"
    )
```

### トランザクション制御
- 各テスト後にデータベースをロールバック
- `pytest-django`の`django_db`マーカーを使用

### アサーション例
```python
def test_ip_geolocation_unique():
    IPGeolocation.objects.create(ip_address="192.0.2.1")
    with pytest.raises(IntegrityError):
        IPGeolocation.objects.create(ip_address="192.0.2.1")
```

## 備考

- すべてのモデルでデータベース制約を確認
- インデックスの効果はEXPLAINクエリで検証
- マイグレーションは本番環境を想定したテストも実施
- パフォーマンステストは大量データで実施（10万件以上）
