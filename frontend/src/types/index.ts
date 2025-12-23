/**
 * CloudFront Analyzer - 型定義
 *
 * このファイルには、CloudFront Analyzerアプリケーションで使用される
 * すべてのTypeScript型定義とインターフェースが含まれています。
 *
 * @packageDocumentation
 */

/**
 * WHOIS情報を表すインターフェース
 *
 * IPアドレスのWHOIS検索結果から取得される情報を格納します。
 * ネットワーク情報や組織情報など、IPアドレスの登録情報を含みます。
 */
export interface WhoisInfo {
  /** WHOIS生データ（未加工のWHOIS応答全文） */
  raw: string;
  /** ネットワーク名 */
  netname?: string | null;
  /** 組織名 */
  org_name?: string | null;
  /** 国コード（ISO 3166-1 alpha-2形式） */
  country?: string | null;
  /** ネットワークアドレス範囲（CIDR表記） */
  net_range?: string | null;
}

/**
 * IP情報を表すインターフェース
 *
 * IP Geolocation APIから取得されるIPアドレスの詳細情報を格納します。
 * 地理情報、ISP情報、プロキシ検出結果などが含まれます。
 */
export interface IPInfo {
  /** IPアドレス（IPv4またはIPv6形式） */
  ip: string;
  /** 大陸名 */
  continent?: string;
  /** 大陸コード */
  continentCode?: string;
  /** 国名 */
  country?: string;
  /** 国コード（ISO 3166-1 alpha-2形式） */
  countryCode?: string;
  /** 地域/州 */
  region?: string;
  /** 都市名 */
  city?: string;
  /** 地区/区 */
  district?: string;
  /** 郵便番号 */
  zip?: string;
  /** 緯度 */
  lat?: number;
  /** 経度 */
  lon?: number;
  /** タイムゾーン（IANA形式） */
  timezone?: string;
  /** UTCからのオフセット（秒） */
  offset?: number;
  /** 通貨コード（ISO 4217形式） */
  currency?: string;
  /** インターネットサービスプロバイダ名 */
  isp?: string;
  /** 組織名 */
  org?: string;
  /** 自律システム番号（AS番号） */
  asn?: string;
  /** 自律システム名 */
  asname?: string;
  /** モバイルネットワークフラグ */
  mobile?: boolean;
  /** プロキシ検出フラグ */
  proxy?: boolean;
  /** ホスティングサービス検出フラグ */
  hosting?: boolean;
  /** WHOIS情報（詳細情報） */
  whois?: WhoisInfo | null;
}

/**
 * ログマークカテゴリ
 *
 * マークのカテゴリを表します。ユーザーが自由に作成可能。
 */
export interface LogMarkCategory {
  /** カテゴリID */
  id: number;
  /** カテゴリ名（表示用） */
  name: string;
  /** スラッグ（識別子） */
  slug: string;
  /** 表示色（HEXカラーコード） */
  color: string;
  /** 説明 */
  description?: string | null;
  /** 作成日時（ISO 8601形式） */
  created_at?: string;
  /** 更新日時（ISO 8601形式） */
  updated_at?: string;
}

/**
 * ログマーク情報
 *
 * User-Agentパターンに基づくログのマーキング情報を表します。
 * ボット、疑わしいアクセス、正規アクセスなどを識別します。
 */
export interface LogMark {
  /** カテゴリ情報 */
  category: LogMarkCategory;
  /** マッチしたUser-Agentパターン */
  pattern: string;
  /** メモ・説明 */
  note: string;
}

/**
 * ログマークパターン設定
 *
 * 複数条件（User-Agent、IP、パス、クエリストリング、リファラ）の組み合わせで
 * ログをマークするための設定情報を表します。
 */
export interface LogMarkPattern {
  /** パターンID */
  id?: number;
  /** 対象のDistribution ID（省略時は全Distribution対象） */
  distribution_id?: string | null;
  /** マッチング対象のUser-Agentパターン（省略可） */
  user_agent_pattern?: string | null;
  /** マッチング対象のIPアドレスパターン（省略可） */
  ip_pattern?: string | null;
  /** マッチング対象のパスパターン（省略可） */
  path_pattern?: string | null;
  /** マッチング対象のクエリストリングパターン（省略可） */
  query_string_pattern?: string | null;
  /** マッチング対象のリファラパターン（省略可） */
  referrer_pattern?: string | null;
  /** マッチング対象の組織名パターン（省略可） */
  org_pattern?: string | null;
  /** マッチング方法（exact: 完全一致、partial: 部分一致） */
  match_type: "exact" | "partial";
  /** カテゴリ情報（読み取り用） */
  category?: LogMarkCategory | null;
  /** カテゴリID（作成・更新用） */
  category_id?: number;
  /** メモ・説明 */
  note?: string;
  /** アクティブフラグ */
  is_active: boolean;
  /** 作成日時（ISO 8601形式） */
  created_at?: string;
  /** 更新日時（ISO 8601形式） */
  updated_at?: string;
}

