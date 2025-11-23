from django.contrib import admin

from .models import AccessLog
from .models import GeoLogCache
from .models import IPGeolocation
from .models import ProcessedLogFile
from .models import WAFBlockedIP
from .models import WAFBlockedIPSnapshot


@admin.register(IPGeolocation)
class IPGeolocationAdmin(admin.ModelAdmin):
    list_display = [
        "ip_address",
        "city",
        "country",
        "isp",
        "hit_count",
        "created_at",
    ]
    list_filter = ["country", "city", "created_at"]
    search_fields = ["ip_address", "city", "country", "isp"]
    readonly_fields = ["created_at", "updated_at", "hit_count"]
    ordering = ["-hit_count", "-created_at"]


@admin.register(WAFBlockedIPSnapshot)
class WAFBlockedIPSnapshotAdmin(admin.ModelAdmin):
    list_display = ["distribution_id", "snapshot_time", "total_ips", "created_at"]
    list_filter = ["distribution_id", "snapshot_time"]
    search_fields = ["distribution_id"]
    readonly_fields = ["created_at"]
    ordering = ["-snapshot_time"]


@admin.register(WAFBlockedIP)
class WAFBlockedIPAdmin(admin.ModelAdmin):
    list_display = [
        "ip_address",
        "cidr",
        "ip_set_name",
        "snapshot",
        "geolocation",
    ]
    list_filter = ["ip_set_name", "snapshot__distribution_id"]
    search_fields = ["ip_address", "cidr", "ip_set_name"]
    raw_id_fields = ["snapshot", "geolocation"]
    ordering = ["ip_address"]


@admin.register(GeoLogCache)
class GeoLogCacheAdmin(admin.ModelAdmin):
    list_display = [
        "distribution_id",
        "start_date",
        "end_date",
        "total_count",
        "created_at",
        "expires_at",
        "is_expired",
    ]
    list_filter = ["distribution_id", "created_at", "expires_at"]
    search_fields = ["distribution_id"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]


@admin.register(ProcessedLogFile)
class ProcessedLogFileAdmin(admin.ModelAdmin):
    list_display = [
        "distribution_id",
        "log_file_key",
        "record_count",
        "file_size",
        "log_start_time",
        "log_end_time",
        "processed_at",
    ]
    list_filter = ["distribution_id", "processed_at"]
    search_fields = ["log_file_key", "distribution_id"]
    readonly_fields = ["processed_at"]
    ordering = ["-processed_at"]


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = [
        "log_datetime",
        "c_ip",
        "cs_method",
        "cs_uri_stem",
        "sc_status",
        "sc_bytes",
        "distribution_id",
    ]
    list_filter = ["distribution_id", "sc_status", "cs_method", "log_datetime"]
    search_fields = ["c_ip", "cs_uri_stem", "cs_host"]
    readonly_fields = ["log_datetime"]
    raw_id_fields = ["log_file", "geolocation"]
    ordering = ["-log_datetime"]
    date_hierarchy = "log_datetime"
