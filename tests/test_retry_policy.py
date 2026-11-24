import unittest
from datetime import datetime, timedelta, timezone

from app.services.retry_policy import RetryLimitExceeded, next_retry_at


class RetryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def test_provider_delay_takes_precedence(self):
        result = next_retry_at(
            first_started_at=self.now,
            attempt_count=1,
            requested_delay=45,
            now=self.now,
        )

        self.assertEqual(result, self.now + timedelta(seconds=45))

    def test_backoff_increases_between_attempts(self):
        result = next_retry_at(
            first_started_at=self.now,
            attempt_count=3,
            requested_delay=1,
            now=self.now,
        )

        self.assertEqual(result, self.now + timedelta(seconds=120))

    def test_fifth_attempt_cannot_schedule_another_retry(self):
        with self.assertRaises(RetryLimitExceeded):
            next_retry_at(
                first_started_at=self.now,
                attempt_count=5,
                requested_delay=30,
                now=self.now,
            )

    def test_retry_must_fit_inside_time_window(self):
        with self.assertRaises(RetryLimitExceeded):
            next_retry_at(
                first_started_at=self.now - timedelta(minutes=29, seconds=50),
                attempt_count=1,
                requested_delay=30,
                now=self.now,
            )

    def test_extremely_large_delay_is_rejected(self):
        with self.assertRaises(RetryLimitExceeded):
            next_retry_at(
                first_started_at=self.now,
                attempt_count=1,
                requested_delay=10**100,
                now=self.now,
            )