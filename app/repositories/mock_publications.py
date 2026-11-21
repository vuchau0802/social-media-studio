import sqlite3

from app.database import connect_db


def save_publication(
    platform: str,
    text: str,
    idempotency_key: str,
) -> dict:
    with connect_db() as connection:
        connection.row_factory = sqlite3.Row

        with connection:
            connection.execute(
                """
                INSERT INTO mock_publications (
                    platform, text, idempotency_key
                )
                VALUES (?, ?, ?)
                ON CONFLICT (platform, idempotency_key) DO NOTHING
                """,
                (platform, text, idempotency_key),
            )

            row = connection.execute(
                """
                SELECT *
                FROM mock_publications
                WHERE platform = ? AND idempotency_key = ?
                """,
                (platform, idempotency_key),
            ).fetchone()

            if row["text"] != text:
                raise ValueError(
                    "Idempotency key was already used with different text."
                )

            return dict(row)


def find_publication(publication_id: int) -> dict | None:
    with connect_db() as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            "SELECT * FROM mock_publications WHERE id = ?",
            (publication_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)