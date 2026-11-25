from app.config import load_mastodon_settings
from app.publishers.base import SocialPublisher
from app.publishers.mastodon import MastodonPublisher
from app.publishers.mock import MockLinkedInPublisher, MockXPublisher


PUBLISHERS: dict[str, SocialPublisher] = {
    "mock_x": MockXPublisher(),
    "mock_linkedin": MockLinkedInPublisher(),
}


def get_publisher(platform: str) -> SocialPublisher:
    if platform == "mastodon":
        settings = load_mastodon_settings()

        return MastodonPublisher(
            base_url=settings.base_url,
            access_token=settings.access_token,
        )

    if platform not in PUBLISHERS:
        raise ValueError(f"No publisher configured for {platform}.")

    return PUBLISHERS[platform]