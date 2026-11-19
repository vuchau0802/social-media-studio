from app.database import connect_db


def insert_post(markdown: str) -> int:
    with connect_db() as connection:
        with connection:
            result = connection.execute(
                "INSERT INTO posts (markdown) VALUES (?)",
                (markdown,),
            )
            return result.lastrowid


def find_post(post_id: int) -> dict | None:
    with connect_db() as connection:
        row = connection.execute(
            "SELECT id, markdown FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()

    if row is None:
        return None

    return {"id": row[0], "markdown": row[1]}