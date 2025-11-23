/**
 * @fileoverview CloudFrontアクセスログとブロックIPの地理的分布を地図上に表示するコンポーネント
 *
 * このファイルは、Leafletを使用してCloudFrontのアクセスログおよび
 * WAFによってブロックされたIPアドレスの地理的分布を
 * インタラクティブな世界地図上に可視化します。
 *
 * 主な機能:
 * - アクセスログの地理的分布をマーカークラスターで表示
 * - ブロックされたIPアドレスの地理的分布を表示（集約/詳細モード）
 * - マーカーのカスタマイズ（ユニークIP数/アクセス数）
 * - ロケーション別の詳細ログ表示
 * - 複数のフィルター条件によるログ検索
 */
import { format } from 'date-fns';
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet/dist/leaflet.css';
import { useCallback, useEffect, useRef, useState } from 'react';
import { CloudFrontService } from '../services/CloudFrontService';
import type {
  BlockedIPGeoLocation,
  BlockedIPsDetailGeoResponse,
  BlockedIPsGeoResponse,
  BlockedIPWithGeo,
  GeoLocation,
  GeoLogsResponse,
  LogEntry,
  RawLogsResponse,
} from '../types';
import { LogDetailModal } from './LogDetailModal';
import { LogsTable } from './LogsTable';

// プロダクションビルドでのデフォルトマーカーアイコンの修正
// biome-ignore lint/suspicious/noExplicitAny: Leaflet内部プロパティへのアクセスが必要
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

/**
 * マップの表示モード
 * - 'access-logs': アクセスログの地理的分布を表示
 * - 'blocked-ips': ブロックされたIPの地理的分布を表示
 */
type MapMode = 'access-logs' | 'blocked-ips';

/**
 * ブロックIPの表示モード
 * - 'aggregated': 地域ごとに集約して表示
 * - 'detailed': 個別のIPを詳細に表示
 */
type BlockedIPsDisplayMode = 'aggregated' | 'detailed';

/**
 * CloudFrontログとブロックIPの地理的分布を地図上に表示するメインコンポーネント
 *
 * Leafletマップを使用して、CloudFrontのアクセスログやWAFでブロックされた
 * IPアドレスの地理的分布をインタラクティブに可視化します。
 * マーカークラスタリング機能により、大量のデータを効率的に表示できます。
 *
 * @returns 地理的ログ分布マップコンポーネント
 */
