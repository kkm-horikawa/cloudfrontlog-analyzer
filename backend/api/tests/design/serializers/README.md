# テスト設計: Django REST Framework Serializers

## 対象Serializer一覧

### Distributions
1. DistributionSerializer

### Logs
2. LogSearchRequestSerializer
3. RawLogsListRequestSerializer
4. LogEntrySerializer
5. IPInfoSerializer (logs)
6. SuspiciousCheckSerializer

### Geo
7. GeoLogsRequestSerializer

### Security
8. CompanyInfoCheckRequestSerializer
9. FrequentIPCheckRequestSerializer
10. MultiDeviceCheckRequestSerializer
11. ResearchToolDetectionRequestSerializer
12. ResearchToolCheckRequestSerializer

### IP Info
13. IPInfoSerializer (ip_info)

## テストケース設計

---

## 1. DistributionSerializer (8ケース)

### 1.1 フィールドバリデーション
- [ ] **DistSer-001**: idフィールドが必須
- [ ] **DistSer-002**: domainフィールドが必須
- [ ] **DistSer-003**: aliasesフィールドがオプション（required=False）
- [ ] **DistSer-004**: aliasesが配列型

### 1.2 シリアライズ（出力）
- [ ] **DistSer-005**: 有効なデータが正しくシリアライズされる
- [ ] **DistSer-006**: aliasesが空配列の場合も正しく処理
- [ ] **DistSer-007**: aliasesが複数要素の場合も正しく処理

### 1.3 デシリアライズ（入力）
- [ ] **DistSer-008**: 有効なJSONデータが正しくデシリアライズされる

---

## 2. LogSearchRequestSerializer (15ケース)

### 2.1 必須フィールド
- [ ] **LogSearchReq-001**: distributionIdが必須
- [ ] **LogSearchReq-002**: targetUrlが必須
- [ ] **LogSearchReq-003**: dateTimeが必須
- [ ] **LogSearchReq-004**: timeWindowMinutesがオプション

### 2.2 デフォルト値
- [ ] **LogSearchReq-005**: timeWindowMinutesのデフォルト値が5

### 2.3 型検証
- [ ] **LogSearchReq-006**: distributionIdが文字列型
- [ ] **LogSearchReq-007**: targetUrlが文字列型
- [ ] **LogSearchReq-008**: dateTimeがDateTimeField
- [ ] **LogSearchReq-009**: timeWindowMinutesが整数型

### 2.4 バリデーション
- [ ] **LogSearchReq-010**: 必須フィールド欠如でエラー
- [ ] **LogSearchReq-011**: 不正な日時フォーマットでエラー
- [ ] **LogSearchReq-012**: 負のtimeWindowMinutesでエラー（min_valueがあれば）
- [ ] **LogSearchReq-013**: ISO8601形式の日時を正しくパース

### 2.5 デシリアライズ
- [ ] **LogSearchReq-014**: 有効なリクエストデータが正しくデシリアライズされる
- [ ] **LogSearchReq-015**: validated_dataに正しい型でデータが格納される

---

## 3. RawLogsListRequestSerializer (20ケース)

### 3.1 必須フィールド
- [ ] **RawLogsReq-001**: distributionIdが必須
- [ ] **RawLogsReq-002**: startDateが必須
- [ ] **RawLogsReq-003**: endDateが必須
- [ ] **RawLogsReq-004**: その他のフィールドがオプション

### 3.2 デフォルト値
- [ ] **RawLogsReq-005**: pageのデフォルト値が1
- [ ] **RawLogsReq-006**: perPageのデフォルト値が1000

### 3.3 制約検証
- [ ] **RawLogsReq-007**: pageのmin_valueが1
- [ ] **RawLogsReq-008**: perPageのmin_valueが1
- [ ] **RawLogsReq-009**: perPageのmax_valueが10000
- [ ] **RawLogsReq-010**: page=0でエラー
- [ ] **RawLogsReq-011**: perPage=0でエラー
- [ ] **RawLogsReq-012**: perPage=10001でエラー

