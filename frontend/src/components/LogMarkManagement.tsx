/**
 * @file ログマーク管理コンポーネント
 *
 * ログマークパターンの一覧表示、作成、編集、削除を行うための管理画面コンポーネント。
 * IP、パス、User-Agent、クエリストリング、リファラの任意の組み合わせでパターンを登録できます。
 * カテゴリの管理機能も提供します。
 */

import { useEffect, useState } from 'react';
import { CloudFrontService } from '../services/CloudFrontService';
import type { LogMarkCategory, LogMarkPattern } from '../types';

/**
 * LogMarkManagementコンポーネントのProps
 */
interface LogMarkManagementProps {
  /** AWSプロファイル名 */
  profile: string;
  /** 対象のDistribution ID（省略可） */
  distributionId?: string;
}

type TabType = 'patterns' | 'categories';

/**
 * ログマーク管理画面コンポーネント
 *
 * ログマークパターンとカテゴリのCRUD操作を提供します。
 *
 * @param props - コンポーネントのProps
 * @param props.profile - AWSプロファイル名
 * @param props.distributionId - 対象のDistribution ID
 * @returns ログマーク管理UI
 */
export function LogMarkManagement({ profile, distributionId }: LogMarkManagementProps) {
  const [activeTab, setActiveTab] = useState<TabType>('patterns');
  const [patterns, setPatterns] = useState<LogMarkPattern[]>([]);
  const [categories, setCategories] = useState<LogMarkCategory[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingPattern, setEditingPattern] = useState<LogMarkPattern | null>(null);

  // カテゴリ編集用の状態
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState<LogMarkCategory | null>(null);
  const [categoryFormData, setCategoryFormData] = useState<Omit<LogMarkCategory, 'id' | 'created_at' | 'updated_at'>>({
    name: '',
    slug: '',
    color: '#6B7280',
    description: '',
  });

  // フォームの状態
  const [formData, setFormData] = useState<Omit<LogMarkPattern, 'id' | 'created_at' | 'updated_at' | 'category'> & { category_id?: number }>({
    distribution_id: distributionId || null,
    user_agent_pattern: null,
    ip_pattern: null,
    path_pattern: null,
    query_string_pattern: null,
    referrer_pattern: null,
    org_pattern: null,
    match_type: 'partial',
    category_id: undefined,
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

  /**
   * カテゴリ一覧を取得
   */
  const loadCategories = async () => {
    try {
      const service = new CloudFrontService(profile);
      const data = await service.getLogMarkCategories();
      setCategories(data);
      // 初回読み込み時にデフォルトカテゴリを設定
      if (data.length > 0 && !formData.category_id) {
        setFormData(prev => ({ ...prev, category_id: data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  useEffect(() => {
    loadPatterns();
    loadCategories();
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
      category_id: categories.length > 0 ? categories[0].id : undefined,
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
      category_id: pattern.category?.id,
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
   * カテゴリのバッジスタイルを取得
   */
  const getCategoryBadgeStyle = (category: LogMarkCategory | null | undefined) => {
    if (!category) {
      return { backgroundColor: '#f3f4f6', color: '#374151' };
    }
    return {
      backgroundColor: `${category.color}20`,
      color: category.color,
    };
  };

  /**
   * カテゴリフォームをリセット
   */
  const resetCategoryForm = () => {
    setCategoryFormData({
      name: '',
      slug: '',
      color: '#6B7280',
      description: '',
    });
    setEditingCategory(null);
    setShowCategoryForm(false);
  };

  /**
   * カテゴリを作成または更新
   */
  const handleCategorySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const service = new CloudFrontService(profile);

      if (editingCategory) {
        await service.updateLogMarkCategory(editingCategory.id, categoryFormData);
      } else {
        await service.createLogMarkCategory(categoryFormData);
      }

      await loadCategories();
      resetCategoryForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save category');
    }
  };

  /**
   * カテゴリを編集
   */
  const handleEditCategory = (category: LogMarkCategory) => {
    setEditingCategory(category);
    setCategoryFormData({
      name: category.name,
      slug: category.slug,
      color: category.color,
      description: category.description || '',
    });
    setShowCategoryForm(true);
  };

  /**
   * カテゴリを削除
   */
  const handleDeleteCategory = async (categoryId: number) => {
    if (!confirm('このカテゴリを削除してもよろしいですか？\n関連するパターンがある場合は削除できません。')) {
      return;
    }

    try {
      const service = new CloudFrontService(profile);
      await service.deleteLogMarkCategory(categoryId);
      await loadCategories();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete category');
    }
  };

  /**
   * カテゴリに関連するパターン数を取得
   */
  const getPatternCountForCategory = (categoryId: number) => {
    return patterns.filter((p) => p.category?.id === categoryId).length;
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">ログマーク管理</h2>

        {/* タブ */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              type="button"
              onClick={() => setActiveTab('patterns')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'patterns'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              パターン管理
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('categories')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'categories'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              カテゴリ管理
            </button>
          </nav>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-800">
          {error}
        </div>
      )}

      {/* カテゴリ管理タブ */}
      {activeTab === 'categories' && (
        <>
          <div className="mb-6 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">カテゴリ一覧</h3>
            <button
              type="button"
              onClick={() => setShowCategoryForm(!showCategoryForm)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {showCategoryForm ? 'キャンセル' : '+ 新規作成'}
            </button>
          </div>

          {/* カテゴリ作成/編集フォーム */}
          {showCategoryForm && (
            <div className="mb-6 p-6 bg-white shadow rounded-lg border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">
                {editingCategory ? 'カテゴリを編集' : '新しいカテゴリを作成'}
              </h4>
              <form onSubmit={handleCategorySubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="cat_name" className="block text-sm font-medium text-gray-700 mb-1">
                      名前 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="cat_name"
                      value={categoryFormData.name}
                      onChange={(e) => setCategoryFormData({ ...categoryFormData, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="例: ボット"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="cat_slug" className="block text-sm font-medium text-gray-700 mb-1">
                      スラッグ <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="cat_slug"
                      value={categoryFormData.slug}
                      onChange={(e) => setCategoryFormData({ ...categoryFormData, slug: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="例: bot"
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">半角英数字とハイフンのみ使用可</p>
                  </div>

                  <div>
                    <label htmlFor="cat_color" className="block text-sm font-medium text-gray-700 mb-1">
                      カラー
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        id="cat_color"
                        value={categoryFormData.color}
                        onChange={(e) => setCategoryFormData({ ...categoryFormData, color: e.target.value })}
                        className="h-10 w-14 border border-gray-300 rounded-md cursor-pointer"
                      />
                      <input
                        type="text"
                        value={categoryFormData.color}
                        onChange={(e) => setCategoryFormData({ ...categoryFormData, color: e.target.value })}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="#6B7280"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="cat_description" className="block text-sm font-medium text-gray-700 mb-1">
                      説明
                    </label>
                    <input
                      type="text"
                      id="cat_description"
                      value={categoryFormData.description || ''}
                      onChange={(e) => setCategoryFormData({ ...categoryFormData, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="例: 検索エンジンのクローラー"
                    />
                  </div>
                </div>

                <div className="mt-4 flex gap-2">
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {editingCategory ? '更新' : '作成'}
                  </button>
                  <button
                    type="button"
                    onClick={resetCategoryForm}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    キャンセル
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* カテゴリ一覧 */}
          {isLoading ? (
            <div className="text-center py-8 text-gray-600">読み込み中...</div>
          ) : categories.length === 0 ? (
            <div className="text-center py-8 text-gray-600">
              カテゴリが登録されていません。「+ 新規作成」ボタンから追加してください。
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        カテゴリ
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        スラッグ
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        説明
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        パターン数
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        アクション
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {categories.map((category) => (
                      <tr key={category.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <span
                              className="w-4 h-4 rounded-full inline-block"
                              style={{ backgroundColor: category.color }}
                            />
                            <span
                              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                              style={getCategoryBadgeStyle(category)}
                            >
                              {category.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {category.slug}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {category.description || '-'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {getPatternCountForCategory(category.id)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm">
                          <button
                            type="button"
                            onClick={() => handleEditCategory(category)}
                            className="text-blue-600 hover:text-blue-800 mr-3"
                          >
                            編集
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteCategory(category.id)}
                            className="text-red-600 hover:text-red-800"
                            disabled={getPatternCountForCategory(category.id) > 0}
                            title={getPatternCountForCategory(category.id) > 0 ? '関連パターンがあるため削除できません' : ''}
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
        </>
      )}

      {/* パターン管理タブ */}
      {activeTab === 'patterns' && (
        <>
          <div className="mb-6 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">パターン一覧</h3>
            <button
              type="button"
              onClick={() => setShowForm(!showForm)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {showForm ? 'キャンセル' : '+ 新規作成'}
            </button>
          </div>

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

              {/* Category */}
              <div>
                <label htmlFor="category_id" className="block text-sm font-medium text-gray-700 mb-1">
                  カテゴリ
                </label>
                <select
                  id="category_id"
                  value={formData.category_id || ''}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">カテゴリを選択...</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
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
                    カテゴリ
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
                      <span
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        style={getCategoryBadgeStyle(pattern.category)}
                      >
                        {pattern.category?.name || '未設定'}
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
        </>
      )}
    </div>
  );
}
