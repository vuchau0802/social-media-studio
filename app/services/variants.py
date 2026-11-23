from app.profiles import validate_variant
from app.repositories.variants import find_variant, insert_variants, list_variants, update_variant_text
from app.generator import generate_variants
from app.services.posts import require_post

def edit_variant(variant_id: int, text: str) -> dict:
    variant = find_variant(variant_id)

    if variant is None:
        raise LookupError("Variant not found.")

    if variant["status"] not in {"draft", "approved", "rejected"}:
        raise RuntimeError("This variant cannot be edited.")

    errors = validate_variant(variant["platform"], text)
    if errors:
        raise ValueError(" ".join(errors))

    if not update_variant_text(variant, text):
        raise RuntimeError("Variant changed or has a scheduled job. Reload before editing.")

    return {**variant, "text": text, "status": "draft"}

class VariantGenerationError(ValueError):
    def __init__(self, platform: str, errors: list[str]):
        self.detail = {"platform": platform, "errors": errors}
        super().__init__(" ".join(errors))


def create_post_variants(post_id: int) -> list[dict]:
    post = require_post(post_id)
    drafts = generate_variants(post["markdown"])

    for draft in drafts:
        errors = validate_variant(draft["platform"], draft["text"])

        if errors:
            raise VariantGenerationError(draft["platform"], errors)

    return insert_variants(post_id, drafts)


def get_post_variants(post_id: int) -> list[dict]:
    require_post(post_id)
    return list_variants(post_id)