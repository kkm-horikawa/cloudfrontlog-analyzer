# テスト設計: WHOIS Batch API

## エンドポイント情報

### エンドポイント1: WHOIS Batch Fetch
- **URL**: `/api/whois/batch/fetch/`
- **HTTPメソッド**: `POST`
- **説明**: データベース内のWHOIS情報未取得IPに対してバックグラウンドでWHOIS情報を取得

### エンドポイント2: WHOIS Batch Status
- **URL**: `/api/whois/batch/status/`
- **HTTPメソッド**: `GET`
- **説明**: WHOIS情報取得の進捗状況を確認

## パラメータ仕様

### `/api/whois/batch/fetch/` (POST)

#### リクエストボディ
パラメータなし（空のPOSTリクエスト）

#### レスポンス
```json
{
  "message": "WHOIS batch fetch started for {count} IPs",
  "pending_count": 0,
  "status": "running" | "completed"
}
```

### `/api/whois/batch/status/` (GET)

#### クエリパラメータ
なし

#### レスポンス
```json
{
  "total_ips": 0,
  "with_whois": 0,
  "without_whois": 0,
  "percentage_complete": 0.0
}
```

## テストケース設計

### 1. WHOIS Batch Fetch API - 正常系テスト (20ケース)

#### 1.1 基本動作
- [ ] **WHOIS-FETCH-001**: WHOIS未取得IPが存在する場合、バックグラウンドタスクが起動
- [ ] **WHOIS-FETCH-002**: pending_countが正しく返される
- [ ] **WHOIS-FETCH-003**: statusが"running"で返される
- [ ] **WHOIS-FETCH-004**: メッセージに取得対象IP数が含まれる
- [ ] **WHOIS-FETCH-005**: HTTPステータスコードが200 OK

#### 1.2 すでに完了している場合
- [ ] **WHOIS-FETCH-006**: WHOIS未取得IPが0件の場合、タスクを起動しない
- [ ] **WHOIS-FETCH-007**: pending_countが0で返される
- [ ] **WHOIS-FETCH-008**: statusが"completed"で返される
- [ ] **WHOIS-FETCH-009**: メッセージが"All IPs already have WHOIS info"

#### 1.3 レスポンス構造検証
- [ ] **WHOIS-FETCH-010**: レスポンスがJSON形式
- [ ] **WHOIS-FETCH-011**: レスポンスにmessageフィールドが存在
- [ ] **WHOIS-FETCH-012**: レスポンスにpending_countフィールドが存在
- [ ] **WHOIS-FETCH-013**: レスポンスにstatusフィールドが存在
- [ ] **WHOIS-FETCH-014**: pending_countが整数型
- [ ] **WHOIS-FETCH-015**: statusが文字列型

#### 1.4 バックグラウンドタスク
- [ ] **WHOIS-FETCH-016**: バックグラウンドスレッドがdaemon=Trueで起動
- [ ] **WHOIS-FETCH-017**: タスク起動後、即座にレスポンスが返る（非同期）
- [ ] **WHOIS-FETCH-018**: タスク実行中に再度リクエストしても新しいタスクが起動
- [ ] **WHOIS-FETCH-019**: バックグラウンドタスクでエラーが発生してもメインスレッドに影響なし
- [ ] **WHOIS-FETCH-020**: バックグラウンドタスクの実行状況をログで確認可能

### 2. WHOIS Batch Fetch API - 異常系テスト (15ケース)

#### 2.1 HTTPメソッド不正
- [ ] **WHOIS-FETCH-ERR-001**: GETメソッド → 405 Method Not Allowed
- [ ] **WHOIS-FETCH-ERR-002**: PUTメソッド → 405 Method Not Allowed
- [ ] **WHOIS-FETCH-ERR-003**: DELETEメソッド → 405 Method Not Allowed
- [ ] **WHOIS-FETCH-ERR-004**: PATCHメソッド → 405 Method Not Allowed

#### 2.2 データベースエラー
- [ ] **WHOIS-FETCH-ERR-005**: データベース接続エラー → 500エラー
- [ ] **WHOIS-FETCH-ERR-006**: IPGeolocationテーブルが存在しない → 500エラー
- [ ] **WHOIS-FETCH-ERR-007**: データベースクエリタイムアウト → 500エラー

#### 2.3 バックグラウンドタスクエラー
- [ ] **WHOIS-FETCH-ERR-008**: fetch_missing_whois_batch関数が存在しない → エラーログ出力
- [ ] **WHOIS-FETCH-ERR-009**: バックグラウンドタスク内で例外発生 → エラーログ出力（メインスレッドは正常）
- [ ] **WHOIS-FETCH-ERR-010**: スレッド起動失敗 → 500エラー