### 3.4 allow_blank検証
- [ ] **RawLogsReq-013**: clientIpが空文字列許可（allow_blank=True）
- [ ] **RawLogsReq-014**: uriPathが空文字列許可
- [ ] **RawLogsReq-015**: referrerが空文字列許可
- [ ] **RawLogsReq-016**: queryStringが空文字列許可

### 3.5 ListField検証
- [ ] **RawLogsReq-017**: clientIpsが配列型
- [ ] **RawLogsReq-018**: clientIpsの各要素が文字列型
- [ ] **RawLogsReq-019**: clientIpsが空配列許可（allow_empty=True）

### 3.6 TimeField検証
- [ ] **RawLogsReq-020**: startTimeとendTimeがnull許可

---

## 4. LogEntrySerializer (18ケース)

### 4.1 必須フィールド
- [ ] **LogEntry-001**: dateが必須
- [ ] **LogEntry-002**: timeが必須
- [ ] **LogEntry-003**: clientIpが必須
- [ ] **LogEntry-004**: その他の基本フィールドが必須

### 4.2 オプショナルフィールド
- [ ] **LogEntry-005**: edgeRequestIdがオプション（required=False）
- [ ] **LogEntry-006**: hostHeaderがオプション
- [ ] **LogEntry-007**: protocolがオプション
- [ ] **LogEntry-008**: ipInfoがオプション（allow_null=True）
- [ ] **LogEntry-009**: suspiciousCheckがオプション

### 4.3 型検証
- [ ] **LogEntry-010**: bytesがIntegerField
- [ ] **LogEntry-011**: statusCodeがIntegerField
- [ ] **LogEntry-012**: timeTakenがFloatField

### 4.4 ネストされたSerializer
- [ ] **LogEntry-013**: ipInfoがIPInfoSerializerのインスタンス
- [ ] **LogEntry-014**: suspiciousCheckがSuspiciousCheckSerializerのインスタンス

### 4.5 シリアライズ
- [ ] **LogEntry-015**: 完全なログエントリが正しくシリアライズされる
- [ ] **LogEntry-016**: オプショナルフィールドが欠如していても正しく処理
- [ ] **LogEntry-017**: ipInfoがnullの場合も正しく処理
- [ ] **LogEntry-018**: suspiciousCheckがnullの場合も正しく処理

---

## 5. IPInfoSerializer (logs/ip_info共通) (15ケース)

### 5.1 必須フィールド
- [ ] **IPInfo-001**: ipが必須

### 5.2 オプショナルフィールド
- [ ] **IPInfo-002**: すべての地理情報フィールドがオプション（required=False）
- [ ] **IPInfo-003**: すべての地理情報フィールドがnull許可（allow_null=True）

### 5.3 型検証
- [ ] **IPInfo-004**: latがFloatField
- [ ] **IPInfo-005**: lonがFloatField
- [ ] **IPInfo-006**: offsetがIntegerField
- [ ] **IPInfo-007**: mobileがBooleanField
- [ ] **IPInfo-008**: proxyがBooleanField
- [ ] **IPInfo-009**: hostingがBooleanField

### 5.4 シリアライズ
- [ ] **IPInfo-010**: 完全なIP情報が正しくシリアライズされる
- [ ] **IPInfo-011**: 部分的なIP情報でも正しくシリアライズされる
- [ ] **IPInfo-012**: nullフィールドが正しく処理される

### 5.5 デシリアライズ
- [ ] **IPInfo-013**: 有効なJSONデータが正しくデシリアライズされる
- [ ] **IPInfo-014**: 不正な緯度経度でエラー（範囲外の値）
- [ ] **IPInfo-015**: Booleanフィールドに文字列を渡すとエラー

---

## 6. SuspiciousCheckSerializer (10ケース)

### 6.1 必須フィールド
- [ ] **SuspCheck-001**: isSuspiciousが必須
- [ ] **SuspCheck-002**: isBlockedが必須
- [ ] **SuspCheck-003**: isAllowedBotが必須
- [ ] **SuspCheck-004**: severityが必須
- [ ] **SuspCheck-005**: matchedPatternsが必須