/**
 * マーク統計情報
 *
 * ログ集約時のカテゴリslug別の件数統計を表します。
 * カテゴリslugをキーとし、件数を値とする動的なオブジェクト。
 */
export interface MarkStats {
  /** カテゴリslugをキーとした件数 */
  [categorySlug: string]: number;
}

/**
 * マーク内訳の個別アイテム
 *
 * パターン別のマーク統計情報を表します。
 */
export interface MarkDetailItem {
  /** このパターンにマッチしたログ数 */
  count: number;
  /** カテゴリ情報 */
  category: LogMarkCategory;
  /** パターンのメモ・説明 */
  note: string;
}

/**
 * マーク内訳情報
 *
 * パターン名をキーとしたマーク内訳の辞書型。
 */
export type MarkDetails = Record<string, MarkDetailItem>;

/**
 * 疑わしいアクセスチェックの詳細結果
 *
 * User-Agent、Referrer、パス、IPアドレスなど、個別の項目ごとの
 * 疑わしいパターンマッチング結果を格納します。
 */
export interface SuspiciousCheckDetail {
  /** 疑わしいアクセスとして判定されたか */
  is_suspicious: boolean;
  /** ブロックリストに含まれているか */
  is_blocked?: boolean;
  /** 許可されたボット（正規のクローラー）か */
  is_allowed_bot?: boolean;
  /** マッチした疑わしいパターンのリスト */
  matched_patterns: string[];
  /** 危険度レベル（"safe", "warning", "danger"） */
  severity: string;
}

/**
 * 疑わしいアクセスチェックの総合結果
 *
 * アクセスログの各要素を分析した結果を統合し、
 * 全体的な疑わしさの判定を提供します。
 */
export interface SuspiciousCheck {
  /** 疑わしいアクセスと判定されたか */
  isSuspicious: boolean;
  /** ブロックされているか */
  isBlocked: boolean;
  /** 許可されたボット（正規のクローラー）か */
  isAllowedBot: boolean;
  /** 危険度レベル */
  severity: 'safe' | 'warning' | 'danger';
  /** マッチした疑わしいパターンのリスト */
  matchedPatterns: string[];
  /** 各項目の詳細チェック結果 */
  details?: {
    /** User-Agentのチェック結果 */
    userAgent: SuspiciousCheckDetail;
    /** Referrerのチェック結果 */
    referrer: SuspiciousCheckDetail;
    /** パス（URI Stem）のチェック結果 */
    path: SuspiciousCheckDetail;
    /** IPアドレスのチェック結果 */
    ip: SuspiciousCheckDetail;
  };
}

/**
 * CloudFrontアクセスログエントリ
 *
 * CloudFrontの標準ログフォーマットに基づくアクセスログの1行を表します。
 * 基本的なHTTPリクエスト情報に加え、CloudFront固有のフィールドや
 * 拡張情報（IP情報、疑わしいアクセスチェック結果）を含みます。
 */
