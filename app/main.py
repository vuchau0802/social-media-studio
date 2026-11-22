from fastapi import FastAPI, HTTPException
from app.generator import generate_variants
from app.profiles import validate_variant
from app.database import init_db
from contextlib import asynccontextmanager
from app.routes.posts import get_post, router as posts_router
from app.repositories.variants import insert_variants, list_variants
from app.services.review import review_variant
from app.schemas import VariantEdit, ScheduleCreate
from app.services.variants import edit_variant
from app.services.scheduling import schedule_variant
from app.repositories.mock_publications import find_publication
from app.repositories.history import list_publish_history

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(posts_router)

@app.post("/posts/{post_id}/variants", status_code=201)
def create_variants(post_id: int):
    post = get_post(post_id)
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

@app.get("/posts/{post_id}/variants")
def get_variants(post_id: int):
    get_post(post_id)
    return list_variants(post_id)

def handle_review(variant_id: int, decision: str):
    try:
        return review_variant(variant_id, decision)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/variants/{variant_id}/approve")
def approve_variant(variant_id: int):
    return handle_review(variant_id, "approved")


@app.post("/variants/{variant_id}/reject")
def reject_variant(variant_id: int):
    return handle_review(variant_id, "rejected")

@app.patch("/variants/{variant_id}")
def update_variant(variant_id: int, body: VariantEdit):
    try:
        return edit_variant(variant_id, body.text)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

@app.post("/variants/{variant_id}/schedule", status_code=201)
def create_schedule(variant_id: int, body: ScheduleCreate):
    try:
        return schedule_variant(variant_id, body.scheduled_at)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

@app.get("/mock-publications/{publication_id}")
def get_mock_publication(publication_id: int):
    publication = find_publication(publication_id)

    if publication is None:
        raise HTTPException(
            status_code=404,
            detail="Mock publication not found.",
        )

    return publication

@app.get("/publish-history")
def get_publish_history():
    return list_publish_history()
