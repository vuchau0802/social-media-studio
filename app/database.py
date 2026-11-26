from multiprocessing.dummy import connection
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "studio.db"


@contextmanager
def connect_db():
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
    finally:
        connection.close()

def init_db():
    with connect_db() as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY,
                    markdown TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS variants (
                    id INTEGER PRIMARY KEY,
                    post_id INTEGER NOT NULL REFERENCES posts(id),
                    platform TEXT NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft'
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS publish_jobs (
                    id INTEGER PRIMARY KEY,
                    variant_id INTEGER NOT NULL REFERENCES variants(id),
                    scheduled_at TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    text TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'pending',
                    UNIQUE (variant_id, scheduled_at)
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS job_leases (
                    job_id INTEGER PRIMARY KEY REFERENCES publish_jobs(id),
                    token TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS publish_attempts (
                    id INTEGER PRIMARY KEY,
                    job_id INTEGER NOT NULL REFERENCES publish_jobs(id),
                    lease_token TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    outcome TEXT NOT NULL DEFAULT 'started'
                        CHECK (outcome IN (
                            'started', 'success', 'failed', 'interrupted'
                        )),
                    provider_post_id TEXT,
                    url TEXT,
                    error TEXT
                )
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_publish_jobs_due
                ON publish_jobs (status, scheduled_at)
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_publish_attempts_job
                ON publish_attempts (job_id, id)
            """)

            connection.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_publish_attempts_success
                ON publish_attempts (job_id)
                WHERE outcome = 'success'
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS mock_publications (
                    id INTEGER PRIMARY KEY,
                    platform TEXT NOT NULL,
                    text TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    ),
                    UNIQUE (platform, idempotency_key)
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS job_retry_state (
                    job_id INTEGER PRIMARY KEY REFERENCES publish_jobs(id),
                    next_attempt_at TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS job_publishers (
                    job_id INTEGER PRIMARY KEY REFERENCES publish_jobs(id),
                    adapter TEXT NOT NULL
                )
            """)