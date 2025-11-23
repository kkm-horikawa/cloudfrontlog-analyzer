/**
 * @fileoverview CloudFront Log Analyzerのメインアプリケーションコンポーネント
 *
 * このファイルは、CloudFrontログ解析アプリケーションのエントリーポイントです。
 * 複数のビューモード（検索、生ログ、集約、地理情報、ブロックリスト）を
 * タブナビゲーションで切り替え可能にします。
 */

import { useState } from 'react';
import BlockedIPs from './components/BlockedIPs';
import CloudFrontAnalyzer from './components/CloudFrontAnalyzer';
import GeoLogMap from './components/GeoLogMap';
import LogAggregation from './components/LogAggregation';
import RawLogs from './components/RawLogs';

/**
 * アプリケーションのビューモード
 *
 * @typedef {'search' | 'rawLogs' | 'aggregation' | 'geoMap' | 'blockedIPs'} ViewMode
 */
type ViewMode = 'search' | 'rawLogs' | 'aggregation' | 'geoMap' | 'blockedIPs';

/**
 * CloudFront Log Analyzerのメインアプリケーションコンポーネント
 *
 * ヘッダーナビゲーションとメインコンテンツエリアを提供し、
 * 以下の機能を含むビューを切り替え可能にします：
 * - Log Search: 条件を指定したログ検索
 * - Raw Logs: 生のログエントリの表示
 * - Log Aggregation: ログの集約・統計情報
 * - Location: ログの地理情報マップ表示
 * - WAF Blocklist: WAFでブロックされたIPアドレスの管理
 *
 * @returns {JSX.Element} Appコンポーネント
 */
function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('search');

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">CloudFront Log Analyzer</h1>

          {/* ナビゲーションタブ */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                type="button"
                onClick={() => setViewMode('search')}
                className={`${
                  viewMode === 'search'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Log Search
              </button>
              <button
                type="button"
                onClick={() => setViewMode('rawLogs')}
                className={`${
                  viewMode === 'rawLogs'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Raw Logs
              </button>
              <button
                type="button"
                onClick={() => setViewMode('aggregation')}
                className={`${
                  viewMode === 'aggregation'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Log Aggregation
              </button>
              <button
                type="button"
                onClick={() => setViewMode('geoMap')}
                className={`${
                  viewMode === 'geoMap'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Location
              </button>
              <button
                type="button"
                onClick={() => setViewMode('blockedIPs')}
                className={`${
                  viewMode === 'blockedIPs'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                WAF Blocklist
              </button>
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {viewMode === 'search' && <CloudFrontAnalyzer />}
        {viewMode === 'rawLogs' && <RawLogs />}
        {viewMode === 'aggregation' && <LogAggregation />}
        {viewMode === 'geoMap' && <GeoLogMap />}
        {viewMode === 'blockedIPs' && <BlockedIPs />}
      </main>
    </div>
  );
}

export default App;