### 6.2 型検証
- [ ] **SuspCheck-006**: isSuspiciousがBooleanField
- [ ] **SuspCheck-007**: matchedPatternsがListField

### 6.3 オプショナルフィールド
- [ ] **SuspCheck-008**: detailsがオプション（required=False）
- [ ] **SuspCheck-009**: detailsがDictField

### 6.4 シリアライズ
- [ ] **SuspCheck-010**: 完全な不審チェック結果が正しくシリアライズされる

---

## 7. GeoLogsRequestSerializer (12ケース)

### 7.1 必須フィールド
- [ ] **GeoLogsReq-001**: distributionIdが必須
- [ ] **GeoLogsReq-002**: startDateが必須
- [ ] **GeoLogsReq-003**: endDateが必須

### 7.2 オプショナルフィールド
- [ ] **GeoLogsReq-004**: startTimeがオプション（required=False）
- [ ] **GeoLogsReq-005**: endTimeがオプション
- [ ] **GeoLogsReq-006**: startTimeがnull許可（allow_null=True）
- [ ] **GeoLogsReq-007**: endTimeがnull許可

### 7.3 型検証
- [ ] **GeoLogsReq-008**: startDateがDateField
- [ ] **GeoLogsReq-009**: endDateがDateField
- [ ] **GeoLogsReq-010**: startTimeがTimeField
- [ ] **GeoLogsReq-011**: endTimeがTimeField

### 7.4 デシリアライズ
- [ ] **GeoLogsReq-012**: 有効なリクエストデータが正しくデシリアライズされる

---

## 8. CompanyInfoCheckRequestSerializer (10ケース)

### 8.1 必須フィールド
- [ ] **CompanyInfoReq-001**: distributionIdが必須
- [ ] **CompanyInfoReq-002**: targetUrlが必須

### 8.2 デフォルト値
- [ ] **CompanyInfoReq-003**: companyInfoUrlのデフォルト値が"/nattoku/about/"

### 8.3 型検証
- [ ] **CompanyInfoReq-004**: すべてのフィールドが文字列型

### 8.4 バリデーション
- [ ] **CompanyInfoReq-005**: 必須フィールド欠如でエラー
- [ ] **CompanyInfoReq-006**: 空文字列でエラー（allow_blankがない場合）

### 8.5 デシリアライズ
- [ ] **CompanyInfoReq-007**: 有効なリクエストデータが正しくデシリアライズされる
- [ ] **CompanyInfoReq-008**: companyInfoUrl省略時にデフォルト値が設定される
- [ ] **CompanyInfoReq-009**: すべてのフィールド指定時に正しく処理される
- [ ] **CompanyInfoReq-010**: validated_dataに正しい型でデータが格納される

---

## 9. FrequentIPCheckRequestSerializer (12ケース)

### 9.1 必須フィールド
- [ ] **FreqIPReq-001**: distributionIdが必須
- [ ] **FreqIPReq-002**: clientIpが必須

### 9.2 デフォルト値
- [ ] **FreqIPReq-003**: daysのデフォルト値が3

### 9.3 制約検証
- [ ] **FreqIPReq-004**: daysのmin_valueが1
- [ ] **FreqIPReq-005**: daysのmax_valueが30
- [ ] **FreqIPReq-006**: days=0でエラー
- [ ] **FreqIPReq-007**: days=31でエラー
- [ ] **FreqIPReq-008**: days=1（境界値）で正常
- [ ] **FreqIPReq-009**: days=30（境界値）で正常

### 9.4 型検証
- [ ] **FreqIPReq-010**: daysがIntegerField

### 9.5 デシリアライズ
- [ ] **FreqIPReq-011**: 有効なリクエストデータが正しくデシリアライズされる
- [ ] **FreqIPReq-012**: days省略時にデフォルト値が設定される

---

## 10. MultiDeviceCheckRequestSerializer (12ケース)

### 10.1 必須フィールド
- [ ] **MultiDevReq-001**: distributionIdが必須
- [ ] **MultiDevReq-002**: clientIpが必須

### 10.2 デフォルト値
- [ ] **MultiDevReq-003**: daysのデフォルト値が3

