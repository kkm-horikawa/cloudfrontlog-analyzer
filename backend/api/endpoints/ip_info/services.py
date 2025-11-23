"""IPジオロケーションサービスモジュール。

このモジュールは、ip-api.comを使用したIPアドレスのジオロケーション検索機能を提供します。
データベースキャッシュとWHOIS情報の統合により、効率的な検索を実現しています。

主な機能:
- IPアドレスのジオロケーション情報取得（緯度経度、国、都市など）
- バッチAPIによる複数IPの一括検索
- データベースキャッシュによる高速化
- WHOIS情報の統合

Example:
    >>> ip_info = get_ip_info("8.8.8.8")
    >>> ip_info['country']
    'United States'
    >>> ip_info['lat']
    37.386
"""

import ipaddress
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from typing import Dict
from typing import List
from typing import Optional

import requests


# IP情報のインメモリキャッシュ（同じリクエスト内での高速アクセス用）
_ip_cache: Dict[str, Optional[Dict]] = {}


def get_ip_info_from_db(ip_address: str) -> Optional[Dict]:
    """データベースキャッシュからIP情報を取得します。

    データベースに保存されているIPアドレスのジオロケーション情報とWHOIS情報を取得します。
    キャッシュヒット時にはヒット回数をインクリメントします。

    Args:
        ip_address (str): 検索するIPアドレス
            例: "8.8.8.8", "2001:4860:4860::8888"

    Returns:
        Optional[Dict]: IP情報を含む辞書、または見つからない場合はNone。
            辞書には以下のキーが含まれます:
            - ip (str): IPアドレス
            - country (str): 国名
            - city (str): 都市名
            - lat (float): 緯度
            - lon (float): 経度
            - whois (Optional[Dict]): WHOIS情報（利用可能な場合）

    Example:
        >>> ip_info = get_ip_info_from_db("8.8.8.8")
        >>> ip_info['country'] if ip_info else None
        'United States'
    """
    from api.models import IPGeolocation

    try:
        geo = IPGeolocation.objects.get(ip_address=ip_address)

        # キャッシュヒット回数を更新
        geo.hit_count += 1
        geo.save(update_fields=["hit_count"])

        result = {
            "ip": geo.ip_address,
            "continent": geo.continent,
            "continentCode": geo.continent_code,
            "country": geo.country,
            "countryCode": geo.country_code,
            "region": geo.region,
            "city": geo.city,
            "district": geo.district,
            "zip": geo.zip_code,
            "lat": geo.latitude,
            "lon": geo.longitude,
            "timezone": geo.timezone,
            "offset": geo.offset,
            "currency": geo.currency,
            "isp": geo.isp,
            "org": geo.org,
            "asn": geo.asn,
            "asname": geo.asname,
            "mobile": geo.mobile,
            "proxy": geo.proxy,
            "hosting": geo.hosting,
        }

        # WHOIS情報が利用可能な場合は追加
        # 注意: WHOIS検索が試行されたが失敗した場合、whois_rawは空文字列""になる可能性がある
        # その場合、None（再フェッチをトリガーする）を返すのではなく、空のdictを返すべき
        if geo.whois_raw is not None:
            # WHOISが試行された（データありで成功、または空文字列で失敗）
            if geo.whois_raw or geo.whois_netname or geo.whois_org_name:
                # WHOIS取得成功
                result["whois"] = {
                    "raw": geo.whois_raw,
                    "netname": geo.whois_netname,
                    "org_name": geo.whois_org_name,
                    "country": geo.whois_country,
                    "net_range": geo.whois_net_range,
                }
            else:
                # WHOIS取得は試行されたが失敗（whois_raw == ""）
                result["whois"] = {}  # 空のdictは「試行されたが失敗」を示す
        else:
            # WHOISはまだ試行されていない - 必要に応じて呼び出し元が取得
            result["whois"] = None

        return result
    except IPGeolocation.DoesNotExist:
        return None


