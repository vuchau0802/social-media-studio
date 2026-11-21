from app.publishers.base import SocialPublisher
from app.publishers.mock import MockLinkedInPublisher, MockXPublisher


PUBLISHERS: dict[str, SocialPublisher] = {
    "mock_x": MockXPublisher(),
    "mock_linkedin": MockLinkedInPublisher(),
}


def get_publisher(platform: str) -> SocialPublisher:
    if platform not in PUBLISHERS:
        raise ValueError(f"No publisher configured for {platform}.")

    return PUBLISHERS[platform]