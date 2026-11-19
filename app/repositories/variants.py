from app.database import connect_db


def insert_variants(post_id: int, drafts: list[dict]) -> list[dict]:
    saved = []

    with connect_db() as connection:
        with connection:
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
                    "platform": draft["platform"],
                    "text": draft["text"],
                    "status": "draft",
                })

    return saved


def list_variants(post_id: int) -> list[dict]:
    with connect_db() as connection:
        rows = connection.execute(
            """
            SELECT id, post_id, platform, text, status
            FROM variants
            WHERE post_id = ?
            ORDER BY id
            """,
            (post_id,),
        ).fetchall()

    return [
        {
            "id": row[0],
            "post_id": row[1],
            "platform": row[2],
            "text": row[3],
            "status": row[4],
        }
        for row in rows
    ]