export interface LogEntry {
  /** ログ日付（YYYY-MM-DD形式） */
  date: string;
  /** ログ時刻（HH:MM:SS形式） */
  time: string;
  /** CloudFrontエッジロケーション */
  edgeLocation: string;
  /** 送受信されたバイト数 */
  bytes: number;
  /** クライアントIPアドレス */
  clientIp: string;
  /** HTTPメソッド（GET、POST等） */
  method: string;
  /** ホスト名 */
  host: string;
  /** URIパス（クエリ文字列を除く） */
  uriStem: string;
  /** HTTPステータスコード */
  statusCode: number;
  /** リファラーURL */
  referrer: string;
  /** User-Agent文字列 */
  userAgent: string;
  /** クエリ文字列 */
  queryString: string;
  /** Cookie */
  cookie: string;
  /** エッジ結果タイプ（Hit、Miss等） */
  edgeResultType: string;
  /** エッジリクエストID */
  edgeRequestId?: string;
  /** ホストヘッダー */
  hostHeader?: string;
  /** プロトコル（http/https） */
  protocol?: string;
  /** 送信バイト数 */
  bytes_sent?: number;
  /** 処理時間（秒） */
  timeTaken?: number;
  /** X-Forwarded-Forヘッダー */
  xForwardedFor?: string;
  /** SSL/TLSプロトコルバージョン */
  sslProtocol?: string;
  /** SSL/TLS暗号スイート */
  sslCipher?: string;
  /** エッジレスポンス結果タイプ */
  edgeResponseResultType?: string;
  /** HTTPプロトコルバージョン */
  protocolVersion?: string;
  /** Field Level Encryptionステータス */
  fleStatus?: string;
  /** Field Level Encryption暗号化フィールド */
  fleEncryptedFields?: string;
  /** クライアントポート番号 */
  clientPort?: number;
  /** 最初のバイトまでの時間（秒） */
  timeToFirstByte?: number;
  /** エッジ詳細結果タイプ */
  edgeDetailedResultType?: string;
  /** コンテンツタイプ（MIMEタイプ） */
  contentType?: string;
  /** コンテンツ長 */
  contentLength?: number;
  /** Rangeリクエスト開始バイト */
  rangeStart?: number;
  /** Rangeリクエスト終了バイト */
  rangeEnd?: number;
  /** キャッシュステータス */
  cacheStatus?: string;
  /** IP地理情報と詳細（拡張情報） */
  ipInfo?: IPInfo;
  /** 疑わしいアクセスチェック結果（拡張情報） */
  suspiciousCheck?: SuspiciousCheck;
  /** ログマーク情報（拡張情報） */
  mark?: LogMark | null;
}

/**
 * CloudFrontディストリビューション情報
 *
 * CloudFrontディストリビューションの基本情報を表します。
 */
export interface Distribution {
  /** ディストリビューションID */
  id: string;
  /** CloudFrontドメイン名（*.cloudfront.net） */
  domain: string;
  /** 代替ドメイン名（CNAME）のリスト */
  aliases?: string[];
}

/**
 * チェック結果の基本インターフェース
 *
 * 各種疑わしいアクセスチェックの結果を表す基本型。
 * 拡張プロパティを持つことができます。
 */
export interface CheckResult {
  /** 疑わしいアクセスと判定されたか */
  isSuspicious: boolean;
  /** チェック結果の説明文 */
  description: string;
  /** 追加プロパティ（各チェックタイプで拡張） */
  [key: string]: string | number | boolean | undefined;
}

/**
 * AWS WAF IP Setの情報
 *
 * WAFで管理されているIPアドレスセットの情報を表します。
 * ブロックリストやホワイトリストとして使用されます。
 */
export interface WAFIPSet {
  /** IP SetのID */
  id: string;
  /** IP Setの名前 */
  name: string;
  /** IP SetのARN（Amazon Resource Name） */
  arn: string;
  /** 登録されているIPアドレス数 */
  addressCount: number;
  /** IPアドレスバージョン（IPv4/IPv6） */
  ipAddressVersion: string;
  /** IP Setの説明文 */
  description?: string;
}

/**
 * WAFブロックチェックのレスポンス
 *
 * 指定されたIPアドレスがWAFでブロックされているかを
 * チェックした結果を格納します。
 */
export interface WAFCheckResponse {
  /** IPアドレスがブロックされているか */
  isBlocked: boolean;
  /** WAFが有効になっているか */
  hasWAF: boolean;
  /** 関連付けられているWeb ACL情報 */
  webAcl?: {
    /** Web ACL名 */
    name: string;
    /** Web ACL ID */
    id: string;
  };
  /** マッチしたブロックルール名 */
  blockingRule?: string | null;
  /** チェックしたIP Setのリスト */
  ipSetsChecked: Array<{
    /** IP Set ID */
    id: string;
    /** IP Set名 */
    name: string;
    /** IP Set ARN */
    arn: string;
  }>;
  /** マッチしたCIDR表記 */
  matchedCidr?: string | null;
  /** マッチしたIP SetのID */
  matchedIpSetId?: string | null;
  /** マッチしたIP Setの名前 */
  matchedIpSetName?: string | null;
}

