from fastapi import APIRouter, HTTPException
from app.services.posts import create_stored_post, require_post
from app.schemas import PostCreate

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", status_code=201)
def create_post(post: PostCreate):
    try:
        post_id = create_stored_post(post.markdown)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return {"id": post_id}


@router.get("/{post_id}")
def get_post(post_id: int):
    return require_post(post_id)