#### 2.4 その他
- [ ] **WHOIS-FETCH-ERR-011**: リクエストボディに不正なJSON → 無視される
- [ ] **WHOIS-FETCH-ERR-012**: 不正なクエリパラメータ → 無視される
- [ ] **WHOIS-FETCH-ERR-013**: 巨大なリクエストボディ → 無視される
- [ ] **WHOIS-FETCH-ERR-014**: Content-Typeが不正 → 無視される
- [ ] **WHOIS-FETCH-ERR-015**: 内部エラー時に適切なエラーメッセージ

### 3. WHOIS Batch Status API - 正常系テスト (15ケース)

#### 3.1 基本動作
- [ ] **WHOIS-STATUS-001**: 全IP数が正しく返される
- [ ] **WHOIS-STATUS-002**: WHOIS取得済みIP数が正しく返される
- [ ] **WHOIS-STATUS-003**: WHOIS未取得IP数が正しく返される
- [ ] **WHOIS-STATUS-004**: 完了率（percentage_complete）が正しく計算される
- [ ] **WHOIS-STATUS-005**: HTTPステータスコードが200 OK

#### 3.2 レスポンス構造検証
- [ ] **WHOIS-STATUS-006**: レスポンスがJSON形式
- [ ] **WHOIS-STATUS-007**: レスポンスにtotal_ipsフィールドが存在
- [ ] **WHOIS-STATUS-008**: レスポンスにwith_whoisフィールドが存在
- [ ] **WHOIS-STATUS-009**: レスポンスにwithout_whoisフィールドが存在
- [ ] **WHOIS-STATUS-010**: レスポンスにpercentage_completeフィールドが存在
- [ ] **WHOIS-STATUS-011**: すべてのフィールドが数値型

#### 3.3 計算の正確性
- [ ] **WHOIS-STATUS-012**: total_ips = with_whois + without_whois
- [ ] **WHOIS-STATUS-013**: percentage_completeが0-100の範囲内
- [ ] **WHOIS-STATUS-014**: percentage_completeが小数点2桁で四捨五入
- [ ] **WHOIS-STATUS-015**: IP数が0の場合、percentage_complete=0

### 4. WHOIS Batch Status API - 異常系テスト (10ケース)

#### 4.1 HTTPメソッド不正
- [ ] **WHOIS-STATUS-ERR-001**: POSTメソッド → 405 Method Not Allowed
- [ ] **WHOIS-STATUS-ERR-002**: PUTメソッド → 405 Method Not Allowed
- [ ] **WHOIS-STATUS-ERR-003**: DELETEメソッド → 405 Method Not Allowed
- [ ] **WHOIS-STATUS-ERR-004**: PATCHメソッド → 405 Method Not Allowed

#### 4.2 データベースエラー
- [ ] **WHOIS-STATUS-ERR-005**: データベース接続エラー → 500エラー
- [ ] **WHOIS-STATUS-ERR-006**: IPGeolocationテーブルが存在しない → 500エラー
- [ ] **WHOIS-STATUS-ERR-007**: データベースクエリタイムアウト → 500エラー

#### 4.3 その他
- [ ] **WHOIS-STATUS-ERR-008**: 不正なクエリパラメータ → 無視される
- [ ] **WHOIS-STATUS-ERR-009**: 内部エラー時に適切なエラーメッセージ
- [ ] **WHOIS-STATUS-ERR-010**: エラーメッセージに機密情報が含まれない

### 5. 境界値テスト (15ケース)

#### 5.1 IP数の境界
- [ ] **WHOIS-EDGE-001**: total_ips=0の場合の動作
- [ ] **WHOIS-EDGE-002**: total_ips=1の場合の動作
- [ ] **WHOIS-EDGE-003**: total_ips=10000の場合の動作（大量）
- [ ] **WHOIS-EDGE-004**: without_whois=0の場合（全IP取得済み）
- [ ] **WHOIS-EDGE-005**: with_whois=0の場合（全IP未取得）
- [ ] **WHOIS-EDGE-006**: with_whois=total_ipsの場合（100%完了）

#### 5.2 完了率の境界
- [ ] **WHOIS-EDGE-007**: percentage_complete=0.00の場合
- [ ] **WHOIS-EDGE-008**: percentage_complete=100.00の場合
- [ ] **WHOIS-EDGE-009**: percentage_complete=50.00の場合
- [ ] **WHOIS-EDGE-010**: percentage_complete=33.33の場合（切り捨て確認）
- [ ] **WHOIS-EDGE-011**: percentage_complete=66.66の場合（切り上げ確認）

