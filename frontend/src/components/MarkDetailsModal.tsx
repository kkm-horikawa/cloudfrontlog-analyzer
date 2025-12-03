/**
 * @file マーク内訳表示モーダルコンポーネント
 *
 * ログ集計結果のマーク（ボット、疑わしい、正規）の内訳を
 * モーダルウィンドウで表示します。
 */

import type { MarkDetails, MarkStats } from '../types';

/**
 * MarkDetailsModalコンポーネントのProps
 */
interface MarkDetailsModalProps {
  /** モーダルを表示するかどうか */
  isOpen: boolean;
  /** モーダルを閉じる際のコールバック関数 */
  onClose: () => void;
  /** 表示するマーク種別（'bot' | 'suspicious' | 'legitimate'） */
  markType: 'bot' | 'suspicious' | 'legitimate';
  /** マーク統計情報 */
  markStats: MarkStats;
  /** マーク内訳（パターン別） */
  markDetails: MarkDetails;
  /** 総リクエスト数 */
  totalRequests: number;
  /** 表示元のラベル（例: "IPアドレス: 1.2.3.4"） */
  sourceLabel?: string;
}

/**
 * マーク種別の表示設定
 */
const MARK_TYPE_CONFIG = {
  bot: {
    label: 'ボット',
    emoji: '🤖',
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-800',
    borderColor: 'border-orange-200',
    headerBg: 'bg-orange-50',
  },
  suspicious: {
    label: '警戒',
    emoji: '⚠️',
    bgColor: 'bg-red-100',
    textColor: 'text-red-800',
    borderColor: 'border-red-200',
    headerBg: 'bg-red-50',
  },
  legitimate: {
    label: '正常',
    emoji: '✓',
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
    borderColor: 'border-green-200',
    headerBg: 'bg-green-50',
  },
};

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

  const config = MARK_TYPE_CONFIG[markType];
  const count = markStats[markType];
  const percentage = totalRequests > 0 ? ((count / totalRequests) * 100).toFixed(1) : '0';

  // markDetailsから該当するmarkTypeのパターンをフィルタしてソート
  const filteredDetails = Object.entries(markDetails)
    .filter(([, detail]) => detail.mark_type === markType)
    .sort(([, a], [, b]) => b.count - a.count);

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
        <div className={`${config.headerBg} border-b ${config.borderColor} px-6 py-4 flex items-center justify-between`}>
          <div>
            <h2 id="mark-details-modal-title" className={`text-xl font-bold ${config.textColor}`}>
              {config.emoji} {config.label}の内訳
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
        <div className={`${config.bgColor} px-6 py-3 border-b ${config.borderColor}`}>
          <div className="flex items-center justify-between">
            <span className={`text-sm font-medium ${config.textColor}`}>
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
                  className={`border ${config.borderColor} rounded-lg p-4 ${config.bgColor} bg-opacity-30`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${config.bgColor} ${config.textColor}`}>
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
