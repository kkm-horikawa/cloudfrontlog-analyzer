"""
Custom Django test runner that uses pytest

This allows running tests with both:
- python manage.py test (Django way)
- pytest (pytest way)
"""
import sys
from django.conf import settings
from django.test.runner import DiscoverRunner


class PytestTestRunner(DiscoverRunner):
    """Test runner that uses pytest instead of Django's default test runner"""

    def run_tests(self, test_labels, **kwargs):
        """Run pytest with the given test labels"""
        import pytest

        # pytest引数を構築
        argv = [
            '--verbose',
            '--tb=short',
            '--strict-markers',
            '-p', 'no:warnings',
        ]

        # test_labelsが指定されている場合はそれを使用
        # 例: python manage.py test api.tests.snapshot
        if test_labels:
            # Djangoのテストラベルをpytestのパスに変換
            # api.tests.snapshot → api/tests/snapshot
            for label in test_labels:
                path = label.replace('.', '/')
                argv.append(path)
        else:
            # ラベル指定なしの場合は全テスト実行
            argv.append('api/tests')

        # pytestを実行
        return pytest.main(argv)
