/**
 * @fileoverview CloudFrontログを集計して統計情報を表示するコンポーネント
 *
 * このファイルは、CloudFrontのアクセスログを様々な単位で集計し、
 * 統計情報を表示するコンポーネントを提供します。
 * IPアドレス、User Agent、Referrer、Query Stringなどで集計でき、
 * 各集計値の詳細ログも表示できます。
 *
 * 主な機能:
 * - 複数の集計単位のサポート（IP、User Agent、Referrer、Query String）
 * - リクエスト数、ステータスコード分布、ユニークパス数の表示
 * - 日本のみフィルター、静的ファイル除外などの高度なフィルタリング
 * - 集計結果から詳細ログへのドリルダウン
 */
import { format } from 'date-fns';
import { useEffect, useState } from 'react';
import { CloudFrontService } from '../services/CloudFrontService';
import type {
  AggregationItem,
  GroupByOption,
  LogAggregationResponse,
  LogEntry,
  LogMarkCategory,
  MarkDetails,
  MarkStats,
  RawLogsResponse,
} from '../types';
import { LogDetailModal } from './LogDetailModal';
import { MarkDetailsModal } from './MarkDetailsModal';

/**
 * CloudFrontログを集計して統計情報を表示するメインコンポーネント
 *
 * 指定された集計単位（IP、User Agent、Referrerなど）でログを集計し、
 * リクエスト数、ステータス分布、ユニークパス数などの統計情報を表示します。
 * 集計結果から詳細なログ一覧にドリルダウンすることもできます。
 *
 * @returns LogAggregationコンポーネント
 */
