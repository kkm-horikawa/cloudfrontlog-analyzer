"""
Snapshot Tests for Raw Logs API

These tests verify that the /api/logs/raw/ endpoint returns consistent results
by comparing against golden data collected from 2025-11-13.
"""

import pytest
from django.test import Client

from api.tests.fixtures.snapshot_helpers import snapshot_comparator


@pytest.mark.django_db
class TestRawLogsSnapshots:
    """Snapshot tests for raw logs endpoint"""

    def setup_method(self):
        """Setup test client"""
        self.client = Client()
        self.base_url = "/api/logs/raw/"
        # TODO: Replace with actual distribution ID from environment or config
        self.distribution_id = "E1234567890ABC"
        self.test_date = "2025-11-13"

    @pytest.mark.snapshot
    def test_raw_logs_no_filter(self):
        """Test raw logs without any filters"""
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
            "raw_logs_no_filter",
            exclude_fields=["cacheStatus"],  # May vary
        )

    @pytest.mark.snapshot
    def test_raw_logs_time_filter(self):
        """Test raw logs with time filter (00:00-12:00)"""
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
            "raw_logs_time_filter",
            exclude_fields=["cacheStatus"],
        )

    @pytest.mark.snapshot
    def test_raw_logs_uri_filter(self):
        """Test raw logs with URI filter"""
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
            "raw_logs_uri_filter",
            exclude_fields=["cacheStatus"],
        )

    @pytest.mark.snapshot
    def test_raw_logs_status_200(self):
        """Test raw logs filtering by status code 200"""
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
            "raw_logs_status_200",
            exclude_fields=["cacheStatus"],
        )

    @pytest.mark.snapshot
    def test_raw_logs_method_get(self):
        """Test raw logs filtering by HTTP method GET"""
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
            "raw_logs_method_get",
            exclude_fields=["cacheStatus"],
        )

    @pytest.mark.snapshot
    def test_raw_logs_combined_filters(self):
        """Test raw logs with multiple filters combined"""
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
            "raw_logs_combined_filters",
            exclude_fields=["cacheStatus"],
        )

    @pytest.mark.snapshot
    def test_raw_logs_referer_filter(self):
        """Test raw logs with referer filter"""
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
            "raw_logs_referer_filter",
            exclude_fields=["cacheStatus"],
        )

    @pytest.mark.snapshot
    def test_raw_logs_query_filter(self):
        """Test raw logs with query string filter"""
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
            "raw_logs_query_filter",
            exclude_fields=["cacheStatus"],
        )

    @pytest.mark.snapshot
    def test_raw_logs_pagination_limit_10(self):
        """Test raw logs with pagination (limit=10)"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
                "limit": "10",
            },
        )

        assert response.status_code == 200
        data = response.json()
        logs = data.get("logs", [])

        # Verify limit is respected
        assert len(logs) <= 10

    @pytest.mark.snapshot
    def test_raw_logs_pagination_offset_10(self):
        """Test raw logs with pagination (offset=10)"""
        response = self.client.get(
            self.base_url,
            {
                "profile": "default",
                "distributionId": self.distribution_id,
                "startDate": self.test_date,
                "endDate": self.test_date,
                "offset": "10",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Just verify it returns successfully
        # Don't snapshot because offset results can vary
        assert "logs" in data

    @pytest.mark.snapshot
    def test_raw_logs_date_range(self):
        """Test raw logs with date range (multiple days)"""
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
        assert "total" in data
