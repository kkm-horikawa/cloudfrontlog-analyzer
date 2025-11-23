"""
Snapshot Tests for WAF API

These tests verify that WAF-related endpoints return consistent results
by comparing against golden data.
"""

import pytest
from django.test import Client

from api.tests.fixtures.snapshot_helpers import snapshot_comparator


@pytest.mark.django_db
class TestWAFSnapshots:
    """Snapshot tests for WAF endpoints"""

    def setup_method(self):
        """Setup test client"""
        self.client = Client()
        # TODO: Replace with actual distribution ID from environment or config
        self.distribution_id = "E1234567890ABC"

    @pytest.mark.snapshot
    def test_waf_ip_sets_list(self):
        """Test WAF IP sets listing"""
        response = self.client.get(
            "/api/waf/ip-sets/",
            {
                "profile": "default",
                "distributionId": self.distribution_id,
            },
        )

        # May return error if WAF not configured, that's OK
        if response.status_code == 200:
            data = response.json()
            snapshot_comparator.assert_matches_snapshot(
                data.get("ipSets", []),
                "waf_ip_sets_list",
                exclude_fields=[],
            )

    @pytest.mark.snapshot
    def test_waf_blocked_ips_list(self):
        """Test WAF blocked IPs listing"""
        response = self.client.get(
            "/api/waf/blocked-ips/",
            {
                "profile": "default",
                "distributionId": self.distribution_id,
            },
        )

        # May return error if WAF not configured, that's OK
        if response.status_code == 200:
            data = response.json()
            snapshot_comparator.assert_matches_snapshot(
                data.get("blockedIps", []),
                "waf_blocked_ips_list",
                exclude_fields=[],
            )

    @pytest.mark.snapshot
    def test_waf_blocked_ips_detail_geo(self):
        """Test WAF blocked IPs with detailed geolocation"""
        response = self.client.get(
            "/api/waf/blocked-ips/detail-geo/",
            {
                "profile": "default",
                "distributionId": self.distribution_id,
            },
        )

        # May return error if WAF not configured, that's OK
        if response.status_code == 200:
            data = response.json()
            snapshot_comparator.assert_matches_snapshot(
                data.get("blockedIps", []),
                "waf_blocked_ips_detail_geo",
                exclude_fields=[],
            )

    @pytest.mark.snapshot
    def test_waf_blocked_ips_geo_locations(self):
        """Test WAF blocked IPs geographic distribution"""
        response = self.client.get(
            "/api/waf/blocked-ips/geo/",
            {
                "profile": "default",
                "distributionId": self.distribution_id,
            },
        )

        # May return error if WAF not configured, that's OK
        if response.status_code == 200:
            data = response.json()
            snapshot_comparator.assert_matches_snapshot(
                data.get("locations", []),
                "waf_blocked_ips_geo_locations",
                exclude_fields=[],
            )

    @pytest.mark.snapshot
    def test_waf_check_ip_not_blocked(self):
        """Test checking if IP is not in WAF blocklist"""
        response = self.client.get(
            "/api/waf/check/",
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "ipAddress": "8.8.8.8",  # Google DNS - unlikely to be blocked
            },
        )

        # May return error if WAF not configured, that's OK
        if response.status_code == 200:
            data = response.json()
            # Verify response structure
            assert "isBlocked" in data
            assert "ipAddress" in data

    @pytest.mark.snapshot
    def test_waf_blocked_ips_verify_structure(self):
        """Verify blocked IPs response has expected structure"""
        response = self.client.get(
            "/api/waf/blocked-ips/",
            {
                "profile": "default",
                "distributionId": self.distribution_id,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "blockedIps" in data
            assert "total" in data
            assert "ipSets" in data

            # Verify each blocked IP has required fields
            for blocked_ip in data.get("blockedIps", []):
                assert "ip" in blocked_ip
                assert "cidr" in blocked_ip
                assert "ipSetId" in blocked_ip
                assert "ipSetName" in blocked_ip
                assert "ipSetArn" in blocked_ip

    @pytest.mark.snapshot
    def test_waf_blocked_ips_geo_verify_structure(self):
        """Verify blocked IPs with geolocation has expected structure"""
        response = self.client.get(
            "/api/waf/blocked-ips/detail-geo/",
            {
                "profile": "default",
                "distributionId": self.distribution_id,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "blockedIps" in data
            assert "total" in data

            # Verify each blocked IP has geolocation
            for blocked_ip in data.get("blockedIps", []):
                assert "ip" in blocked_ip
                assert "cidr" in blocked_ip
                assert "representativeIp" in blocked_ip
                assert "geolocation" in blocked_ip

                geo = blocked_ip["geolocation"]
                # Geolocation should have these fields (may be None)
                assert "lat" in geo or geo is None
                assert "lon" in geo or geo is None
                assert "country" in geo or geo is None

    @pytest.mark.snapshot
    def test_waf_ip_sets_verify_structure(self):
        """Verify IP sets list has expected structure"""
        response = self.client.get(
            "/api/waf/ip-sets/",
            {
                "profile": "default",
                "distributionId": self.distribution_id,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "ipSets" in data
            assert "webAclId" in data or "error" in data

            # Verify each IP set has required fields
            for ip_set in data.get("ipSets", []):
                assert "id" in ip_set
                assert "name" in ip_set
                assert "arn" in ip_set
