from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routes.posts import router as posts_router
from app.routes.publishing import router as publishing_router
from app.routes.variants import router as variants_router
from app.services.posts import PostNotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(posts_router)
app.include_router(variants_router)
app.include_router(publishing_router)


@app.exception_handler(PostNotFoundError)
async def handle_missing_post(request: Request, error: PostNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(error)},
    )