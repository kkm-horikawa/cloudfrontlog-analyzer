/**
 * @file マーク内訳表示モーダルコンポーネント
 *
 * ログ集計結果のマーク（カテゴリ別）の内訳を
 * モーダルウィンドウで表示します。
 */

import type { LogMarkCategory, MarkDetails, MarkStats } from '../types';

/**
 * MarkDetailsModalコンポーネントのProps
 */
interface MarkDetailsModalProps {
  /** モーダルを表示するかどうか */
  isOpen: boolean;
  /** モーダルを閉じる際のコールバック関数 */
  onClose: () => void;
  /** 表示するカテゴリslug */
  markType: string;
  /** マーク統計情報 */
  markStats: MarkStats;
  /** マーク内訳（パターン別） */
  markDetails: MarkDetails;
  /** 総リクエスト数 */
  totalRequests: number;
  /** 表示元のラベル（例: "IPアドレス: 1.2.3.4"） */
  sourceLabel?: string;
  /** カテゴリ情報（動的スタイル用） */
  category?: LogMarkCategory;
}

/**
 * マーク内訳表示モーダルコンポーネント
 *
 * @param props - コンポーネントのProps
 * @returns マーク内訳モーダルUI、またはnull
 */
export function MarkDetailsModal({
  isOpen,
  onClose,
  markType,
  markStats,
  markDetails,
  totalRequests,
  sourceLabel,
}: MarkDetailsModalProps) {
  if (!isOpen) return null;

  const count = markStats[markType] || 0;
  const percentage = totalRequests > 0 ? ((count / totalRequests) * 100).toFixed(1) : '0';

  // markDetailsから該当するカテゴリslugのパターンをフィルタしてソート
  const filteredDetails = Object.entries(markDetails)
    .filter(([, detail]) => detail.category?.slug === markType)
    .sort(([, a], [, b]) => b.count - a.count);

  // カテゴリ情報を取得（最初のパターンから）
  const category = filteredDetails.length > 0 ? filteredDetails[0][1].category : null;
  const categoryColor = category?.color || '#6b7280';
  const categoryName = category?.name || markType;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4"
      style={{ zIndex: 10000 }}
      onClick={onClose}
      onKeyDown={(e) => e.key === 'Escape' && onClose()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="mark-details-modal-title"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
        role="document"
      >
        {/* モーダルヘッダー */}
        <div
          className="border-b px-6 py-4 flex items-center justify-between"
          style={{
            backgroundColor: `${categoryColor}15`,
            borderColor: `${categoryColor}40`,
          }}
        >
          <div>
            <h2
              id="mark-details-modal-title"
              className="text-xl font-bold flex items-center gap-2"
              style={{ color: categoryColor }}
            >
              <span
                className="w-4 h-4 rounded-full inline-block"
                style={{ backgroundColor: categoryColor }}
              />
              {categoryName}の内訳
            </h2>
            {sourceLabel && (
              <p className="text-sm text-gray-600 mt-1">{sourceLabel}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
              role="img"
              aria-label="Close icon"
            >
              <title>Close</title>
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* サマリー */}
        <div
          className="px-6 py-3 border-b"
          style={{
            backgroundColor: `${categoryColor}10`,
            borderColor: `${categoryColor}30`,
          }}
        >
          <div className="flex items-center justify-between">
            <span
              className="text-sm font-medium"
              style={{ color: categoryColor }}
            >
              合計: {count.toLocaleString()} 件 ({percentage}%)
            </span>
            <span className="text-sm text-gray-600">
              {filteredDetails.length} パターン
            </span>
          </div>
        </div>

        {/* モーダルコンテンツ */}
        <div className="flex-1 overflow-y-auto p-6">
          {filteredDetails.length > 0 ? (
            <div className="space-y-3">
              {filteredDetails.map(([pattern, detail]) => (
                <div
                  key={pattern}
                  className="rounded-lg p-4"
                  style={{
                    border: `1px solid ${categoryColor}30`,
                    backgroundColor: `${categoryColor}08`,
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                          style={{
                            backgroundColor: `${categoryColor}20`,
                            color: categoryColor,
                          }}
                        >
                          {detail.count.toLocaleString()} 件
                        </span>
                        <span className="text-xs text-gray-500">
                          ({totalRequests > 0 ? ((detail.count / totalRequests) * 100).toFixed(1) : '0'}%)
                        </span>
                      </div>
                      <p className="mt-2 text-sm font-mono text-gray-800 break-all">
                        {pattern || '(パターンなし)'}
                      </p>
                      {detail.note && (
                        <p className="mt-1 text-sm text-gray-600">
                          {detail.note}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>内訳情報がありません</p>
            </div>
          )}
        </div>

        {/* モーダルフッター */}
        <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
}