export default function GeoLogMap() {
  const [profile, setProfile] = useState('default');
  const [distributionId, setDistributionId] = useState('');
  const [startDate, setStartDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [endDate, setEndDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [geoData, setGeoData] = useState<GeoLogsResponse | null>(null);
  const [blockedIPsGeoData, setBlockedIPsGeoData] = useState<BlockedIPsGeoResponse | null>(null);
  const [blockedIPsDetailData, setBlockedIPsDetailData] =
    useState<BlockedIPsDetailGeoResponse | null>(null);
  const [mapMode, setMapMode] = useState<MapMode>('access-logs');
  const [blockedIPsDisplayMode, setBlockedIPsDisplayMode] =
    useState<BlockedIPsDisplayMode>('aggregated');
  const [markerCountMode, setMarkerCountMode] = useState<'unique-ips' | 'access-count'>(
    'unique-ips'
  );
  const [distributions, setDistributions] = useState<
    Array<{ id: string; domain: string; aliases?: string[] }>
  >([]);

  // アクセスログ用のフィルター状態
  const [uriFilter, setUriFilter] = useState('');
  const [userAgentFilter, setUserAgentFilter] = useState('');
  const [refererFilter, setRefererFilter] = useState('');
  const [queryFilter, setQueryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [methodFilter, setMethodFilter] = useState('');
  const [excludeStaticFiles, setExcludeStaticFiles] = useState(false);

  const [selectedLocation, setSelectedLocation] = useState<GeoLocation | null>(null);
  const [locationLogs, setLocationLogs] = useState<LogEntry[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [logsCache, setLogsCache] = useState<Map<string, LogEntry[]>>(new Map());

  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markerClusterGroupRef = useRef<L.MarkerClusterGroup | null>(null);

  /**
   * 指定されたロケーションの詳細ログを取得して表示する
   *
   * ロケーション内の全IPアドレスのログを一度に取得し、キャッシュします。
   * キャッシュがある場合は再取得せずにキャッシュから表示します。
   *
   * @param location - 詳細ログを表示する地理的ロケーション
   */
  const handleShowLocationLogs = useCallback(
    async (location: GeoLocation) => {
      setSelectedLocation(location);

      // ロケーションのIPからキャッシュキーを作成
      const cacheKey = location.ips.sort().join(',');

      // すでにこのロケーションのログがキャッシュにあるか確認
      if (logsCache.has(cacheKey)) {
        console.log('Using cached logs for location:', location.city);
        setLocationLogs(logsCache.get(cacheKey) || []);
        return;
      }

      setLoadingLogs(true);

      try {
        const service = new CloudFrontService(profile);

        // このロケーション内の全IPのログを1つのリクエストで取得
        const response: RawLogsResponse = await service.listRawLogs(
          distributionId,
          startDate,
          endDate,
          undefined, // clientIp (single)
          undefined, // uriPath
          userAgentFilter || undefined, // userAgent
          undefined, // referrer
          undefined, // queryString
          startTime || undefined, // startTime
          endTime || undefined, // endTime
          1, // page
          10000, // perPage - Increased page size for multiple IPs
          location.ips, // clientIps - 全IPを一度に渡す
          excludeStaticFiles // 静的ファイル除外設定を適用
        );

        // 日付/時刻で降順にソート
        const allLogs = response.logs.sort((a, b) => {
          const dateA = new Date(`${a.date}T${a.time}`);
          const dateB = new Date(`${b.date}T${b.time}`);
          return dateB.getTime() - dateA.getTime();
        });

        // キャッシュに保存
        setLogsCache((prev) => new Map(prev).set(cacheKey, allLogs));
        setLocationLogs(allLogs);
        console.log(
          `Fetched and cached logs for location: ${location.city} (${location.ips.length} IPs, ${allLogs.length} logs)`
        );
      } catch (err) {
        console.error('Failed to load location logs:', err);
      } finally {
        setLoadingLogs(false);
      }
    },
    [
      profile,
      distributionId,
      startDate,
      endDate,
      startTime,
      endTime,
      userAgentFilter,
      excludeStaticFiles,
      logsCache,
    ]
  );

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // マップを初期化
    const map = L.map(mapContainerRef.current, {
      zoomControl: true,
    }).setView([20, 0], 2);
    mapRef.current = map;

    // OpenStreetMapタイルを追加
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    // マーカークラスターグループを初期化
    const markerClusterGroup = L.markerClusterGroup({
      chunkedLoading: true,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
    });
    markerClusterGroupRef.current = markerClusterGroup;
    map.addLayer(markerClusterGroup);

    // モーダルの下になるようにマップペインのz-indexを設定
    const mapPane = map.getPane('mapPane');
    if (mapPane) {
      mapPane.style.zIndex = '1';
    }

    // クリーンアップ
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // アクセスログのmarkerCountMode変更時にマーカーを再描画
  useEffect(() => {
    if (!geoData || !mapRef.current || !markerClusterGroupRef.current) return;

    markerClusterGroupRef.current.clearLayers();

    geoData.locations.forEach((location: GeoLocation) => {
      // モードに基づいて表示値を決定
      const displayValue = markerCountMode === 'unique-ips' ? location.ips.length : location.count;

      const marker = L.marker([location.lat, location.lon], {
        // @ts-expect-error - クラスター計算用のカスタムプロパティ
        displayValue: displayValue,
      });

      // カウントに基づいてカスタムアイコンを作成
      const iconSize = Math.min(50, 20 + Math.log(displayValue) * 5);
      const customIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
          background-color: rgba(220, 38, 38, 0.7);
          border: 2px solid white;
          border-radius: 50%;
          width: ${iconSize}px;
          height: ${iconSize}px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 12px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        ">${displayValue}</div>`,
        iconSize: [iconSize, iconSize],
        iconAnchor: [iconSize / 2, iconSize / 2],
      });

      marker.setIcon(customIcon);

      // イベントをトリガーするボタン付きのポップアップコンテンツを作成
      const popupContent = document.createElement('div');
      popupContent.style.minWidth = '200px';
      popupContent.innerHTML = `
        <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold;">${location.city}, ${location.country}</h3>
        <p style="margin: 4px 0;"><strong>Unique IPs:</strong> ${location.ips.length}</p>
        <p style="margin: 4px 0;"><strong>Accesses:</strong> ${location.count}</p>
      `;

      const viewButton = document.createElement('button');
      viewButton.textContent = 'View Logs';
      viewButton.style.cssText = `
        margin-top: 8px;
        padding: 6px 12px;
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
      `;
      viewButton.addEventListener('click', () => {
        handleShowLocationLogs(location);
      });

      popupContent.appendChild(viewButton);
      marker.bindPopup(popupContent);

      markerClusterGroupRef.current?.addLayer(marker);
    });
  }, [markerCountMode, geoData, handleShowLocationLogs]);

  // ブロックIP（集約）のmarkerCountMode変更時にマーカーを再描画
  useEffect(() => {
    if (!blockedIPsGeoData || !mapRef.current || !markerClusterGroupRef.current) return;

    markerClusterGroupRef.current.clearLayers();

    blockedIPsGeoData.locations.forEach((location: BlockedIPGeoLocation) => {
      const marker = L.marker([location.lat, location.lon]);

      // モードに基づいて表示値を決定
      const displayValue =
        markerCountMode === 'unique-ips' ? location.cidrs.length : location.count;

      // カウントに基づいてカスタムアイコンを作成（ブロックIPは青色）
      const iconSize = Math.min(50, 20 + Math.log(displayValue) * 5);
      const customIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
          background-color: rgba(37, 99, 235, 0.7);
          border: 2px solid white;
          border-radius: 50%;
          width: ${iconSize}px;
          height: ${iconSize}px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 12px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        ">${displayValue}</div>`,
        iconSize: [iconSize, iconSize],
        iconAnchor: [iconSize / 2, iconSize / 2],
      });

      marker.setIcon(customIcon);

      // ブロックIP用のポップアップコンテンツを作成
      const popupContent = document.createElement('div');
      popupContent.style.minWidth = '250px';
      popupContent.innerHTML = `
        <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold;">🚫 ${location.city}, ${location.country}</h3>
        <p style="margin: 4px 0;"><strong>Unique IPs/CIDRs:</strong> ${location.cidrs.length}</p>
        <p style="margin: 4px 0;"><strong>Total Entries:</strong> ${location.count}</p>
        <p style="margin: 4px 0;"><strong>IP Sets:</strong> ${location.ipSetNames.join(', ')}</p>
        <details style="margin-top: 8px;">
          <summary style="cursor: pointer; font-weight: 500;">View CIDRs</summary>
          <div style="margin-top: 8px; max-height: 200px; overflow-y: auto;">
            ${location.cidrs.map((cidr) => `<div style="padding: 2px 0; font-family: monospace; font-size: 11px;">${cidr}</div>`).join('')}
          </div>
        </details>
      `;

      marker.bindPopup(popupContent);

      markerClusterGroupRef.current?.addLayer(marker);
    });
  }, [markerCountMode, blockedIPsGeoData]);

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
   * ブロックされたIPの地理的分布を検索して地図に表示する
   *
   * WAF IP Setに登録されているブロック対象IPの地理情報を取得し、
   * 集約モードまたは詳細モードで地図上にマーカーを配置します。
   * 詳細モードでは大量データの場合に警告を表示します。
   */
  const handleSearchBlockedIPs = async () => {
    if (!distributionId) {
      setError('Please select a distribution');
      return;
    }

    setLoading(true);
    setLoadingMessage('ブロックされたIPリストを取得中...');
    setError(null);

    try {
      const service = new CloudFrontService(profile);

      if (blockedIPsDisplayMode === 'aggregated') {
        // 集約モード - 地域ごとにグループ化
        setLoadingMessage('IPアドレスの地理情報を取得中...');
        const response = await service.getBlockedIPsGeo(distributionId);
        setBlockedIPsGeoData(response);
        setBlockedIPsDetailData(null);

        setLoadingMessage('地図にマーカーを配置中...');

        // ブロックIP用のマップマーカーを更新
        if (mapRef.current && markerClusterGroupRef.current) {
          markerClusterGroupRef.current.clearLayers();

          response.locations.forEach((location: BlockedIPGeoLocation) => {
            const marker = L.marker([location.lat, location.lon]);

            // モードに基づいて表示値を決定
            const displayValue =
              markerCountMode === 'unique-ips' ? location.cidrs.length : location.count;

            // カウントに基づいてカスタムアイコンを作成（ブロックIPは青色）
            const iconSize = Math.min(50, 20 + Math.log(displayValue) * 5);
            const customIcon = L.divIcon({
              className: 'custom-marker',
              html: `<div style="
                background-color: rgba(37, 99, 235, 0.7);
                border: 2px solid white;
                border-radius: 50%;
                width: ${iconSize}px;
                height: ${iconSize}px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
              ">${displayValue}</div>`,
              iconSize: [iconSize, iconSize],
              iconAnchor: [iconSize / 2, iconSize / 2],
            });

            marker.setIcon(customIcon);

            // ブロックIP用のポップアップコンテンツを作成
            const popupContent = document.createElement('div');
            popupContent.style.minWidth = '250px';
            popupContent.innerHTML = `
              <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold;">🚫 ${location.city}, ${location.country}</h3>
              <p style="margin: 4px 0;"><strong>Unique IPs/CIDRs:</strong> ${location.cidrs.length}</p>
              <p style="margin: 4px 0;"><strong>Total Entries:</strong> ${location.count}</p>
              <p style="margin: 4px 0;"><strong>IP Sets:</strong> ${location.ipSetNames.join(', ')}</p>
              <details style="margin-top: 8px;">
                <summary style="cursor: pointer; font-weight: 500;">View CIDRs</summary>
                <div style="margin-top: 8px; max-height: 200px; overflow-y: auto;">
                  ${location.cidrs.map((cidr) => `<div style="padding: 2px 0; font-family: monospace; font-size: 11px;">${cidr}</div>`).join('')}
                </div>
              </details>
            `;

            marker.bindPopup(popupContent);

            markerClusterGroupRef.current?.addLayer(marker);
          });

          // マーカーがある場合はマップを合わせる
          if (response.locations.length > 0) {
            const group = new L.FeatureGroup(
              response.locations.map((loc: BlockedIPGeoLocation) => L.marker([loc.lat, loc.lon]))
            );
            mapRef.current.fitBounds(group.getBounds().pad(0.1));
          }
        }

        if (response.locations.length === 0) {
          setError(response.message || 'No blocked IPs found');
        }
      } else {
        // 詳細モード - 個別のIPを表示
        // まず集約表示で件数を確認
        setLoadingMessage('ブロックIPの件数を確認中...');
        const aggregatedResponse = await service.getBlockedIPsGeo(distributionId);

        // 100件以上の場合は警告
        if (aggregatedResponse.total > 100) {
          const estimatedMinutes = Math.ceil(((aggregatedResponse.total / 100) * 4.5) / 60);
          const estimatedSeconds = Math.ceil((aggregatedResponse.total / 100) * 4.5);
          const timeDisplay =
            estimatedMinutes >= 2 ? `約${estimatedMinutes}分` : `約${estimatedSeconds}秒`;

          const proceed = window.confirm(
            `⚠️ 警告: ${aggregatedResponse.total}件のブロックIPが見つかりました。\n\n` +
              '詳細表示モードでは、各IPの地理情報を個別に取得するため、処理に時間がかかります。\n' +
              `推定時間: ${timeDisplay} (APIレート制限: 15リクエスト/分)\n\n` +
              '続行しますか？\n\n' +
              '※100件以上の場合は集約表示モードをお勧めします。'
          );

          if (!proceed) {
            setLoading(false);
            setLoadingMessage('');
            return;
          }
        }

        setLoadingMessage(
          `IPアドレスの詳細な地理情報を取得中...\n(${aggregatedResponse.total}件のIPを処理中、お待ちください)`
        );
        const response = await service.getBlockedIPsDetailGeo(distributionId);
        setBlockedIPsDetailData(response);
        setBlockedIPsGeoData(null);

        setLoadingMessage('地図にマーカーを配置中...');

        // 詳細なブロックIP用のマップマーカーを更新
        if (mapRef.current && markerClusterGroupRef.current) {
          markerClusterGroupRef.current.clearLayers();

          response.blockedIps.forEach((blockedIP: BlockedIPWithGeo) => {
            if (!blockedIP.geolocation) return;

            const { lat, lon, city, country, isp } = blockedIP.geolocation;
            const marker = L.marker([lat, lon]);

            // CIDRカテゴリラベルを取得
            const getCategoryLabel = (category: string) => {
              switch (category) {
                case 'single':
                  return '単一IP';
                case 'small':
                  return '小規模ブロック (≤256)';
                case 'medium':
                  return '中規模ブロック (≤65K)';
                case 'large':
                  return '大規模ブロック (≤16M)';
                case 'very_large':
                  return '超大規模ブロック (>16M)';
                default:
                  return '不明';
              }
            };

            // CIDRカテゴリに基づいて警告メッセージを取得
            const getWarningMessage = (category: string) => {
              if (category === 'medium' || category === 'large' || category === 'very_large') {
                return '<p style="margin: 8px 0; padding: 8px; background-color: #fef3c7; border-left: 4px solid #f59e0b; font-size: 12px;">⚠️ この範囲の代表地点です。実際のブロック対象地域は広範囲に及ぶ可能性があります。</p>';
              }
              return '';
            };

            // ブロックIP用のカスタムアイコンを作成（黒/ダークグレー）
            const customIcon = L.divIcon({
              className: 'blocked-ip-marker',
              html: `<div style="
                background-color: rgba(0, 0, 0, 0.8);
                border: 2px solid white;
                border-radius: 50%;
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
              ">🚫</div>`,
              iconSize: [28, 28],
              iconAnchor: [14, 14],
            });

            marker.setIcon(customIcon);

            // ポップアップコンテンツを作成
            const popupContent = document.createElement('div');
            popupContent.style.minWidth = '250px';
            popupContent.innerHTML = `
              <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold; color: #dc2626;">
                🚫 ブロック中
              </h3>
              <div style="border-bottom: 1px solid #e5e7eb; margin-bottom: 8px;"></div>
              <p style="margin: 4px 0;"><strong>場所:</strong> ${city || 'Unknown'}, ${country || 'Unknown'}</p>
              <p style="margin: 4px 0;"><strong>IP:</strong> ${blockedIP.ip}</p>
              <p style="margin: 4px 0;"><strong>CIDR:</strong> ${blockedIP.cidr}</p>
              <p style="margin: 4px 0;"><strong>範囲:</strong> ${getCategoryLabel(blockedIP.cidrCategory)}</p>
              ${blockedIP.representativeIp !== blockedIP.ip ? `<p style="margin: 4px 0;"><strong>代表IP:</strong> ${blockedIP.representativeIp}</p>` : ''}
              <p style="margin: 4px 0;"><strong>IP Set:</strong> ${blockedIP.ipSetName}</p>
              ${isp ? `<p style="margin: 4px 0;"><strong>ISP:</strong> ${isp}</p>` : ''}
              ${getWarningMessage(blockedIP.cidrCategory)}
            `;

            marker.bindPopup(popupContent);
            markerClusterGroupRef.current?.addLayer(marker);
          });

          // マーカーがある場合はマップを合わせる
          if (response.blockedIps.length > 0) {
            const group = new L.FeatureGroup(
              response.blockedIps
                .filter((ip) => ip.geolocation)
                .map((ip) => {
                  const geo = ip.geolocation;
                  if (geo) {
                    return L.marker([geo.lat, geo.lon]);
                  }
                  return null;
                })
                .filter((marker): marker is L.Marker => marker !== null)
            );
            mapRef.current.fitBounds(group.getBounds().pad(0.1));
          }
        }

        if (response.total === 0) {
          setError('No blocked IPs found with geolocation data');
        } else if (response.totalWithoutGeo > 0) {
          console.log(
            `${response.totalWithoutGeo} blocked IPs could not be geolocated and are not shown on the map`
          );
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get blocked IPs geo data');
      setBlockedIPsGeoData(null);
      setBlockedIPsDetailData(null);
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  /**
   * 現在のマップモードに応じて検索を実行する
   *
   * アクセスログモードの場合はhandleSearchAccessLogsを、
   * ブロックIPモードの場合はhandleSearchBlockedIPsを呼び出します。
   */
  const handleSearch = async () => {
    if (mapMode === 'access-logs') {
      if (!distributionId || !startDate || !endDate) {
        setError('Please fill in distribution, start date, and end date');
        return;
      }
      await handleSearchAccessLogs();
    } else {
      await handleSearchBlockedIPs();
    }
  };

  /**
   * アクセスログの地理的分布を検索して地図に表示する
   *
   * 指定された条件でCloudFrontアクセスログを検索し、
   * IPアドレスの地理情報を取得して地図上にマーカーを配置します。
   * 既存のログキャッシュはクリアされます。
   */
  const handleSearchAccessLogs = async () => {
    setLoading(true);
    setLoadingMessage('ログファイルを検索中...');
    setError(null);

    // 新しいデータを検索する際にログキャッシュをクリア
    setLogsCache(new Map());

    try {
      const service = new CloudFrontService(profile);
      const response = await service.getGeoLogs(
        distributionId,
        startDate,
        endDate,
        startTime || undefined,
        endTime || undefined,
        uriFilter || undefined,
        userAgentFilter || undefined,
        refererFilter || undefined,
        queryFilter || undefined,
        statusFilter || undefined,
        methodFilter || undefined,
        excludeStaticFiles
      );

      setGeoData(response);

      setLoadingMessage('地図にマーカーを配置中...');

      // マップマーカーを更新
      if (mapRef.current && markerClusterGroupRef.current) {
        markerClusterGroupRef.current.clearLayers();

        response.locations.forEach((location: GeoLocation) => {
          const marker = L.marker([location.lat, location.lon]);

          // モードに基づいて表示値を決定
          const displayValue =
            markerCountMode === 'unique-ips' ? location.ips.length : location.count;

          // カウントに基づいてカスタムアイコンを作成
          const iconSize = Math.min(50, 20 + Math.log(displayValue) * 5);
          const customIcon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="
              background-color: rgba(220, 38, 38, 0.7);
              border: 2px solid white;
              border-radius: 50%;
              width: ${iconSize}px;
              height: ${iconSize}px;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-weight: bold;
              font-size: 12px;
              box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            ">${displayValue}</div>`,
            iconSize: [iconSize, iconSize],
            iconAnchor: [iconSize / 2, iconSize / 2],
          });

          marker.setIcon(customIcon);

          // イベントをトリガーするボタン付きのポップアップコンテンツを作成
          const popupContent = document.createElement('div');
          popupContent.style.minWidth = '200px';
          popupContent.innerHTML = `
            <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold;">${location.city}, ${location.country}</h3>
            <p style="margin: 4px 0;"><strong>Unique IPs:</strong> ${location.ips.length}</p>
            <p style="margin: 4px 0;"><strong>Accesses:</strong> ${location.count}</p>
          `;

          const viewButton = document.createElement('button');
          viewButton.textContent = 'View Logs';
          viewButton.style.cssText = `
            margin-top: 8px;
            padding: 6px 12px;
            background-color: #3b82f6;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
          `;
          viewButton.addEventListener('click', () => {
            handleShowLocationLogs(location);
          });

          popupContent.appendChild(viewButton);
          marker.bindPopup(popupContent);

          markerClusterGroupRef.current?.addLayer(marker);
        });

        // マーカーがある場合はマップを合わせる
        if (response.locations.length > 0) {
          const group = new L.FeatureGroup(
            response.locations.map((loc: GeoLocation) => L.marker([loc.lat, loc.lon]))
          );
          mapRef.current.fitBounds(group.getBounds().pad(0.1));
        }
      }

      if (response.locations.length === 0) {
        setError('No geo data found for the specified criteria');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get geo logs');
      setGeoData(null);
    } finally {
      setLoading(false);
      setLoadingMessage('');
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
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Distribution and Mode</h2>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="distribution"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
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

            <div>
              <span className="block text-sm font-medium text-gray-700 mb-2">Map Mode:</span>
              <div className="flex gap-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="access-logs"
                    checked={mapMode === 'access-logs'}
                    onChange={(e) => setMapMode(e.target.value as MapMode)}
                    className="mr-2"
                  />
                  <span>Access Logs (アクセスログ)</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="blocked-ips"
                    checked={mapMode === 'blocked-ips'}
                    onChange={(e) => setMapMode(e.target.value as MapMode)}
                    className="mr-2"
                  />
                  <span>Blocked IPs (ブロックIP)</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* フィルタ条件 */}
      {distributionId && mapMode === 'access-logs' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Time Range</h2>
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

            {/* ログフィルタ */}
            <div className="border-t pt-4 mt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Filters (Optional)</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="uriFilter"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    URI Path:
                  </label>
                  <input
                    id="uriFilter"
                    type="text"
                    value={uriFilter}
                    onChange={(e) => setUriFilter(e.target.value)}
                    placeholder="e.g. /api/"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="userAgentFilter"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    User Agent:
                  </label>
                  <input
                    id="userAgentFilter"
                    type="text"
                    value={userAgentFilter}
                    onChange={(e) => setUserAgentFilter(e.target.value)}
                    placeholder="e.g. Chrome, Googlebot"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="refererFilter"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Referer:
                  </label>
                  <input
                    id="refererFilter"
                    type="text"
                    value={refererFilter}
                    onChange={(e) => setRefererFilter(e.target.value)}
                    placeholder="e.g. google.com"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="queryFilter"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Query String:
                  </label>
                  <input
                    id="queryFilter"
                    type="text"
                    value={queryFilter}
                    onChange={(e) => setQueryFilter(e.target.value)}
                    placeholder="e.g. id=123"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="statusFilter"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Status Code:
                  </label>
                  <input
                    id="statusFilter"
                    type="text"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    placeholder="e.g. 404"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="methodFilter"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    HTTP Method:
                  </label>
                  <select
                    id="methodFilter"
                    value={methodFilter}
                    onChange={(e) => setMethodFilter(e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Methods</option>
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                    <option value="PATCH">PATCH</option>
                    <option value="HEAD">HEAD</option>
                    <option value="OPTIONS">OPTIONS</option>
                  </select>
                </div>

                <div className="flex items-center">
                  <input
                    id="excludeStaticFiles"
                    type="checkbox"
                    checked={excludeStaticFiles}
                    onChange={(e) => setExcludeStaticFiles(e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="excludeStaticFiles" className="ml-2 block text-sm text-gray-700">
                    静的ファイルを除外 (js, css, 画像など)
                  </label>
                </div>

                <div className="flex items-end">
                  <button
                    type="button"
                    onClick={() => {
                      setUriFilter('');
                      setUserAgentFilter('');
                      setRefererFilter('');
                      setQueryFilter('');
                      setStatusFilter('');
                      setMethodFilter('');
                      setExcludeStaticFiles(false);
                    }}
                    className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Clear Filters
                  </button>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
              <button
                type="button"
                onClick={handleSearch}
                disabled={loading}
                className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Analyzing...' : 'Analyze Geographic Distribution'}
              </button>

              {/* マーカーカウントモード切り替え */}
              {geoData && (
                <div className="flex items-center gap-4 px-4 py-2 bg-gray-50 rounded-md">
                  <span className="text-sm font-medium text-gray-700">マーカー表示:</span>
                  <div className="flex gap-3">
                    <label className="flex items-center cursor-pointer">
                      <input
                        type="radio"
                        value="unique-ips"
                        checked={markerCountMode === 'unique-ips'}
                        onChange={() => setMarkerCountMode('unique-ips')}
                        className="mr-2"
                      />
                      <span className="text-sm">ユニークIP数</span>
                    </label>
                    <label className="flex items-center cursor-pointer">
                      <input
                        type="radio"
                        value="access-count"
                        checked={markerCountMode === 'access-count'}
                        onChange={() => setMarkerCountMode('access-count')}
                        className="mr-2"
                      />
                      <span className="text-sm">アクセス数</span>
                    </label>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ブロックIPモード用の検索ボタン */}
      {distributionId && mapMode === 'blocked-ips' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Analyze Blocked IPs</h2>
          <p className="text-sm text-gray-600 mb-4">
            View the geographic distribution of IP addresses currently blocked in WAF IP Sets.
          </p>

          {/* 表示モード切り替え */}
          <div className="mb-4">
            <span className="block text-sm font-medium text-gray-700 mb-2">表示モード:</span>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  value="aggregated"
                  checked={blockedIPsDisplayMode === 'aggregated'}
                  onChange={(e) =>
                    setBlockedIPsDisplayMode(e.target.value as BlockedIPsDisplayMode)
                  }
                  className="mr-2"
                />
                <span>集約表示 (地域ごとにグループ化)</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  value="detailed"
                  checked={blockedIPsDisplayMode === 'detailed'}
                  onChange={(e) =>
                    setBlockedIPsDisplayMode(e.target.value as BlockedIPsDisplayMode)
                  }
                  className="mr-2"
                />
                <span>詳細表示 (個別IPを表示)</span>
              </label>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {blockedIPsDisplayMode === 'aggregated'
                ? '📊 地理的に近いIPをまとめて表示します。大量のIPがある場合に推奨。'
                : '🔍 個別のIPと詳細情報を表示します。CIDR範囲の情報も確認できます。'}
            </p>
          </div>

          <button
            type="button"
            onClick={handleSearch}
            disabled={loading}
            className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyzing...' : 'Show Blocked IPs on Map'}
          </button>
        </div>
      )}

      {/* エラーメッセージ */}
      {error && (
        <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      {/* 読み込み進捗メッセージ */}
      {loading && loadingMessage && (
        <div className="bg-blue-50 border border-blue-400 text-blue-700 px-4 py-3 rounded relative">
          <div className="flex items-center">
            <div className="mr-3">
              <svg
                className="animate-spin h-5 w-5 text-blue-700"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                role="img"
                aria-label="Loading spinner"
              >
                <title>Loading</title>
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </div>
            <div className="whitespace-pre-line">
              <strong className="font-bold">処理中: </strong>
              <span>{loadingMessage}</span>
            </div>
          </div>
        </div>
      )}

      {/* 統計情報 */}
      {geoData && mapMode === 'access-logs' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Statistics</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <div className="text-sm text-blue-600 font-medium">Total Logs</div>
              <div className="text-2xl font-bold text-blue-900">
                {geoData.total.toLocaleString()}
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <div className="text-sm text-green-600 font-medium">Locations</div>
              <div className="text-2xl font-bold text-green-900">{geoData.locations.length}</div>
            </div>
            <div className="bg-purple-50 p-4 rounded">
              <div className="text-sm text-purple-600 font-medium">Unique IPs</div>
              <div className="text-2xl font-bold text-purple-900">
                {geoData.locations.reduce((sum, loc) => sum + loc.ips.length, 0)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ブロックIPの統計情報 */}
      {blockedIPsGeoData && mapMode === 'blocked-ips' && blockedIPsDisplayMode === 'aggregated' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Blocked IPs Statistics (集約表示)
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <div className="text-sm text-blue-600 font-medium">Total Blocked IPs/CIDRs</div>
              <div className="text-2xl font-bold text-blue-900">
                {blockedIPsGeoData.total.toLocaleString()}
              </div>
            </div>
            <div className="bg-red-50 p-4 rounded">
              <div className="text-sm text-red-600 font-medium">Locations</div>
              <div className="text-2xl font-bold text-red-900">
                {blockedIPsGeoData.locations.length}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 詳細なブロックIPの統計情報 */}
      {blockedIPsDetailData &&
        mapMode === 'blocked-ips' &&
        blockedIPsDisplayMode === 'detailed' && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Blocked IPs Statistics (詳細表示)
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded">
                <div className="text-sm text-blue-600 font-medium">Total with Geolocation</div>
                <div className="text-2xl font-bold text-blue-900">
                  {blockedIPsDetailData.total.toLocaleString()}
                </div>
              </div>
              <div className="bg-yellow-50 p-4 rounded">
                <div className="text-sm text-yellow-600 font-medium">Without Geolocation</div>
                <div className="text-2xl font-bold text-yellow-900">
                  {blockedIPsDetailData.totalWithoutGeo.toLocaleString()}
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <div className="text-sm text-green-600 font-medium">IP Sets</div>
                <div className="text-2xl font-bold text-green-900">
                  {blockedIPsDetailData.ipSets.length}
                </div>
              </div>
            </div>
          </div>
        )}

      {/* マップ */}
      <div className="bg-white shadow rounded-lg p-6 relative" style={{ zIndex: 1 }}>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Geographic Distribution Map</h2>
        <div
          ref={mapContainerRef}
          style={{
            height: '600px',
            width: '100%',
            borderRadius: '8px',
            position: 'relative',
            zIndex: 1,
          }}
        />
        <p className="text-sm text-gray-500 mt-2">
          Click on markers to view details. Marker size represents access count.
        </p>
      </div>

      {/* ロケーションログモーダル */}
      {selectedLocation && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4"
          style={{ zIndex: 9999 }}
        >
          <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-6 border-b">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold">
                    Logs from {selectedLocation.city}, {selectedLocation.country}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Total Accesses: {selectedLocation.count} | Unique IPs:{' '}
                    {selectedLocation.ips.length} | Showing: {locationLogs.length} logs
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedLocation(null)}
                  className="text-gray-400 hover:text-gray-600"
                  aria-label="Close"
                >
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Close icon"
                  >
                    <title>Close</title>
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-6">
              {loadingLogs ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                  <p className="mt-2 text-gray-600">Loading logs...</p>
                </div>
              ) : (
                <LogsTable
                  logs={locationLogs}
                  showColumnSelector={true}
                  profile={profile}
                  distributionId={distributionId}
                  onLogClick={(log) => setSelectedLog(log)}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* ログ詳細モーダル */}
      {selectedLog && (
        <LogDetailModal
          entry={selectedLog}
          profile={profile}
          distributionId={distributionId}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </div>
  );
}
