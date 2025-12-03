/**
 * @file アクセスログ詳細表示コンポーネント
 *
 * CloudFrontアクセスログの詳細情報を表示します。
 * IP情報（WHOIS含む）の取得、位置情報の表示、セキュリティチェック機能を提供します。
 *
 * 主な機能:
 * - ログエントリの基本情報表示（日時、IP、ステータス、リクエスト詳細等）
 * - IP情報の取得と表示（地理情報、ISP、WHOIS等）
 * - 地図上での位置表示
 * - セキュリティチェック機能の統合
 * - 折りたたみ可能な詳細ビュー
 */

import { useCallback, useEffect, useState } from 'react';
import { CloudFrontService } from '../services/CloudFrontService';
import type { IPInfo, LogEntry } from '../types';
import { LocationMap } from './LocationMap';
import { SecurityChecks } from './SecurityChecks';

/**
 * AccessLogDetailsコンポーネントのProps
 */
interface AccessLogDetailsProps {
  /** 表示するログエントリ */
  entry: LogEntry;
  /** AWSプロファイル名 */
  profile: string;
  /** CloudFrontディストリビューションID */
  distributionId: string;
  /** チェック対象のURL */
  targetUrl: string;
  /** 初期表示時に詳細を展開するかどうか（デフォルト: false） */
  initiallyExpanded?: boolean;
}

/**
 * アクセスログ詳細表示コンポーネント
 *
 * CloudFrontアクセスログエントリの詳細情報を表示します。
 * サマリーセクションは常に表示され、詳細セクションは折りたたみ可能です。
 * IP情報は初回展開時に自動取得されます。
 *
 * @param props - コンポーネントのProps
 * @param props.entry - 表示するログエントリ
 * @param props.profile - AWSプロファイル名
 * @param props.distributionId - CloudFrontディストリビューションID
 * @param props.targetUrl - チェック対象のURL
 * @param props.initiallyExpanded - 初期表示時に詳細を展開するか
 * @returns アクセスログ詳細UI
 */
