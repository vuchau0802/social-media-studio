from fastapi import APIRouter, HTTPException

from app.generator import generate_variants
from app.profiles import validate_variant
from app.repositories.variants import insert_variants, list_variants
from app.schemas import ScheduleCreate, VariantEdit
from app.services.posts import require_post
from app.services.review import review_variant
from app.services.scheduling import schedule_variant
from app.services.variants import edit_variant

router = APIRouter(tags=["variants"])

@router.post("/posts/{post_id}/variants", status_code=201)
def create_variants(post_id: int):
    post = require_post(post_id)
    drafts = generate_variants(post["markdown"])

    for draft in drafts:
        errors = validate_variant(draft["platform"], draft["text"])

        if errors:
            raise HTTPException(
                status_code=422,
                detail={
                    "platform": draft["platform"],
                    "errors": errors,
                },
            )

    return insert_variants(post_id, drafts)

@router.get("/posts/{post_id}/variants")
def get_variants(post_id: int):
    require_post(post_id)
    return list_variants(post_id)

def handle_review(variant_id: int, decision: str):
    try:
        return review_variant(variant_id, decision)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/variants/{variant_id}/approve")
def approve_variant(variant_id: int):
    return handle_review(variant_id, "approved")


@router.post("/variants/{variant_id}/reject")
def reject_variant(variant_id: int):
    return handle_review(variant_id, "rejected")

@router.patch("/variants/{variant_id}")
def update_variant(variant_id: int, body: VariantEdit):
    try:
        return edit_variant(variant_id, body.text)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

@router.post("/variants/{variant_id}/schedule", status_code=201)
def create_schedule(variant_id: int, body: ScheduleCreate):
    try:
        return schedule_variant(variant_id, body.scheduled_at)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
