/**
 * @file WAFブロックリスト管理コンポーネント
 *
 * CloudFront WAFのIPブロックリストを表示・管理します。
 * ディストリビューション単位でブロックされているIPアドレスの一覧表示、
 * フィルタリング、ブロック解除、Excelダウンロード機能を提供します。
 *
 * 主な機能:
 * - ディストリビューション選択
 * - ブロックされているIPアドレスの一覧表示
 * - IPアドレス・IP Set名によるフィルタリング
 * - ブロック解除機能
 * - ブロックリストのExcelエクスポート
 */

import { useEffect, useState } from 'react';
import { CloudFrontService } from '../services/CloudFrontService';
import type { Distribution } from '../types';

/**
 * ブロックされたIPアドレスの情報
 */
interface BlockedIP {
  /** IPアドレス */
  ip: string;
  /** CIDR表記 */
  cidr: string;
  /** IP Set ID */
  ipSetId: string;
  /** IP Set名 */
  ipSetName: string;
  /** IP Set ARN */
  ipSetArn: string;
}

/**
 * WAFブロックリスト管理コンポーネント
 *
 * CloudFront WAFでブロックされているIPアドレスの一覧を表示し、
 * 管理する機能を提供します。ディストリビューション選択、フィルタリング、
 * ブロック解除、Excelダウンロード機能があります。
 *
 * @returns WAFブロックリスト管理UI
 */