/**
 * WAFブロックリスト追加のレスポンス
 *
 * IPアドレスをWAFのブロックリストに追加した結果を格納します。
 */
export interface WAFAddBlocklistResponse {
  /** 追加が成功したか */
  success: boolean;
  /** 追加されたIPアドレス */
  ipAddress: string;
  /** 追加先のIP Set ID */
  ipSetId: string;
  /** 追加先のIP Set名 */
  ipSetName: string;
  /** 結果メッセージ */
  message: string;
}

/**
 * 会社情報ページアクセスチェックの結果
 *
 * 会社情報ページ等への不審なアクセスパターン
 * （例：直接アクセス、短期間の大量アクセス）を検出した結果を格納します。
 */
export interface CompanyInfoCheckResult {
  /** チェックタイプ識別子 */
  checkType: string;
  /** チェック条件 */
  criteria: {
    /** 対象URL */
    targetUrl: string;
    /** 会社情報ページURL */
    companyInfoUrl: string;
    /** チェック期間 */
    period: string;
  };
  /** チェック結果 */
  result: CheckResult & {
    /** 総アクセス数 */
    totalAccessCount: number;
    /** 疑わしいアクセス数 */
    suspiciousAccessCount: number;
  };
  /** アクセス詳細のリスト */
  details: Array<{
    /** アクセス日付 */
    date: string;
    /** アクセス時刻 */
    time: string;
    /** クライアントIPアドレス */
    clientIp: string;
    /** リファラー */
    referrer: string;
    /** User-Agent */
    userAgent: string;
    /** HTTPステータスコード */
    statusCode: number;
  }>;
}

/**
 * 頻繁アクセスIPチェックの結果
 *
 * 特定のIPアドレスからの頻繁なアクセスや
 * スクレイピング疑いを検出した結果を格納します。
 */
export interface FrequentIPCheckResult {
  /** チェックタイプ識別子 */
  checkType: string;
  /** チェック条件 */
  criteria: {
    /** 対象クライアントIPアドレス */
    clientIp: string;
    /** チェック期間 */
    period: string;
    /** 閾値 */
    threshold: string;
  };
  /** チェック結果 */
  result: CheckResult & {
    /** 総アクセス数 */
    totalAccessCount: number;
    /** アクセスしたユニークURL数 */
    uniqueUrlsAccessed: number;
  };
  /** URLごとのアクセス詳細 */
  details: Array<{
    /** アクセスされたURL */
    url: string;
    /** このURLへのアクセス数 */
    accessCount: number;
    /** アクセスのリスト */
    accesses: Array<{
      /** アクセス日付 */
      date: string;
      /** アクセス時刻 */
      time: string;
      /** HTTPステータスコード */
      statusCode: number;
      /** User-Agent */
      userAgent: string;
    }>;
  }>;
}

/**
 * マルチデバイスアクセスチェックの結果
 *
 * 同一IPアドレスから複数のデバイスタイプでアクセスがあった場合を
 * 検出した結果を格納します（User-Agent偽装の疑い）。
 */
export interface MultiDeviceCheckResult {
  /** チェックタイプ識別子 */
  checkType: string;
  /** チェック条件 */
  criteria: {
    /** 対象クライアントIPアドレス */
    clientIp: string;
    /** チェック期間 */
    period: string;
    /** 閾値 */
    threshold: string;
  };
  /** チェック結果 */
  result: CheckResult & {
    /** 総アクセス数 */
    totalAccessCount: number;
    /** 検出されたデバイスタイプのリスト */
    deviceTypesDetected: string[];
    /** 実際のデバイスタイプ（重複除去後） */
    realDeviceTypes: string[];
  };
  /** デバイスタイプごとの詳細 */
  details: {
    /** デバイスタイプをキーとした詳細情報 */
    [deviceType: string]: {
      /** このデバイスタイプのアクセス数 */
      count: number;
      /** サンプルアクセスのリスト */
      samples: Array<{
        /** アクセス日付 */
        date: string;
        /** アクセス時刻 */
        time: string;
        /** User-Agent */
        userAgent: string;
        /** アクセスされたURI */
        uriStem: string;
        /** HTTPステータスコード */
        statusCode: number;
      }>;
    };
  };
}

/**
 * リサーチツールアクセスチェックの結果
 *
 * リサーチツールやスクレイピングツールと思われる
 * User-Agentやパターンを検出した結果を格納します。
 */