export default function LogAggregation() {
  const [profile, setProfile] = useState('default');
  const [distributionId, setDistributionId] = useState('');
  const [startDate, setStartDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [endDate, setEndDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [groupBy, setGroupBy] = useState<GroupByOption>('ip');
  const [limit, setLimit] = useState(1000);
  const [minCount, setMinCount] = useState(1);
  const [excludeStaticFiles, setExcludeStaticFiles] = useState(false);
  const [filterJapanOnly, setFilterJapanOnly] = useState(false);
  // カテゴリ除外フィルタ
  const [categories, setCategories] = useState<LogMarkCategory[]>([]);
  const [excludedCategories, setExcludedCategories] = useState<Set<string>>(new Set());
  // フィルタ用のstate
  const [clientIp, setClientIp] = useState('');
  const [uriPath, setUriPath] = useState('');
  const [userAgent, setUserAgent] = useState('');
  const [referrer, setReferrer] = useState('');
  const [queryString, setQueryString] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aggregationResponse, setAggregationResponse] = useState<LogAggregationResponse | null>(
    null
  );
  const [distributions, setDistributions] = useState<
    Array<{ id: string; domain: string; aliases?: string[] }>
  >([]);

  // 詳細表示の状態
  const [viewMode, setViewMode] = useState<'summary' | 'detail'>('summary');
  const [selectedValue, setSelectedValue] = useState<string | null>(null);
  const [detailLogs, setDetailLogs] = useState<RawLogsResponse | null>(null);
  const [detailPage, setDetailPage] = useState(1);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);

  // マーク内訳モーダルの状態
  const [markDetailsModal, setMarkDetailsModal] = useState<{
    isOpen: boolean;
    markType: string;
    markStats: MarkStats;
    markDetails: MarkDetails;
    totalRequests: number;
    sourceLabel?: string;
  }>({
    isOpen: false,
    markType: '',
    markStats: { unmarked: 0 },
    markDetails: {},
    totalRequests: 0,
  });

  /**
   * CloudFront Distributionリストを取得する
   *
   * 指定されたAWSプロファイルを使用して、利用可能な
   * CloudFront Distributionの一覧を取得します。
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
   * ログマークカテゴリを読み込む
   */
  const loadCategories = async () => {
    try {
      const service = new CloudFrontService(profile);
      const cats = await service.getLogMarkCategories();
      setCategories(cats);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  // 初期ロード時にカテゴリを取得
  useEffect(() => {
    loadCategories();
  }, [profile]);

  /**
   * カテゴリ除外の切り替え
   */
  const toggleExcludeCategory = (slug: string) => {
    setExcludedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(slug)) {
        newSet.delete(slug);
      } else {
        newSet.add(slug);
      }
      return newSet;
    });
  };

  /**
   * 指定された条件でログを集計する
   *
   * 選択された集計単位（IP、User Agent、Referrer、Query String）で
   * ログを集計し、統計情報を取得します。
   */
  const handleAggregation = async () => {
    if (!distributionId || !startDate || !endDate) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError(null);
    setAggregationResponse(null);
    setViewMode('summary');

    try {
      const service = new CloudFrontService(profile);
      const response = await service.getLogAggregation(
        distributionId,
        startDate,
        endDate,
        groupBy,
        startTime || undefined,
        endTime || undefined,
        limit,
        minCount,
        excludeStaticFiles,
        clientIp || undefined,
        uriPath || undefined,
        userAgent || undefined,
        referrer || undefined,
        queryString || undefined
      );
      setAggregationResponse(response);

      if (response.aggregations.length === 0) {
        setError('No aggregation results found for the specified criteria');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to aggregate logs');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 集計結果の特定値の詳細ログを表示する
   *
   * @param value - 詳細を表示する集計値（IPアドレス、User Agentなど）
   */
  const handleViewDetail = async (value: string) => {
    setSelectedValue(value);
    setViewMode('detail');
    setDetailPage(1);
    await loadDetailLogs(value, 1);
  };

  /**
   * 指定された集計値の詳細ログを取得する
   *
   * @param value - 詳細ログを取得する集計値
   * @param page - 取得するページ番号
   */
  const loadDetailLogs = async (value: string, page: number) => {
    setLoading(true);
    setError(null);

    try {
      const service = new CloudFrontService(profile);

      // groupByに基づいてフィルターパラメータを構築
      let clientIp: string | undefined;
      let userAgent: string | undefined;
      let referrer: string | undefined;
      let queryString: string | undefined;

      if (groupBy === 'ip') {
        clientIp = value;
      } else if (groupBy === 'user_agent') {
        userAgent = value;
      } else if (groupBy === 'referrer') {
        referrer = value;
      } else if (groupBy === 'query_string') {
        queryString = value;
      }

      const response = await service.listRawLogs(
        distributionId,
        startDate,
        endDate,
        clientIp,
        undefined,
        userAgent,
        referrer,
        queryString,
        startTime || undefined,
        endTime || undefined,
        page,
        1000
      );

      setDetailLogs(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load detail logs');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 詳細ログの次のページを表示する
   */
  const handleDetailNextPage = () => {
    if (detailLogs && selectedValue && detailPage < detailLogs.pagination.totalPages) {
      const newPage = detailPage + 1;
      setDetailPage(newPage);
      loadDetailLogs(selectedValue, newPage);
    }
  };

  /**
   * 詳細ログの前のページを表示する
   */
  const handleDetailPrevPage = () => {
    if (selectedValue && detailPage > 1) {
      const newPage = detailPage - 1;
      setDetailPage(newPage);
      loadDetailLogs(selectedValue, newPage);
    }
  };

  /**
   * 詳細ビューから集計結果サマリーに戻る
   */
  const handleBackToSummary = () => {
    setViewMode('summary');
    setSelectedValue(null);
    setDetailLogs(null);
    setDetailPage(1);
  };

  /**
   * マーク内訳モーダルを開く
   */
  const handleOpenMarkDetails = (
    markType: string,
    markStats: MarkStats,
    markDetails: MarkDetails,
    totalRequests: number,
    sourceLabel?: string
  ) => {
    setMarkDetailsModal({
      isOpen: true,
      markType,
      markStats,
      markDetails,
      totalRequests,
      sourceLabel,
    });
  };

  /**
   * マーク内訳モーダルを閉じる
   */
  const handleCloseMarkDetails = () => {
    setMarkDetailsModal((prev) => ({ ...prev, isOpen: false }));
  };

  /**
   * 集計単位の表示ラベルを取得する
   *
   * @param groupByValue - 集計単位のオプション
   * @returns 日本語の表示ラベル
   */
  const getGroupByLabel = (groupByValue: GroupByOption): string => {
    const labels: Record<GroupByOption, string> = {
      ip: 'IPアドレス',
      user_agent: 'User Agent',
      referrer: 'Referrer',
      query_string: 'Query String',
    };
    return labels[groupByValue];
  };

  /**
   * ステータスコード分布を色付きバッジで表示する
   *
   * ステータスコードの範囲に応じて異なる色のバッジで表示します。
   * 最大5件まで表示します。
   *
   * @param statusDist - ステータスコードとその出現回数のマップ
   * @returns レンダリングされたステータス分布バッジ
   */
  const renderStatusDistribution = (statusDist: Record<string, number>) => {
    const entries = Object.entries(statusDist)
      .sort(([a], [b]) => Number(a) - Number(b))
      .slice(0, 5);

    return entries.map(([status, count]) => (
      <span
        key={status}
        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mr-1 ${
          Number(status) >= 200 && Number(status) < 300
            ? 'bg-green-100 text-green-800'
            : Number(status) >= 300 && Number(status) < 400
              ? 'bg-blue-100 text-blue-800'
              : Number(status) >= 400 && Number(status) < 500
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
        }`}
      >
        {status}: {count.toLocaleString()}
      </span>
    ));
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

      {/* 集計条件 */}
      {distributionId && viewMode === 'summary' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Aggregation Criteria</h2>
          <div className="space-y-4">
            {/* グループ化選択 */}
            <div>
              <label htmlFor="groupBy" className="block text-sm font-medium text-gray-700 mb-1">
                集計単位:
              </label>
              <select
                id="groupBy"
                value={groupBy}
                onChange={(e) => setGroupBy(e.target.value as GroupByOption)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="ip">IPアドレス</option>
                <option value="user_agent">User Agent</option>
                <option value="referrer">Referrer</option>
                <option value="query_string">Query String</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">ログを集計する単位を選択してください</p>
            </div>

            {/* 日付範囲 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date:
                </label>
                <input
                  id="startDate"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-1">
                  End Date:
                </label>
                <input
                  id="endDate"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* 時間範囲（任意） */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="startTime" className="block text-sm font-medium text-gray-700 mb-1">
                  Start Time (JST, optional):
                </label>
                <input
                  id="startTime"
                  type="time"
                  step="1"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="endTime" className="block text-sm font-medium text-gray-700 mb-1">
                  End Time (JST, optional):
                </label>
                <input
                  id="endTime"
                  type="time"
                  step="1"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* 詳細フィルタ（任意） */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">詳細フィルタ (任意)</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="clientIp" className="block text-sm font-medium text-gray-700 mb-1">
                    Client IP:
                  </label>
                  <input
                    id="clientIp"
                    type="text"
                    value={clientIp}
                    onChange={(e) => setClientIp(e.target.value)}
                    placeholder="例: 192.168.1.1"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">完全一致</p>
                </div>

                <div>
                  <label htmlFor="uriPath" className="block text-sm font-medium text-gray-700 mb-1">
                    URI Path:
                  </label>
                  <input
                    id="uriPath"
                    type="text"
                    value={uriPath}
                    onChange={(e) => setUriPath(e.target.value)}
                    placeholder="例: /api/"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">部分一致</p>
                </div>

                <div>
                  <label htmlFor="userAgent" className="block text-sm font-medium text-gray-700 mb-1">
                    User Agent:
                  </label>
                  <input
                    id="userAgent"
                    type="text"
                    value={userAgent}
                    onChange={(e) => setUserAgent(e.target.value)}
                    placeholder="例: Mozilla/5.0..."
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">完全一致</p>
                </div>

                <div>
                  <label htmlFor="referrer" className="block text-sm font-medium text-gray-700 mb-1">
                    Referrer:
                  </label>
                  <input
                    id="referrer"
                    type="text"
                    value={referrer}
                    onChange={(e) => setReferrer(e.target.value)}
                    placeholder="例: google.com"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">部分一致</p>
                </div>

                <div className="sm:col-span-2">
                  <label htmlFor="queryString" className="block text-sm font-medium text-gray-700 mb-1">
                    Query String:
                  </label>
                  <input
                    id="queryString"
                    type="text"
                    value={queryString}
                    onChange={(e) => setQueryString(e.target.value)}
                    placeholder="例: utm_source=google"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">部分一致</p>
                </div>
              </div>
            </div>

            {/* フィルタ */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="limit" className="block text-sm font-medium text-gray-700 mb-1">
                  表示件数 (Top N):
                </label>
                <input
                  id="limit"
                  type="number"
                  min="1"
                  max="100000"
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">最大100,000件まで</p>
              </div>

              <div>
                <label htmlFor="minCount" className="block text-sm font-medium text-gray-700 mb-1">
                  最小リクエスト数:
                </label>
                <input
                  id="minCount"
                  type="number"
                  min="1"
                  value={minCount}
                  onChange={(e) => setMinCount(Number(e.target.value))}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">この値以上のリクエスト数のみ表示</p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <div className="flex items-center">
                <input
                  id="excludeStaticFiles"
                  type="checkbox"
                  checked={excludeStaticFiles}
                  onChange={(e) => setExcludeStaticFiles(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="excludeStaticFiles" className="ml-2 block text-sm text-gray-700">
                  静的ファイルを除外 (js, css, 画像など)
                </label>
              </div>

              {groupBy === 'ip' && (
                <div className="flex items-center">
                  <input
                    id="filterJapanOnly"
                    type="checkbox"
                    checked={filterJapanOnly}
                    onChange={(e) => setFilterJapanOnly(e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="filterJapanOnly" className="ml-2 block text-sm text-gray-700">
                    日本からのアクセスのみ表示
                  </label>
                </div>
              )}

              {/* カテゴリ除外フィルタ */}
              {categories.length > 0 && (
                <div className="flex items-center flex-wrap gap-2">
                  <span className="text-sm text-gray-700">除外:</span>
                  {categories.map((cat) => (
                    <label
                      key={cat.id}
                      className={`inline-flex items-center px-2 py-1 rounded-md cursor-pointer border transition-colors ${
                        excludedCategories.has(cat.slug)
                          ? 'border-gray-400 bg-gray-100'
                          : 'border-gray-200 bg-white hover:bg-gray-50'
                      }`}
                      style={{
                        borderColor: excludedCategories.has(cat.slug) ? cat.color : undefined,
                        backgroundColor: excludedCategories.has(cat.slug) ? `${cat.color}20` : undefined,
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={excludedCategories.has(cat.slug)}
                        onChange={() => toggleExcludeCategory(cat.slug)}
                        className="sr-only"
                      />
                      <span
                        className="w-3 h-3 rounded-full mr-1.5"
                        style={{ backgroundColor: cat.color }}
                      />
                      <span className="text-sm text-gray-700">{cat.name}</span>
                    </label>
                  ))}
                </div>
              )}

              <button
                type="button"
                onClick={handleAggregation}
                disabled={loading}
                className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Aggregating...' : '集計実行'}
              </button>
            </div>
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

      {/* 集計結果 - サマリービュー */}
      {viewMode === 'summary' &&
        aggregationResponse &&
        aggregationResponse.aggregations.length > 0 &&
        (() => {
          // フィルタを適用
          let filteredAggregations = aggregationResponse.aggregations;

          // 日本のみフィルタ
          if (filterJapanOnly && groupBy === 'ip') {
            filteredAggregations = filteredAggregations.filter(
              (item) => item.geo_info?.country_code === 'JP'
            );
          }

          // カテゴリ除外フィルタ
          if (excludedCategories.size > 0) {
            filteredAggregations = filteredAggregations.filter(
              (item) => !item.mark_category || !excludedCategories.has(item.mark_category.slug)
            );
          }

          return (
            <div className="space-y-4">
              {/* サマリー */}
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                <h3 className="text-sm font-medium text-blue-800 mb-2">集計結果サマリー</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-blue-600 font-medium">集計単位:</span>
                    <p className="text-blue-900">{getGroupByLabel(aggregationResponse.group_by)}</p>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">総リクエスト数:</span>
                    <p className="text-blue-900 font-semibold">
                      {aggregationResponse.total_requests.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">ユニーク値:</span>
                    <p className="text-blue-900 font-semibold">
                      {aggregationResponse.unique_values.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">表示件数:</span>
                    <p className="text-blue-900 font-semibold">
                      {filteredAggregations.length.toLocaleString()}
                      {filteredAggregations.length !== aggregationResponse.aggregations.length && (
                        <span className="text-blue-600 font-normal ml-1">
                          (
                          {filterJapanOnly && groupBy === 'ip' && '日本のみ'}
                          {filterJapanOnly && groupBy === 'ip' && excludedCategories.size > 0 && ', '}
                          {excludedCategories.size > 0 && (
                            <>
                              {Array.from(excludedCategories).map((slug, index) => {
                                const cat = categories.find(c => c.slug === slug);
                                return (
                                  <span key={slug}>
                                    {index > 0 && ', '}
                                    {cat?.name || slug}除外
                                  </span>
                                );
                              })}
                            </>
                          )}
                          )
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                {/* マーク統計情報 */}
                {aggregationResponse.mark_stats && (
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-blue-200 mt-2">
                    {Object.entries(aggregationResponse.mark_stats)
                      .filter(([slug, count]) => slug !== 'unmarked' && count > 0)
                      .map(([slug, count]) => {
                        const cat = categories.find(c => c.slug === slug);
                        return (
                          <button
                            key={slug}
                            type="button"
                            onClick={() => aggregationResponse.mark_details && handleOpenMarkDetails(
                              slug,
                              aggregationResponse.mark_stats!,
                              aggregationResponse.mark_details,
                              aggregationResponse.total_requests,
                              '全体'
                            )}
                            disabled={!aggregationResponse.mark_details}
                            className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${aggregationResponse.mark_details ? 'hover:opacity-80 cursor-pointer' : ''}`}
                            style={{
                              backgroundColor: cat ? `${cat.color}20` : '#f3f4f6',
                              color: cat?.color || '#374151',
                            }}
                          >
                            <span
                              className="w-2 h-2 rounded-full mr-1"
                              style={{ backgroundColor: cat?.color || '#6b7280' }}
                            />
                            {cat?.name || slug}: {count.toLocaleString()} (
                            {((count / aggregationResponse.total_requests) * 100).toFixed(1)}%)
                          </button>
                        );
                      })}
                    {aggregationResponse.mark_stats.unmarked > 0 && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                        未マーク: {aggregationResponse.mark_stats.unmarked.toLocaleString()} (
                        {((aggregationResponse.mark_stats.unmarked / aggregationResponse.total_requests) * 100).toFixed(1)}%)
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* 集計テーブル */}
              <div className="bg-white shadow rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {getGroupByLabel(aggregationResponse.group_by)}
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          リクエスト数
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          割合
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ユニークパス
                        </th>
                        {groupBy === 'ip' && (
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            国/都市
                          </th>
                        )}
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          マーク統計
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ステータス分布
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          アクション
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredAggregations.map((item: AggregationItem) => (
                        <tr key={item.value} className="hover:bg-gray-50">
                          <td className="px-4 py-2 text-sm text-gray-900 font-mono whitespace-nowrap">
                            <div
                              className="max-w-xl overflow-x-auto"
                              style={{
                                scrollbarWidth: 'thin',
                                scrollbarColor: '#CBD5E0 #F7FAFC',
                              }}
                            >
                              <style>{`
                            .max-w-xl::-webkit-scrollbar {
                              height: 6px;
                            }
                            .max-w-xl::-webkit-scrollbar-track {
                              background: #F7FAFC;
                            }
                            .max-w-xl::-webkit-scrollbar-thumb {
                              background: #CBD5E0;
                              border-radius: 3px;
                            }
                            .max-w-xl::-webkit-scrollbar-thumb:hover {
                              background: #A0AEC0;
                            }
                          `}</style>
                              {item.value}
                            </div>
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900 font-semibold whitespace-nowrap">
                            {item.request_count.toLocaleString()}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                            {item.percentage.toFixed(2)}%
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                            {item.unique_paths.toLocaleString()}
                          </td>
                          {groupBy === 'ip' && (
                            <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                              {item.geo_info
                                ? `${item.geo_info.country || '-'} / ${item.geo_info.city || '-'}`
                                : '-'}
                            </td>
                          )}
                          <td className="px-4 py-2 text-sm whitespace-nowrap">
                            {item.mark_stats && (
                              <div className="flex flex-wrap gap-1">
                                {Object.entries(item.mark_stats)
                                  .filter(([slug, count]) => slug !== 'unmarked' && count > 0)
                                  .map(([slug, count]) => {
                                    const cat = categories.find(c => c.slug === slug);
                                    return (
                                      <button
                                        key={slug}
                                        type="button"
                                        onClick={() => item.mark_details && handleOpenMarkDetails(
                                          slug,
                                          item.mark_stats!,
                                          item.mark_details,
                                          item.request_count,
                                          `${getGroupByLabel(groupBy)}: ${item.value}`
                                        )}
                                        disabled={!item.mark_details}
                                        className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${item.mark_details ? 'hover:opacity-80 cursor-pointer' : ''}`}
                                        style={{
                                          backgroundColor: cat ? `${cat.color}20` : '#f3f4f6',
                                          color: cat?.color || '#374151',
                                        }}
                                      >
                                        <span
                                          className="w-2 h-2 rounded-full mr-1"
                                          style={{ backgroundColor: cat?.color || '#6b7280' }}
                                        />
                                        {count} ({((count / item.request_count) * 100).toFixed(0)}%)
                                      </button>
                                    );
                                  })}
                                {item.mark_stats.unmarked > 0 && (
                                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                    - {item.mark_stats.unmarked} ({((item.mark_stats.unmarked / item.request_count) * 100).toFixed(0)}%)
                                  </span>
                                )}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-2 text-sm whitespace-nowrap">
                            {renderStatusDistribution(item.status_distribution)}
                          </td>
                          <td className="px-4 py-2 text-sm whitespace-nowrap">
                            <button
                              type="button"
                              onClick={() => handleViewDetail(item.value)}
                              className="text-blue-600 hover:text-blue-800 font-medium"
                            >
                              詳細 →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          );
        })()}

      {/* 詳細ビュー - 生ログ */}
      {viewMode === 'detail' && selectedValue && (
        <div className="space-y-4">
          {/* 戻るボタンとヘッダー */}
          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={handleBackToSummary}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                ← 集計結果に戻る
              </button>
              <div className="text-sm text-gray-700">
                <span className="font-medium">{getGroupByLabel(groupBy)}:</span>
                <span className="ml-2 font-mono bg-gray-100 px-2 py-1 rounded">
                  {selectedValue}
                </span>
              </div>
            </div>
          </div>

          {/* 詳細ログテーブル */}
          {detailLogs && detailLogs.logs.length > 0 && (
            <div className="space-y-4">
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                <p className="text-sm text-blue-700">
                  <strong className="font-medium">Results:</strong> Showing {detailLogs.logs.length}{' '}
                  of {detailLogs.pagination.total} total logs (Page {detailLogs.pagination.page} of{' '}
                  {detailLogs.pagination.totalPages})
                </p>
              </div>

              {/* ページネーションコントロール */}
              {detailLogs.pagination.totalPages > 1 && (
                <div className="bg-white shadow rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <button
                      type="button"
                      onClick={handleDetailPrevPage}
                      disabled={loading || detailPage === 1}
                      className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>

                    <span className="text-sm text-gray-700">
                      Page {detailPage} of {detailLogs.pagination.totalPages}
                    </span>

                    <button
                      type="button"
                      onClick={handleDetailNextPage}
                      disabled={loading || detailPage === detailLogs.pagination.totalPages}
                      className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/* ログテーブル */}
              <div className="bg-white shadow rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Date (JST)
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Time (JST)
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Client IP
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Method
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          URI
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Status
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          User Agent
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {detailLogs.logs.map((log: LogEntry, index: number) => (
                        <tr
                          key={`${log.date}-${log.time}-${log.clientIp}-${log.uriStem}-${index}`}
                          onClick={() => setSelectedLog(log)}
                          className="hover:bg-gray-50 cursor-pointer"
                        >
                          <td className="px-4 py-1 text-sm text-gray-900 font-mono">{log.date}</td>
                          <td className="px-4 py-1 text-sm text-gray-900 font-mono">{log.time}</td>
                          <td className="px-4 py-1 text-sm text-gray-900 font-mono">
                            {log.clientIp}
                          </td>
                          <td className="px-4 py-1 text-sm">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {log.method}
                            </span>
                          </td>
                          <td className="px-4 py-1 text-sm text-gray-900 font-mono whitespace-nowrap">
                            <div
                              className="max-w-md overflow-x-auto"
                              style={{
                                scrollbarWidth: 'thin',
                                scrollbarColor: '#CBD5E0 #F7FAFC',
                              }}
                            >
                              <style>{`
                                .max-w-md::-webkit-scrollbar {
                                  height: 6px;
                                }
                                .max-w-md::-webkit-scrollbar-track {
                                  background: #F7FAFC;
                                }
                                .max-w-md::-webkit-scrollbar-thumb {
                                  background: #CBD5E0;
                                  border-radius: 3px;
                                }
                                .max-w-md::-webkit-scrollbar-thumb:hover {
                                  background: #A0AEC0;
                                }
                              `}</style>
                              {log.uriStem}
                            </div>
                          </td>
                          <td className="px-4 py-1 text-sm">
                            <span
                              className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                log.statusCode >= 200 && log.statusCode < 300
                                  ? 'bg-green-100 text-green-800'
                                  : log.statusCode >= 300 && log.statusCode < 400
                                    ? 'bg-blue-100 text-blue-800'
                                    : log.statusCode >= 400 && log.statusCode < 500
                                      ? 'bg-yellow-100 text-yellow-800'
                                      : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {log.statusCode}
                            </span>
                          </td>
                          <td className="px-4 py-1 text-sm text-gray-900 font-mono whitespace-nowrap">
                            <div
                              className="max-w-md overflow-x-auto"
                              style={{
                                scrollbarWidth: 'thin',
                                scrollbarColor: '#CBD5E0 #F7FAFC',
                              }}
                            >
                              {log.userAgent || '-'}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {detailLogs && detailLogs.logs.length === 0 && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
              <p className="text-sm text-yellow-700">No detail logs found.</p>
            </div>
          )}
        </div>
      )}

      {/* ログ詳細モーダル */}
      <LogDetailModal
        entry={selectedLog}
        profile={profile}
        distributionId={distributionId}
        onClose={() => setSelectedLog(null)}
      />

      {/* マーク内訳モーダル */}
      <MarkDetailsModal
        isOpen={markDetailsModal.isOpen}
        onClose={handleCloseMarkDetails}
        markType={markDetailsModal.markType}
        markStats={markDetailsModal.markStats}
        markDetails={markDetailsModal.markDetails}
        totalRequests={markDetailsModal.totalRequests}
        sourceLabel={markDetailsModal.sourceLabel}
      />
    </div>
  );
}
