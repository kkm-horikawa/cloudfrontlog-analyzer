/**
 * @file セキュリティチェック機能を提供するコンポーネント
 *
 * CloudFrontアクセスログに対して様々なセキュリティチェックを実行し、
 * 不審なアクセスパターンの検出やWAFブロックリストの管理を行います。
 *
 * 主な機能:
 * - 会社情報ページアクセスチェック
 * - 頻繁なIPアクセスチェック
 * - マルチデバイスアクセスチェック
 * - 調査ツール検出チェック
 * - WAFブロックリストの確認・追加・削除
 */

import { useState } from 'react';
import { CloudFrontService } from '../services/CloudFrontService';
import type {
  CompanyInfoCheckResult,
  FrequentIPCheckResult,
  LogEntry,
  MultiDeviceCheckResult,
  ResearchToolCheckResult,
  WAFAddBlocklistResponse,
  WAFCheckResponse,
  WAFIPSet,
} from '../types';

/**
 * SecurityChecksコンポーネントのProps
 */
interface SecurityChecksProps {
  /** 対象のログエントリ */
  entry: LogEntry;
  /** AWSプロファイル名 */
  profile: string;
  /** CloudFrontディストリビューションID */
  distributionId: string;
  /** チェック対象のURL */
  targetUrl: string;
}

/**
 * セキュリティチェックコンポーネント
 *
 * アクセスログに対して複数のセキュリティチェックを実行し、
 * 不審なアクセスパターンを検出します。また、WAFブロックリストの
 * 確認・追加・削除機能を提供します。
 *
 * @param props - コンポーネントのProps
 * @param props.entry - 対象のログエントリ
 * @param props.profile - AWSプロファイル名
 * @param props.distributionId - CloudFrontディストリビューションID
 * @param props.targetUrl - チェック対象のURL
 * @returns セキュリティチェックUI
 */