export function AccessLogDetails({
  entry,
  profile,
  distributionId,
  targetUrl,
  initiallyExpanded = false,
}: AccessLogDetailsProps) {
  const [isExpanded, setIsExpanded] = useState(initiallyExpanded);
  const [ipInfo, setIpInfo] = useState<IPInfo | null>(entry.ipInfo || null);
  const [isLoadingIpInfo, setIsLoadingIpInfo] = useState(false);
  const [ipInfoError, setIpInfoError] = useState<string | null>(null);
  const [hasAttemptedAutoFetch, setHasAttemptedAutoFetch] = useState(false);

  /**
   * 日時フォーマット関数
   *
   * バックエンドから返されるJST形式の日付と時刻をUTCとJST両方の形式にフォーマットします。
   * バックエンドはログのUTC時刻を既にJSTに変換して返すため、
   * UTC表示用にはJSTから9時間引く必要があります。
   *
   * @param date - 日付文字列（YYYY-MM-DD形式、JST）
   * @param time - 時刻文字列（HH:MM:SS形式、JST）
   * @returns UTC形式とJST形式の日時オブジェクト
   */
  const formatDateTime = (date: string, time: string) => {
    // バックエンドからの日時は既にJST
    const jstString = `${date} ${time}`;

    // JSTからUTCに変換（-9時間）
    const jstDateTime = new Date(`${date}T${time}+09:00`);
    const utcString = jstDateTime.toISOString().replace('T', ' ').slice(0, 19);

    return {
      utc: utcString,
      jst: jstString,
    };
  };

  const dateTime = formatDateTime(entry.date, entry.time);

  /**
   * IP情報を取得する関数
   *
   * 指定されたIPアドレスの詳細情報（地理情報、ISP、WHOIS等）をバックエンドから取得します。
   * WHOISデータが既に存在する場合は再取得をスキップします。
   */
  const handleFetchIpInfo = useCallback(async () => {
    // WHOISデータを持つipInfoがある場合は再取得不要
    // 注：whoisはnull（未試行）、{}（試行したが失敗）、またはデータを持つオブジェクト（成功）のいずれか
    if (ipInfo?.whois && Object.keys(ipInfo.whois).length > 0) {
      return; // Already loaded with WHOIS
    }

    setIsLoadingIpInfo(true);
    setIpInfoError(null);

    try {
      const service = new CloudFrontService(profile);
      const data = await service.getIPInfo(entry.clientIp);
      setIpInfo(data);
    } catch (err) {
      setIpInfoError(err instanceof Error ? err.message : 'Failed to fetch IP info');
    } finally {
      setIsLoadingIpInfo(false);
    }
  }, [profile, entry.clientIp, ipInfo]);

  // 初回展開時にIP情報（WHOISを含む）を自動取得
  useEffect(() => {
    if (isExpanded && !hasAttemptedAutoFetch) {
      setHasAttemptedAutoFetch(true);
      // WHOISデータがまだない場合のみ自動取得
      const hasWhoisData = ipInfo?.whois && Object.keys(ipInfo.whois).length > 0;
      if (!hasWhoisData) {
        handleFetchIpInfo();
      }
    }
  }, [isExpanded, hasAttemptedAutoFetch, handleFetchIpInfo, ipInfo]);

  /**
   * 重要度に応じた背景色クラスを取得
   *
   * @param severity - 重要度レベル（danger、warning、またはundefined）
   * @returns Tailwind CSSクラス名
   */
  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'danger':
        return 'bg-red-50 border-red-400';
      case 'warning':
        return 'bg-yellow-50 border-yellow-400';
      default:
        return 'bg-white border-gray-200';
    }
  };

  /**
   * 重要度に応じたバッジ色クラスを取得
   *
   * @param severity - 重要度レベル（danger、warning、またはundefined）
   * @returns Tailwind CSSクラス名
   */
  const getBadgeColor = (severity?: string) => {
    switch (severity) {
      case 'danger':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  return (
    <div
      className={`shadow rounded-lg mb-4 border ${getSeverityColor(entry.suspiciousCheck?.severity)}`}
    >
      {/* サマリーセクション - 常に表示 */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-sm font-medium text-gray-900">{dateTime.jst}</span>
              <span className="text-xs font-mono text-gray-600">{entry.clientIp}</span>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  entry.statusCode === 200
                    ? 'bg-green-100 text-green-800'
                    : entry.statusCode >= 400
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                {entry.statusCode}
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {entry.method}
              </span>
              {entry.suspiciousCheck?.isSuspicious && (
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getBadgeColor(entry.suspiciousCheck.severity)}`}
                >
                  {entry.suspiciousCheck.isBlocked
                    ? '🚫 Blocked'
                    : entry.suspiciousCheck.severity === 'warning'
                      ? '⚠️ Suspicious'
                      : '✓ Safe'}
                </span>
              )}
              {ipInfo?.country && (
                <span className="text-xs text-gray-500">
                  {ipInfo.country} ({ipInfo.countryCode})
                </span>
              )}
            </div>
            <div className="text-xs text-gray-600 font-mono truncate">{entry.uriStem}</div>
          </div>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="ml-4 px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
          >
            {isExpanded ? '詳細を閉じる ▲' : '詳細を見る ▼'}
          </button>
        </div>
      </div>

      {/* 詳細セクション - 折りたたみ可能 */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">
                Basic Information
              </h3>

              <div>
                <span className="text-sm font-medium text-gray-500">Date/Time (UTC):</span>
                <p className="text-sm text-gray-900">{dateTime.utc}</p>
              </div>

              <div>
                <span className="text-sm font-medium text-gray-500">Date/Time (JST):</span>
                <p className="text-sm text-gray-900 font-medium">{dateTime.jst}</p>
              </div>

              <div>
                <span className="text-sm font-medium text-gray-500">Client IP:</span>
                <div className="flex items-center gap-2">
                  <p className="text-sm text-gray-900 font-mono">{entry.clientIp}</p>
                  {/* Show button if: no ipInfo, no WHOIS data (null or empty object), or not loading */}
                  {!isLoadingIpInfo &&
                    (!ipInfo ||
                      !ipInfo.whois ||
                      (ipInfo.whois && Object.keys(ipInfo.whois).length === 0)) && (
                      <button
                        type="button"
                        onClick={handleFetchIpInfo}
                        className="px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded border border-blue-300"
                      >
                        {ipInfo ? 'WHOIS取得' : '詳細確認'}
                      </button>
                    )}
                  {isLoadingIpInfo && <span className="text-xs text-gray-500">読み込み中...</span>}
                </div>
                {ipInfoError && <p className="mt-1 text-xs text-red-600">{ipInfoError}</p>}
                {ipInfo && (
                  <div className="mt-2 text-xs text-gray-600 space-y-1 bg-blue-50 p-3 rounded">
                    {/* 位置情報 */}
                    {ipInfo.continent && (
                      <p>
                        <span className="font-medium">Continent:</span> {ipInfo.continent} (
                        {ipInfo.continentCode})
                      </p>
                    )}
                    {ipInfo.country && (
                      <p>
                        <span className="font-medium">Country:</span> {ipInfo.country} (
                        {ipInfo.countryCode})
                      </p>
                    )}
                    {ipInfo.city && (
                      <p>
                        <span className="font-medium">City:</span> {ipInfo.city}
                        {ipInfo.region && `, ${ipInfo.region}`}
                        {ipInfo.district && ` - ${ipInfo.district}`}
                      </p>
                    )}
                    {ipInfo.zip && (
                      <p>
                        <span className="font-medium">Postal Code:</span> {ipInfo.zip}
                      </p>
                    )}
                    {ipInfo.lat !== undefined && ipInfo.lon !== undefined && (
                      <>
                        <p>
                          <span className="font-medium">Coordinates:</span> {ipInfo.lat},{' '}
                          {ipInfo.lon}
                        </p>
                        <LocationMap lat={ipInfo.lat} lon={ipInfo.lon} city={ipInfo.city} />
                      </>
                    )}

                    {/* タイムゾーンと通貨 */}
                    {ipInfo.timezone && (
                      <p>
                        <span className="font-medium">Timezone:</span> {ipInfo.timezone}
                        {ipInfo.offset !== undefined &&
                          ` (UTC${ipInfo.offset >= 0 ? '+' : ''}${ipInfo.offset / 3600})`}
                      </p>
                    )}
                    {ipInfo.currency && (
                      <p>
                        <span className="font-medium">Currency:</span> {ipInfo.currency}
                      </p>
                    )}

                    {/* ネットワーク情報 */}
                    {ipInfo.isp && (
                      <p>
                        <span className="font-medium">ISP:</span> {ipInfo.isp}
                      </p>
                    )}
                    {ipInfo.org && (
                      <p>
                        <span className="font-medium">Organization:</span> {ipInfo.org}
                      </p>
                    )}
                    {ipInfo.asn && (
                      <p>
                        <span className="font-medium">ASN:</span> {ipInfo.asn}
                      </p>
                    )}
                    {ipInfo.asname && (
                      <p>
                        <span className="font-medium">AS Name:</span> {ipInfo.asname}
                      </p>
                    )}

                    {/* 接続タイプフラグ */}
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {ipInfo.mobile && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          📱 Mobile
                        </span>
                      )}
                      {ipInfo.proxy && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
                          🔒 Proxy
                        </span>
                      )}
                      {ipInfo.hosting && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-cyan-100 text-cyan-800">
                          🖥️ Hosting
                        </span>
                      )}
                    </div>

                    {/* WHOIS情報 */}
                    {ipInfo.whois && Object.keys(ipInfo.whois).length > 0 && (
                      <div className="mt-3 pt-3 border-t border-blue-200">
                        <p className="font-medium text-gray-700 mb-2">WHOIS Information:</p>
                        {ipInfo.whois.netname && (
                          <p>
                            <span className="font-medium">Network Name:</span>{' '}
                            {ipInfo.whois.netname}
                          </p>
                        )}
                        {ipInfo.whois.org_name && (
                          <p>
                            <span className="font-medium">Organization:</span>{' '}
                            {ipInfo.whois.org_name}
                          </p>
                        )}
                        {ipInfo.whois.country && (
                          <p>
                            <span className="font-medium">Country:</span> {ipInfo.whois.country}
                          </p>
                        )}
                        {ipInfo.whois.net_range && (
                          <p>
                            <span className="font-medium">Network Range:</span>{' '}
                            {ipInfo.whois.net_range}
                          </p>
                        )}
                        {ipInfo.whois.raw && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-blue-600 hover:text-blue-800 font-medium">
                              View Raw WHOIS Data
                            </summary>
                            <pre className="mt-2 text-xs bg-gray-800 text-gray-100 p-3 rounded overflow-x-auto whitespace-pre-wrap">
                              {ipInfo.whois.raw}
                            </pre>
                          </details>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div>
                <span className="text-sm font-medium text-gray-500">Method:</span>
                <p className="text-sm">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {entry.method}
                  </span>
                </p>
              </div>

              <div>
                <span className="text-sm font-medium text-gray-500">Status:</span>
                <p className="text-sm">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      entry.statusCode === 200
                        ? 'bg-green-100 text-green-800'
                        : entry.statusCode >= 400
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {entry.statusCode}
                  </span>
                </p>
              </div>

              <div>
                <span className="text-sm font-medium text-gray-500">Edge Location:</span>
                <p className="text-sm text-gray-900">{entry.edgeLocation}</p>
              </div>

              <div>
                <span className="text-sm font-medium text-gray-500">Cache Status:</span>
                <p className="text-sm">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      entry.cacheStatus === 'Hit'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {entry.cacheStatus}
                  </span>
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Request Details</h3>

              <div>
                <span className="text-sm font-medium text-gray-500">Host:</span>
                <p className="text-sm text-gray-900 font-mono break-all">{entry.host}</p>
              </div>

              <div>
                <span className="text-sm font-medium text-gray-500">URI:</span>
                <p className="text-sm text-gray-900 font-mono break-all">{entry.uriStem}</p>
              </div>

              {entry.queryString && entry.queryString !== '-' && (
                <div>
                  <span className="text-sm font-medium text-gray-500">Query String:</span>
                  <p className="text-xs text-gray-700 font-mono break-all bg-gray-50 p-2 rounded">
                    {decodeURIComponent(entry.queryString)}
                  </p>
                </div>
              )}

              {entry.referrer && entry.referrer !== '-' && (
                <div>
                  <span className="text-sm font-medium text-gray-500">Referrer:</span>
                  <p className="text-xs text-gray-700 font-mono break-all">{entry.referrer}</p>
                </div>
              )}

              <div>
                <span className="text-sm font-medium text-gray-500">User Agent:</span>
                <p className="text-xs text-gray-700 break-all bg-gray-50 p-2 rounded">
                  {entry.userAgent}
                </p>
                {/* Mark buttons */}
                {entry.mark ? (
                  <div
                    className="mt-2 p-2 rounded border"
                    style={{
                      backgroundColor: `${entry.mark.category.color}15`,
                      borderColor: `${entry.mark.category.color}40`,
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                          style={{
                            backgroundColor: `${entry.mark.category.color}20`,
                            color: entry.mark.category.color,
                          }}
                        >
                          {entry.mark.category.name}
                        </span>
                        {entry.mark.note && (
                          <span className="text-xs text-gray-600">({entry.mark.note})</span>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="mt-2 text-xs text-gray-500">
                    マークするにはログマーク管理画面からパターンを追加してください
                  </div>
                )}
              </div>

              <div>
                <span className="text-sm font-medium text-gray-500">Protocol:</span>
                <p className="text-sm text-gray-900">{entry.protocol}</p>
              </div>

              <div>
                <span className="text-sm font-medium text-gray-500">Bytes:</span>
                <p className="text-sm text-gray-900">{entry.bytes.toLocaleString()} bytes</p>
              </div>
            </div>
          </div>

          {/* 疑わしいチェックセクション */}
          {entry.suspiciousCheck && (
            <div className="mt-6 border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 border-b pb-2 mb-4">
                Suspicious Check Results
              </h3>

              <div className="space-y-4">
                {/* 全体的なステータス */}
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium text-gray-700">Overall Status:</span>
                  <span
                    className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium ${getBadgeColor(entry.suspiciousCheck.severity)}`}
                  >
                    {entry.suspiciousCheck.isBlocked
                      ? '🚫 Blocked'
                      : entry.suspiciousCheck.isAllowedBot
                        ? '✅ Allowed Bot'
                        : entry.suspiciousCheck.isSuspicious
                          ? '⚠️ Suspicious'
                          : '✓ Safe'}
                  </span>
                  <span
                    className={`text-sm font-medium ${
                      entry.suspiciousCheck.severity === 'danger'
                        ? 'text-red-600'
                        : entry.suspiciousCheck.severity === 'warning'
                          ? 'text-yellow-600'
                          : 'text-green-600'
                    }`}
                  >
                    Severity: {entry.suspiciousCheck.severity.toUpperCase()}
                  </span>
                </div>

                {/* マッチしたパターン */}
                {entry.suspiciousCheck.matchedPatterns.length > 0 && (
                  <div>
                    <span className="text-sm font-medium text-gray-700 block mb-2">
                      Matched Patterns:
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 bg-gray-50 p-3 rounded">
                      {entry.suspiciousCheck.matchedPatterns.map((pattern) => (
                        <li key={pattern}>{pattern}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 詳細なチェック */}
                {entry.suspiciousCheck.details && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    {/* User Agentチェック */}
                    {entry.suspiciousCheck.details.userAgent.matched_patterns.length > 0 && (
                      <div className="bg-gray-50 p-3 rounded">
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">User Agent</h4>
                        <ul className="list-disc list-inside space-y-1 text-xs text-gray-600">
                          {entry.suspiciousCheck.details.userAgent.matched_patterns.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Referrerチェック */}
                    {entry.suspiciousCheck.details.referrer.matched_patterns.length > 0 && (
                      <div className="bg-gray-50 p-3 rounded">
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">Referrer</h4>
                        <ul className="list-disc list-inside space-y-1 text-xs text-gray-600">
                          {entry.suspiciousCheck.details.referrer.matched_patterns.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* パスチェック */}
                    {entry.suspiciousCheck.details.path.matched_patterns.length > 0 && (
                      <div className="bg-gray-50 p-3 rounded">
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">Request Path</h4>
                        <ul className="list-disc list-inside space-y-1 text-xs text-gray-600">
                          {entry.suspiciousCheck.details.path.matched_patterns.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* IPチェック */}
                    {entry.suspiciousCheck.details.ip.matched_patterns.length > 0 && (
                      <div className="bg-gray-50 p-3 rounded">
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">IP Patterns</h4>
                        <ul className="list-disc list-inside space-y-1 text-xs text-gray-600">
                          {entry.suspiciousCheck.details.ip.matched_patterns.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 高度なセキュリティチェック */}
          <div className="mt-6 border-t border-gray-200 pt-6">
            <SecurityChecks
              entry={entry}
              profile={profile}
              distributionId={distributionId}
              targetUrl={targetUrl}
            />
          </div>
        </div>
      )}
    </div>
  );
}