export interface ResearchToolCheckResult {
  /** チェックタイプ識別子 */
  checkType: string;
  /** チェック条件 */
  criteria: {
    /** 検出対象のパターンリスト */
    patterns: string[];
  };
  /** チェック結果 */
  result: CheckResult & {
    /** マッチしたパターン数 */
    matchedPatternCount: number;
  };
  /** マッチした詳細情報 */
  details: {
    /** User-Agent文字列 */
    userAgent: string;
    /** リファラー */
    referrer: string;
    /** マッチしたパターンのリスト */
    matchedPatterns: string[];
  };
}

/**
 * 生ログ取得APIのレスポンス
 *
 * CloudFrontの生アクセスログとページネーション情報を含みます。
 */
export interface RawLogsResponse {
  /** アクセスログエントリのリスト */
  logs: LogEntry[];
  /** ページネーション情報 */
  pagination: {
    /** 現在のページ番号（1から開始） */
    page: number;
    /** 1ページあたりのエントリ数 */
    perPage: number;
    /** 総エントリ数 */
    total: number;
    /** 総ページ数 */
    totalPages: number;
  };
}

/**
 * 地理位置情報
 *
 * 特定の地理的位置からのアクセス集計情報を表します。
 * 地図上のマーカー表示などに使用されます。
 */
export interface GeoLocation {
  /** 緯度 */
  lat: number;
  /** 経度 */
  lon: number;
  /** 都市名 */
  city: string;
  /** 国名 */
  country: string;
  /** 国コード（ISO 3166-1 alpha-2形式） */
  countryCode: string;
  /** この位置からのアクセス数 */
  count: number;
  /** この位置からアクセスしたIPアドレスのリスト */
  ips: string[];
}

/**
 * 地理位置ログ取得APIのレスポンス
 *
 * アクセスログの地理的分布情報を格納します。
 */
export interface GeoLogsResponse {
  /** 地理位置情報のリスト */
  locations: GeoLocation[];
  /** 総アクセス数 */
  total: number;
}

/**
 * ブロックされたIPの地理位置情報
 *
 * WAFでブロックされているIPアドレスの地理的位置を表します。
 * 複数のCIDRやIP Setをまとめた情報を含みます。
 */
export interface BlockedIPGeoLocation {
  /** 緯度 */
  lat: number;
  /** 経度 */
  lon: number;
  /** 都市名 */
  city: string;
  /** 国名 */
  country: string;
  /** 国コード（ISO 3166-1 alpha-2形式） */
  countryCode: string;
  /** この位置のブロックされたIP/CIDR数 */
  count: number;
  /** この位置のCIDRリスト */
  cidrs: string[];
  /** 関連するIP Set名のリスト */
  ipSetNames: string[];
}

/**
 * ブロックされたIPの地理位置取得APIのレスポンス
 *
 * WAFでブロックされているIPの地理的分布情報を格納します。
 */
export interface BlockedIPsGeoResponse {
  /** 地理位置情報のリスト */
  locations: BlockedIPGeoLocation[];
  /** 総ブロックIP数 */
  total: number;
  /** レスポンスメッセージ */
  message?: string;
}

/**
 * 個別ブロックIPの地理位置情報
 *
 * 単一のブロックされたIPアドレスの詳細な地理情報を表します。
 * GeoLocationよりも詳細なISP情報などを含みます。
 */
export interface BlockedIPGeolocation {
  /** 緯度 */
  lat: number;
  /** 経度 */
  lon: number;
  /** 国名 */
  country?: string;
  /** 国コード（ISO 3166-1 alpha-2形式） */
  countryCode?: string;
  /** 地域/州 */
  region?: string;
  /** 都市名 */
  city?: string;
  /** インターネットサービスプロバイダ名 */
  isp?: string;
  /** 組織名 */
  org?: string;
  /** 自律システム番号（AS番号） */
  asn?: string;
}

/**
 * 地理情報付きブロックIP
 *
 * WAFでブロックされている個別のIPアドレスと
 * その地理情報、CIDR情報を含む詳細データを表します。
 */
export interface BlockedIPWithGeo {
  /** IPアドレス */
  ip: string;
  /** CIDR表記 */
  cidr: string;
  /** 代表IPアドレス（CIDRレンジの最初のIP） */
  representativeIp: string;
  /** CIDRカテゴリ（サイズによる分類） */
  cidrCategory: 'single' | 'small' | 'medium' | 'large' | 'very_large' | 'unknown';
  /** 所属するIP Set ID */
  ipSetId: string;
  /** 所属するIP Set名 */
  ipSetName: string;
  /** 所属するIP Set ARN */
  ipSetArn: string;
  /** 地理位置情報（取得できない場合はnull） */
  geolocation: BlockedIPGeolocation | null;
}

