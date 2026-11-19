from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.generator import generate_variants
from app.profiles import validate_variant
from app.database import init_db
from contextlib import asynccontextmanager
from app.repositories.posts import insert_post, find_post
from app.repositories.variants import insert_variants, list_variants

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