#### 5.3 データ状態の境界
- [ ] **WHOIS-EDGE-012**: whois_raw=nullのIPが対象
- [ ] **WHOIS-EDGE-013**: whois_raw=""（空文字列）のIPが対象
- [ ] **WHOIS-EDGE-014**: whois_raw=" "（スペースのみ）のIPは対象外
- [ ] **WHOIS-EDGE-015**: 部分的に取得済みのIPの扱い

### 6. 統合テスト (20ケース)

#### 6.1 Fetch + Status連携
- [ ] **WHOIS-INT-001**: Fetchリクエスト後、Statusで進捗確認
- [ ] **WHOIS-INT-002**: Fetchリクエスト前後でwithout_whoisが変化
- [ ] **WHOIS-INT-003**: バックグラウンドタスク完了後、percentage_complete=100
- [ ] **WHOIS-INT-004**: 複数回Fetchリクエストしても重複取得しない
- [ ] **WHOIS-INT-005**: Fetchリクエスト中にStatusリクエスト可能

#### 6.2 データベース統合
- [ ] **WHOIS-INT-006**: IPGeolocationテーブルが正しく更新される
- [ ] **WHOIS-INT-007**: whois_rawフィールドが正しく設定される
- [ ] **WHOIS-INT-008**: whois_netnameフィールドが正しく設定される
- [ ] **WHOIS-INT-009**: whois_org_nameフィールドが正しく設定される
- [ ] **WHOIS-INT-010**: whois_countryフィールドが正しく設定される
- [ ] **WHOIS-INT-011**: updated_atフィールドが更新される

#### 6.3 外部API統合
- [ ] **WHOIS-INT-012**: fetch_missing_whois_batch関数が正しく呼び出される
- [ ] **WHOIS-INT-013**: 外部WHOIS APIが正しく呼び出される
- [ ] **WHOIS-INT-014**: レート制限を遵守する
- [ ] **WHOIS-INT-015**: API障害時にリトライする
- [ ] **WHOIS-INT-016**: タイムアウト時に適切に処理される

#### 6.4 並行処理統合
- [ ] **WHOIS-INT-017**: 複数の同時Fetchリクエストが正しく処理される
- [ ] **WHOIS-INT-018**: バックグラウンドタスク実行中にStatusリクエスト可能
- [ ] **WHOIS-INT-019**: スレッドセーフな実装
- [ ] **WHOIS-INT-020**: データベース接続のリークなし

### 7. パフォーマンステスト (10ケース)

- [ ] **WHOIS-PERF-001**: Fetchリクエストのレスポンスタイム < 200ms（タスク起動のみ）
- [ ] **WHOIS-PERF-002**: Statusリクエストのレスポンスタイム < 100ms
- [ ] **WHOIS-PERF-003**: 10件のIP取得完了時間 < 30秒
- [ ] **WHOIS-PERF-004**: 100件のIP取得完了時間 < 300秒
- [ ] **WHOIS-PERF-005**: 1000件のIP取得完了時間測定
- [ ] **WHOIS-PERF-006**: 同時10 Statusリクエストの並行処理
- [ ] **WHOIS-PERF-007**: 60秒間に100 Statusリクエスト（スループット）
- [ ] **WHOIS-PERF-008**: バックグラウンドタスクのメモリ使用量
- [ ] **WHOIS-PERF-009**: データベースクエリのパフォーマンス
- [ ] **WHOIS-PERF-010**: 長時間稼働時のメモリリークなし

### 8. セキュリティテスト (8ケース)

- [ ] **WHOIS-SEC-001**: CORS設定が正しい
- [ ] **WHOIS-SEC-002**: 認証なし未認証ユーザーは拒否される（認証実装時）
- [ ] **WHOIS-SEC-003**: HTTPSのみ許可（本番環境）
- [ ] **WHOIS-SEC-004**: レスポンスヘッダーにセキュリティヘッダー設定
- [ ] **WHOIS-SEC-005**: エラーメッセージに機密情報が含まれない
- [ ] **WHOIS-SEC-006**: Rate Limiting実装（DDoS対策）
- [ ] **WHOIS-SEC-007**: 大量リクエストでのサービス拒否攻撃対策
- [ ] **WHOIS-SEC-008**: バックグラウンドタスクの権限が適切

### 9. エッジケーステスト (12ケース)

- [ ] **WHOIS-EDGE-016**: IP数が非常に多い場合（10万件）
- [ ] **WHOIS-EDGE-017**: バックグラウンドタスク実行中にサーバー再起動
- [ ] **WHOIS-EDGE-018**: 同じIPが複数回データベースに存在する場合
- [ ] **WHOIS-EDGE-019**: 不正なIPアドレス形式のデータが存在する場合
- [ ] **WHOIS-EDGE-020**: 外部API障害が連続する場合
- [ ] **WHOIS-EDGE-021**: 外部APIがタイムアウトする場合
- [ ] **WHOIS-EDGE-022**: データベースロックが発生する場合
- [ ] **WHOIS-EDGE-023**: メモリ不足の場合
- [ ] **WHOIS-EDGE-024**: ディスク容量不足の場合
- [ ] **WHOIS-EDGE-025**: 外部APIのレスポンスが不正な形式
- [ ] **WHOIS-EDGE-026**: 外部APIのレスポンスが空
- [ ] **WHOIS-EDGE-027**: ネットワーク接続が不安定な場合

