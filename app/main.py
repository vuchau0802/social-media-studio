from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.generator import generate_variants
from app.profiles import validate_variant
from app.database import init_db
from contextlib import asynccontextmanager
from app.repositories.posts import insert_post, find_post
from app.repositories.variants import insert_variants, list_variants
from app.services.review import review_variant
from app.schemas import VariantEdit, ScheduleCreate
from app.services.variants import edit_variant
from app.services.scheduling import schedule_variant

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

class PostCreate(BaseModel):
    markdown: str


@app.post("/posts", status_code=201)
def create_post(post: PostCreate):
    if not post.markdown.strip():
        raise HTTPException(
            status_code=422,
            detail="Markdown must contain text.",
        )

    post_id = insert_post(post.markdown)
    return {"id": post_id}


@app.get("/posts/{post_id}")
def get_post(post_id: int):
    post = find_post(post_id)

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Post not found.",
        )

    return post

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