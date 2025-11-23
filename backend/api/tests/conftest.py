"""
Pytest configuration and shared fixtures for API tests
"""
import pytest
from django.test import Client
from unittest.mock import MagicMock, patch


@pytest.fixture
def api_client():
    """Provides a Django test client"""
    return Client()


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client for AWS operations"""
    with patch('boto3.Session') as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_distribution():
    """Sample CloudFront distribution data"""
    return {
        'Id': 'E1234567890ABC',
        'DomainName': 'd1234567890abc.cloudfront.net',
        'Aliases': {
            'Quantity': 1,
            'Items': ['example.com']
        },
        'Status': 'Deployed',
        'Enabled': True
    }


@pytest.fixture
def sample_log_entry():
    """Sample CloudFront log entry"""
    return {
        'date': '2025-01-15',
        'time': '12:00:00',
        'x-edge-location': 'NRT57-C1',
        'sc-bytes': '1234',
        'c-ip': '1.2.3.4',
        'cs-method': 'GET',
        'cs-host': 'example.com',
        'cs-uri-stem': '/index.html',
        'sc-status': '200',
        'cs-referer': '-',
        'cs-user-agent': 'Mozilla/5.0',
        'cs-uri-query': '-',
        'cs-cookie': '-',
        'x-edge-result-type': 'Hit',
        'x-edge-request-id': 'abc123',
        'x-host-header': 'example.com',
        'cs-protocol': 'https',
        'cs-bytes': '456',
        'time-taken': '0.001',
        'x-forwarded-for': '-',
        'ssl-protocol': 'TLSv1.3',
        'ssl-cipher': 'ECDHE-RSA-AES128-GCM-SHA256',
        'x-edge-response-result-type': 'Hit',
        'cs-protocol-version': 'HTTP/2.0',
        'fle-status': '-',
        'fle-encrypted-fields': '-',
        'c-port': '443',
        'time-to-first-byte': '0.001',
        'x-edge-detailed-result-type': 'Hit',
        'sc-content-type': 'text/html',
        'sc-content-len': '1234',
        'sc-range-start': '-',
        'sc-range-end': '-'
    }


@pytest.fixture
def sample_ip_info():
    """Sample IP geolocation information"""
    return {
        'ip': '1.2.3.4',
        'continent': 'Asia',
        'continentCode': 'AS',
        'country': 'Japan',
        'countryCode': 'JP',
        'region': 'Tokyo',
        'city': 'Tokyo',
        'district': None,
        'zip': '100-0001',
        'lat': 35.6895,
        'lon': 139.6917,
        'timezone': 'Asia/Tokyo',
        'offset': 32400,
        'currency': 'JPY',
        'isp': 'Example ISP',
        'org': 'Example Organization',
        'asn': 'AS12345',
        'asname': 'EXAMPLE-AS',
        'mobile': False,
        'proxy': False,
        'hosting': False,
        'whois': {
            'raw': 'Sample WHOIS data',
            'netname': 'EXAMPLE-NET',
            'org_name': 'Example Organization',
            'country': 'JP',
            'net_range': '1.2.3.0/24'
        }
    }


@pytest.fixture
def sample_waf_ip_set():
    """Sample WAF IP Set data"""
    return {
        'Name': 'test-ip-set',
        'Id': 'abc123-def456',
        'ARN': 'arn:aws:wafv2:us-east-1:123456789012:global/ipset/test-ip-set/abc123-def456',
        'Addresses': ['1.2.3.4/32', '5.6.7.8/32'],
        'IPAddressVersion': 'IPV4',
        'LockToken': 'lock-token-123'
    }
