import os
import unittest
from unittest.mock import patch

from app.config import load_mastodon_settings
from app.publishers.mastodon import MastodonPublisher
from app.publishers.registry import get_publisher


class ConfigTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

        file_values = patch(
            "app.config.dotenv_values",
            return_value={},
        )
        self.file_values = file_values.start()
        self.addCleanup(file_values.stop)

    def test_registry_builds_mastodon_publisher(self):
        os.environ["MASTODON_BASE_URL"] = "https://mastodon.example/"
        os.environ["MASTODON_ACCESS_TOKEN"] = "test-token"

        publisher = get_publisher("mastodon")

        self.assertIsInstance(publisher, MastodonPublisher)
        self.assertEqual(
            publisher.base_url,
            "https://mastodon.example",
        )
        self.assertEqual(publisher.access_token, "test-token")

        settings = load_mastodon_settings()
        self.assertNotIn("test-token", repr(settings))

    def test_environment_overrides_file_values(self):
        self.file_values.return_value = {
            "MASTODON_BASE_URL": "https://file.example",
            "MASTODON_ACCESS_TOKEN": "file-token",
        }
        os.environ["MASTODON_BASE_URL"] = "https://environment.example"
        os.environ["MASTODON_ACCESS_TOKEN"] = "environment-token"

        settings = load_mastodon_settings()

        self.assertEqual(
            settings.base_url,
            "https://environment.example",
        )
        self.assertEqual(settings.access_token, "environment-token")

    def test_missing_token_has_clear_error(self):
        os.environ["MASTODON_BASE_URL"] = "https://mastodon.example"

        with self.assertRaisesRegex(
            ValueError,
            "MASTODON_BASE_URL and MASTODON_ACCESS_TOKEN are required.",
        ):
            load_mastodon_settings()