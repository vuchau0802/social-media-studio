import sqlite3
from uuid import uuid4

from app.database import connect_db
from app.config import resolve_publisher

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

            inserted = connection.execute(
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

            if inserted.rowcount == 1:
                adapter = resolve_publisher(variant["platform"])
            else:
                adapter = job["platform"]

            connection.execute(
                """
                INSERT INTO job_publishers (job_id, adapter)
                VALUES (?, ?)
                ON CONFLICT (job_id) DO NOTHING
                """,
                (job["id"], adapter),
            )

            saved_adapter = connection.execute(
                "SELECT adapter FROM job_publishers WHERE job_id = ?",
                (job["id"],),
            ).fetchone()[0]

            return {**dict(job), "adapter": saved_adapter}