/**
 * @fileoverview 単一の地理的位置を地図上に表示するコンポーネント
 *
 * このファイルは、Leafletを使用して特定の緯度経度座標を
 * OpenStreetMapのタイル上にマーカーで表示します。
 * ログ詳細モーダルなどで、IPアドレスの位置情報を視覚化する際に使用されます。
 */
import L from 'leaflet';
import { useEffect, useRef } from 'react';
import 'leaflet/dist/leaflet.css';

/**
 * LocationMapコンポーネントのProps
 */
interface MapProps {
  /** 緯度 */
  lat: number;
  /** 経度 */
  lon: number;
  /** 都市名（任意）- マーカーのポップアップに表示されます */
  city?: string;
}

// プロダクションビルドでのデフォルトマーカーアイコンの修正
// biome-ignore lint/suspicious/noExplicitAny: Leaflet内部プロパティへのアクセスが必要
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

/**
 * 単一の地理的位置を地図上に表示するコンポーネント
 *
 * OpenStreetMapを使用して、指定された緯度経度の位置にマーカーを表示します。
 * Google MapsとOpenStreetMapへのリンクも提供します。
 *
 * @param props - コンポーネントのProps
 * @param props.lat - 表示する位置の緯度
 * @param props.lon - 表示する位置の経度
 * @param props.city - 都市名（任意）
 * @returns LocationMapコンポーネント
 */
export function LocationMap({ lat, lon, city }: MapProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // マップを初期化
    const map = L.map(mapContainerRef.current).setView([lat, lon], 12);
    mapRef.current = map;

    // OpenStreetMapタイルを追加
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    // マーカーを追加
    L.marker([lat, lon])
      .addTo(map)
      .bindPopup(city || `${lat}, ${lon}`)
      .openPopup();

    // クリーンアップ
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [lat, lon, city]);

  return (
    <div className="mt-2">
      <div ref={mapContainerRef} style={{ height: '200px', width: '100%', borderRadius: '4px' }} />
      <p className="text-xs text-gray-500 mt-1">
        <a
          href={`https://www.google.com/maps?q=${lat},${lon}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          Google Mapsで開く ↗
        </a>
        {' | '}
        <a
          href={`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}&zoom=12`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          OpenStreetMapで開く ↗
        </a>
      </p>
    </div>
  );
}