def save_ip_info_to_db(ip_address: str, info: Dict) -> None:
    """
    IP情報をデータベースキャッシュに保存

    Args:
        ip_address: IPアドレス
        info: IP情報のdictionary
    """
    from api.models import IPGeolocation

    try:
        defaults = {
            "continent": info.get("continent"),
            "continent_code": info.get("continentCode"),
            "country": info.get("country"),
            "country_code": info.get("countryCode"),
            "region": info.get("region"),
            "city": info.get("city"),
            "district": info.get("district"),
            "zip_code": info.get("zip"),
            "latitude": info.get("lat"),
            "longitude": info.get("lon"),
            "timezone": info.get("timezone"),
            "offset": info.get("offset"),
            "currency": info.get("currency"),
            "isp": info.get("isp"),
            "org": info.get("org"),
            "asn": info.get("asn"),
            "asname": info.get("asname"),
            "mobile": info.get("mobile"),
            "proxy": info.get("proxy"),
            "hosting": info.get("hosting"),
        }

        # WHOIS情報が利用可能な場合は追加
        whois_info = info.get("whois")
        if whois_info is not None:
            # whois_infoは以下の可能性がある: データありのdict（成功）、空のdict {}（失敗）、またはNone（未試行）
            if isinstance(whois_info, dict):
                if whois_info:  # データあり
                    defaults["whois_raw"] = whois_info.get("raw", "")
                    defaults["whois_netname"] = whois_info.get("netname")
                    defaults["whois_org_name"] = whois_info.get("org_name")
                    defaults["whois_country"] = whois_info.get("country")
                    defaults["whois_net_range"] = whois_info.get("net_range")
                else:  # 空のdict - 試行されたが失敗としてマーク
                    defaults["whois_raw"] = ""
                    defaults["whois_netname"] = None
                    defaults["whois_org_name"] = None
                    defaults["whois_country"] = None
                    defaults["whois_net_range"] = None

        IPGeolocation.objects.update_or_create(
            ip_address=ip_address,
            defaults=defaults,
        )
    except Exception as e:
        print(f"Error saving IP info to DB: {str(e)}")


