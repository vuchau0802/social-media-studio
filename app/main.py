from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.repositories.history import list_publish_history
from app.repositories.mock_publications import find_publication
from app.routes.posts import router as posts_router
from app.routes.variants import router as variants_router
from app.services.posts import PostNotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(posts_router)
app.include_router(variants_router)


@app.exception_handler(PostNotFoundError)
async def handle_missing_post(request: Request, error: PostNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(error)},
    )


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