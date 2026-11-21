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

def find_variant(variant_id: int) -> dict | None:
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT id, post_id, platform, text, status
            FROM variants
            WHERE id = ?
            """,
            (variant_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "post_id": row[1],
        "platform": row[2],
        "text": row[3],
        "status": row[4],
    }


def change_draft_status(
    variant_id: int,
    status: str,
    expected_text: str,
) -> bool:
    with connect_db() as connection:
        with connection:
            result = connection.execute(
                """
                UPDATE variants
                SET status = ?
                WHERE id = ? AND status = 'draft' AND text = ?
                """,
                (status, variant_id, expected_text),
            )
            return result.rowcount == 1

def update_variant_text(variant: dict, text: str) -> bool:
    with connect_db() as connection:
        with connection:
            result = connection.execute(
                """
                UPDATE variants
                SET text = ?, status = 'draft'
                WHERE id = ? AND text = ? AND status = ?
                    AND NOT EXISTS (
                        SELECT 1
                        FROM publish_jobs
                        WHERE variant_id = variants.id
                    )
                """,
                (
                    text,
                    variant["id"],
                    variant["text"],
                    variant["status"],
                ),
            )
            return result.rowcount == 1