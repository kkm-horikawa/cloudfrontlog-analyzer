/**
 * @fileoverview CloudFrontアクセスログ解析のメインコンポーネント
 *
 * このコンポーネントは、CloudFrontディストリビューションの選択、
 * ログ検索条件の指定、およびログ検索結果の表示を行います。
 * AWS CLIプロファイルを使用してCloudFront APIにアクセスし、
 * S3に保存されたアクセスログを検索・解析します。
 */

import { format } from 'date-fns';
import { useState } from 'react';
import { CloudFrontService } from '../services/CloudFrontService';
import type { LogEntry } from '../types';
import { AccessLogDetails } from './AccessLogDetails';

/**
 * CloudFrontアクセスログ解析のメインコンポーネント
 *
 * 以下の機能を提供します：
 * 1. AWSプロファイルの設定
 * 2. CloudFrontディストリビューション一覧の取得と選択
 * 3. ログ検索条件の指定（URL、日時、時間幅）
 * 4. ログエントリの検索と結果表示
 *
 * @returns {JSX.Element} CloudFrontAnalyzerコンポーネント
 */
export default function CloudFrontAnalyzer() {
  const [profile, setProfile] = useState('default');
  const [distributionId, setDistributionId] = useState('');
  const [targetUrl, setTargetUrl] = useState('/nattoku/special/');
  const [targetDate, setTargetDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [targetTime, setTargetTime] = useState('12:00');
  const [timeWindow, setTimeWindow] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [distributions, setDistributions] = useState<
    Array<{ id: string; domain: string; aliases?: string[] }>
  >([]);

  /**
   * CloudFrontディストリビューション一覧を読み込みます
   *
   * 指定されたAWSプロファイルを使用してCloudFront APIにアクセスし、
   * 利用可能なディストリビューションの一覧を取得します。
   * 取得したディストリビューション情報（ID、ドメイン、エイリアス）を
   * ステートに保存し、選択可能な形式で表示します。
   *
   * @async
   * @returns {Promise<void>}
   * @throws {Error} ディストリビューションの取得に失敗した場合
   */
  const handleLoadDistributions = async () => {
    setLoading(true);
    setError(null);
    try {
      const service = new CloudFrontService(profile);
      const dists = await service.listDistributions();
      setDistributions(dists);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load distributions');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 指定された条件でCloudFrontアクセスログを検索します
   *
   * 以下の条件を基にS3に保存されたアクセスログを検索します：
   * - ディストリビューションID
   * - 対象URLパス
   * - 検索日時（JST）
   * - 検索時間幅（指定時刻の前後±分）
   *
   * 検索結果はLogEntry配列としてステートに保存され、
   * AccessLogDetailsコンポーネントで詳細表示されます。
   *
   * @async
   * @returns {Promise<void>}
   * @throws {Error} ログ検索に失敗した場合
   */
  const handleSearch = async () => {
    if (!distributionId || !targetUrl || !targetDate || !targetTime) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError(null);
    setLogEntries([]);

    try {
      const service = new CloudFrontService(profile);
      const dateTime = new Date(`${targetDate}T${targetTime}:00`);
      const entries = await service.searchLogs(distributionId, targetUrl, dateTime, timeWindow);
      setLogEntries(entries);

      if (entries.length === 0) {
        setError('No log entries found for the specified criteria');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search logs');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* AWS設定 */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">AWS Configuration</h2>
        <div className="space-y-4">
          <div>
            <label htmlFor="profile" className="block text-sm font-medium text-gray-700 mb-1">
              AWS Profile:
            </label>
            <input
              id="profile"
              type="text"
              value={profile}
              onChange={(e) => setProfile(e.target.value)}
              placeholder="e.g., default"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            type="button"
            onClick={handleLoadDistributions}
            disabled={loading}
            className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Loading...' : 'Load Distributions'}
          </button>
        </div>
      </div>

      {/* ディストリビューションを選択 */}
      {distributions.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Distribution</h2>
          <div>
            <label htmlFor="distribution" className="block text-sm font-medium text-gray-700 mb-1">
              Distribution:
            </label>
            <select
              id="distribution"
              value={distributionId}
              onChange={(e) => setDistributionId(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">-- Select a distribution --</option>
              {distributions.map((dist) => {
                const displayName =
                  dist.aliases && dist.aliases.length > 0
                    ? `${dist.aliases[0]} (${dist.domain})`
                    : dist.domain;
                return (
                  <option key={dist.id} value={dist.id}>
                    {displayName}
                  </option>
                );
              })}
            </select>
          </div>
        </div>
      )}

      {/* 検索条件 */}
      {distributionId && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Search Criteria</h2>
          <div className="space-y-4">
            <div>
              <label htmlFor="targetUrl" className="block text-sm font-medium text-gray-700 mb-1">
                Target URL Path:
              </label>
              <input
                id="targetUrl"
                type="text"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="e.g., /nattoku/special/91265/77164/"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="targetDate"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Date (JST):
                </label>
                <input
                  id="targetDate"
                  type="date"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label
                  htmlFor="targetTime"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Time (JST):
                </label>
                <input
                  id="targetTime"
                  type="time"
                  value={targetTime}
                  onChange={(e) => setTargetTime(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <label htmlFor="timeWindow" className="block text-sm font-medium text-gray-700 mb-1">
                Search Window (minutes):
              </label>
              <input
                id="timeWindow"
                type="number"
                min="1"
                max="60"
                value={timeWindow}
                onChange={(e) => setTimeWindow(Number(e.target.value))}
                className="block w-full sm:w-32 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Searches ±{timeWindow} minutes around the specified time
              </p>
            </div>

            <button
              type="button"
              onClick={handleSearch}
              disabled={loading}
              className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Searching...' : 'Search Logs'}
            </button>
          </div>
        </div>
      )}

      {/* エラーメッセージ */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-label="Error icon"
              >
                <title>Error</title>
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                <strong className="font-medium">Error:</strong> {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 検索結果 */}
      {logEntries.length > 0 && (
        <div className="space-y-4">
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
            <p className="text-sm text-blue-700">
              <strong className="font-medium">Results:</strong> Found {logEntries.length} log{' '}
              {logEntries.length === 1 ? 'entry' : 'entries'}
            </p>
          </div>
          {logEntries.map((entry, index) => (
            <AccessLogDetails
              key={
                entry.edgeRequestId ||
                `${entry.date}-${entry.time}-${entry.clientIp}-${entry.uriStem}-${index}`
              }
              entry={entry}
              profile={profile}
              distributionId={distributionId}
              targetUrl={targetUrl}
            />
          ))}
        </div>
      )}
    </div>
  );
}
