import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app import database
from app.services.posts import (
    PostNotFoundError,
    create_stored_post,
    require_post,
)
from app.services.variants import (
    VariantGenerationError,
    create_post_variants,
    get_post_variants,
)


class ContentServiceTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)

        original_path = database.DB_PATH
        self.addCleanup(setattr, database, "DB_PATH", original_path)

        database.DB_PATH = Path(directory.name) / "content.db"
        database.init_db()

    def test_blank_article_is_rejected_without_saving(self):
        with self.assertRaisesRegex(
            ValueError,
            "Markdown must contain text.",
        ):
            create_stored_post("   ")

        with database.connect_db() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM posts"
            ).fetchone()[0]

        self.assertEqual(count, 0)

    def test_stored_article_produces_three_saved_drafts(self):
        markdown = "Stored article text."
        post_id = create_stored_post(markdown)

        self.assertEqual(require_post(post_id)["markdown"], markdown)

        drafts = create_post_variants(post_id)

        self.assertEqual(len(drafts), 3)
        self.assertEqual(
            {draft["platform"] for draft in drafts},
            {"mock_x", "mock_linkedin", "mastodon"},
        )

        for draft in drafts:
            self.assertEqual(draft["post_id"], post_id)
            self.assertEqual(draft["status"], "draft")
            self.assertIn(markdown, draft["text"])

        self.assertEqual(get_post_variants(post_id), drafts)

    def test_invalid_generated_draft_blocks_the_whole_batch(self):
        post_id = create_stored_post("An article.")

        generated = [
            {"platform": "mock_x", "text": "A valid draft."},
            {"platform": "mock_linkedin", "text": "Invalid tone!"},
        ]

        with patch(
            "app.services.variants.generate_variants",
            return_value=generated,
        ):
            with self.assertRaises(VariantGenerationError) as caught:
                create_post_variants(post_id)

        self.assertEqual(
            caught.exception.detail,
            {
                "platform": "mock_linkedin",
                "errors": [
                    "Tone rule allows at most 0 exclamation marks."
                ],
            },
        )
        self.assertEqual(get_post_variants(post_id), [])

    def test_missing_article_cannot_generate_or_list_drafts(self):
        with self.assertRaises(PostNotFoundError):
            create_post_variants(999)

        with self.assertRaises(PostNotFoundError):
            get_post_variants(999)