/**
 * @fileoverview ログエントリをテーブル形式で表示する再利用可能なコンポーネント
 *
 * このファイルは、CloudFrontログエントリのリストを
 * カスタマイズ可能なテーブルで表示するコンポーネントを提供します。
 * カラムの表示/非表示切り替え、ドラッグ&ドロップによる並び替え、
 * 各種データ型の適切な表示フォーマットをサポートします。
 */
import { useState } from 'react';
import type { LogEntry } from '../types';

/**
 * ログテーブルのカラム定義
 * 各カラムの表示ラベル、キー、デフォルト表示状態を定義します
 */
export const DEFAULT_COLUMNS = [
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
] as const;

/** カラムキーの型定義 */
export type ColumnKey = (typeof DEFAULT_COLUMNS)[number]['key'];

/** カラム定義の型 */
export type ColumnDef = { key: ColumnKey; label: string; defaultVisible: boolean };

/**
 * LogsTableコンポーネントのProps
 */
interface LogsTableProps {
  /** 表示するログエントリのリスト */
  logs: LogEntry[];
  /** カラムセレクターを表示するかどうか（デフォルト: true） */
  showColumnSelector?: boolean;
  /** AWSプロファイル名（未使用だが互換性のため残されています） */
  profile?: string;
  /** CloudFront Distribution ID（未使用だが互換性のため残されています） */
  distributionId?: string;
  /** ログ行がクリックされたときのコールバック関数 */
  onLogClick?: (log: LogEntry) => void;
}

/**
 * ログエントリをテーブル形式で表示するコンポーネント
 *
 * ログのリストをカスタマイズ可能なテーブルで表示します。
 * カラムの表示/非表示、並び替え、クリック時の詳細表示をサポートします。
 *
 * @param props - コンポーネントのProps
 * @param props.logs - 表示するログエントリのリスト
 * @param props.showColumnSelector - カラムセレクターを表示するかどうか
 * @param props.onLogClick - ログクリック時のコールバック
 * @returns LogsTableコンポーネント
 */
export function LogsTable({ logs, showColumnSelector = true, onLogClick }: LogsTableProps) {
  const [columnOrder, setColumnOrder] = useState<ColumnDef[]>([...DEFAULT_COLUMNS]);
  const [visibleColumns, setVisibleColumns] = useState<Set<ColumnKey>>(
    new Set(DEFAULT_COLUMNS.filter((col) => col.defaultVisible).map((col) => col.key))
  );
  const [showSelector, setShowSelector] = useState(false);
  const [draggedColumnIndex, setDraggedColumnIndex] = useState<number | null>(null);

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
  const renderCellValue = (log: LogEntry, columnKey: ColumnKey) => {
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
        return typeof value === 'number' ? `${value}s` : '-';
      case 'date':
      case 'time':
      case 'clientIp':
      case 'edgeRequestId':
      case 'xForwardedFor':
        return <span className="font-mono text-sm">{String(value || '-')}</span>;
      case 'method':
        return <span className="font-semibold">{String(value || '-')}</span>;
      case 'uriStem':
      case 'referrer':
      case 'userAgent':
      case 'queryString':
      case 'cookie':
        return (
          <div className="max-w-md truncate" title={String(value || '')}>
            {String(value || '-')}
          </div>
        );
      default:
        if (typeof value === 'object' && value !== null) {
          return '-';
        }
        return value !== undefined && value !== null ? String(value) : '-';
    }
  };

  if (logs.length === 0) {
    return <div className="text-center py-8 text-gray-500">No logs to display</div>;
  }

  return (
    <div className="space-y-4">
      {/* カラムセレクター */}
      {showColumnSelector && (
        <div className="bg-white shadow rounded-lg p-4">
          <button
            type="button"
            onClick={() => setShowSelector(!showSelector)}
            className="w-full sm:w-auto px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 text-sm font-medium"
          >
            {showSelector ? '▼' : '▶'} Select Columns ({visibleColumns.size}/{columnOrder.length})
          </button>

          {showSelector && (
            <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
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
      )}

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
                {onLogClick && (
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map((log) => (
                <tr
                  key={`${log.date}-${log.time}-${log.clientIp}-${log.edgeRequestId || ''}`}
                  className="hover:bg-gray-50"
                >
                  {columnOrder
                    .filter((col) => visibleColumns.has(col.key))
                    .map((column) => (
                      <td key={column.key} className="px-4 py-2 text-sm text-gray-900">
                        {renderCellValue(log, column.key)}
                      </td>
                    ))}
                  {onLogClick && (
                    <td className="px-4 py-2 text-sm whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => onLogClick(log)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Details
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
