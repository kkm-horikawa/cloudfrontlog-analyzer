"""Shared utilities for CloudFront log analysis"""

from .cloudfront_constants import CLOUDFRONT_LOG_COLUMNS
from .cloudfront_constants import FIELD_NAME_MAPPING

__all__ = [
    "CLOUDFRONT_LOG_COLUMNS",
    "FIELD_NAME_MAPPING",
]
