import json

from app.database import init_db
from app.services.posts import create_stored_post
from app.services.variants import create_post_variants

SAMPLE_MARKDOWN = """# Building reliable publishing workflows

A reliable publishing workflow stores the source article, validates
platform drafts, and requires human approval before scheduling.

Persistent jobs and stable idempotency keys help workers recover
from interrupted publishing attempts.
"""


def main():
    init_db()

    post_id = create_stored_post(SAMPLE_MARKDOWN)
    drafts = create_post_variants(post_id)

    print(json.dumps(
        {
            "post_id": post_id,
            "variants": drafts,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()