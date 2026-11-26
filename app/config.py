import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


@dataclass(frozen=True)
class MastodonSettings:
    base_url: str
    access_token: str = field(repr=False)


def load_mastodon_settings() -> MastodonSettings:
    values = {
        **dotenv_values(ENV_PATH),
        **os.environ,
    }

    base_url = (values.get("MASTODON_BASE_URL") or "").strip().rstrip("/")
    access_token = (values.get("MASTODON_ACCESS_TOKEN") or "").strip()

    if not base_url or not access_token:
        raise ValueError(
            "MASTODON_BASE_URL and MASTODON_ACCESS_TOKEN are required."
        )

    parsed = urlsplit(base_url)

    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "MASTODON_BASE_URL must be an HTTPS server origin."
        )

    return MastodonSettings(
        base_url=base_url,
        access_token=access_token,
    )

def resolve_publisher(platform: str) -> str:
    supported = {"mock_x", "mock_linkedin", "mastodon"}

    if platform not in supported:
        raise ValueError("Unknown platform.")

    values = {
        **dotenv_values(ENV_PATH),
        **os.environ,
    }

    variable = f"PUBLISHER_{platform.upper()}"
    adapter = (values.get(variable) or platform).strip()

    if adapter not in supported:
        raise ValueError(
            f"{variable} must be mock_x, mock_linkedin, or mastodon."
        )

    return adapter