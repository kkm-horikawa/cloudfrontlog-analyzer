"""
Snapshot Tests for Geo-Aggregated Logs API

These tests verify that the /api/geo/ endpoint returns consistent results
by comparing against golden data collected from 2025-11-13.
"""

import pytest
from django.test import Client

from api.tests.fixtures.snapshot_helpers import snapshot_comparator


@pytest.mark.django_db
class TestGeoLogsSnapshots:
    """Snapshot tests for geo-aggregated logs endpoint"""

    def setup_method(self):
        """Setup test client"""
        self.client = Client()
        self.base_url = "/api/geo/"
        # TODO: Replace with actual distribution ID from environment or config
        self.distribution_id = "E1234567890ABC"
        self.test_date = "2025-11-13"

    @pytest.mark.snapshot
    def test_geo_logs_no_filter(self):
        """Test geo logs without any filters"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Compare against golden data
        snapshot_comparator.assert_matches_snapshot(
            data.get("logs", []),
            "geo_logs_no_filter",
            exclude_fields=[],  # Geo data should be stable
        )

    @pytest.mark.snapshot
    def test_geo_logs_time_filter(self):
        """Test geo logs with time filter (00:00-12:00)"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
                "startTime": "00:00:00",
                "endTime": "12:00:00",
            },
        )

        assert response.status_code == 200
        data = response.json()

        snapshot_comparator.assert_matches_snapshot(
            data.get("logs", []),
            "geo_logs_time_filter",
            exclude_fields=[],
        )

    @pytest.mark.snapshot
    def test_geo_logs_uri_filter(self):
        """Test geo logs with URI filter"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
                "uriFilter": "/nattoku/",
            },
        )

        assert response.status_code == 200
        data = response.json()

        snapshot_comparator.assert_matches_snapshot(
            data.get("logs", []),
            "geo_logs_uri_filter",
            exclude_fields=[],
        )

    @pytest.mark.snapshot
    def test_geo_logs_combined_filters(self):
        """Test geo logs with multiple filters combined"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
                "uriFilter": "/nattoku/",
                "statusFilter": "200",
                "methodFilter": "GET",
            },
        )

        assert response.status_code == 200
        data = response.json()

        snapshot_comparator.assert_matches_snapshot(
            data.get("logs", []),
            "geo_logs_combined_filters",
            exclude_fields=[],
        )

    @pytest.mark.snapshot
    def test_geo_logs_status_filter(self):
        """Test geo logs with status code filter"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
                "statusFilter": "200",
            },
        )

        assert response.status_code == 200
        data = response.json()

        snapshot_comparator.assert_matches_snapshot(
            data.get("logs", []),
            "geo_logs_status_filter",
            exclude_fields=[],
        )

    @pytest.mark.snapshot
    def test_geo_logs_method_filter(self):
        """Test geo logs with HTTP method filter"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
                "methodFilter": "GET",
            },
        )

        assert response.status_code == 200
        data = response.json()

        snapshot_comparator.assert_matches_snapshot(
            data.get("logs", []),
            "geo_logs_method_filter",
            exclude_fields=[],
        )

    @pytest.mark.snapshot
    def test_geo_logs_referer_filter(self):
        """Test geo logs with referer filter"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
                "refererFilter": "google",
            },
        )

        assert response.status_code == 200
        data = response.json()

        snapshot_comparator.assert_matches_snapshot(
            data.get("logs", []),
            "geo_logs_referer_filter",
            exclude_fields=[],
        )

    @pytest.mark.snapshot
    def test_geo_logs_query_filter(self):
        """Test geo logs with query string filter"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
                "queryFilter": "utm_",
            },
        )

        assert response.status_code == 200
        data = response.json()

        snapshot_comparator.assert_matches_snapshot(
            data.get("logs", []),
            "geo_logs_query_filter",
            exclude_fields=[],
        )

    @pytest.mark.snapshot
    def test_geo_logs_verify_aggregation(self):
        """Verify that geo logs are properly aggregated by location"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
            },
        )

        assert response.status_code == 200
        data = response.json()
        logs = data.get("logs", [])

        # Verify each entry has required geolocation fields
        for log in logs:
            assert "lat" in log
            assert "lon" in log
            assert "country" in log
            assert "countryCode" in log
            assert "uniqueIPs" in log
            assert "totalRequests" in log

    @pytest.mark.snapshot
    def test_geo_logs_date_range(self):
        """Test geo logs with date range (multiple days)"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": "2025-11-13",
                "endDate": "2025-11-15",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "logs" in data
        logs = data.get("logs", [])

        # Verify aggregation structure
        for log in logs:
            assert "lat" in log
            assert "lon" in log
            assert "uniqueIPs" in log
