import httpx

from app.publishers.base import PublishResult
from app.publishers.errors import RetryablePublishError
from app.publishers.retry import retry_delay

class MastodonPublisher:
    def __init__(
        self,
        base_url: str,
        access_token: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.transport = transport

    def publish(self, text: str, idempotency_key: str) -> PublishResult:
        try:
            with httpx.Client(
                timeout=10,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = client.post(
                    f"{self.base_url}/api/v1/statuses",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Idempotency-Key": idempotency_key,
                    },
                    data={
                        "status": text,
                        "visibility": "private",
                    },
                )
        except httpx.RequestError:
            raise RetryablePublishError("Mastodon request failed.") from None

        if response.status_code == 429 or 500 <= response.status_code < 600:
            raise RetryablePublishError(
                f"Mastodon returned HTTP {response.status_code}.",
                retry_after_seconds=retry_delay(response.headers),
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Mastodon returned HTTP {response.status_code}."
            )

        try:
            data = response.json()
        except ValueError:
            raise RuntimeError("Mastodon returned invalid JSON.") from None

        if (
            not isinstance(data, dict)
            or not isinstance(data.get("id"), str)
            or not isinstance(data.get("url"), str)
        ):
            raise RuntimeError("Mastodon response is missing post details.")

        return PublishResult(
            post_id=data["id"],
            url=data["url"],
        )