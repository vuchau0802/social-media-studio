from fastapi import APIRouter, HTTPException

from app.repositories.history import list_publish_history
from app.repositories.mock_publications import find_publication

router = APIRouter(tags=["publishing"])


@router.get("/mock-publications/{publication_id}")
def get_mock_publication(publication_id: int):
    publication = find_publication(publication_id)

    if publication is None:
        raise HTTPException(
            status_code=404,
            detail="Mock publication not found.",
        )

    return publication


@router.get("/publish-history")
def get_publish_history():
    return list_publish_history()