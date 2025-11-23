"""
Golden Data Collection Script

This script collects baseline API responses from the CloudFront Analyzer API
and saves them as Parquet files for snapshot testing.

Usage:
    python collect_golden_data.py --profile <aws_profile> --distribution-id <dist_id> --date 2025-11-13
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests


class GoldenDataCollector:
    """Collects API responses and saves as golden data"""

    def __init__(
        self, base_url: str, profile: str, distribution_id: str, date: str
    ):
        self.base_url = base_url
        self.profile = profile
        self.distribution_id = distribution_id
        self.date = date
        self.output_dir = Path(__file__).parent.parent / "data" / "golden"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _make_request(
        self, endpoint: str, params: Dict[str, Any] = None, method: str = "GET"
    ) -> Dict:
        """Make API request and return response"""
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}

        # Add profile to all requests
        params["profile"] = self.profile

        print(f"Requesting {method} {url} with params: {params}")

        if method == "GET":
            response = requests.get(url, params=params, timeout=120)
        elif method == "POST":
            response = requests.post(url, json=params, timeout=120)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    def _save_as_parquet(self, data: Dict, filename: str):
        """Save data as Parquet with maximum compression"""
        filepath = self.output_dir / f"{filename}.parquet"

        # Convert to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # For nested dict, flatten or store as JSON column
            df = pd.DataFrame([data])
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        # Clean data for Parquet serialization
        # Convert columns with mixed types to string representation
        for col in df.columns:
            # Check if column has mixed types (including None/nan with other types)
            if df[col].dtype == 'object':
                # Convert complex types (lists, dicts) and None to string
                def serialize_value(x):
                    # Check for list/dict first before pd.isna
                    if isinstance(x, (list, dict)):
                        return str(x)
                    # Use try-except for pd.isna to handle edge cases
                    try:
                        if pd.isna(x):
                            return ''
                    except (ValueError, TypeError):
                        # If pd.isna fails, just convert to string
                        pass
                    return str(x)

                df[col] = df[col].apply(serialize_value)

        # Save with maximum compression
        df.to_parquet(
            filepath,
            engine="pyarrow",
            compression="zstd",
            compression_level=22,
            index=False,
        )
        print(f"✓ Saved {filepath} ({len(df)} rows)")

    def collect_distributions(self):
        """Collect CloudFront distributions list"""
        print("\n=== Collecting Distributions ===")
        data = self._make_request("/api/cloudfront/distributions/")
        self._save_as_parquet(data, "distributions_list")

    def collect_raw_logs(self):
        """Collect raw logs with various filters"""
        print("\n=== Collecting Raw Logs ===")

        # Base request
        params = {
            "distributionId": self.distribution_id,
            "startDate": self.date,
            "endDate": self.date,
        }

        # 1. No filters
        data = self._make_request("/api/cloudfront/logs/raw/", params)
        self._save_as_parquet(data.get("logs", []), "raw_logs_no_filter")

        # 2. With time filter
        params_time = params.copy()
        params_time.update({"startTime": "00:00:00", "endTime": "12:00:00"})
        data = self._make_request("/api/cloudfront/logs/raw/", params_time)
        self._save_as_parquet(data.get("logs", []), "raw_logs_time_filter")

        # 3. With URI filter
        params_uri = params.copy()
        params_uri["uriFilter"] = "/nattoku/"
        data = self._make_request("/api/cloudfront/logs/raw/", params_uri)
        self._save_as_parquet(data.get("logs", []), "raw_logs_uri_filter")

        # 4. With status filter
        params_status = params.copy()
        params_status["statusFilter"] = "200"
        data = self._make_request("/api/cloudfront/logs/raw/", params_status)
        self._save_as_parquet(data.get("logs", []), "raw_logs_status_200")

        # 5. With method filter
        params_method = params.copy()
        params_method["methodFilter"] = "GET"
        data = self._make_request("/api/cloudfront/logs/raw/", params_method)
        self._save_as_parquet(data.get("logs", []), "raw_logs_method_get")

        # 6. Combined filters
        params_combined = params.copy()
        params_combined.update(
            {
                "uriFilter": "/nattoku/",
                "statusFilter": "200",
                "methodFilter": "GET",
            }
        )
        data = self._make_request("/api/cloudfront/logs/raw/", params_combined)
        self._save_as_parquet(data.get("logs", []), "raw_logs_combined_filters")

        # 7. With referer filter
        params_referer = params.copy()
        params_referer["refererFilter"] = "google"
        data = self._make_request("/api/cloudfront/logs/raw/", params_referer)
        self._save_as_parquet(data.get("logs", []), "raw_logs_referer_filter")

        # 8. With query filter
        params_query = params.copy()
        params_query["queryFilter"] = "utm_"
        data = self._make_request("/api/cloudfront/logs/raw/", params_query)
        self._save_as_parquet(data.get("logs", []), "raw_logs_query_filter")

    def collect_geo_logs(self):
        """Collect geo-aggregated logs"""
        print("\n=== Collecting Geo Logs ===")

        params = {
            "distributionId": self.distribution_id,
            "startDate": self.date,
            "endDate": self.date,
        }

        # 1. No filters
        data = self._make_request("/api/cloudfront/logs/geo/", params)
        self._save_as_parquet(data.get("logs", []), "geo_logs_no_filter")

        # 2. With time filter
        params_time = params.copy()
        params_time.update({"startTime": "00:00:00", "endTime": "12:00:00"})
        data = self._make_request("/api/cloudfront/logs/geo/", params_time)
        self._save_as_parquet(data.get("logs", []), "geo_logs_time_filter")

        # 3. With URI filter
        params_uri = params.copy()
        params_uri["uriFilter"] = "/nattoku/"
        data = self._make_request("/api/cloudfront/logs/geo/", params_uri)
        self._save_as_parquet(data.get("logs", []), "geo_logs_uri_filter")

        # 4. With combined filters
        params_combined = params.copy()
        params_combined.update(
            {
                "uriFilter": "/nattoku/",
                "statusFilter": "200",
                "methodFilter": "GET",
            }
        )
        data = self._make_request("/api/cloudfront/logs/geo/", params_combined)
        self._save_as_parquet(data.get("logs", []), "geo_logs_combined_filters")

    def collect_waf_data(self):
        """Collect WAF-related data"""
        print("\n=== Collecting WAF Data ===")

        params = {"distributionId": self.distribution_id}

        # 1. IP Sets list
        try:
            data = self._make_request("/api/waf/ip-sets/", params)
            self._save_as_parquet(data.get("ipSets", []), "waf_ip_sets_list")
        except Exception as e:
            print(f"Warning: Could not collect IP sets: {e}")

        # 2. Blocked IPs list
        try:
            data = self._make_request("/api/waf/blocked-ips/", params)
            self._save_as_parquet(data.get("blockedIps", []), "waf_blocked_ips_list")
        except Exception as e:
            print(f"Warning: Could not collect blocked IPs: {e}")

        # 3. Blocked IPs with geolocation
        try:
            data = self._make_request("/api/waf/blocked-ips/detail-geo/", params)
            self._save_as_parquet(
                data.get("blockedIps", []), "waf_blocked_ips_detail_geo"
            )
        except Exception as e:
            print(f"Warning: Could not collect blocked IPs geo: {e}")

        # 4. Blocked IPs geographic distribution
        try:
            data = self._make_request("/api/waf/blocked-ips/geo/", params)
            self._save_as_parquet(
                data.get("locations", []), "waf_blocked_ips_geo_locations"
            )
        except Exception as e:
            print(f"Warning: Could not collect blocked IPs locations: {e}")

    def collect_ip_info(self):
        """Collect IP geolocation info"""
        print("\n=== Collecting IP Info ===")

        # Sample IPs to test
        test_ips = [
            "8.8.8.8",  # Google DNS
            "1.1.1.1",  # Cloudflare DNS
            "208.67.222.222",  # OpenDNS
        ]

        for ip in test_ips:
            try:
                params = {"ipAddress": ip}
                data = self._make_request("/api/ip-info/", params)
                filename = f"ip_info_{ip.replace('.', '_')}"
                self._save_as_parquet([data], filename)
            except Exception as e:
                print(f"Warning: Could not collect IP info for {ip}: {e}")

    def collect_all(self):
        """Collect all golden data"""
        print(f"\n{'='*60}")
        print(f"Collecting Golden Data")
        print(f"Distribution: {self.distribution_id}")
        print(f"Date: {self.date}")
        print(f"Output: {self.output_dir}")
        print(f"{'='*60}")

        self.collect_distributions()
        self.collect_raw_logs()
        self.collect_geo_logs()
        self.collect_waf_data()
        self.collect_ip_info()

        print(f"\n{'='*60}")
        print(f"✓ Golden data collection complete!")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Collect golden data for snapshot testing"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8001",
        help="Base URL of the API (default: http://localhost:8001)",
    )
    parser.add_argument(
        "--profile", default="default", help="AWS profile name (default: default)"
    )
    parser.add_argument(
        "--distribution-id", required=True, help="CloudFront distribution ID"
    )
    parser.add_argument(
        "--date", default="2025-11-13", help="Date to collect data from (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    collector = GoldenDataCollector(
        base_url=args.base_url,
        profile=args.profile,
        distribution_id=args.distribution_id,
        date=args.date,
    )

    collector.collect_all()


if __name__ == "__main__":
    main()
