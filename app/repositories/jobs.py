import sqlite3
from uuid import uuid4

from app.database import connect_db


def insert_job(variant_id: int, scheduled_at: str) -> dict:
    with connect_db() as connection:
        connection.row_factory = sqlite3.Row

        with connection:
            connection.execute("BEGIN IMMEDIATE")

            variant = connection.execute(
                "SELECT * FROM variants WHERE id = ?",
                (variant_id,),
            ).fetchone()

            if variant is None:
                raise LookupError("Variant not found.")

            if variant["status"] != "approved":
                raise RuntimeError("Only approved variants can be scheduled.")

            connection.execute(
                """
                INSERT INTO publish_jobs (
                    variant_id, scheduled_at, platform, text, idempotency_key
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (variant_id, scheduled_at) DO NOTHING
                """,
                (
                    variant_id,
                    scheduled_at,
                    variant["platform"],
                    variant["text"],
                    str(uuid4()),
                ),
            )

            job = connection.execute(
                """
                SELECT *
                FROM publish_jobs
                WHERE variant_id = ? AND scheduled_at = ?
                """,
                (variant_id, scheduled_at),
            ).fetchone()

            return dict(job)