/**
 * ブロックIP詳細地理情報取得APIのレスポンス
 *
 * WAFでブロックされている全IPの詳細リストと
 * 関連するIP Set情報を格納します。
 */
export interface BlockedIPsDetailGeoResponse {
  /** ブロックされたIPの詳細リスト */
  blockedIps: BlockedIPWithGeo[];
  /** 総ブロックIP数 */
  total: number;
  /** 地理情報が取得できなかったIP数 */
  totalWithoutGeo: number;
  /** 関連するIP Setのリスト */
  ipSets: Array<{
    /** IP Set ID */
    id: string;
    /** IP Set名 */
    name: string;
    /** IP Set ARN */
    arn: string;
  }>;
}

/**
 * 簡易地理情報
 *
 * ログ集計で使用される簡易版の地理情報を表します。
 */
export interface GeoInfo {
  /** 国名 */
  country?: string;
  /** 国コード（ISO 3166-1 alpha-2形式） */
  country_code?: string;
  /** 都市名 */
  city?: string;
}

/**
 * サンプルログエントリ
 *
 * 集計結果の代表的なログサンプルを表します。
 */
export interface SampleLog {
  /** ログ日付 */
  date: string;
  /** ログ時刻 */
  time: string;
  /** アクセスされたURI */
  uri: string;
  /** HTTPステータスコード */
  status: number;
}

/**
 * 集計アイテム
 *
 * IP、User-Agent、Referrerなどでグループ化された
 * アクセスログの集計結果を表します。
 */
export interface AggregationItem {
  /** 集計キーの値（IPアドレス、User-Agent文字列等） */
  value: string;
  /** リクエスト数 */
  request_count: number;
  /** 全体に対する割合（パーセント） */
  percentage: number;
  /** 最初に確認された日時 */
  first_seen: string;
  /** 最後に確認された日時 */
  last_seen: string;
  /** アクセスしたユニークパス数 */
  unique_paths: number;
  /** ユニークUser-Agent数（IPでグループ化時のみ） */
  unique_user_agents?: number;
  /** ステータスコード別の分布 */
  status_distribution: Record<string, number>;
  /** HTTPメソッド別の分布 */
  method_distribution: Record<string, number>;
  /** 地理情報（IPでグループ化時のみ） */
  geo_info?: GeoInfo;
  /** この集計アイテムのマーク統計 */
  mark_stats?: MarkStats;
  /** この集計アイテムのマーク内訳（パターン別） */
  mark_details?: MarkDetails;
  /** この集計値自体のカテゴリ情報（user_agentでグループ化時のみ） */
  mark_category?: LogMarkCategory | null;
  /** サンプルログ */
  sample_log?: SampleLog;
}

/**
 * 日付範囲
 *
 * 集計対象の期間を表します。
 */
export interface DateRange {
  /** 開始日（YYYY-MM-DD形式） */
  start: string;
  /** 終了日（YYYY-MM-DD形式） */
  end: string;
}

/**
 * ログ集計APIのレスポンス
 *
 * 指定された条件でグループ化されたアクセスログの
 * 集計結果を格納します。
 */
export interface LogAggregationResponse {
  /** 対象ディストリビューションID */
  distribution_id: string;
  /** 集計対象の日付範囲 */
  date_range: DateRange;
  /** グループ化キー */
  group_by: 'ip' | 'user_agent' | 'referrer' | 'query_string' | 'page_path';
  /** 総リクエスト数 */
  total_requests: number;
  /** ユニークな値の数 */
  unique_values: number;
  /** 集計結果のリスト */
  aggregations: AggregationItem[];
  /** マーク統計情報 */
  mark_stats?: MarkStats;
  /** マーク内訳情報（パターン別） */
  mark_details?: MarkDetails;
}

/**
 * グループ化オプション型
 *
 * ログ集計時に使用できるグループ化キーの型定義。
 * IP、User-Agent、Referrer、クエリ文字列のいずれかを指定できます。
 */
export type GroupByOption = 'ip' | 'user_agent' | 'referrer' | 'query_string' | 'page_path';
