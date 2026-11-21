from app.profiles import validate_variant
from app.repositories.variants import change_draft_status, find_variant


def review_variant(variant_id: int, decision: str) -> dict:
    if decision not in {"approved", "rejected"}:
        raise ValueError("Review decision must be approved or rejected.")

    variant = find_variant(variant_id)

    if variant is None:
        raise LookupError("Variant not found.")

    if variant["status"] != "draft":
        raise ValueError("Only draft variants can be reviewed.")

    if decision == "approved":
        errors = validate_variant(variant["platform"], variant["text"])
        if errors:
            raise ValueError(" ".join(errors))

    if not change_draft_status(variant_id, decision, variant["text"]):
        raise ValueError("Variant changed during review. Reload and retry.")

    return {**variant, "status": decision}