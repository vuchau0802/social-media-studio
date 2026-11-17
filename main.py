import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
DB_PATH = Path(__file__).with_name("studio.db")


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