/**
 * @fileoverview CloudFrontの生ログをテーブル形式で表示するコンポーネント
 *
 * このファイルは、CloudFrontのアクセスログを検索・表示するための
 * メインコンポーネントを提供します。複数のフィルター条件による検索、
 * ページネーション、カラムのカスタマイズ機能を備えています。
 *
 * 主な機能:
 * - 複数の条件によるログ検索（日時、IP、URI、User Agentなど）
 * - カラムの表示/非表示切り替えとドラッグ&ドロップによる並び替え
 * - ページネーションによる大量データの効率的な表示
 * - ログ詳細モーダルの表示
 */
import { format } from 'date-fns';
import { type ReactNode, useState } from 'react';
import { CloudFrontService } from '../services/CloudFrontService';
import type { LogEntry, RawLogsResponse } from '../types';
import { LogDetailModal } from './LogDetailModal';

/**
 * ログテーブルのカラム定義
 * 各カラムの表示ラベル、キー、デフォルト表示状態を定義します
 */
const DEFAULT_COLUMNS = [
  { key: 'date', label: 'Date (JST)', defaultVisible: true },
  { key: 'time', label: 'Time (JST)', defaultVisible: true },
  { key: 'clientIp', label: 'Client IP', defaultVisible: true },
  { key: 'method', label: 'Method', defaultVisible: true },
  { key: 'uriStem', label: 'URI', defaultVisible: true },
  { key: 'statusCode', label: 'Status', defaultVisible: true },
  { key: 'bytes', label: 'Bytes', defaultVisible: true },
  { key: 'userAgent', label: 'User Agent', defaultVisible: true },
  { key: 'referrer', label: 'Referrer', defaultVisible: false },
  { key: 'edgeLocation', label: 'Edge Location', defaultVisible: false },
  { key: 'queryString', label: 'Query String', defaultVisible: false },
  { key: 'cookie', label: 'Cookie', defaultVisible: false },
  { key: 'edgeResultType', label: 'Edge Result Type', defaultVisible: false },
  { key: 'edgeRequestId', label: 'Edge Request ID', defaultVisible: false },
  { key: 'host', label: 'Host', defaultVisible: false },
  { key: 'hostHeader', label: 'Host Header', defaultVisible: false },
  { key: 'protocol', label: 'Protocol', defaultVisible: false },
  { key: 'bytes_sent', label: 'Bytes Sent', defaultVisible: false },
  { key: 'timeTaken', label: 'Time Taken', defaultVisible: false },
  { key: 'xForwardedFor', label: 'X-Forwarded-For', defaultVisible: false },
  { key: 'sslProtocol', label: 'SSL Protocol', defaultVisible: false },
  { key: 'sslCipher', label: 'SSL Cipher', defaultVisible: false },
  { key: 'edgeResponseResultType', label: 'Edge Response Result', defaultVisible: false },
  { key: 'protocolVersion', label: 'Protocol Version', defaultVisible: false },
  { key: 'fleStatus', label: 'FLE Status', defaultVisible: false },
  { key: 'fleEncryptedFields', label: 'FLE Encrypted Fields', defaultVisible: false },
  { key: 'clientPort', label: 'Client Port', defaultVisible: false },
  { key: 'timeToFirstByte', label: 'Time to First Byte', defaultVisible: false },
  { key: 'edgeDetailedResultType', label: 'Edge Detailed Result', defaultVisible: false },
  { key: 'contentType', label: 'Content Type', defaultVisible: false },
  { key: 'contentLength', label: 'Content Length', defaultVisible: false },
  { key: 'rangeStart', label: 'Range Start', defaultVisible: false },
  { key: 'rangeEnd', label: 'Range End', defaultVisible: false },
  { key: 'ipInfo', label: 'IP Info', defaultVisible: false },
  { key: 'suspiciousCheck', label: 'Suspicious Check', defaultVisible: false },
] as const;

/** カラムキーの型定義 */
type ColumnKey = (typeof DEFAULT_COLUMNS)[number]['key'];

/** カラム定義の型 */
type ColumnDef = { key: ColumnKey; label: string; defaultVisible: boolean };