### 10.3 制約検証
- [ ] **MultiDevReq-004**: daysのmin_valueが1
- [ ] **MultiDevReq-005**: daysのmax_valueが30
- [ ] **MultiDevReq-006**: days=0でエラー
- [ ] **MultiDevReq-007**: days=31でエラー
- [ ] **MultiDevReq-008**: days=1（境界値）で正常
- [ ] **MultiDevReq-009**: days=30（境界値）で正常

### 10.4 型検証
- [ ] **MultiDevReq-010**: daysがIntegerField

### 10.5 デシリアライズ
- [ ] **MultiDevReq-011**: 有効なリクエストデータが正しくデシリアライズされる
- [ ] **MultiDevReq-012**: days省略時にデフォルト値が設定される

---

## 11. ResearchToolDetectionRequestSerializer (12ケース)

### 11.1 必須フィールド
- [ ] **ResToolDetReq-001**: distributionIdが必須
- [ ] **ResToolDetReq-002**: startDateが必須
- [ ] **ResToolDetReq-003**: endDateが必須

### 11.2 オプショナルフィールド
- [ ] **ResToolDetReq-004**: startTimeがオプション
- [ ] **ResToolDetReq-005**: endTimeがオプション
- [ ] **ResToolDetReq-006**: startTimeがnull許可
- [ ] **ResToolDetReq-007**: endTimeがnull許可

### 11.3 型検証
- [ ] **ResToolDetReq-008**: startDateがDateField
- [ ] **ResToolDetReq-009**: endDateがDateField
- [ ] **ResToolDetReq-010**: startTimeがTimeField
- [ ] **ResToolDetReq-011**: endTimeがTimeField

### 11.4 デシリアライズ
- [ ] **ResToolDetReq-012**: 有効なリクエストデータが正しくデシリアライズされる

---

## 12. ResearchToolCheckRequestSerializer (8ケース)

### 12.1 必須フィールド
- [ ] **ResToolCheckReq-001**: userAgentが必須

### 12.2 オプショナルフィールド
- [ ] **ResToolCheckReq-002**: referrerがオプション
- [ ] **ResToolCheckReq-003**: referrerが空文字列許可（allow_blank=True）

### 12.3 型検証
- [ ] **ResToolCheckReq-004**: すべてのフィールドが文字列型

### 12.4 バリデーション
- [ ] **ResToolCheckReq-005**: userAgent欠如でエラー
- [ ] **ResToolCheckReq-006**: userAgentが空文字列でエラー（allow_blankがない場合）

### 12.5 デシリアライズ
- [ ] **ResToolCheckReq-007**: 有効なリクエストデータが正しくデシリアライズされる
- [ ] **ResToolCheckReq-008**: referrer省略時に正しく処理される

---

## 13. 横断的テスト (20ケース)

### 13.1 エラーメッセージ
- [ ] **Ser-Cross-001**: 必須フィールド欠如時に適切なエラーメッセージ
- [ ] **Ser-Cross-002**: 型不一致時に適切なエラーメッセージ
- [ ] **Ser-Cross-003**: 範囲外の値で適切なエラーメッセージ
- [ ] **Ser-Cross-004**: エラーメッセージが日本語または英語

### 13.2 シリアライズ/デシリアライズ往復
- [ ] **Ser-Cross-005**: すべてのSerializerでシリアライズ→デシリアライズの往復テスト
- [ ] **Ser-Cross-006**: データが損失なく往復される

### 13.3 境界値テスト
- [ ] **Ser-Cross-007**: 最小値/最大値の境界値テスト
- [ ] **Ser-Cross-008**: 空文字列、null、未定義の扱い

### 13.4 特殊文字テスト
- [ ] **Ser-Cross-009**: URLエンコード文字列の処理
- [ ] **Ser-Cross-010**: 日本語文字列の処理
- [ ] **Ser-Cross-011**: 特殊文字（&, =, ?, /等）の処理
- [ ] **Ser-Cross-012**: Unicodeエスケープシーケンスの処理

### 13.5 パフォーマンス
- [ ] **Ser-Cross-013**: 大量データのシリアライズ/デシリアライズパフォーマンス
- [ ] **Ser-Cross-014**: ネストされたSerializerのパフォーマンス

