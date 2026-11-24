import unittest
from urllib.parse import parse_qs

import httpx

from app.publishers.mastodon import MastodonPublisher
from app.publishers.errors import RetryablePublishError

class MastodonPublisherTests(unittest.TestCase):
    def test_publish_sends_credentials_text_and_stable_key(self):
        requests = []

        def respond(request):
            requests.append(request)

            self.assertEqual(request.method, "POST")
            self.assertEqual(
                str(request.url),
                "https://mastodon.example/api/v1/statuses",
            )
            self.assertEqual(
                request.headers["Authorization"],
                "Bearer test-token",
            )
            self.assertEqual(
                request.headers["Idempotency-Key"],
                "test-slot-key",
            )
            self.assertEqual(
                parse_qs(request.content.decode()),
                {
                    "status": ["Example article."],
                    "visibility": ["private"],
                },
            )

            return httpx.Response(
                200,
                json={
                    "id": "123",
                    "url": "https://mastodon.example/@tester/123",
                },
            )

        publisher = MastodonPublisher(
            "https://mastodon.example/",
            "test-token",
            transport=httpx.MockTransport(respond),
        )

        first = publisher.publish("Example article.", "test-slot-key")
        second = publisher.publish("Example article.", "test-slot-key")

        self.assertEqual(len(requests), 2)
        self.assertEqual(first, second)
        self.assertEqual(first.post_id, "123")
        self.assertEqual(
            first.url,
            "https://mastodon.example/@tester/123",
        )

    def test_http_error_has_a_safe_message(self):
        def respond(request):
            return httpx.Response(
                401,
                json={"error": "Provider error details"},
            )

        publisher = MastodonPublisher(
            "https://mastodon.example",
            "test-token",
            transport=httpx.MockTransport(respond),
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Mastodon returned HTTP 401.",
        ):
            publisher.publish("Example article.", "test-slot-key")

    def test_rate_limit_reports_retry_delay(self):
        def respond(request):
            return httpx.Response(
                429,
                headers={"Retry-After": "45"},
            )

        publisher = MastodonPublisher(
            "https://mastodon.example",
            "test-token",
            transport=httpx.MockTransport(respond),
        )

        with self.assertRaises(RetryablePublishError) as caught:
            publisher.publish("Example article.", "test-slot-key")

        self.assertEqual(caught.exception.retry_after_seconds, 45)