/**
 * CloudFrontの生ログを表示・検索するメインコンポーネント
 *
 * Distribution選択、日時範囲、各種フィルター条件を指定して
 * CloudFrontのアクセスログを検索し、カスタマイズ可能なテーブルで表示します。
 * ページネーション機能により大量のログを効率的に閲覧できます。
 *
 * @returns RawLogsコンポーネント
 */
export default function RawLogs() {
  const [profile, setProfile] = useState('default');
  const [distributionId, setDistributionId] = useState('');
  const [startDate, setStartDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [endDate, setEndDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [clientIp, setClientIp] = useState('');
  const [uriPath, setUriPath] = useState('');
  const [userAgent, setUserAgent] = useState('');
  const [referrer, setReferrer] = useState('');
  const [queryString, setQueryString] = useState('');
  const [page, setPage] = useState(1);
  const [perPage] = useState(10000);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logsResponse, setLogsResponse] = useState<RawLogsResponse | null>(null);
  const [distributions, setDistributions] = useState<
    Array<{ id: string; domain: string; aliases?: string[] }>
  >([]);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [columnOrder, setColumnOrder] = useState<ColumnDef[]>([...DEFAULT_COLUMNS]);
  const [visibleColumns, setVisibleColumns] = useState<Set<ColumnKey>>(
    new Set(DEFAULT_COLUMNS.filter((col) => col.defaultVisible).map((col) => col.key))
  );
  const [showColumnSelector, setShowColumnSelector] = useState(false);
  const [draggedColumnIndex, setDraggedColumnIndex] = useState<number | null>(null);

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
   * 指定された条件でログを検索する
   *
   * @param newPage - 取得するページ番号（デフォルト: 1）
   */
  const handleSearch = async (newPage: number = 1) => {
    if (!distributionId || !startDate || !endDate) {
      setError('Please fill in distribution, start date, and end date');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const service = new CloudFrontService(profile);

      const response = await service.listRawLogs(
        distributionId,
        startDate,
        endDate,
        clientIp || undefined,
        uriPath || undefined,
        userAgent || undefined,
        referrer || undefined,
        queryString || undefined,
        startTime || undefined,
        endTime || undefined,
        newPage,
        perPage
      );
      setLogsResponse(response);
      setPage(newPage);

      if (response.logs.length === 0) {
        setError('No log entries found for the specified criteria');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to list logs');
      setLogsResponse(null);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 次のページを表示する
   */
  const handleNextPage = () => {
    if (logsResponse && page < logsResponse.pagination.totalPages) {
      handleSearch(page + 1);
    }
  };

  /**
   * 前のページを表示する
   */
  const handlePrevPage = () => {
    if (page > 1) {
      handleSearch(page - 1);
    }
  };

  /**
   * 指定されたページ番号に移動する
   *
   * @param inputPage - 移動先のページ番号
   */
  const handlePageInput = (inputPage: number) => {
    if (logsResponse && inputPage >= 1 && inputPage <= logsResponse.pagination.totalPages) {
      handleSearch(inputPage);
    }
  };

  /**
   * カラムの表示/非表示を切り替える
   *
   * @param columnKey - 切り替えるカラムのキー
   */
  const toggleColumn = (columnKey: ColumnKey) => {
    setVisibleColumns((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(columnKey)) {
        newSet.delete(columnKey);
      } else {
        newSet.add(columnKey);
      }
      return newSet;
    });
  };

  /**
   * カラムのドラッグを開始する
   *
   * @param index - ドラッグを開始するカラムのインデックス
   */
  const handleDragStart = (index: number) => {
    setDraggedColumnIndex(index);
  };

  /**
   * カラムのドラッグオーバーイベントを処理する
   *
   * @param e - ドラッグイベント
   * @param index - ドラッグオーバー中のカラムのインデックス
   */
  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedColumnIndex === null || draggedColumnIndex === index) return;

    const newOrder = [...columnOrder];
    const draggedItem = newOrder[draggedColumnIndex];
    newOrder.splice(draggedColumnIndex, 1);
    newOrder.splice(index, 0, draggedItem);

    setColumnOrder(newOrder);
    setDraggedColumnIndex(index);
  };

  /**
   * カラムのドラッグを終了する
   */
  const handleDragEnd = () => {
    setDraggedColumnIndex(null);
  };

  /**
   * ログエントリの特定カラムの値をレンダリングする
   *
   * カラムのタイプに応じて適切な形式（色付きバッジ、数値フォーマットなど）で表示します。
   *
   * @param log - ログエントリ
   * @param columnKey - 表示するカラムのキー
   * @returns レンダリングされたセル内容
   */
  const renderCellValue = (log: LogEntry, columnKey: ColumnKey): ReactNode => {
    const value = log[columnKey as keyof LogEntry];

    switch (columnKey) {
      case 'statusCode':
        return (
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
        );
      case 'bytes':
      case 'bytes_sent':
      case 'contentLength':
        return typeof value === 'number' ? value.toLocaleString() : '-';
      case 'timeTaken':
      case 'timeToFirstByte':
        return typeof value === 'number' ? `${value.toFixed(3)}s` : '-';
      case 'clientPort':
      case 'rangeStart':
      case 'rangeEnd':
        return typeof value === 'number' ? value.toString() : '-';
      case 'date':
      case 'time':
        return typeof value === 'string' ? value : '-';
      case 'ipInfo':
        if (value && typeof value === 'object' && 'city' in value) {
          return `${value.city || '-'}, ${value.country || '-'}`;
        }
        return '-';
      case 'suspiciousCheck':
        if (value && typeof value === 'object' && 'isSuspicious' in value) {
          return value.isSuspicious ? '⚠️ Suspicious' : '✓ Safe';
        }
        return '-';
      default:
        // Handle any other object types that might not be renderable
        if (value && typeof value === 'object') {
          return JSON.stringify(value);
        }
        return typeof value === 'string' || typeof value === 'number' ? String(value || '-') : '-';
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

      {/* フィルタ条件 */}
      {distributionId && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Filter Criteria</h2>
          <div className="space-y-4">
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

            <div>
              <label htmlFor="clientIp" className="block text-sm font-medium text-gray-700 mb-1">
                Client IP (optional):
              </label>
              <input
                id="clientIp"
                type="text"
                value={clientIp}
                onChange={(e) => setClientIp(e.target.value)}
                placeholder="e.g., 203.0.113.42"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              />
            </div>

            <div>
              <label htmlFor="uriPath" className="block text-sm font-medium text-gray-700 mb-1">
                URI Path (optional):
              </label>
              <input
                id="uriPath"
                type="text"
                value={uriPath}
                onChange={(e) => setUriPath(e.target.value)}
                placeholder="e.g., /nattoku/special/"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              />
            </div>

            <div>
              <label htmlFor="userAgent" className="block text-sm font-medium text-gray-700 mb-1">
                User Agent (optional):
              </label>
              <input
                id="userAgent"
                type="text"
                value={userAgent}
                onChange={(e) => setUserAgent(e.target.value)}
                placeholder="e.g., Mozilla/5.0"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              />
            </div>

            <div>
              <label htmlFor="referrer" className="block text-sm font-medium text-gray-700 mb-1">
                Referrer (optional):
              </label>
              <input
                id="referrer"
                type="text"
                value={referrer}
                onChange={(e) => setReferrer(e.target.value)}
                placeholder="e.g., https://www.google.com/"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              />
            </div>

            <div>
              <label htmlFor="queryString" className="block text-sm font-medium text-gray-700 mb-1">
                Query String (optional):
              </label>
              <input
                id="queryString"
                type="text"
                value={queryString}
                onChange={(e) => setQueryString(e.target.value)}
                placeholder="e.g., utm_source=google"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              />
            </div>

            <button
              type="button"
              onClick={() => handleSearch(1)}
              disabled={loading}
              className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'List Logs'}
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
      {logsResponse && logsResponse.logs.length > 0 && (
        <div className="space-y-4">
          {/* サマリーとカラムセレクター */}
          <div className="flex items-start justify-between gap-4">
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded flex-1">
              <p className="text-sm text-blue-700">
                <strong className="font-medium">Results:</strong> Showing {logsResponse.logs.length}{' '}
                of {logsResponse.pagination.total} total logs (Page {logsResponse.pagination.page}{' '}
                of {logsResponse.pagination.totalPages})
              </p>
            </div>

            {/* カラムセレクター */}
            <div className="bg-white shadow rounded-lg p-4 min-w-[200px]">
              <button
                type="button"
                onClick={() => setShowColumnSelector(!showColumnSelector)}
                className="w-full px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 text-sm font-medium"
              >
                {showColumnSelector ? '▼' : '▶'} Select Columns ({visibleColumns.size}/
                {columnOrder.length})
              </button>

              {showColumnSelector && (
                <div className="mt-3 space-y-1 max-h-96 overflow-y-auto">
                  <div className="text-xs text-gray-500 mb-2 px-1">
                    Drag to reorder, check to show/hide
                  </div>
                  {columnOrder.map((column, index) => (
                    // biome-ignore lint/a11y/useSemanticElements: This is a draggable element that needs custom role
                    <div
                      key={column.key}
                      draggable
                      onDragStart={() => handleDragStart(index)}
                      onDragOver={(e) => handleDragOver(e, index)}
                      onDragEnd={handleDragEnd}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          toggleColumn(column.key);
                        }
                      }}
                      role="button"
                      tabIndex={0}
                      className={`flex items-center space-x-2 p-2 rounded cursor-move hover:bg-gray-50 ${
                        draggedColumnIndex === index
                          ? 'bg-blue-50 border-blue-300 border'
                          : 'border border-transparent'
                      }`}
                    >
                      <span className="text-gray-400">⋮⋮</span>
                      <input
                        type="checkbox"
                        checked={visibleColumns.has(column.key)}
                        onChange={() => toggleColumn(column.key)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <span className="text-sm text-gray-700 flex-1">{column.label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* ページネーションコントロール */}
          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={handlePrevPage}
                disabled={loading || page === 1}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>

              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-700">Page</span>
                <input
                  type="number"
                  min="1"
                  max={logsResponse.pagination.totalPages}
                  value={page}
                  onChange={(e) => {
                    const newPage = Number.parseInt(e.target.value, 10);
                    if (!Number.isNaN(newPage)) {
                      handlePageInput(newPage);
                    }
                  }}
                  className="w-20 px-2 py-1 border border-gray-300 rounded-md text-center focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="text-sm text-gray-700">
                  of {logsResponse.pagination.totalPages}
                </span>
              </div>

              <button
                type="button"
                onClick={handleNextPage}
                disabled={loading || page === logsResponse.pagination.totalPages}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>

          {/* ログテーブル */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {columnOrder
                      .filter((col) => visibleColumns.has(col.key))
                      .map((column) => (
                        <th
                          key={column.key}
                          className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {column.label}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logsResponse.logs.map((log: LogEntry, index: number) => (
                    <tr
                      key={`${log.date}-${log.time}-${log.clientIp}-${index}`}
                      onClick={() => setSelectedLog(log)}
                      className="hover:bg-gray-50 cursor-pointer"
                    >
                      {columnOrder
                        .filter((col) => visibleColumns.has(col.key))
                        .map((column) => (
                          <td
                            key={column.key}
                            className="px-4 py-1 text-sm text-gray-900 font-mono whitespace-nowrap"
                            title={String(log[column.key as keyof LogEntry] || '')}
                          >
                            {renderCellValue(log, column.key)}
                          </td>
                        ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 下部ページネーション */}
          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={handlePrevPage}
                disabled={loading || page === 1}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>

              <div className="text-sm text-gray-700">
                Page {page} of {logsResponse.pagination.totalPages} (
                {logsResponse.pagination.total.toLocaleString()} total logs)
              </div>

              <button
                type="button"
                onClick={handleNextPage}
                disabled={loading || page === logsResponse.pagination.totalPages}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ログ詳細モーダル */}
      <LogDetailModal
        entry={selectedLog}
        profile={profile}
        distributionId={distributionId}
        onClose={() => setSelectedLog(null)}
      />
    </div>
  );
}
