import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.generator import generate_variants
from app.profiles import validate_variant

app = FastAPI()
DB_PATH = Path(__file__).resolve().parent.parent / "studio.db"


class PostCreate(BaseModel):
    markdown: str


@app.post("/posts", status_code=201)
def create_post(post: PostCreate):
    if not post.markdown.strip():
        raise HTTPException(
            status_code=422,
            detail="Markdown must contain text.",
        )

    with closing(sqlite3.connect(DB_PATH)) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY,
                    markdown TEXT NOT NULL
                )
            """)
            result = connection.execute(
                "INSERT INTO posts (markdown) VALUES (?)",
                (post.markdown,),
            )
            post_id = result.lastrowid

    return {"id": post_id}

@app.get("/posts/{post_id}")
def get_post(post_id: int):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        row = connection.execute(
            "SELECT id, markdown FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Post not found.")

    return {"id": row[0], "markdown": row[1]}

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

    saved = []

    with closing(sqlite3.connect(DB_PATH)) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS variants (
                    id INTEGER PRIMARY KEY,
                    post_id INTEGER NOT NULL REFERENCES posts(id),
                    platform TEXT NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft'
                )
            """)

            for draft in drafts:
                result = connection.execute(
                    """
                    INSERT INTO variants (post_id, platform, text)
                    VALUES (?, ?, ?)
                    """,
                    (post_id, draft["platform"], draft["text"]),
                )

                saved.append({
                    "id": result.lastrowid,
                    "post_id": post_id,
                    **draft,
                    "status": "draft",
                })

    return saved