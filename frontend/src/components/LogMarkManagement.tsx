/**
 * @file ログマーク管理コンポーネント
 *
 * ログマークパターンの一覧表示、作成、編集、削除を行うための管理画面コンポーネント。
 * IP、パス、User-Agent、クエリストリング、リファラの任意の組み合わせでパターンを登録できます。
 */

import { useEffect, useState } from 'react';
import { CloudFrontService } from '../services/CloudFrontService';
import type { LogMarkPattern } from '../types';

/**
 * LogMarkManagementコンポーネントのProps
 */
interface LogMarkManagementProps {
  /** AWSプロファイル名 */
  profile: string;
  /** 対象のDistribution ID（省略可） */
  distributionId?: string;
}

/**
 * ログマーク管理画面コンポーネント
 *
 * ログマークパターンのCRUD操作を提供します。
 *
 * @param props - コンポーネントのProps
 * @param props.profile - AWSプロファイル名
 * @param props.distributionId - 対象のDistribution ID
 * @returns ログマーク管理UI
 */
export function LogMarkManagement({ profile, distributionId }: LogMarkManagementProps) {
  const [patterns, setPatterns] = useState<LogMarkPattern[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingPattern, setEditingPattern] = useState<LogMarkPattern | null>(null);

  // フォームの状態
  const [formData, setFormData] = useState<Omit<LogMarkPattern, 'id' | 'created_at' | 'updated_at'>>({
    distribution_id: distributionId || null,
    user_agent_pattern: null,
    ip_pattern: null,
    path_pattern: null,
    query_string_pattern: null,
    referrer_pattern: null,
    org_pattern: null,
    match_type: 'partial',
    mark_type: 'bot',
    note: '',
    is_active: true,
  });

  /**
   * パターン一覧を取得
   */
  const loadPatterns = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const service = new CloudFrontService(profile);
      const data = await service.getLogMarkPatterns(distributionId);
      setPatterns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patterns');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPatterns();
  }, [profile, distributionId]);

  /**
   * フォームをリセット
   */
  const resetForm = () => {
    setFormData({
      distribution_id: distributionId || null,
      user_agent_pattern: null,
      ip_pattern: null,
      path_pattern: null,
      query_string_pattern: null,
      referrer_pattern: null,
      org_pattern: null,
      match_type: 'partial',
      mark_type: 'bot',
      note: '',
      is_active: true,
    });
    setEditingPattern(null);
    setShowForm(false);
  };

  /**
   * パターンを作成または更新
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const service = new CloudFrontService(profile);

      // 空の文字列をnullに変換
      const cleanedData = {
        ...formData,
        user_agent_pattern: formData.user_agent_pattern?.trim() || null,
        ip_pattern: formData.ip_pattern?.trim() || null,
        path_pattern: formData.path_pattern?.trim() || null,
        query_string_pattern: formData.query_string_pattern?.trim() || null,
        referrer_pattern: formData.referrer_pattern?.trim() || null,
        org_pattern: formData.org_pattern?.trim() || null,
      };

      if (editingPattern) {
        await service.updateLogMarkPattern(editingPattern.id!, cleanedData);
      } else {
        await service.createLogMarkPattern(cleanedData);
      }

      await loadPatterns();
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save pattern');
    }
  };

  /**
   * パターンを編集
   */
  const handleEdit = (pattern: LogMarkPattern) => {
    setEditingPattern(pattern);
    setFormData({
      distribution_id: pattern.distribution_id,
      user_agent_pattern: pattern.user_agent_pattern,
      ip_pattern: pattern.ip_pattern,
      path_pattern: pattern.path_pattern,
      query_string_pattern: pattern.query_string_pattern,
      referrer_pattern: pattern.referrer_pattern,
      org_pattern: pattern.org_pattern,
      match_type: pattern.match_type,
      mark_type: pattern.mark_type,
      note: pattern.note || '',
      is_active: pattern.is_active,
    });
    setShowForm(true);
  };

  /**
   * パターンを削除
   */
  const handleDelete = async (patternId: number) => {
    if (!confirm('このパターンを削除してもよろしいですか?')) {
      return;
    }

    try {
      const service = new CloudFrontService(profile);
      await service.deleteLogMarkPattern(patternId);
      await loadPatterns();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete pattern');
    }
  };

  /**
   * マークタイプのバッジ色を取得
   */
  const getMarkTypeBadgeColor = (markType: string) => {
    switch (markType) {
      case 'bot':
        return 'bg-orange-100 text-orange-800';
      case 'suspicious':
        return 'bg-red-100 text-red-800';
      case 'legitimate':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  /**
   * マークタイプのラベルを取得
   */
  const getMarkTypeLabel = (markType: string) => {
    switch (markType) {
      case 'bot':
        return '🤖 ボット';
      case 'suspicious':
        return '⚠️ 疑わしい';
      case 'legitimate':
        return '✅ 正常';
      default:
        return markType;
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">ログマークパターン管理</h2>
        <button
          type="button"
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {showForm ? 'キャンセル' : '+ 新規作成'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-800">
          {error}
        </div>
      )}

      {/* 作成/編集フォーム */}
      {showForm && (
        <div className="mb-6 p-6 bg-white shadow rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {editingPattern ? 'パターンを編集' : '新しいパターンを作成'}
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* User-Agent Pattern */}
              <div>
                <label htmlFor="user_agent_pattern" className="block text-sm font-medium text-gray-700 mb-1">
                  User-Agentパターン
                </label>
                <input
                  type="text"
                  id="user_agent_pattern"
                  value={formData.user_agent_pattern || ''}
                  onChange={(e) => setFormData({ ...formData, user_agent_pattern: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例: Googlebot"
                />
              </div>

              {/* IP Pattern */}
              <div>
                <label htmlFor="ip_pattern" className="block text-sm font-medium text-gray-700 mb-1">
                  IPアドレスパターン
                </label>
                <input
                  type="text"
                  id="ip_pattern"
                  value={formData.ip_pattern || ''}
                  onChange={(e) => setFormData({ ...formData, ip_pattern: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例: 192.168"
                />
              </div>

              {/* Path Pattern */}
              <div>
                <label htmlFor="path_pattern" className="block text-sm font-medium text-gray-700 mb-1">
                  パスパターン
                </label>
                <input
                  type="text"
                  id="path_pattern"
                  value={formData.path_pattern || ''}
                  onChange={(e) => setFormData({ ...formData, path_pattern: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例: /api/"
                />
              </div>

              {/* Query String Pattern */}
              <div>
                <label htmlFor="query_string_pattern" className="block text-sm font-medium text-gray-700 mb-1">
                  クエリストリングパターン
                </label>
                <input
                  type="text"
                  id="query_string_pattern"
                  value={formData.query_string_pattern || ''}
                  onChange={(e) => setFormData({ ...formData, query_string_pattern: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例: debug=true"
                />
              </div>

              {/* Referrer Pattern */}
              <div>
                <label htmlFor="referrer_pattern" className="block text-sm font-medium text-gray-700 mb-1">
                  リファラパターン
                </label>
                <input
                  type="text"
                  id="referrer_pattern"
                  value={formData.referrer_pattern || ''}
                  onChange={(e) => setFormData({ ...formData, referrer_pattern: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例: google.com"
                />
              </div>

              {/* Organization Pattern */}
              <div>
                <label htmlFor="org_pattern" className="block text-sm font-medium text-gray-700 mb-1">
                  組織名パターン
                </label>
                <input
                  type="text"
                  id="org_pattern"
                  value={formData.org_pattern || ''}
                  onChange={(e) => setFormData({ ...formData, org_pattern: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例: Anthropic, OpenAI, Criteo"
                />
                <p className="text-xs text-gray-500 mt-1">
                  IPGeolocationのorg/isp/asnameフィールドと照合されます
                </p>
              </div>

              {/* Match Type */}
              <div>
                <label htmlFor="match_type" className="block text-sm font-medium text-gray-700 mb-1">
                  マッチング方法
                </label>
                <select
                  id="match_type"
                  value={formData.match_type}
                  onChange={(e) => setFormData({ ...formData, match_type: e.target.value as 'exact' | 'partial' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="partial">部分一致</option>
                  <option value="exact">完全一致</option>
                </select>
              </div>

              {/* Mark Type */}
              <div>
                <label htmlFor="mark_type" className="block text-sm font-medium text-gray-700 mb-1">
                  マークタイプ
                </label>
                <select
                  id="mark_type"
                  value={formData.mark_type}
                  onChange={(e) => setFormData({ ...formData, mark_type: e.target.value as 'bot' | 'suspicious' | 'legitimate' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="bot">🤖 ボット</option>
                  <option value="suspicious">⚠️ 疑わしい</option>
                  <option value="legitimate">✅ 正常</option>
                </select>
              </div>

              {/* Active Status */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
                  アクティブ
                </label>
              </div>

              {/* Note */}
              <div className="md:col-span-2">
                <label htmlFor="note" className="block text-sm font-medium text-gray-700 mb-1">
                  メモ
                </label>
                <textarea
                  id="note"
                  value={formData.note || ''}
                  onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="このパターンに関するメモ..."
                />
              </div>
            </div>

            <div className="mt-4 flex gap-2">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {editingPattern ? '更新' : '作成'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                キャンセル
              </button>
            </div>
          </form>
        </div>
      )}

      {/* パターン一覧 */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-600">読み込み中...</div>
      ) : patterns.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          パターンが登録されていません。「+ 新規作成」ボタンから追加してください。
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    マークタイプ
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    パターン条件
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    マッチング
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ステータス
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    作成日時
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    アクション
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {patterns.map((pattern) => (
                  <tr key={pattern.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getMarkTypeBadgeColor(pattern.mark_type)}`}>
                        {getMarkTypeLabel(pattern.mark_type)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <div className="space-y-1">
                        {pattern.user_agent_pattern && (
                          <div><span className="font-medium">UA:</span> {pattern.user_agent_pattern}</div>
                        )}
                        {pattern.ip_pattern && (
                          <div><span className="font-medium">IP:</span> {pattern.ip_pattern}</div>
                        )}
                        {pattern.path_pattern && (
                          <div><span className="font-medium">Path:</span> {pattern.path_pattern}</div>
                        )}
                        {pattern.query_string_pattern && (
                          <div><span className="font-medium">QS:</span> {pattern.query_string_pattern}</div>
                        )}
                        {pattern.referrer_pattern && (
                          <div><span className="font-medium">Ref:</span> {pattern.referrer_pattern}</div>
                        )}
                        {pattern.org_pattern && (
                          <div><span className="font-medium">Org:</span> {pattern.org_pattern}</div>
                        )}
                        {pattern.note && (
                          <div className="text-xs text-gray-500 mt-1">{pattern.note}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {pattern.match_type === 'exact' ? '完全一致' : '部分一致'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${pattern.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {pattern.is_active ? 'アクティブ' : '無効'}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {pattern.created_at ? new Date(pattern.created_at).toLocaleString('ja-JP') : '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <button
                        type="button"
                        onClick={() => handleEdit(pattern)}
                        className="text-blue-600 hover:text-blue-800 mr-3"
                      >
                        編集
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(pattern.id!)}
                        className="text-red-600 hover:text-red-800"
                      >
                        削除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
