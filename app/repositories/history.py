import sqlite3

from app.database import connect_db


def list_publish_history() -> list[dict]:
    with connect_db() as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT attempts.*, jobs.variant_id, jobs.platform,
                   jobs.scheduled_at, jobs.status AS job_status
            FROM publish_attempts AS attempts
            JOIN publish_jobs AS jobs ON jobs.id = attempts.job_id
            ORDER BY attempts.id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]