### 13.6 セキュリティ
- [ ] **Ser-Cross-015**: SQLインジェクション文字列の処理
- [ ] **Ser-Cross-016**: XSS文字列の処理
- [ ] **Ser-Cross-017**: パストラバーサル文字列の処理

### 13.7 データ整合性
- [ ] **Ser-Cross-018**: validated_dataの型が正しい
- [ ] **Ser-Cross-019**: デフォルト値が正しく設定される
- [ ] **Ser-Cross-020**: required=Falseのフィールドが省略可能

---

## 合計テストケース数: 172ケース

## テスト実装優先度

1. **高（優先実装）**:
   - すべてのSerializerの必須フィールドテスト
   - デフォルト値テスト
   - 型検証テスト
   - デシリアライズテスト

2. **中（次期実装）**:
   - 制約検証テスト（min_value, max_value）
   - allow_blank、allow_nullテスト
   - ネストされたSerializerテスト
   - 横断的テスト（エラーメッセージ、境界値）

3. **低（後回し可）**:
   - シリアライズテスト（出力のみの確認）
   - パフォーマンステスト
   - セキュリティテスト

## 自動化対象

- すべてのテストケースを自動化
- CIパイプラインで優先度「高」「中」を実行
- Nightlyビルドでパフォーマンステスト実行

## テストデータ

### LogSearchRequestSerializer テストデータ
```python
# 有効なデータ
valid_data = {
    "distributionId": "E1234567890ABC",
    "targetUrl": "/test/path",
    "dateTime": "2025-11-15T12:00:00+09:00",
    "timeWindowMinutes": 5
}

# 不正なデータ
invalid_data = {
    "distributionId": "",  # 空文字列
    "targetUrl": "/test/path",
    "dateTime": "invalid-datetime",  # 不正な日時
    "timeWindowMinutes": -1  # 負の値
}
```

### IPInfoSerializer テストデータ
```python
# 完全なデータ
full_data = {
    "ip": "192.0.2.1",
    "country": "Japan",
    "countryCode": "JP",
    "city": "Tokyo",
    "lat": 35.6895,
    "lon": 139.6917,
    "mobile": False,
    "proxy": False,
    "hosting": False
}

# 部分的なデータ
partial_data = {
    "ip": "192.0.2.1",
    "country": "Japan",
    "city": None  # nullを含む
}
```

## テスト実装方法

### 基本的なバリデーションテスト
```python
def test_required_fields():
    serializer = LogSearchRequestSerializer(data={})
    assert not serializer.is_valid()
    assert 'distributionId' in serializer.errors
    assert 'targetUrl' in serializer.errors
    assert 'dateTime' in serializer.errors
```

### デフォルト値テスト
```python
def test_default_values():
    data = {
        "distributionId": "E1234567890ABC",
        "targetUrl": "/test",
        "dateTime": "2025-11-15T12:00:00Z"
        # timeWindowMinutes省略
    }
    serializer = LogSearchRequestSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data['timeWindowMinutes'] == 5
```

### 制約検証テスト
```python
def test_min_max_values():
    data = {
        "distributionId": "E1234567890ABC",
        "clientIp": "192.0.2.1",
        "days": 0  # min_value=1に違反
    }
    serializer = FrequentIPCheckRequestSerializer(data=data)
    assert not serializer.is_valid()
    assert 'days' in serializer.errors
```

### シリアライズテスト
```python
def test_serialization():
    data = {"ip": "192.0.2.1", "country": "Japan"}
    serializer = IPInfoSerializer(data)
    serialized = serializer.data
    assert serialized['ip'] == "192.0.2.1"
    assert serialized['country'] == "Japan"
```

## 依存ライブラリ

- Django REST Framework
- pytest
- pytest-django

## 備考

- すべてのSerializerで入力バリデーションを徹底的にテスト
- エラーメッセージが適切でユーザーフレンドリーか確認
- セキュリティ関連のバリデーション（インジェクション対策等）も考慮
- パフォーマンステストは大量データ（1000件以上）で実施
