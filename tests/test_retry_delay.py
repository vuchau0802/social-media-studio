import unittest
from datetime import datetime, timezone

import httpx

from app.publishers.retry import retry_delay


class RetryDelayTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def test_seconds_header(self):
        headers = httpx.Headers({"Retry-After": "45"})
        self.assertEqual(retry_delay(headers, self.now), 45)

    def test_http_date_header(self):
        headers = httpx.Headers({
            "Retry-After": "Thu, 01 Jan 2026 00:01:00 GMT",
        })
        self.assertEqual(retry_delay(headers, self.now), 60)

    def test_later_reset_time_wins(self):
        headers = httpx.Headers({
            "Retry-After": "30",
            "X-RateLimit-Reset": "2026-01-01T00:02:00Z",
        })
        self.assertEqual(retry_delay(headers, self.now), 120)

    def test_invalid_headers_use_fallback(self):
        headers = httpx.Headers({
            "Retry-After": "invalid",
            "X-RateLimit-Reset": "invalid",
        })
        self.assertEqual(retry_delay(headers, self.now), 30)