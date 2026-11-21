from app.publishers.base import PublishResult
from app.repositories.mock_publications import save_publication


class MockPublisher:
    def __init__(self, platform: str):
        self.platform = platform

    def publish(self, text: str, idempotency_key: str) -> PublishResult:
        publication = save_publication(
            self.platform,
            text,
            idempotency_key,
        )

        return PublishResult(
            post_id=str(publication["id"]),
            url=f"/mock-publications/{publication['id']}",
        )


class MockXPublisher(MockPublisher):
    def __init__(self):
        super().__init__("mock_x")


class MockLinkedInPublisher(MockPublisher):
    def __init__(self):
        super().__init__("mock_linkedin")