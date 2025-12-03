/**
 * @fileoverview CloudFront APIクライアントサービス
 *
 * このファイルは、CloudFrontディストリビューションの管理、ログ検索、WAF操作、
 * 不正アクセスチェックなどを行うサービスクラスを提供します。
 * バックエンドAPIとの通信を抽象化し、フロントエンドで使いやすいインターフェースを提供します。
 */

import type {
  BlockedIPsDetailGeoResponse,
  BlockedIPsGeoResponse,
  CompanyInfoCheckResult,
  Distribution,
  FrequentIPCheckResult,
  GeoLogsResponse,
  GroupByOption,
  IPInfo,
  LogAggregationResponse,
  LogEntry,
  LogMarkCategory,
  LogMarkPattern,
  MultiDeviceCheckResult,
  RawLogsResponse,
  ResearchToolCheckResult,
  WAFAddBlocklistResponse,
  WAFCheckResponse,
  WAFIPSet,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * CloudFront APIクライアントサービスクラス
 *
 * CloudFrontのディストリビューション管理、ログ検索、WAF操作、不正アクセスチェックなどの
 * 機能を提供するサービスクラスです。バックエンドAPIとの通信を担当し、
 * 各種CloudFront関連の操作をTypeScriptの型安全な形で利用できるようにします。
 *
 * 主な機能:
 * - ディストリビューション一覧の取得
 * - アクセスログの検索と分析
 * - IPアドレス情報の取得
 * - 不正アクセスの検出（企業情報アクセス、頻繁なIPアクセス、マルチデバイスアクセス、リサーチツール検出）
 * - WAF IP Setの管理とブロックリスト操作
 * - 地理情報を含むログデータの取得
 * - WHOIS情報のバッチ取得
 * - ログの集約と分析
 */
export class CloudFrontService {
  private profile: string;

  /**
   * CloudFrontServiceのインスタンスを作成します
   *
   * @param profile - AWS CLIプロファイル名。AWS認証情報の識別に使用されます
   */
  constructor(profile: string) {
    this.profile = profile;
  }

  /**
   * CloudFrontディストリビューションの一覧を取得します
   *
   * 現在のAWSプロファイルに関連付けられた全てのCloudFrontディストリビューションの
   * 一覧を取得します。各ディストリビューションにはID、ドメイン名、ステータスなどの
   * 基本情報が含まれます。
   *
   * @returns ディストリビューション情報の配列
   * @throws APIリクエストが失敗した場合、または認証エラーが発生した場合にエラーをスロー
   */
  async listDistributions(): Promise<Distribution[]> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/cloudfront/distributions/?profile=${encodeURIComponent(this.profile)}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error listing distributions:', error);
      throw error;
    }
  }

  /**
   * 特定のURLとタイムウィンドウでCloudFrontログを検索します
   *
   * 指定されたディストリビューションのログを、対象URLと日時を基準に検索します。
   * タイムウィンドウを使用して、指定時刻の前後のログを取得できます。
   *
   * @param distributionId - 検索対象のCloudFrontディストリビューションID
   * @param targetUrl - 検索対象のURL（部分一致）
   * @param dateTime - 検索の基準となる日時
   * @param timeWindowMinutes - 検索する時間範囲（分単位）。デフォルトは5分
   * @returns 検索条件に一致するログエントリの配列
   * @throws APIリクエストが失敗した場合、またはログが見つからない場合にエラーをスロー
   */
  async searchLogs(
    distributionId: string,
    targetUrl: string,
    dateTime: Date,
    timeWindowMinutes: number = 5
  ): Promise<LogEntry[]> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/cloudfront/logs/search/?profile=${encodeURIComponent(this.profile)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            distributionId,
            targetUrl,
            dateTime: dateTime.toISOString(),
            timeWindowMinutes,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error searching logs:', error);
      throw error;
    }
  }

  /**
   * IPアドレスの詳細情報を取得します
   *
   * 指定されたIPアドレスの地理情報、ISP情報、WHOIS情報などの詳細を取得します。
   * 不正アクセスの調査やアクセス元の特定に使用されます。
   *
   * @param ipAddress - 情報を取得するIPアドレス（IPv4またはIPv6）
   * @returns IPアドレスに関連する詳細情報（国、地域、ISP、WHOIS等）
   * @throws APIリクエストが失敗した場合、または無効なIPアドレスが指定された場合にエラーをスロー
   */
  async getIPInfo(ipAddress: string): Promise<IPInfo> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/ip-info/${encodeURIComponent(ipAddress)}/?profile=${encodeURIComponent(this.profile)}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching IP info:', error);
      throw error;
    }
  }

  /**
   * 企業情報ページへのアクセス状況をチェックします
   *
   * 対象URLにアクセスしたIPアドレスが、企業情報ページ（会社概要など）にもアクセスしているかを
   * チェックします。企業情報ページへのアクセスがない場合、不正なアクセスの可能性があります。
   *
   * @param distributionId - チェック対象のCloudFrontディストリビューションID
   * @param targetUrl - 分析対象のターゲットURL
   * @param companyInfoUrl - 企業情報ページのURL。デフォルトは '/nattoku/about/'
   * @returns 企業情報ページへのアクセス有無と詳細情報
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async checkCompanyInfoAccess(
    distributionId: string,
    targetUrl: string,
    companyInfoUrl: string = '/nattoku/about/'
  ): Promise<CompanyInfoCheckResult> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/checks/company-info-access/?profile=${encodeURIComponent(this.profile)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            distributionId,
            targetUrl,
            companyInfoUrl,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error checking company info access:', error);
      throw error;
    }
  }

  /**
   * 特定IPアドレスの頻繁なアクセスをチェックします
   *
   * 指定されたIPアドレスが過去N日間でどの程度頻繁にアクセスしているかを分析します。
   * 異常に高いアクセス頻度は、スクレイピングやボット攻撃の可能性を示唆します。
   *
   * @param distributionId - チェック対象のCloudFrontディストリビューションID
   * @param clientIp - チェックするクライアントIPアドレス
   * @param days - チェック対象の日数。デフォルトは10日
   * @returns IPアクセスの頻度と分析結果
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async checkFrequentIPAccess(
    distributionId: string,
    clientIp: string,
    days: number = 10
  ): Promise<FrequentIPCheckResult> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/checks/frequent-ip-access/?profile=${encodeURIComponent(this.profile)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            distributionId,
            clientIp,
            days,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error checking frequent IP access:', error);
      throw error;
    }
  }

  /**
   * 同一IPアドレスからの複数デバイスアクセスをチェックします
   *
   * 指定されたIPアドレスから、複数の異なるUser-Agent（デバイス）を使用した
   * アクセスがあるかをチェックします。複数のデバイスからのアクセスは、
   * 代理アクセスやアカウント共有の可能性を示唆します。
   *
   * @param distributionId - チェック対象のCloudFrontディストリビューションID
   * @param clientIp - チェックするクライアントIPアドレス
   * @param days - チェック対象の日数。デフォルトは10日
   * @returns 使用されたデバイス（User-Agent）のリストと分析結果
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async checkMultiDeviceAccess(
    distributionId: string,
    clientIp: string,
    days: number = 10
  ): Promise<MultiDeviceCheckResult> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/checks/multi-device-access/?profile=${encodeURIComponent(this.profile)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            distributionId,
            clientIp,
            days,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error checking multi-device access:', error);
      throw error;
    }
  }

  /**
   * リサーチツールやクローラーの検出をチェックします
   *
   * User-AgentとRefererヘッダーを解析して、スクレイピングツール、クローラー、
   * リサーチツールなどの自動化されたアクセスを検出します。
   *
   * @param userAgent - チェックするUser-Agent文字列
   * @param referrer - チェックするReferrer文字列（オプション）
   * @returns リサーチツール検出の結果と詳細情報
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async checkResearchToolDetection(
    userAgent: string,
    referrer?: string
  ): Promise<ResearchToolCheckResult> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/checks/research-tool-detection/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userAgent,
          referrer: referrer || '',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error checking research tool detection:', error);
      throw error;
    }
  }

  /**
   * WAF IP Setの一覧を取得します
   *
   * 指定されたCloudFrontディストリビューションに関連付けられているWAF Web ACLと、
   * そのWeb ACLで使用されているIP Setの一覧を取得します。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @returns WAFの有無、Web ACL情報、およびIP Setのリスト
   * @throws APIリクエストが失敗した場合、またはWAF設定が見つからない場合にエラーをスロー
   */
  async listWAFIPSets(distributionId: string): Promise<{
    hasWAF: boolean;
    webAcl?: { name: string; id: string };
    ipSets: WAFIPSet[];
  }> {
    try {
      const params = new URLSearchParams({
        profile: this.profile,
        distributionId,
      });

      const response = await fetch(`${API_BASE_URL}/api/waf/ip-sets/?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error listing WAF IP Sets:', error);
      throw error;
    }
  }

  /**
   * 指定したIPアドレスがWAFブロックリストに含まれているかをチェックします
   *
   * WAF IP Setに特定のIPアドレスが登録されているかを確認します。
   * ブロック済みのIPアドレスを確認する際に使用します。
   *
   * @param distributionId - チェック対象のCloudFrontディストリビューションID
   * @param ipAddress - チェックするIPアドレス
   * @returns ブロックリストへの登録状況と詳細情報
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async checkWAFBlocklist(distributionId: string, ipAddress: string): Promise<WAFCheckResponse> {
    try {
      const params = new URLSearchParams({
        profile: this.profile,
        distributionId,
        ipAddress,
      });

      const response = await fetch(
        `${API_BASE_URL}/api/waf/blocklist/check/?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error checking WAF blocklist:', error);
      throw error;
    }
  }

  /**
   * WAFブロックリストにIPアドレスを追加します
   *
   * 指定されたIPアドレスをWAF IP Setに追加して、アクセスをブロックします。
   * IP Set IDを指定しない場合は、デフォルトのIP Setが使用されます。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @param ipAddress - ブロックリストに追加するIPアドレス
   * @param ipSetId - 追加先のIP Set ID（オプション。未指定の場合はデフォルトのIP Setを使用）
   * @returns ブロックリスト追加の結果と詳細情報
   * @throws APIリクエストが失敗した場合、またはIP Setの更新に失敗した場合にエラーをスロー
   */
  async addToWAFBlocklist(
    distributionId: string,
    ipAddress: string,
    ipSetId?: string
  ): Promise<WAFAddBlocklistResponse> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/waf/blocklist/add/?profile=${encodeURIComponent(this.profile)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            distributionId,
            ipAddress,
            ipSetId,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error adding to WAF blocklist:', error);
      throw error;
    }
  }

  /**
   * WAFブロックリストからIPアドレスを削除します
   *
   * 指定されたIPアドレスをWAF IP Setから削除して、アクセスブロックを解除します。
   * IP Set IDを指定しない場合は、デフォルトのIP Setが使用されます。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @param ipAddress - ブロックリストから削除するIPアドレス
   * @param ipSetId - 削除元のIP Set ID（オプション。未指定の場合はデフォルトのIP Setを使用）
   * @returns ブロックリスト削除の結果と詳細情報
   * @throws APIリクエストが失敗した場合、またはIP Setの更新に失敗した場合にエラーをスロー
   */
  async removeFromWAFBlocklist(
    distributionId: string,
    ipAddress: string,
    ipSetId?: string
  ): Promise<WAFAddBlocklistResponse> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/waf/blocklist/remove/?profile=${encodeURIComponent(this.profile)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            distributionId,
            ipAddress,
            ipSetId,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error removing from WAF blocklist:', error);
      throw error;
    }
  }

  /**
   * WAFでブロックされているIPアドレスの一覧を取得します
   *
   * 指定されたCloudFrontディストリビューションのWAF IP Setに登録されている
   * 全てのブロック済みIPアドレスの一覧を取得します。各IPアドレスには、
   * 所属するIP SetのIDや名前などの詳細情報が含まれます。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @returns ブロックされているIPアドレスのリスト、総数、およびIP Set情報
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async getBlockedIPs(distributionId: string): Promise<{
    blockedIps: Array<{
      ip: string;
      cidr: string;
      ipSetId: string;
      ipSetName: string;
      ipSetArn: string;
    }>;
    total: number;
    ipSets: Array<{ id: string; name: string; arn: string }>;
  }> {
    try {
      const params = new URLSearchParams({
        profile: this.profile,
        distributionId,
      });

      const response = await fetch(`${API_BASE_URL}/api/waf/blocked-ips/?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting blocked IPs:', error);
      throw error;
    }
  }

  /**
   * ブロックされているIPアドレスのリストをExcelファイルとしてダウンロードします
   *
   * WAF IP Setに登録されているブロック済みIPアドレスの一覧をExcel形式で
   * エクスポートします。レポート作成や外部ツールでの分析に使用できます。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @returns ブロックIPリストを含むExcelファイルのBlobオブジェクト
   * @throws APIリクエストが失敗した場合、またはファイル生成に失敗した場合にエラーをスロー
   */
  async downloadBlockedIPsExcel(distributionId: string): Promise<Blob> {
    try {
      const params = new URLSearchParams({
        profile: this.profile,
        distributionId,
      });

      const response = await fetch(
        `${API_BASE_URL}/api/waf/blocked-ips/export/?${params.toString()}`,
        {
          method: 'GET',
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      return blob;
    } catch (error) {
      console.error('Error downloading blocked IPs Excel:', error);
      throw error;
    }
  }

  /**
   * CloudFrontの生ログを取得します
   *
   * 指定された期間と条件でCloudFrontのアクセスログを取得します。
   * 複数のフィルター条件を組み合わせて、詳細な検索が可能です。
   * ページネーション機能により、大量のログデータを効率的に取得できます。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @param startDate - 検索開始日（YYYY-MM-DD形式）
   * @param endDate - 検索終了日（YYYY-MM-DD形式）
   * @param clientIp - フィルターするクライアントIPアドレス（オプション）
   * @param uriPath - フィルターするURIパス（部分一致、オプション）
   * @param userAgent - フィルターするUser-Agent（部分一致、オプション）
   * @param referrer - フィルターするReferrer（部分一致、オプション）
   * @param queryString - フィルターするクエリ文字列（部分一致、オプション）
   * @param startTime - 検索開始時刻（HH:MM:SS形式、オプション）
   * @param endTime - 検索終了時刻（HH:MM:SS形式、オプション）
   * @param page - ページ番号。デフォルトは1
   * @param perPage - 1ページあたりの件数。デフォルトは1000
   * @param clientIps - フィルターする複数のクライアントIPアドレス（オプション）
   * @returns ページネーション情報を含むログエントリのリスト
   * @throws APIリクエストが失敗した場合、または無効なパラメータが指定された場合にエラーをスロー
   */
  async listRawLogs(
    distributionId: string,
    startDate: string,
    endDate: string,
    clientIp?: string,
    uriPath?: string,
    userAgent?: string,
    referrer?: string,
    queryString?: string,
    startTime?: string,
    endTime?: string,
    page: number = 1,
    perPage: number = 1000,
    clientIps?: string[],
    excludeStaticFiles?: boolean
  ): Promise<RawLogsResponse> {
    try {
      const params = new URLSearchParams({
        profile: this.profile,
        distributionId,
        startDate,
        endDate,
        page: page.toString(),
        perPage: perPage.toString(),
      });

      if (clientIp) {
        params.append('clientIp', clientIp);
      }
      if (clientIps && clientIps.length > 0) {
        params.append('clientIps', clientIps.join(','));
      }
      if (uriPath) {
        params.append('uriPath', uriPath);
      }
      if (userAgent) {
        params.append('userAgent', userAgent);
      }
      if (referrer) {
        params.append('referrer', referrer);
      }
      if (queryString) {
        params.append('queryString', queryString);
      }
      if (startTime) {
        params.append('startTime', startTime);
      }
      if (endTime) {
        params.append('endTime', endTime);
      }
      if (excludeStaticFiles !== undefined) {
        params.append('excludeStaticFiles', excludeStaticFiles.toString());
      }

      const response = await fetch(
        `${API_BASE_URL}/api/cloudfront/logs/raw/?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error listing raw logs:', error);
      throw error;
    }
  }

  /**
   * 地理情報を含むCloudFrontログを取得します
   *
   * アクセスログに地理情報（国、地域、座標など）を付加したデータを取得します。
   * 地図上での可視化やアクセス元の地理的分析に使用されます。
   * 複数のフィルター条件を指定して、特定の条件に合致するログのみを取得できます。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @param startDate - 検索開始日（YYYY-MM-DD形式）
   * @param endDate - 検索終了日（YYYY-MM-DD形式）
   * @param startTime - 検索開始時刻（HH:MM:SS形式、オプション）
   * @param endTime - 検索終了時刻（HH:MM:SS形式、オプション）
   * @param uriFilter - URIパスのフィルター（部分一致、オプション）
   * @param userAgentFilter - User-Agentのフィルター（部分一致、オプション）
   * @param refererFilter - Refererのフィルター（部分一致、オプション）
   * @param queryFilter - クエリ文字列のフィルター（部分一致、オプション）
   * @param statusFilter - HTTPステータスコードのフィルター（オプション）
   * @param methodFilter - HTTPメソッドのフィルター（オプション）
   * @returns 地理情報を含むログエントリのリスト
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async getGeoLogs(
    distributionId: string,
    startDate: string,
    endDate: string,
    startTime?: string,
    endTime?: string,
    uriFilter?: string,
    userAgentFilter?: string,
    refererFilter?: string,
    queryFilter?: string,
    statusFilter?: string,
    methodFilter?: string,
    excludeStaticFiles?: boolean
  ): Promise<GeoLogsResponse> {
    try {
      const params = new URLSearchParams({
        profile: this.profile,
        distributionId,
        startDate,
        endDate,
      });

      if (startTime) {
        params.append('startTime', startTime);
      }
      if (endTime) {
        params.append('endTime', endTime);
      }
      if (uriFilter) {
        params.append('uriFilter', uriFilter);
      }
      if (userAgentFilter) {
        params.append('userAgentFilter', userAgentFilter);
      }
      if (refererFilter) {
        params.append('refererFilter', refererFilter);
      }
      if (queryFilter) {
        params.append('queryFilter', queryFilter);
      }
      if (statusFilter) {
        params.append('statusFilter', statusFilter);
      }
      if (methodFilter) {
        params.append('methodFilter', methodFilter);
      }
      if (excludeStaticFiles !== undefined) {
        params.append('excludeStaticFiles', excludeStaticFiles.toString());
      }

      const response = await fetch(
        `${API_BASE_URL}/api/cloudfront/logs/geo/?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting geo logs:', error);
      throw error;
    }
  }

  /**
   * ブロックされているIPアドレスの地理情報を取得します（集約版）
   *
   * WAF IP Setに登録されているブロック済みIPアドレスを国ごとに集約し、
   * 地理情報とともに取得します。地図上でブロック状況を可視化する際に使用されます。
   * getBlockedIPsDetailGeoと比較して、処理が高速で大量のIPに対応できます。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @returns 国ごとに集約されたブロックIP情報と地理座標
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async getBlockedIPsGeo(distributionId: string): Promise<BlockedIPsGeoResponse> {
    try {
      const params = new URLSearchParams({
        profile: this.profile,
        distributionId,
      });

      const response = await fetch(
        `${API_BASE_URL}/api/waf/blocked-ips/geo/?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting blocked IPs geo:', error);
      throw error;
    }
  }

  /**
   * ブロックされているIPアドレスの詳細な地理情報を取得します（詳細版）
   *
   * WAF IP Setに登録されているブロック済みIPアドレスの詳細な地理情報を取得します。
   * 各IPアドレスごとの正確な位置情報を含むため、処理時間がかかる場合があります。
   * 15分のタイムアウトが設定されており、大量のIPがある場合は集約版の使用を推奨します。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @returns 各IPアドレスの詳細な地理情報のリスト
   * @throws APIリクエストが失敗した場合、またはタイムアウトした場合にエラーをスロー
   */
  async getBlockedIPsDetailGeo(distributionId: string): Promise<BlockedIPsDetailGeoResponse> {
    try {
      const params = new URLSearchParams({
        profile: this.profile,
        distributionId,
      });

      // 5分のタイムアウトを設定
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 900000); // 15分

      const response = await fetch(
        `${API_BASE_URL}/api/waf/blocked-ips/geo/detail/?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: controller.signal,
        }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(
          '処理がタイムアウトしました。ブロックIPが多すぎる可能性があります。集約表示モードをお試しください。'
        );
      }
      console.error('Error getting blocked IPs detail geo:', error);
      throw error;
    }
  }

  /**
   * WHOIS情報のバッチ取得を開始します
   *
   * データベース内のWHOIS情報が未取得のIPアドレスに対して、
   * バックグラウンドでWHOIS情報を一括取得するプロセスを開始します。
   * 処理は非同期で実行され、完了状況はgetWHOISBatchStatusで確認できます。
   *
   * @returns バッチ処理の開始結果（メッセージ、未取得IP数、ステータス）
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async startWHOISBatchFetch(): Promise<{
    message: string;
    pending_count: number;
    status: string;
  }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/whois/batch/fetch/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error starting WHOIS batch fetch:', error);
      throw error;
    }
  }

  /**
   * WHOIS情報のバッチ取得ステータスを取得します
   *
   * データベース内の全IPアドレスに対するWHOIS情報の取得状況を確認します。
   * 総IP数、WHOIS取得済み数、未取得数、完了率などの統計情報を提供します。
   *
   * @returns WHOIS情報取得の進捗状況（総IP数、取得済み数、未取得数、完了率）
   * @throws APIリクエストが失敗した場合にエラーをスロー
   */
  async getWHOISBatchStatus(): Promise<{
    total_ips: number;
    with_whois: number;
    without_whois: number;
    percentage_complete: number;
  }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/whois/batch/status/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting WHOIS batch status:', error);
      throw error;
    }
  }

  /**
   * CloudFrontログの集約データを取得します
   *
   * 指定された期間のアクセスログを、指定した条件で集約して取得します。
   * IPアドレス、URI、User-Agent、Refererなどの項目でグループ化し、
   * アクセスパターンの分析や統計情報の取得に使用されます。
   *
   * @param distributionId - 対象のCloudFrontディストリビューションID
   * @param startDate - 集約期間の開始日（YYYY-MM-DD形式）
   * @param endDate - 集約期間の終了日（YYYY-MM-DD形式）
   * @param groupBy - グループ化の基準（'ip', 'uri', 'user_agent', 'referer'など）
   * @param startTime - 集約期間の開始時刻（HH:MM:SS形式、オプション）
   * @param endTime - 集約期間の終了時刻（HH:MM:SS形式、オプション）
   * @param limit - 取得する集約結果の最大件数。デフォルトは1000
   * @param minCount - 結果に含める最小アクセス数。デフォルトは1
   * @param excludeStaticFiles - 静的ファイル（画像、CSS、JSなど）を除外するか。デフォルトはfalse
   * @returns グループ化されたアクセス統計情報のリスト
   * @throws APIリクエストが失敗した場合、または無効なgroupByオプションが指定された場合にエラーをスロー
   */
  async getLogAggregation(
    distributionId: string,
    startDate: string,
    endDate: string,
    groupBy: GroupByOption,
    startTime?: string,
    endTime?: string,
    limit: number = 1000,
    minCount: number = 1,
    excludeStaticFiles: boolean = false,
    clientIp?: string,
    uriPath?: string,
    userAgent?: string,
    referrer?: string,
    queryString?: string
  ): Promise<LogAggregationResponse> {
    try {
      const params = new URLSearchParams({
        profile: this.profile,
        distributionId,
        startDate,
        endDate,
        groupBy,
        limit: limit.toString(),
        minCount: minCount.toString(),
        excludeStaticFiles: excludeStaticFiles.toString(),
      });

      if (startTime) {
        params.append('startTime', startTime);
      }
      if (endTime) {
        params.append('endTime', endTime);
      }
      if (clientIp) {
        params.append('clientIp', clientIp);
      }
      if (uriPath) {
        params.append('uriPath', uriPath);
      }
      if (userAgent) {
        params.append('userAgent', userAgent);
      }
      if (referrer) {
        params.append('referrer', referrer);
      }
      if (queryString) {
        params.append('queryString', queryString);
      }

      const response = await fetch(
        `${API_BASE_URL}/api/cloudfront/logs/aggregation/?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting log aggregation:', error);
      throw error;
    }
  }

  /**
   * ログマークカテゴリ一覧を取得
   *
   * 登録されているログマークカテゴリの一覧を取得します。
   *
   * @returns ログマークカテゴリの配列
   * @throws APIエラーまたはネットワークエラー
   */
  async getLogMarkCategories(): Promise<LogMarkCategory[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/log-mark-categories/`, {
        headers: {
          'X-Profile': this.profile,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching log mark categories:', error);
      throw error;
    }
  }

  /**
   * ログマークカテゴリを作成
   *
   * 新しいログマークカテゴリを登録します。
   *
   * @param category - 作成するカテゴリ情報
   * @returns 作成されたカテゴリ
   * @throws APIエラーまたはネットワークエラー
   */
  async createLogMarkCategory(
    category: Omit<LogMarkCategory, 'id' | 'created_at' | 'updated_at'>
  ): Promise<LogMarkCategory> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/log-mark-categories/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Profile': this.profile,
        },
        body: JSON.stringify(category),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating log mark category:', error);
      throw error;
    }
  }

  /**
   * ログマークカテゴリを更新
   *
   * 指定されたIDのログマークカテゴリを更新します。
   *
   * @param categoryId - 更新するカテゴリのID
   * @param category - 更新するカテゴリ情報
   * @returns 更新されたカテゴリ
   * @throws APIエラーまたはネットワークエラー
   */
  async updateLogMarkCategory(
    categoryId: number,
    category: Omit<LogMarkCategory, 'id' | 'created_at' | 'updated_at'>
  ): Promise<LogMarkCategory> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/log-mark-categories/${categoryId}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Profile': this.profile,
        },
        body: JSON.stringify(category),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating log mark category:', error);
      throw error;
    }
  }

  /**
   * ログマークカテゴリを削除
   *
   * 指定されたIDのログマークカテゴリを削除します。
   * 関連するパターンがある場合は削除できません。
   *
   * @param categoryId - 削除するカテゴリのID
   * @throws APIエラーまたはネットワークエラー
   */
  async deleteLogMarkCategory(categoryId: number): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/log-mark-categories/${categoryId}/`, {
        method: 'DELETE',
        headers: {
          'X-Profile': this.profile,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error deleting log mark category:', error);
      throw error;
    }
  }

  /**
   * ログマークパターンを取得
   *
   * 登録されているログマークパターンの一覧を取得します。
   * オプションでDistribution IDやカテゴリslugでフィルタリングできます。
   *
   * @param distributionId - Distribution IDでフィルタ（オプション）
   * @param category - カテゴリslugでフィルタ（オプション）
   * @returns ログマークパターンの配列
   * @throws APIエラーまたはネットワークエラー
   */
  async getLogMarkPatterns(
    distributionId?: string,
    category?: string
  ): Promise<LogMarkPattern[]> {
    try {
      const params = new URLSearchParams();
      if (distributionId) params.append('distribution_id', distributionId);
      if (category) params.append('category', category);

      const response = await fetch(
        `${API_BASE_URL}/api/log-marks/?${params.toString()}`,
        {
          headers: {
            'X-Profile': this.profile,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching log mark patterns:', error);
      throw error;
    }
  }

  /**
   * ログマークパターンを作成
   *
   * 新しいログマークパターンを登録します。
   * カテゴリIDを指定してログを自動的にマークします。
   *
   * @param pattern - 作成するログマークパターン（category_idを含む）
   * @returns 作成されたログマークパターン
   * @throws APIエラーまたはネットワークエラー
   */
  async createLogMarkPattern(pattern: Omit<LogMarkPattern, 'id' | 'created_at' | 'updated_at' | 'category'>): Promise<LogMarkPattern> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/log-marks/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Profile': this.profile,
        },
        body: JSON.stringify(pattern),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating log mark pattern:', error);
      throw error;
    }
  }

  /**
   * ログマークパターンを更新
   *
   * 指定されたIDのログマークパターンを更新します。
   *
   * @param patternId - 更新するパターンのID
   * @param pattern - 更新するパターン情報（category_idを含む）
   * @returns 更新されたログマークパターン
   * @throws APIエラーまたはネットワークエラー
   */
  async updateLogMarkPattern(
    patternId: number,
    pattern: Omit<LogMarkPattern, 'id' | 'created_at' | 'updated_at' | 'category'>
  ): Promise<LogMarkPattern> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/log-marks/${patternId}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Profile': this.profile,
        },
        body: JSON.stringify(pattern),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      console.error('Error updating log mark pattern:', error);
      throw error;
    }
  }

  /**
   * ログマークパターンを削除
   *
   * 指定されたIDのログマークパターンを削除します。
   *
   * @param patternId - 削除するパターンのID
   * @throws APIエラーまたはネットワークエラー
   */
  async deleteLogMarkPattern(patternId: number): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/log-marks/${patternId}/`, {
        method: 'DELETE',
        headers: {
          'X-Profile': this.profile,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error deleting log mark pattern:', error);
      throw error;
    }
  }
}
