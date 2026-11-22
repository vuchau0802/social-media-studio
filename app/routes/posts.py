from fastapi import APIRouter, HTTPException

from app.repositories.posts import insert_post
from app.services.posts import require_post
from app.schemas import PostCreate

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", status_code=201)
def create_post(post: PostCreate):
    if not post.markdown.strip():
        raise HTTPException(
            status_code=422,
            detail="Markdown must contain text.",
        )

    post_id = insert_post(post.markdown)
    return {"id": post_id}


@router.get("/{post_id}")
def get_post(post_id: int):
    return require_post(post_id)