export function SecurityChecks({ entry, profile, distributionId, targetUrl }: SecurityChecksProps) {
  const [companyInfoResult, setCompanyInfoResult] = useState<CompanyInfoCheckResult | null>(null);
  const [frequentIPResult, setFrequentIPResult] = useState<FrequentIPCheckResult | null>(null);
  const [multiDeviceResult, setMultiDeviceResult] = useState<MultiDeviceCheckResult | null>(null);
  const [researchToolResult, setResearchToolResult] = useState<ResearchToolCheckResult | null>(
    null
  );
  const [wafCheckResult, setWafCheckResult] = useState<WAFCheckResponse | null>(null);
  const [wafAddResult, setWafAddResult] = useState<WAFAddBlocklistResponse | null>(null);
  const [wafRemoveResult, setWafRemoveResult] = useState<WAFAddBlocklistResponse | null>(null);
  const [wafIPSets, setWafIPSets] = useState<WAFIPSet[]>([]);
  const [selectedIPSetId, setSelectedIPSetId] = useState<string>('');
  const [loadingStates, setLoadingStates] = useState({
    companyInfo: false,
    frequentIP: false,
    multiDevice: false,
    researchTool: false,
    wafCheck: false,
    wafAdd: false,
    wafRemove: false,
    wafIPSets: false,
  });
  const [errors, setErrors] = useState({
    companyInfo: null as string | null,
    frequentIP: null as string | null,
    multiDevice: null as string | null,
    researchTool: null as string | null,
    wafCheck: null as string | null,
    wafAdd: null as string | null,
  });

  /**
   * 会社情報ページアクセスチェックを実行
   *
   * 過去3日間でターゲットURLからの遷移で会社情報ページ（/nattoku/about/）に
   * アクセスしているかをチェックします。
   */
  const handleCompanyInfoCheck = async () => {
    setLoadingStates((prev) => ({ ...prev, companyInfo: true }));
    setErrors((prev) => ({ ...prev, companyInfo: null }));

    try {
      const service = new CloudFrontService(profile);
      const result = await service.checkCompanyInfoAccess(
        distributionId,
        targetUrl,
        '/nattoku/about/'
      );
      setCompanyInfoResult(result);
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        companyInfo: err instanceof Error ? err.message : 'Failed to check',
      }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, companyInfo: false }));
    }
  };

  /**
   * 頻繁なIPアクセスチェックを実行
   *
   * 過去3日間の同一IPからのアクセス数と、アクセスしたユニークなURL数を
   * チェックし、スクレイピングやボットの可能性を判定します。
   */
  const handleFrequentIPCheck = async () => {
    setLoadingStates((prev) => ({ ...prev, frequentIP: true }));
    setErrors((prev) => ({ ...prev, frequentIP: null }));

    try {
      const service = new CloudFrontService(profile);
      const result = await service.checkFrequentIPAccess(distributionId, entry.clientIp, 3);
      setFrequentIPResult(result);
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        frequentIP: err instanceof Error ? err.message : 'Failed to check',
      }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, frequentIP: false }));
    }
  };

  /**
   * マルチデバイスアクセスチェックを実行
   *
   * 同一IPからスマートフォンとデスクトップ両方のアクセスがあるかをチェックし、
   * 複数デバイスからのアクセスパターンを検出します。
   */
  const handleMultiDeviceCheck = async () => {
    setLoadingStates((prev) => ({ ...prev, multiDevice: true }));
    setErrors((prev) => ({ ...prev, multiDevice: null }));

    try {
      const service = new CloudFrontService(profile);
      const result = await service.checkMultiDeviceAccess(distributionId, entry.clientIp, 3);
      setMultiDeviceResult(result);
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        multiDevice: err instanceof Error ? err.message : 'Failed to check',
      }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, multiDevice: false }));
    }
  };

  /**
   * 調査ツール検出チェックを実行
   *
   * User AgentやReferrerに調査ツール系の名前（SimilarWeb、Ahrefs等）が
   * 含まれているかをチェックします。
   */
  const handleResearchToolCheck = async () => {
    setLoadingStates((prev) => ({ ...prev, researchTool: true }));
    setErrors((prev) => ({ ...prev, researchTool: null }));

    try {
      const service = new CloudFrontService(profile);
      const result = await service.checkResearchToolDetection(entry.userAgent, entry.referrer);
      setResearchToolResult(result);
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        researchTool: err instanceof Error ? err.message : 'Failed to check',
      }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, researchTool: false }));
    }
  };

  /**
   * WAFのIP Setリストを読み込む
   *
   * CloudFrontディストリビューションに関連付けられたWAFのIP Setリストを
   * 取得し、ブロックリストへの追加先として選択できるようにします。
   */
  const handleLoadWAFIPSets = async () => {
    setLoadingStates((prev) => ({ ...prev, wafIPSets: true }));

    try {
      console.log('Loading WAF IP Sets for distribution:', distributionId, 'profile:', profile);
      const service = new CloudFrontService(profile);
      const result = await service.listWAFIPSets(distributionId);
      console.log('WAF IP Sets result:', result);
      if (result?.ipSets && result.ipSets.length > 0) {
        console.log('Setting IP Sets:', result.ipSets);
        setWafIPSets(result.ipSets);
        // 最初のIP Setを自動選択
        setSelectedIPSetId(result.ipSets[0].id);
        console.log('Auto-selected IP Set:', result.ipSets[0].id);
      } else {
        console.log('No IP Sets found');
      }
    } catch (err) {
      console.error('Failed to load WAF IP Sets:', err);
      setErrors((prev) => ({
        ...prev,
        wafCheck: `IP Setsの読み込みに失敗しました: ${err instanceof Error ? err.message : String(err)}`,
      }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, wafIPSets: false }));
    }
  };

  /**
   * WAFブロックリスト確認チェックを実行
   *
   * 指定されたIPアドレスがCloudFrontディストリビューションのWAFブロックリストに
   * 含まれているかを確認します。
   */
  const handleWAFCheck = async () => {
    setLoadingStates((prev) => ({ ...prev, wafCheck: true }));
    setErrors((prev) => ({ ...prev, wafCheck: null }));
    setWafCheckResult(null);

    try {
      const service = new CloudFrontService(profile);
      const result = await service.checkWAFBlocklist(distributionId, entry.clientIp);
      console.log('WAF Check result:', result);
      setWafCheckResult(result);

      // まだロードされていない場合はIP Setsをロード
      if (wafIPSets.length === 0) {
        await handleLoadWAFIPSets();
      }
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        wafCheck: err instanceof Error ? err.message : 'Failed to check WAF blocklist',
      }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, wafCheck: false }));
    }
  };

  /**
   * WAFブロックリストへIPアドレスを追加
   *
   * 指定されたIPアドレスをWAFのIP Setに追加し、今後のアクセスをブロックします。
   * 追加後、自動的にWAFチェックを更新します。
   */
  const handleWAFAdd = async () => {
    setLoadingStates((prev) => ({ ...prev, wafAdd: true }));
    setErrors((prev) => ({ ...prev, wafAdd: null }));
    setWafAddResult(null);

    try {
      const service = new CloudFrontService(profile);
      const result = await service.addToWAFBlocklist(
        distributionId,
        entry.clientIp,
        selectedIPSetId || undefined
      );
      setWafAddResult(result);
      // 追加後にWAFチェックを更新
      if (result.success) {
        await handleWAFCheck();
      }
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        wafAdd: err instanceof Error ? err.message : 'Failed to add to WAF blocklist',
      }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, wafAdd: false }));
    }
  };

  /**
   * WAFブロックリストからIPアドレスを削除
   *
   * 指定されたIPアドレス（またはCIDRブロック）をWAFのIP Setから削除し、
   * ブロックを解除します。削除後、自動的にWAFチェックを更新します。
   */
  const handleWAFRemove = async () => {
    setLoadingStates((prev) => ({ ...prev, wafRemove: true }));
    setWafRemoveResult(null);

    try {
      const service = new CloudFrontService(profile);
      // マッチしたCIDRがあればそれを使用、なければクライアントIPを使用
      const ipToRemove = wafCheckResult?.matchedCidr || entry.clientIp;
      const ipSetId = wafCheckResult?.matchedIpSetId || selectedIPSetId || undefined;

      const result = await service.removeFromWAFBlocklist(distributionId, ipToRemove, ipSetId);
      setWafRemoveResult(result);

      // 成功した場合、WAFチェックステータスを更新
      if (result.success) {
        // AWSの変更が反映されるまで少し待つ
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await handleWAFCheck();
      }
    } catch (err) {
      setWafRemoveResult({
        success: false,
        ipAddress: entry.clientIp,
        ipSetId: '',
        ipSetName: '',
        message: err instanceof Error ? err.message : 'Failed to remove from WAF blocklist',
      });
    } finally {
      setLoadingStates((prev) => ({ ...prev, wafRemove: false }));
    }
  };

  return (
    <div className="space-y-4">
      <h4 className="text-md font-semibold text-gray-800">個別セキュリティチェック</h4>

      {/* 会社情報ページアクセスチェック */}
      <div className="border border-gray-300 rounded p-3">
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-sm font-medium text-gray-700">会社情報ページアクセスチェック</h5>
          <button
            type="button"
            onClick={handleCompanyInfoCheck}
            disabled={loadingStates.companyInfo}
            className="px-3 py-1 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded disabled:opacity-50"
          >
            {loadingStates.companyInfo ? 'チェック中...' : 'チェック実行'}
          </button>
        </div>
        <p className="text-xs text-gray-600 mb-2">
          過去3日間でターゲットURLからの遷移で会社情報ページ（/nattoku/about/）にアクセスしているかチェック
        </p>

        {errors.companyInfo && <p className="text-xs text-red-600">{errors.companyInfo}</p>}

        {companyInfoResult && (
          <div className="mt-3 space-y-2">
            <div
              className={`p-2 rounded text-sm ${
                companyInfoResult.result.isSuspicious
                  ? 'bg-red-50 border border-red-300'
                  : 'bg-green-50 border border-green-300'
              }`}
            >
              <p className="font-medium">
                {companyInfoResult.result.isSuspicious ? '⚠️ 要注意' : '✓ 正常'}
              </p>
              <p className="text-xs">{companyInfoResult.result.description}</p>
              <p className="text-xs mt-1">
                会社情報ページへの総アクセス数: {companyInfoResult.result.totalAccessCount} /
                怪しいアクセス: {companyInfoResult.result.suspiciousAccessCount}
              </p>
            </div>

            {companyInfoResult.details.length > 0 && (
              <details className="text-xs">
                <summary className="cursor-pointer font-medium text-blue-600">
                  詳細を表示 ({companyInfoResult.details.length}件)
                </summary>
                <div className="mt-2 space-y-1 max-h-64 overflow-y-auto">
                  {companyInfoResult.details.map((item) => (
                    <div
                      key={`${item.date}-${item.time}-${item.clientIp}`}
                      className="bg-gray-50 p-2 rounded"
                    >
                      <p className="font-mono text-xs">
                        {item.date} {item.time} - IP: {item.clientIp}
                      </p>
                      <p className="text-xs mt-1">Referrer: {item.referrer}</p>
                      <p className="text-xs truncate">UA: {item.userAgent}</p>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </div>

      {/* 頻繁なIPアクセスチェック */}
      <div className="border border-gray-300 rounded p-3">
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-sm font-medium text-gray-700">頻繁なIPアクセスチェック</h5>
          <button
            type="button"
            onClick={handleFrequentIPCheck}
            disabled={loadingStates.frequentIP}
            className="px-3 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
          >
            {loadingStates.frequentIP ? 'チェック中...' : 'チェック実行'}
          </button>
        </div>
        <p className="text-xs text-gray-600 mb-2">過去3日間の同一IPからのアクセスを確認</p>

        {errors.frequentIP && <p className="text-xs text-red-600">{errors.frequentIP}</p>}

        {frequentIPResult && (
          <div className="mt-3 space-y-2">
            <div
              className={`p-2 rounded text-sm ${
                frequentIPResult.result.isSuspicious
                  ? 'bg-red-50 border border-red-300'
                  : 'bg-green-50 border border-green-300'
              }`}
            >
              <p className="font-medium">
                {frequentIPResult.result.isSuspicious ? '⚠️ 要注意' : '✓ 正常'}
              </p>
              <p className="text-xs">{frequentIPResult.result.description}</p>
              <p className="text-xs mt-1">
                総アクセス数: {frequentIPResult.result.totalAccessCount} / ユニークURL数:{' '}
                {frequentIPResult.result.uniqueUrlsAccessed}
              </p>
            </div>

            {frequentIPResult.details.length > 0 && (
              <details className="text-xs">
                <summary className="cursor-pointer font-medium text-blue-600">
                  詳細を表示 (上位{Math.min(frequentIPResult.details.length, 20)}URL)
                </summary>
                <div className="mt-2 space-y-1 max-h-64 overflow-y-auto">
                  {frequentIPResult.details.map((item) => (
                    <div key={item.url} className="bg-gray-50 p-2 rounded">
                      <p className="font-mono break-all">
                        {item.url} ({item.accessCount}回)
                      </p>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </div>

      {/* マルチデバイスアクセスチェック */}
      <div className="border border-gray-300 rounded p-3">
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-sm font-medium text-gray-700">マルチデバイスアクセスチェック</h5>
          <button
            type="button"
            onClick={handleMultiDeviceCheck}
            disabled={loadingStates.multiDevice}
            className="px-3 py-1 text-xs font-medium text-white bg-purple-600 hover:bg-purple-700 rounded disabled:opacity-50"
          >
            {loadingStates.multiDevice ? 'チェック中...' : 'チェック実行'}
          </button>
        </div>
        <p className="text-xs text-gray-600 mb-2">
          同一IPからスマホ＋デスクトップ両方のアクセスを確認
        </p>

        {errors.multiDevice && <p className="text-xs text-red-600">{errors.multiDevice}</p>}

        {multiDeviceResult && (
          <div className="mt-3 space-y-2">
            <div
              className={`p-2 rounded text-sm ${
                multiDeviceResult.result.isSuspicious
                  ? 'bg-red-50 border border-red-300'
                  : 'bg-green-50 border border-green-300'
              }`}
            >
              <p className="font-medium">
                {multiDeviceResult.result.isSuspicious ? '⚠️ 要注意' : '✓ 正常'}
              </p>
              <p className="text-xs">{multiDeviceResult.result.description}</p>
              <p className="text-xs mt-1">
                検出デバイスタイプ: {multiDeviceResult.result.deviceTypesDetected.join(', ')}
              </p>
            </div>

            {Object.keys(multiDeviceResult.details).length > 0 && (
              <details className="text-xs">
                <summary className="cursor-pointer font-medium text-blue-600">
                  デバイスタイプ別詳細
                </summary>
                <div className="mt-2 space-y-2">
                  {Object.entries(multiDeviceResult.details).map(([deviceType, data]) => (
                    <div key={deviceType} className="bg-gray-50 p-2 rounded">
                      <p className="font-medium">
                        {deviceType}: {data.count}回
                      </p>
                      {data.samples.length > 0 && (
                        <div className="mt-1 space-y-1">
                          {data.samples.slice(0, 3).map((sample) => (
                            <p
                              key={`${sample.date}-${sample.time}-${sample.uriStem}`}
                              className="text-xs font-mono truncate"
                            >
                              {sample.date} {sample.time} - {sample.uriStem}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </div>

      {/* 調査ツール検出チェック */}
      <div className="border border-gray-300 rounded p-3">
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-sm font-medium text-gray-700">調査ツール検出チェック</h5>
          <button
            type="button"
            onClick={handleResearchToolCheck}
            disabled={loadingStates.researchTool}
            className="px-3 py-1 text-xs font-medium text-white bg-orange-600 hover:bg-orange-700 rounded disabled:opacity-50"
          >
            {loadingStates.researchTool ? 'チェック中...' : 'チェック実行'}
          </button>
        </div>
        <p className="text-xs text-gray-600 mb-2">UA/Referrerに調査ツール系の名前を検出</p>

        {errors.researchTool && <p className="text-xs text-red-600">{errors.researchTool}</p>}

        {researchToolResult && (
          <div className="mt-3 space-y-2">
            <div
              className={`p-2 rounded text-sm ${
                researchToolResult.result.isSuspicious
                  ? 'bg-red-50 border border-red-300'
                  : 'bg-green-50 border border-green-300'
              }`}
            >
              <p className="font-medium">
                {researchToolResult.result.isSuspicious ? '⚠️ 検出あり' : '✓ 検出なし'}
              </p>
              <p className="text-xs">{researchToolResult.result.description}</p>
              {researchToolResult.result.matchedPatternCount > 0 && (
                <p className="text-xs mt-1">
                  マッチ数: {researchToolResult.result.matchedPatternCount}
                </p>
              )}
            </div>

            {researchToolResult.details.matchedPatterns.length > 0 && (
              <div className="bg-yellow-50 p-2 rounded">
                <p className="text-xs font-medium mb-1">検出パターン:</p>
                <ul className="list-disc list-inside text-xs space-y-1">
                  {researchToolResult.details.matchedPatterns.map((pattern) => (
                    <li key={pattern}>{pattern}</li>
                  ))}
                </ul>
              </div>
            )}

            <details className="text-xs">
              <summary className="cursor-pointer font-medium text-blue-600">
                チェック基準を表示
              </summary>
              <ul className="list-disc list-inside mt-2 space-y-1 text-gray-600">
                {researchToolResult.criteria.patterns.map((pattern) => (
                  <li key={pattern}>{pattern}</li>
                ))}
              </ul>
            </details>
          </div>
        )}
      </div>

      {/* WAFブロックリストチェック */}
      <div className="border border-gray-300 rounded p-3">
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-sm font-medium text-gray-700">WAFブロックリスト確認</h5>
          <button
            type="button"
            onClick={handleWAFCheck}
            disabled={loadingStates.wafCheck}
            className="px-3 py-1 text-xs font-medium text-white bg-purple-600 hover:bg-purple-700 rounded disabled:opacity-50"
          >
            {loadingStates.wafCheck ? '確認中...' : 'ブロック状態確認'}
          </button>
        </div>
        <p className="text-xs text-gray-600 mb-2">
          このIPアドレスがCloudFrontディストリビューションのWAFブロックリストに含まれているか確認
        </p>

        {errors.wafCheck && <p className="text-xs text-red-600">{errors.wafCheck}</p>}

        {wafCheckResult && (
          <div className="mt-3 space-y-2">
            <div
              className={`p-2 rounded text-sm ${
                wafCheckResult.isBlocked
                  ? 'bg-red-50 border border-red-300'
                  : 'bg-green-50 border border-green-300'
              }`}
            >
              <p className="font-medium">
                {wafCheckResult.isBlocked ? '🚫 ブロック済み' : '✓ ブロックされていません'}
              </p>
              {wafCheckResult.webAcl && (
                <p className="text-xs mt-1">WebACL: {wafCheckResult.webAcl.name}</p>
              )}
              {wafCheckResult.blockingRule && (
                <p className="text-xs">Blocking Rule: {wafCheckResult.blockingRule}</p>
              )}
            </div>

            {!wafCheckResult.isBlocked && (
              <div className="pt-2 space-y-2">
                {loadingStates.wafIPSets ? (
                  <div className="bg-yellow-50 p-2 rounded">
                    <p className="text-xs text-yellow-800">IP Setを読み込み中です...</p>
                  </div>
                ) : wafIPSets.length === 0 ? (
                  <div className="bg-gray-50 p-2 rounded">
                    <p className="text-xs text-gray-800">
                      IP Setが見つかりませんでした。WAFが設定されていない可能性があります。
                    </p>
                  </div>
                ) : (
                  <>
                    <div>
                      <label
                        htmlFor="ipSetSelect"
                        className="block text-xs font-medium text-gray-700 mb-1"
                      >
                        追加先のIP Set:
                      </label>
                      <select
                        id="ipSetSelect"
                        value={selectedIPSetId}
                        onChange={(e) => setSelectedIPSetId(e.target.value)}
                        className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        {wafIPSets.map((ipSet) => (
                          <option key={ipSet.id} value={ipSet.id}>
                            {ipSet.name} ({ipSet.addressCount}個のIP)
                          </option>
                        ))}
                      </select>
                    </div>
                    <button
                      type="button"
                      onClick={handleWAFAdd}
                      disabled={loadingStates.wafAdd}
                      className="w-full px-3 py-2 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded disabled:opacity-50"
                    >
                      {loadingStates.wafAdd ? '追加中...' : 'このIPをブロックリストに追加'}
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {wafAddResult && (
          <div className="mt-3">
            <div
              className={`p-2 rounded text-sm ${
                wafAddResult.success
                  ? 'bg-green-50 border border-green-300'
                  : 'bg-red-50 border border-red-300'
              }`}
            >
              <p className="font-medium">{wafAddResult.success ? '✓ 成功' : '✗ 失敗'}</p>
              <p className="text-xs">{wafAddResult.message}</p>
              {wafAddResult.success && wafAddResult.ipSetName && (
                <p className="text-xs mt-1">IP Set: {wafAddResult.ipSetName}</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* WAFブロックリスト削除セクション */}
      {wafCheckResult?.isBlocked && (
        <div className="bg-orange-50 border border-orange-200 p-3 rounded space-y-2">
          <h3 className="text-sm font-semibold text-orange-900">🔓 ブロック解除</h3>
          <p className="text-xs text-gray-600">このIPアドレスをWAFブロックリストから削除します</p>

          {wafCheckResult.matchedCidr && (
            <div className="bg-white p-2 rounded border border-orange-300 text-xs">
              <p className="font-medium text-gray-700">マッチしたCIDRブロック:</p>
              <p className="font-mono text-orange-700">{wafCheckResult.matchedCidr}</p>
              {wafCheckResult.matchedIpSetName && (
                <p className="text-gray-600 mt-1">IP Set: {wafCheckResult.matchedIpSetName}</p>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={handleWAFRemove}
            disabled={loadingStates.wafRemove}
            className="w-full px-3 py-2 text-xs font-medium text-white bg-orange-600 hover:bg-orange-700 rounded disabled:opacity-50"
          >
            {loadingStates.wafRemove ? '解除中...' : 'ブロックリストから削除'}
          </button>

          {wafRemoveResult && (
            <div
              className={`p-2 rounded text-sm ${
                wafRemoveResult.success
                  ? 'bg-green-50 border border-green-300'
                  : 'bg-red-50 border border-red-300'
              }`}
            >
              <p className="font-medium">{wafRemoveResult.success ? '✓ 解除成功' : '✗ 失敗'}</p>
              <p className="text-xs">{wafRemoveResult.message}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
