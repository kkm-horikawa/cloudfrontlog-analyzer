/**
 * @file ログ詳細表示モーダルコンポーネント
 *
 * CloudFrontアクセスログの詳細情報をモーダルウィンドウで表示します。
 * AccessLogDetailsコンポーネントをラップし、モーダル機能を提供します。
 */

import type { LogEntry } from '../types';
import { AccessLogDetails } from './AccessLogDetails';

/**
 * LogDetailModalコンポーネントのProps
 */
interface LogDetailModalProps {
  /** 表示するログエントリ（nullの場合はモーダルを表示しない） */
  entry: LogEntry | null;
  /** AWSプロファイル名 */
  profile: string;
  /** CloudFrontディストリビューションID */
  distributionId: string;
  /** モーダルを閉じる際のコールバック関数 */
  onClose: () => void;
}

/**
 * ログ詳細表示モーダルコンポーネント
 *
 * CloudFrontアクセスログの詳細情報をフルスクリーンモーダルで表示します。
 * モーダルの外側をクリックまたはEscキーでモーダルを閉じることができます。
 *
 * @param props - コンポーネントのProps
 * @param props.entry - 表示するログエントリ（nullの場合はモーダルを表示しない）
 * @param props.profile - AWSプロファイル名
 * @param props.distributionId - CloudFrontディストリビューションID
 * @param props.onClose - モーダルを閉じる際のコールバック関数
 * @returns ログ詳細モーダルUI、またはnull
 */
export function LogDetailModal({ entry, profile, distributionId, onClose }: LogDetailModalProps) {
  if (!entry) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4"
      style={{ zIndex: 10000 }}
      onClick={onClose}
      onKeyDown={(e) => e.key === 'Escape' && onClose()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
        role="document"
      >
        {/* モーダルヘッダー */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <h2 id="modal-title" className="text-2xl font-bold text-gray-900">
            Log Details
          </h2>
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

        {/* モーダルコンテンツ */}
        <div className="p-6">
          <AccessLogDetails
            entry={{ ...entry }}
            profile={profile}
            distributionId={distributionId}
            targetUrl={entry.uriStem}
            initiallyExpanded={true}
          />
        </div>

        {/* モーダルフッター */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
