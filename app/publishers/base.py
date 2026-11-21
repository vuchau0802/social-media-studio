from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PublishResult:
    post_id: str
    url: str


class SocialPublisher(Protocol):
    def publish(self, text: str, idempotency_key: str) -> PublishResult:
        ...