def get_ip_info(ip_address: str) -> Optional[Dict]:
    """ip-api.comからIPアドレスのジオロケーション情報を取得します。

    IPアドレスのジオロケーション情報をip-api.comから取得します。
    データベースキャッシュを優先的に使用し、必要な場合のみAPIを呼び出します。
    取得した情報はWHOIS情報とともにデータベースに保存されます。

    Args:
        ip_address (str): 検索するIPアドレス
            例: "8.8.8.8", "203.0.113.1"

    Returns:
        Optional[Dict]: IP情報を含む辞書、または失敗した場合はNone。
            辞書には以下のキーが含まれます:
            - ip (str): IPアドレス
            - continent (str): 大陸名
            - country (str): 国名
            - countryCode (str): 国コード
            - region (str): 地域名
            - city (str): 都市名
            - lat (float): 緯度
            - lon (float): 経度
            - timezone (str): タイムゾーン
            - isp (str): ISP名
            - org (str): 組織名
            - asn (str): AS番号
            - whois (Optional[Dict]): WHOIS情報

    Note:
        ip-api.comの無料プランは1分あたり45リクエストの制限があります。

    Example:
        >>> ip_info = get_ip_info("8.8.8.8")
        >>> ip_info['country']
        'United States'
        >>> ip_info['isp']
        'Google LLC'
    """
    # まずインメモリキャッシュを確認
    # ただし、WHOIS情報が存在する場合のみ使用（Noneでもなくかつ空dictでもない）
    if ip_address in _ip_cache:
        cached_info = _ip_cache[ip_address]
        # WHOIS情報がある（None以外、かつ空dictでもない）場合のみ、キャッシュから返す
        if (
            cached_info
            and "whois" in cached_info
            and cached_info["whois"] not in (None, {})
        ):
            return cached_info
        # WHOIS情報がない場合は、DBを再チェックして取得を試みる
        print(f"Memory cache hit for {ip_address} but WHOIS missing, checking DB...")

    # 次にデータベースキャッシュを確認
    db_info = get_ip_info_from_db(ip_address)
    if db_info:
        print(f"DB cache hit for {ip_address}")

        # WHOIS情報が欠けている場合は、今すぐ取得
        if "whois" not in db_info or db_info["whois"] is None:
            print(f"WHOIS info missing for {ip_address}, fetching now...")
            whois_info = get_whois_info(ip_address)
            if whois_info:
                db_info["whois"] = whois_info
                # キャッシュとDBを更新
                save_ip_info_to_db(ip_address, db_info)
                print(f"✓ WHOIS info fetched and saved for {ip_address}")
            else:
                # 空のdictを保存して試行済みとしてマーク（次回のリクエストで再試行しないように）
                db_info["whois"] = {}
                save_ip_info_to_db(ip_address, db_info)
                print(f"✗ WHOIS fetch failed for {ip_address}, marked as attempted")

        # 最終結果（WHOISありまたはなし）でインメモリキャッシュを更新
        _ip_cache[ip_address] = db_info
        return db_info

    try:
        # ip-api.comの無料プラン: 1分あたり45リクエスト、APIキー不要
        response = requests.get(
            f"http://ip-api.com/json/{ip_address}",
            params={
                "fields": "status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,currency,isp,org,as,asname,mobile,proxy,hosting,query"
            },
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("status") == "success":
                result = {
                    "ip": data.get("query"),
                    "continent": data.get("continent"),
                    "continentCode": data.get("continentCode"),
                    "country": data.get("country"),
                    "countryCode": data.get("countryCode"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "district": data.get("district"),
                    "zip": data.get("zip"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "timezone": data.get("timezone"),
                    "offset": data.get("offset"),
                    "currency": data.get("currency"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                    "asn": data.get("as"),
                    "asname": data.get("asname"),
                    "mobile": data.get("mobile"),
                    "proxy": data.get("proxy"),
                    "hosting": data.get("hosting"),
                }

                # バックグラウンドでWHOIS情報を取得（ノンブロッキング）
                print(f"Fetching WHOIS info for {ip_address}...")
                whois_info = get_whois_info(ip_address)
                if whois_info:
                    result["whois"] = whois_info
                    print(f"✓ WHOIS info fetched for {ip_address}")
                else:
                    # 空のdictで試行済みとしてマーク（再試行を回避）
                    result["whois"] = {}
                    print(f"✗ WHOIS info not available for {ip_address}")

                _ip_cache[ip_address] = result
                # データベースキャッシュに保存
                save_ip_info_to_db(ip_address, result)
                print(f"API fetch and DB save for {ip_address}")
                return result
            else:
                print(f"IP lookup failed: {data.get('message', 'Unknown error')}")
                _ip_cache[ip_address] = None
                return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching IP info for {ip_address}: {str(e)}")
        _ip_cache[ip_address] = None
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        _ip_cache[ip_address] = None
        return None


def get_ip_info_batch(ip_addresses: List[str]) -> Dict[str, Optional[Dict]]:
    """バッチAPIを使用して複数のIPアドレスのジオロケーション情報を取得します。

    ip-api.comのバッチAPIを使用して、複数のIPアドレスの情報を効率的に取得します。
    データベースキャッシュを活用し、キャッシュに存在しないIPのみをAPIから取得します。
    レート制限を考慮した自動リトライ機能を備えています。

    Args:
        ip_addresses (List[str]): 検索するIPアドレスのリスト（最大100個）
            例: ["8.8.8.8", "1.1.1.1", "208.67.222.222"]

    Returns:
        Dict[str, Optional[Dict]]: IPアドレスをキー、情報を値とする辞書。
            各IP情報の辞書には以下のキーが含まれます:
            - ip (str): IPアドレス
            - country (str): 国名
            - city (str): 都市名
            - lat (float): 緯度
            - lon (float): 経度
            - その他のジオロケーション情報

    Note:
        - ip-api.comのバッチAPIは1分あたり15リクエストの制限があります
        - レート制限到達時は自動的に待機してリトライします
        - 100個を超えるIPは自動的に分割されて処理されます

    Example:
        >>> ips = ["8.8.8.8", "1.1.1.1"]
        >>> results = get_ip_info_batch(ips)
        >>> results["8.8.8.8"]["country"]
        'United States'
        >>> results["1.1.1.1"]["country"]
        'Australia'
    """
    result = {}

    # まず、インメモリキャッシュを確認
    uncached_ips = []
    for ip in ip_addresses:
        if ip in _ip_cache:
            result[ip] = _ip_cache[ip]
        else:
            uncached_ips.append(ip)

    if not uncached_ips:
        return result

    # 次に、データベースキャッシュを一括で確認
    print(
        f"Checking DB cache for {len(uncached_ips)} IPs that were not in memory cache..."
    )
    from api.models import IPGeolocation

    # すべてのIPGeolocationオブジェクトを一度にバルクフェッチ
    db_geo_objects = IPGeolocation.objects.filter(ip_address__in=uncached_ips)

    uncached_after_db = []
    db_hits = 0

    # 高速検索用のマップを作成し、バルク更新を準備
    geo_map = {}
    geo_objects_to_update = []

    for geo in db_geo_objects:
        db_hits += 1
        info = {
            "ip": geo.ip_address,
            "continent": geo.continent,
            "continentCode": geo.continent_code,
            "country": geo.country,
            "countryCode": geo.country_code,
            "region": geo.region,
            "city": geo.city,
            "district": geo.district,
            "zip": geo.zip_code,
            "lat": geo.latitude,
            "lon": geo.longitude,
            "timezone": geo.timezone,
            "offset": geo.offset,
            "currency": geo.currency,
            "isp": geo.isp,
            "org": geo.org,
            "asn": geo.asn,
            "asname": geo.asname,
            "mobile": geo.mobile,
            "proxy": geo.proxy,
            "hosting": geo.hosting,
        }
        geo_map[geo.ip_address] = info
        result[geo.ip_address] = info
        _ip_cache[geo.ip_address] = info  # インメモリキャッシュを更新

        # バルク更新の準備
        geo.hit_count += 1
        geo_objects_to_update.append(geo)

    # ヒットカウントをバルク更新（単一のUPDATEクエリ）
    if geo_objects_to_update:
        IPGeolocation.objects.bulk_update(
            geo_objects_to_update, ["hit_count"], batch_size=1000
        )

    # DB内にないIPを検索
    for ip in uncached_ips:
        if ip not in geo_map:
            uncached_after_db.append(ip)

    if db_hits > 0:
        print(f"DB cache hits: {db_hits}/{len(uncached_ips)} IPs")

    if not uncached_after_db:
        print("All IPs were found in DB cache!")
        return result

    print(f"Fetching {len(uncached_after_db)} IPs from API...")
    uncached_ips = uncached_after_db

    # キャッシュされていないIPを100個のバッチで処理（API制限）
    batch_size = 100
    batches = [
        uncached_ips[i : i + batch_size]
        for i in range(0, len(uncached_ips), batch_size)
    ]

    # 並列度: 最大10バッチを同時実行
    max_workers = 10
    print(f"Processing {len(batches)} batches with {max_workers} parallel workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 各バッチの処理をサブミット
        future_to_batch = {
            executor.submit(fetch_single_batch, batch, idx): (batch, idx)
            for idx, batch in enumerate(batches)
        }

        # 完了したものから順次処理
        for future in as_completed(future_to_batch):
            batch, idx = future_to_batch[future]
            try:
                batch_result = future.result()
                # 結果をマージ
                for ip, info in batch_result.items():
                    result[ip] = info
                    _ip_cache[ip] = info
                    if info is not None:
                        save_ip_info_to_db(ip, info)
                print(f"✓ Batch {idx + 1}/{len(batches)} completed")
            except Exception as e:
                print(f"✗ Batch {idx + 1}/{len(batches)} failed: {e}")
                for ip in batch:
                    result[ip] = None
                    _ip_cache[ip] = None

    return result


def fetch_single_batch(batch: List[str], batch_idx: int) -> Dict[str, Optional[Dict]]:
    """
    単一バッチのIP情報を取得（並列処理用）

    Args:
        batch: IPアドレスのリスト（最大100個）
        batch_idx: バッチのインデックス（ログ用）

    Returns:
        IP -> 情報のマッピング
    """
    batch_result = {}
    max_retries = 3
    retry_delay = 2

    for retry in range(max_retries):
        try:
            # POSTバッチエンドポイントを使用
            response = requests.post(
                "http://ip-api.com/batch",
                json=[
                    {
                        "query": ip,
                        "fields": "status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,currency,isp,org,as,asname,mobile,proxy,hosting,query",
                    }
                    for ip in batch
                ],
                params={"lang": "en"},
                timeout=60,
            )

            # レート制限ヘッダーを確認
            x_rl = response.headers.get("X-Rl")
            x_ttl = response.headers.get("X-Ttl")

            if x_rl is not None:
                print(
                    f"[Batch {batch_idx + 1}] Rate limit: {x_rl} requests remaining, resets in {x_ttl}s"
                )

            if response.status_code == 200:
                batch_results = response.json()

                for data in batch_results:
                    if data.get("status") == "success":
                        ip = data.get("query")
                        info = {
                            "ip": ip,
                            "continent": data.get("continent"),
                            "continentCode": data.get("continentCode"),
                            "country": data.get("country"),
                            "countryCode": data.get("countryCode"),
                            "region": data.get("regionName"),
                            "city": data.get("city"),
                            "district": data.get("district"),
                            "zip": data.get("zip"),
                            "lat": data.get("lat"),
                            "lon": data.get("lon"),
                            "timezone": data.get("timezone"),
                            "offset": data.get("offset"),
                            "currency": data.get("currency"),
                            "isp": data.get("isp"),
                            "org": data.get("org"),
                            "asn": data.get("as"),
                            "asname": data.get("asname"),
                            "mobile": data.get("mobile"),
                            "proxy": data.get("proxy"),
                            "hosting": data.get("hosting"),
                        }
                        batch_result[ip] = info
                    else:
                        ip = data.get("query")
                        batch_result[ip] = None

                return batch_result

            elif response.status_code == 429:
                # レート制限エラー
                if retry < max_retries - 1:
                    wait_time = int(x_ttl) + 1 if x_ttl else retry_delay * (retry + 1)
                    print(
                        f"[Batch {batch_idx + 1}] Rate limit hit (429), waiting {wait_time}s before retry {retry + 1}/{max_retries}..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    print(
                        f"[Batch {batch_idx + 1}] Max retries reached due to rate limiting"
                    )
                    for ip in batch:
                        batch_result[ip] = None
                    return batch_result
            else:
                print(
                    f"[Batch {batch_idx + 1}] Unexpected status code: {response.status_code}"
                )
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    for ip in batch:
                        batch_result[ip] = None
                    return batch_result

        except requests.exceptions.RequestException as e:
            if retry < max_retries - 1:
                print(
                    f"[Batch {batch_idx + 1}] Error fetching (retry {retry + 1}/{max_retries}): {str(e)}"
                )
                time.sleep(retry_delay)
                continue
            else:
                print(
                    f"[Batch {batch_idx + 1}] Error after {max_retries} retries: {str(e)}"
                )
                for ip in batch:
                    batch_result[ip] = None
                return batch_result
        except Exception as e:
            print(f"[Batch {batch_idx + 1}] Unexpected error: {str(e)}")
            for ip in batch:
                batch_result[ip] = None
            return batch_result

    return batch_result


def get_whois_server(ip_address: str) -> str:
    """
    IPアドレスのプレフィックスに基づいて適切なWHOISサーバーを決定

    Args:
        ip_address: 検索するIPアドレス

    Returns:
        WHOISサーバーのホスト名
    """
    try:
        ip = ipaddress.ip_address(ip_address)

        if isinstance(ip, ipaddress.IPv6Address):
            # IPv6アドレス - プレフィックスを確認
            ip_int = int(ip)

            # RIPE NCC（ヨーロッパ） - 2a00::/12
            if (
                0x2A000000000000000000000000000000
                <= ip_int
                < 0x2B000000000000000000000000000000
            ):
                return "whois.ripe.net"

            # APNIC（アジア太平洋） - 2400::/12
            if (
                0x24000000000000000000000000000000
                <= ip_int
                < 0x25000000000000000000000000000000
            ):
                return "whois.apnic.net"

            # ARIN（北米） - 2600::/12
            if (
                0x26000000000000000000000000000000
                <= ip_int
                < 0x27000000000000000000000000000000
            ):
                return "whois.arin.net"

            # LACNIC（ラテンアメリカ） - 2800::/12
            if (
                0x28000000000000000000000000000000
                <= ip_int
                < 0x29000000000000000000000000000000
            ):
                return "whois.lacnic.net"

            # AFRINIC（アフリカ） - 2c00::/12
            if (
                0x2C000000000000000000000000000000
                <= ip_int
                < 0x2D000000000000000000000000000000
            ):
                return "whois.afrinic.net"

            # 2001::/16 空間 - より具体的なチェック
            if (
                0x20010000000000000000000000000000
                <= ip_int
                < 0x20020000000000000000000000000000
            ):
                # 2001::/16内のAPNIC範囲
                # 2001:200::/23から2001:dff::/23まで
                if (
                    0x20010200000000000000000000000000
                    <= ip_int
                    < 0x20010E00000000000000000000000000
                ):
                    return "whois.apnic.net"
                # ARIN範囲
                # 2001:400::/23から2001:5ff::/23まで
                if (
                    0x20010400000000000000000000000000
                    <= ip_int
                    < 0x20010600000000000000000000000000
                ):
                    return "whois.arin.net"
                # RIPE範囲
                # 2001:600::/23から2001:9ff::/23まで
                if (
                    0x20010600000000000000000000000000
                    <= ip_int
                    < 0x20010A00000000000000000000000000
                ):
                    return "whois.ripe.net"

        # IPv4および一致しないIPv6のデフォルトはARIN
        return "whois.arin.net"

    except Exception as e:
        print(f"Error determining WHOIS server: {str(e)}")
        return "whois.arin.net"


def get_whois_info(ip_address: str) -> Optional[Dict]:
    """
    WHOISプロトコルを使用してIPアドレスのWHOIS情報を取得

    Args:
        ip_address: 検索するIPアドレス

    Returns:
        WHOIS情報を含むDictionary、または検索失敗の場合はNone
    """
    try:
        # IPアドレスを検証
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            print(f"Invalid IP address: {ip_address}")
            return None

        # IPアドレスのプレフィックスに基づいてWHOISサーバーを決定
        whois_server = get_whois_server(ip_address)
        whois_port = 43
        print(f"Using WHOIS server: {whois_server} for {ip_address}")

        # ソケット接続を作成
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10秒タイムアウト

        try:
            sock.connect((whois_server, whois_port))
            sock.send(f"{ip_address}\r\n".encode())

            # レスポンスを読み取り
            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data

            whois_text = response.decode("utf-8", errors="ignore")

            # WHOISレスポンスを解析
            result = {
                "raw": whois_text,
                "netname": None,
                "org_name": None,
                "country": None,
                "net_range": None,
            }

            for line in whois_text.split("\n"):
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("%"):
                    continue

                # 複数のRIRフォーマットをサポート（大文字小文字を区別しない）
                line_lower = line.lower()

                # ネットワーク名（ARIN: NetName、RIPE/APNIC: netname）
                if line_lower.startswith("netname:") and not result["netname"]:
                    result["netname"] = line.split(":", 1)[1].strip()

                # 組織名（ARIN: OrgName、RIPE: org-name/descr、APNIC: descr）
                elif (
                    line_lower.startswith("orgname:")
                    or line_lower.startswith("org-name:")
                ) and not result["org_name"]:
                    result["org_name"] = line.split(":", 1)[1].strip()
                elif line_lower.startswith("descr:") and not result["org_name"]:
                    # 組織名がまだ見つかっていない場合は最初のdescrラインを使用
                    result["org_name"] = line.split(":", 1)[1].strip()

                # 国
                elif line_lower.startswith("country:") and not result["country"]:
                    result["country"] = line.split(":", 1)[1].strip()

                # ネットワーク範囲（ARIN: NetRange/CIDR、RIPE/APNIC: inetnum/inet6num）
                elif (
                    line_lower.startswith("netrange:")
                    or line_lower.startswith("cidr:")
                    or line_lower.startswith("inetnum:")
                    or line_lower.startswith("inet6num:")
                ) and not result["net_range"]:
                    result["net_range"] = line.split(":", 1)[1].strip()

            return result

        finally:
            sock.close()

    except socket.timeout:
        print(f"WHOIS lookup timeout for {ip_address}")
        return None
    except Exception as e:
        print(f"Error fetching WHOIS for {ip_address}: {str(e)}")
        return None


def fetch_missing_whois_batch() -> Dict:
    """
    データベース内のWHOIS情報を持たないすべてのIPに対してWHOIS情報を取得
    これはバックグラウンドで実行されるように設計されています

    Returns:
        統計情報を含むDictionary
    """
    from api.models import IPGeolocation

    print("Starting WHOIS batch fetch...")

    # WHOIS情報を持たないすべてのIPを検索
    ips_without_whois = IPGeolocation.objects.filter(
        whois_raw__isnull=True
    ) | IPGeolocation.objects.filter(whois_raw="")

    total_count = ips_without_whois.count()
    print(f"Found {total_count} IPs without WHOIS info")

    if total_count == 0:
        return {
            "status": "completed",
            "message": "No IPs need WHOIS info",
            "total": 0,
            "processed": 0,
            "successful": 0,
            "failed": 0,
        }

    processed = 0
    successful = 0
    failed = 0

    # 各IPを処理
    for geo in ips_without_whois:
        processed += 1
        ip_address = geo.ip_address

        print(f"[{processed}/{total_count}] Fetching WHOIS for {ip_address}...")

        whois_info = get_whois_info(ip_address)

        if whois_info:
            # レコードを更新
            geo.whois_raw = whois_info.get("raw", "")
            geo.whois_netname = whois_info.get("netname")
            geo.whois_org_name = whois_info.get("org_name")
            geo.whois_country = whois_info.get("country")
            geo.whois_net_range = whois_info.get("net_range")
            geo.save(
                update_fields=[
                    "whois_raw",
                    "whois_netname",
                    "whois_org_name",
                    "whois_country",
                    "whois_net_range",
                ]
            )
            successful += 1
            print(f"✓ WHOIS saved for {ip_address}")
        else:
            # 試行済みとしてマーク（再試行を避けるため空文字列を保存）
            geo.whois_raw = ""
            geo.save(update_fields=["whois_raw"])
            failed += 1
            print(f"✗ WHOIS failed for {ip_address}")

        # WHOISサーバーへの過負荷を避けるため小さな遅延を追加
        time.sleep(0.5)

        # 10 IPごとに進捗レポート
        if processed % 10 == 0:
            print(
                f"Progress: {processed}/{total_count} "
                f"({successful} successful, {failed} failed)"
            )

    print(
        f"WHOIS batch fetch completed: {processed} processed, "
        f"{successful} successful, {failed} failed"
    )

    return {
        "status": "completed",
        "message": "WHOIS batch fetch completed",
        "total": total_count,
        "processed": processed,
        "successful": successful,
        "failed": failed,
    }