export default function BlockedIPs() {
  const [profile, setProfile] = useState('default');
  const [distributions, setDistributions] = useState<Distribution[]>([]);
  const [selectedDistribution, setSelectedDistribution] = useState('');
  const [blockedIPs, setBlockedIPs] = useState<BlockedIP[]>([]);
  const [isLoadingDists, setIsLoadingDists] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterText, setFilterText] = useState('');

  /**
   * CloudFrontディストリビューション一覧を取得
   *
   * 指定されたAWSプロファイルから利用可能なCloudFrontディストリビューションの
   * 一覧を取得し、最初のディストリビューションを自動選択します。
   */
  const fetchDistributions = async () => {
    setIsLoadingDists(true);
    try {
      const service = new CloudFrontService(profile);
      const dists = await service.listDistributions();
      setDistributions(dists);
      if (dists.length > 0) {
        setSelectedDistribution(dists[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch distributions');
    } finally {
      setIsLoadingDists(false);
    }
  };

  /**
   * ブロックされているIPアドレス一覧を取得
   *
   * 選択されたディストリビューションのWAFブロックリストから
   * ブロックされているIPアドレスの一覧を取得します。
   */
  const fetchBlockedIPs = async () => {
    if (!selectedDistribution) return;

    setIsLoading(true);
    setError(null);

    try {
      const service = new CloudFrontService(profile);
      const result = await service.getBlockedIPs(selectedDistribution);
      setBlockedIPs(result.blockedIps);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch blocked IPs');
    } finally {
      setIsLoading(false);
    }
  };

  // biome-ignore lint/correctness/useExhaustiveDependencies: fetchDistributionsはprofile変更時のみ実行すべき
  useEffect(() => {
    fetchDistributions();
  }, [profile]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: fetchBlockedIPsはselectedDistributionまたはprofile変更時のみ実行すべき
  useEffect(() => {
    if (selectedDistribution) {
      fetchBlockedIPs();
    }
  }, [selectedDistribution, profile]);

  /**
   * ブロックリストをExcelファイルとしてダウンロード
   *
   * 現在表示されているブロックリストをExcel形式でダウンロードします。
   * ファイル名には日付とディストリビューションIDが含まれます。
   */
  const handleDownloadExcel = async () => {
    if (!selectedDistribution) return;

    try {
      const service = new CloudFrontService(profile);
      const blob = await service.downloadBlockedIPsExcel(selectedDistribution);

      // ダウンロードリンクを作成
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `waf_blocked_ips_${selectedDistribution}_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download Excel file');
    }
  };

  /**
   * IPアドレスのブロックを解除
   *
   * 指定されたIPアドレス（CIDR）をWAFブロックリストから削除します。
   * 確認ダイアログを表示し、成功後にリストを自動更新します。
   *
   * @param _ip - IPアドレス（現在未使用）
   * @param cidr - 削除するCIDR表記のIPアドレス
   * @param ipSetId - IP Set ID
   */
  const handleUnblock = async (_ip: string, cidr: string, ipSetId: string) => {
    if (!selectedDistribution) return;

    if (!window.confirm(`IPアドレス ${cidr} をブロックリストから削除しますか？`)) {
      return;
    }

    try {
      const service = new CloudFrontService(profile);
      const result = await service.removeFromWAFBlocklist(selectedDistribution, cidr, ipSetId);

      if (result.success) {
        // リストを更新
        await fetchBlockedIPs();
        alert(`${cidr} をブロックリストから削除しました`);
      } else {
        alert(`削除に失敗しました: ${result.message}`);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to unblock IP');
    }
  };

  const filteredIPs = blockedIPs.filter(
    (item) =>
      item.ip.toLowerCase().includes(filterText.toLowerCase()) ||
      item.ipSetName.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">WAF ブロックリスト</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={fetchBlockedIPs}
            disabled={isLoading || !selectedDistribution}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
          >
            {isLoading ? '更新中...' : '🔄 更新'}
          </button>
          <button
            type="button"
            onClick={handleDownloadExcel}
            disabled={isLoading || blockedIPs.length === 0 || !selectedDistribution}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
          >
            📥 Excelダウンロード
          </button>
        </div>
      </div>

      {/* プロファイル選択 */}
      <div className="bg-white shadow rounded-lg p-4">
        <label htmlFor="profileSelect" className="block text-sm font-medium text-gray-700 mb-2">
          AWS Profile:
        </label>
        <div className="flex gap-2">
          <input
            id="profileSelect"
            type="text"
            value={profile}
            onChange={(e) => setProfile(e.target.value)}
            placeholder="e.g., default, default"
            className="block flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            type="button"
            onClick={fetchDistributions}
            disabled={isLoadingDists}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
          >
            {isLoadingDists ? '読込中...' : 'ディストリビューション取得'}
          </button>
        </div>
      </div>

      {/* ディストリビューション選択 */}
      {distributions.length > 0 && (
        <div className="bg-white shadow rounded-lg p-4">
          <label
            htmlFor="distributionSelect"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            CloudFront Distribution:
          </label>
          {isLoadingDists ? (
            <p className="text-sm text-gray-600">ディストリビューションを読み込み中...</p>
          ) : (
            <select
              id="distributionSelect"
              value={selectedDistribution}
              onChange={(e) => setSelectedDistribution(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
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
          )}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-300 rounded p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-4">
        <div className="mb-4">
          <label htmlFor="filterInput" className="block text-sm font-medium text-gray-700 mb-2">
            フィルター:
          </label>
          <input
            id="filterInput"
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="IPアドレスまたはIP Set名で検索..."
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            <p className="mt-2 text-gray-600">読み込み中...</p>
          </div>
        ) : blockedIPs.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600">ブロックされているIPアドレスはありません</p>
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-600">
              合計: {filteredIPs.length} / {blockedIPs.length} IP
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      IPアドレス
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      CIDR
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      IP Set名
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      IP Set ID
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      アクション
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredIPs.map((item, index) => (
                    <tr key={`${item.ipSetId}-${item.cidr}-${index}`} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm font-mono text-gray-900">{item.ip}</td>
                      <td className="px-4 py-2 text-sm font-mono text-gray-600">{item.cidr}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{item.ipSetName}</td>
                      <td className="px-4 py-2 text-sm font-mono text-gray-600 truncate max-w-xs">
                        {item.ipSetId}
                      </td>
                      <td className="px-4 py-2 text-sm whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => handleUnblock(item.ip, item.cidr, item.ipSetId)}
                          className="text-orange-600 hover:text-orange-800 font-medium"
                        >
                          🔓 解除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
