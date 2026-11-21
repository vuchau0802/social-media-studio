from app.profiles import validate_variant
from app.repositories.variants import find_variant, update_variant_text


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