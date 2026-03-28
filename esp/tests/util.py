"""
esp/tests/util.py
-----------------
Stub of ESP's real CacheFlushTestCase.

The real implementation lives in the ESP repo. For this prototype we
replicate the exact behaviour: flush Django's cache before and after
every test so cached accounting values never bleed between test cases.
"""

from django.core.cache import cache
from django.test import TestCase


class CacheFlushTestCase(TestCase):
    """
    Drop-in base class that mirrors ESP's production CacheFlushTestCase.

    WHY inherit from this instead of plain TestCase:
    ESP's accounting controllers cache computed balances (amount_owed,
    line item totals) in Django's cache backend for performance. Without
    flushing, a value cached in test_A is returned in test_B, causing
    false passes that are invisible until production.
    """

    def setUp(self):
        super().setUp()
        cache.clear()  # pre-test flush

    def tearDown(self):
        super().tearDown()
        cache.clear()  # post-test flush
