"""
API URL Configuration

All endpoints are organized by functional domain in the endpoints directory.
"""

from django.urls import path

# Distributions
from .endpoints.distributions.views import DistributionListView
from .endpoints.geo.views import GeoLogsView

# IP Info
from .endpoints.ip_info.views import IPInfoView
from .endpoints.logs.views import LogAggregationView

# Logs & Geo
from .endpoints.logs.views import LogSearchView
from .endpoints.logs.views import RawLogsListView

# Log Marks
from .endpoints.log_marks.views import check_log_marks
from .endpoints.log_marks.views import log_mark_categories_list
from .endpoints.log_marks.views import log_mark_category_detail
from .endpoints.log_marks.views import log_mark_pattern_detail
from .endpoints.log_marks.views import log_mark_patterns_list

# Security Checks
from .endpoints.security.views import CompanyInfoAccessCheckView
from .endpoints.security.views import FrequentIPAccessCheckView
from .endpoints.security.views import MultiDeviceAccessCheckView
from .endpoints.security.views import ResearchToolDetectionCheckView

# WAF
from .endpoints.waf.views import WAFBlockedIPsDetailGeoView
from .endpoints.waf.views import WAFBlockedIPsExportView
from .endpoints.waf.views import WAFBlockedIPsGeoView
from .endpoints.waf.views import WAFBlockedIPsListView
from .endpoints.waf.views import WAFBlocklistAddView
from .endpoints.waf.views import WAFBlocklistCheckView
from .endpoints.waf.views import WAFBlocklistRemoveView
from .endpoints.waf.views import WAFIPSetsListView

# WHOIS
from .endpoints.whois.views import WHOISBatchFetchView
from .endpoints.whois.views import WHOISBatchStatusView


urlpatterns = [
    # CloudFront Distributions
    path(
        "cloudfront/distributions/",
        DistributionListView.as_view(),
        name="distribution-list",
    ),
    # CloudFront Logs
    path("cloudfront/logs/search/", LogSearchView.as_view(), name="log-search"),
    path("cloudfront/logs/raw/", RawLogsListView.as_view(), name="raw-logs-list"),
    path(
        "cloudfront/logs/aggregation/",
        LogAggregationView.as_view(),
        name="log-aggregation",
    ),
    path("cloudfront/logs/geo/", GeoLogsView.as_view(), name="geo-logs"),
    # Log Marking
    path("log-marks/", log_mark_patterns_list, name="log-mark-patterns-list"),
    path("log-marks/<int:pk>/", log_mark_pattern_detail, name="log-mark-pattern-detail"),
    path("log-marks/check/", check_log_marks, name="check-log-marks"),
    path("log-mark-categories/", log_mark_categories_list, name="log-mark-categories-list"),
    path("log-mark-categories/<int:pk>/", log_mark_category_detail, name="log-mark-category-detail"),
    # IP Information
    path("ip-info/<str:ip_address>/", IPInfoView.as_view(), name="ip-info"),
    # WAF Operations
    path(
        "waf/ip-sets/",
        WAFIPSetsListView.as_view(),
        name="waf-ip-sets-list",
    ),
    path(
        "waf/blocklist/check/",
        WAFBlocklistCheckView.as_view(),
        name="waf-blocklist-check",
    ),
    path(
        "waf/blocklist/add/",
        WAFBlocklistAddView.as_view(),
        name="waf-blocklist-add",
    ),
    path(
        "waf/blocklist/remove/",
        WAFBlocklistRemoveView.as_view(),
        name="waf-blocklist-remove",
    ),
    path(
        "waf/blocked-ips/",
        WAFBlockedIPsListView.as_view(),
        name="waf-blocked-ips-list",
    ),
    path(
        "waf/blocked-ips/export/",
        WAFBlockedIPsExportView.as_view(),
        name="waf-blocked-ips-export",
    ),
    path(
        "waf/blocked-ips/geo/",
        WAFBlockedIPsGeoView.as_view(),
        name="waf-blocked-ips-geo",
    ),
    path(
        "waf/blocked-ips/geo/detail/",
        WAFBlockedIPsDetailGeoView.as_view(),
        name="waf-blocked-ips-detail-geo",
    ),
    # Advanced Security Checks
    path(
        "checks/company-info-access/",
        CompanyInfoAccessCheckView.as_view(),
        name="check-company-info",
    ),
    path(
        "checks/frequent-ip-access/",
        FrequentIPAccessCheckView.as_view(),
        name="check-frequent-ip",
    ),
    path(
        "checks/multi-device-access/",
        MultiDeviceAccessCheckView.as_view(),
        name="check-multi-device",
    ),
    path(
        "checks/research-tool-detection/",
        ResearchToolDetectionCheckView.as_view(),
        name="check-research-tool",
    ),
    # WHOIS Batch Operations
    path(
        "whois/batch/fetch/",
        WHOISBatchFetchView.as_view(),
        name="whois-batch-fetch",
    ),
    path(
        "whois/batch/status/",
        WHOISBatchStatusView.as_view(),
        name="whois-batch-status",
    ),
]
