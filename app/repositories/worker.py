import sqlite3
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.database import connect_db


def claim_due_job(lease_seconds: int = 60) -> dict | None:
    if lease_seconds <= 0:
        raise ValueError("Lease duration must be positive.")

    with connect_db() as connection:
        connection.row_factory = sqlite3.Row

        with connection:
            connection.execute("BEGIN IMMEDIATE")

            now = datetime.now(timezone.utc)
            now_text = now.isoformat(timespec="microseconds")

            job = connection.execute(
                """
                SELECT jobs.*
                FROM publish_jobs AS jobs
                JOIN variants ON variants.id = jobs.variant_id
                LEFT JOIN job_leases AS leases ON leases.job_id = jobs.id
                WHERE jobs.scheduled_at <= ?
                  AND variants.status IN ('approved', 'published')
                  AND (
                      jobs.status = 'pending'
                      OR (
                          jobs.status = 'processing'
                          AND (
                              leases.job_id IS NULL
                              OR leases.expires_at <= ?
                          )
                      )
                  )
                ORDER BY jobs.scheduled_at, jobs.id
                LIMIT 1
                """,
                (now_text, now_text),
            ).fetchone()

            if job is None:
                return None

            token = str(uuid4())
            expires_at = (
                now + timedelta(seconds=lease_seconds)
            ).isoformat(timespec="microseconds")

            connection.execute(
                """
                UPDATE publish_attempts
                SET outcome = 'interrupted', finished_at = ?
                WHERE job_id = ? AND outcome = 'started'
                """,
                (now_text, job["id"]),
            )

            connection.execute(
                """
                INSERT INTO job_leases (job_id, token, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT (job_id) DO UPDATE
                SET token = excluded.token,
                    expires_at = excluded.expires_at
                """,
                (job["id"], token, expires_at),
            )

            connection.execute(
                "UPDATE publish_jobs SET status = 'processing' WHERE id = ?",
                (job["id"],),
            )

            attempt = connection.execute(
                """
                INSERT INTO publish_attempts (
                    job_id, lease_token, started_at
                )
                VALUES (?, ?, ?)
                """,
                (job["id"], token, now_text),
            )

            return {
                **dict(job),
                "status": "processing",
                "lease_token": token,
                "attempt_id": attempt.lastrowid,
            }

def finish_attempt(
    job: dict,
    outcome: str,
    post_id: str | None = None,
    url: str | None = None,
    error: str | None = None,
) -> bool:
    if outcome not in {"success", "failed"}:
        raise ValueError("Outcome must be success or failed.")

    with connect_db() as connection:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            now = datetime.now(timezone.utc).isoformat(
                timespec="microseconds"
            )

            current = connection.execute(
                """
                SELECT jobs.variant_id
                FROM publish_jobs AS jobs
                JOIN job_leases AS leases ON leases.job_id = jobs.id
                JOIN publish_attempts AS attempts
                  ON attempts.job_id = jobs.id
                WHERE jobs.id = ?
                  AND jobs.status = 'processing'
                  AND leases.token = ?
                  AND leases.expires_at > ?
                  AND attempts.id = ?
                  AND attempts.lease_token = leases.token
                  AND attempts.outcome = 'started'
                """,
                (
                    job["id"],
                    job["lease_token"],
                    now,
                    job["attempt_id"],
                ),
            ).fetchone()

            if current is None:
                return False

            connection.execute(
                """
                UPDATE publish_attempts
                SET outcome = ?, finished_at = ?,
                    provider_post_id = ?, url = ?, error = ?
                WHERE id = ?
                """,
                (
                    outcome,
                    now,
                    post_id,
                    url,
                    error,
                    job["attempt_id"],
                ),
            )

            job_status = "published" if outcome == "success" else "failed"

            connection.execute(
                "UPDATE publish_jobs SET status = ? WHERE id = ?",
                (job_status, job["id"]),
            )

            if outcome == "success":
                connection.execute(
                    "UPDATE variants SET status = 'published' WHERE id = ?",
                    (current[0],),
                )

            connection.execute(
                "DELETE FROM job_leases WHERE job_id = ? AND token = ?",
                (job["id"], job["lease_token"]),
            )

            return True