### 10. データ整合性テスト (10ケース)

- [ ] **WHOIS-DATA-001**: Statusの数値が常に整合性がある
- [ ] **WHOIS-DATA-002**: percentage_completeの計算が常に正確
- [ ] **WHOIS-DATA-003**: 取得済みIPが再度対象にならない
- [ ] **WHOIS-DATA-004**: バックグラウンドタスク完了後、データが正しく保存される
- [ ] **WHOIS-DATA-005**: whois_rawフィールドの内容が有効
- [ ] **WHOIS-DATA-006**: 取得日時（updated_at）が正しく記録される
- [ ] **WHOIS-DATA-007**: 並行実行時のデータ競合なし
- [ ] **WHOIS-DATA-008**: トランザクション処理が正しく行われる
- [ ] **WHOIS-DATA-009**: ロールバック処理が正しく行われる
- [ ] **WHOIS-DATA-010**: データベース制約違反が適切に処理される

## 合計テストケース数: 125ケース

## テスト実装優先度

1. **高（優先実装）**:
   - Fetch正常系1.1-1.3（基本動作、レスポンス構造）
   - Status正常系3.1-3.3（基本動作、計算の正確性）
   - 統合テスト6.1-6.2（Fetch+Status連携、データベース統合）
   - データ整合性テスト

2. **中（次期実装）**:
   - Fetch正常系1.4（バックグラウンドタスク）
   - Fetch異常系2.1-2.3
   - Status異常系4.1-4.2
   - 境界値テスト5.1-5.3
   - 統合テスト6.3-6.4（外部API、並行処理）

3. **低（後回し可）**:
   - Fetch異常系2.4（その他）
   - Status異常系4.3（その他）
   - パフォーマンステスト（Nightlyビルド用）
   - セキュリティテスト（セキュリティ監査時）
   - エッジケーステスト

## 自動化対象

- すべてのテストケースを自動化
- CIパイプラインで優先度「高」「中」を実行
- Nightlyビルドでパフォーマンステスト実行
- エッジケーステストは手動テストと併用

## テストデータ

### モックIPGeolocationデータ
```python
# WHOIS未取得IPのサンプル
IPGeolocation.objects.create(
    ip_address="192.0.2.1",
    country="Japan",
    whois_raw=None  # 未取得
)

# WHOIS取得済みIPのサンプル
IPGeolocation.objects.create(
    ip_address="192.0.2.2",
    country="Japan",
    whois_raw="NetRange: 192.0.2.0 - 192.0.2.255...",
    whois_netname="TEST-NET",
    whois_org_name="Test Organization"
)
```

### Fetch APIレスポンス例（未取得IPあり）
```json
{
  "message": "WHOIS batch fetch started for 10 IPs",
  "pending_count": 10,
  "status": "running"
}
```

### Fetch APIレスポンス例（全取得済み）
```json
{
  "message": "All IPs already have WHOIS info",
  "pending_count": 0,
  "status": "completed"
}
```

### Status APIレスポンス例
```json
{
  "total_ips": 100,
  "with_whois": 75,
  "without_whois": 25,
  "percentage_complete": 75.00
}
```

## 依存サービス

- PostgreSQL/SQLite データベース
- IPGeolocationモデル
- WHOIS API（ipwhois.app または類似サービス）
- Pythonスレッド（threading.Thread）
- fetch_missing_whois_batch関数（ip_info.py）

## 特記事項

### バックグラウンドタスクのテスト方法
- モックを使用して`fetch_missing_whois_batch`の呼び出しを確認
- スレッドの起動をモックして制御
- 実際のバックグラウンド処理は統合テストで実施

### 外部API呼び出しのテスト方法
- 単体テストではモックを使用
- 統合テストでは実際のAPI呼び出し（制限あり）
- レート制限を考慮してテストを設計

### 並行処理のテスト方法
- pytestのfixtureでデータベースをリセット
- 複数のクライアントシミュレーション
- スレッドセーフティの確認

## 備考

- バックグラウンドタスクは非同期のため、完了を待つテストは時間がかかる
- 外部API（WHOIS）の呼び出し制限に注意（多くのサービスは1000req/day）
- 本番環境ではタスクキューシステム（Celery等）への移行を検討
- エラーハンドリングとログ出力を重視
