import subprocess
import sys
from textwrap import dedent

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from app import database
from app.publishers.mock import MockXPublisher
from app.repositories.worker import claim_due_job, finish_attempt
from app.services.retry_policy import MAX_ATTEMPTS
from app.worker import run_once


class WorkerRecoveryTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)

        original_path = database.DB_PATH
        self.addCleanup(setattr, database, "DB_PATH", original_path)

        database.DB_PATH = Path(directory.name) / "recovery.db"
        database.init_db()

        due = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat(timespec="microseconds")

        with database.connect_db() as connection:
            with connection:
                connection.execute(
                    "INSERT INTO posts (id, markdown) VALUES (1, 'Article')"
                )
                connection.execute(
                    """
                    INSERT INTO variants (
                        id, post_id, platform, text, status
                    )
                    VALUES (1, 1, 'mock_x', 'Recovery example', 'approved')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO publish_jobs (
                        variant_id, scheduled_at, platform,
                        text, idempotency_key
                    )
                    VALUES (
                        1, ?, 'mock_x', 'Recovery example', 'recovery-check'
                    )
                    """,
                    (due,),
                )

    def test_future_retry_time_blocks_claim(self):
        future = (
            datetime.now(timezone.utc) + timedelta(minutes=5)
        ).isoformat(timespec="microseconds")

        with database.connect_db() as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO job_retry_state (job_id, next_attempt_at)
                    VALUES (1, ?)
                    """,
                    (future,),
                )

        self.assertIsNone(claim_due_job())

        past = (
            datetime.now(timezone.utc) - timedelta(seconds=1)
        ).isoformat(timespec="microseconds")

        with database.connect_db() as connection:
            with connection:
                connection.execute(
                    """
                    UPDATE job_retry_state
                    SET next_attempt_at = ?
                    WHERE job_id = 1
                    """,
                    (past,),
                )

        job = claim_due_job()
        self.assertIsNotNone(job)
        self.assertEqual(job["id"], 1)
        self.assertEqual(job["idempotency_key"], "recovery-check")

    def test_expired_retry_window_blocks_recovery(self):
        original_job = claim_due_job()
        self.assertIsNotNone(original_job)

        old_start = (
            datetime.now(timezone.utc) - timedelta(minutes=31)
        ).isoformat(timespec="microseconds")
        expired_lease = (
            datetime.now(timezone.utc) - timedelta(seconds=1)
        ).isoformat(timespec="microseconds")

        with database.connect_db() as connection:
            with connection:
                connection.execute(
                    "UPDATE publish_attempts SET started_at = ?",
                    (old_start,),
                )
                connection.execute(
                    "UPDATE job_leases SET expires_at = ?",
                    (expired_lease,),
                )

        self.assertIsNone(claim_due_job())

        with database.connect_db() as connection:
            job_status = connection.execute(
                "SELECT status FROM publish_jobs WHERE id = 1"
            ).fetchone()[0]
            attempts = connection.execute(
                "SELECT outcome, error FROM publish_attempts"
            ).fetchall()
            lease_count = connection.execute(
                "SELECT COUNT(*) FROM job_leases"
            ).fetchone()[0]

        self.assertEqual(job_status, "failed")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0][0], "interrupted")
        self.assertIn("Retry window exceeded", attempts[0][1])
        self.assertEqual(lease_count, 0)

    def test_attempt_limit_blocks_another_recovery(self):
        for _ in range(MAX_ATTEMPTS):
            self.assertIsNotNone(claim_due_job())

            expired = (
                datetime.now(timezone.utc) - timedelta(seconds=1)
            ).isoformat(timespec="microseconds")
            with database.connect_db() as connection:
                with connection:
                    connection.execute(
                        "UPDATE job_leases SET expires_at = ?",
                        (expired,),
                    )

        self.assertIsNone(claim_due_job())

        with database.connect_db() as connection:
            attempt_count = connection.execute(
                "SELECT COUNT(*) FROM publish_attempts"
            ).fetchone()[0]
            job_status = connection.execute(
                "SELECT status FROM publish_jobs WHERE id = 1"
            ).fetchone()[0]
            last_attempt = connection.execute(
                """
                SELECT outcome, error FROM publish_attempts
                ORDER BY id DESC LIMIT 1
                """
            ).fetchone()

        self.assertEqual(attempt_count, MAX_ATTEMPTS)
        self.assertEqual(job_status, "failed")
        self.assertEqual(last_attempt[0], "interrupted")
        self.assertIn("Maximum publish attempts", last_attempt[1])

    def test_recovery_after_adapter_accepts_post(self):
        original_job = claim_due_job()
        self.assertIsNotNone(original_job)

        publisher = MockXPublisher()
        original_result = publisher.publish(
            original_job["text"],
            original_job["idempotency_key"],
        )

        # Simulate a stopped worker by leaving its attempt unfinished.
        expired = (
            datetime.now(timezone.utc) - timedelta(seconds=1)
        ).isoformat(timespec="microseconds")

        with database.connect_db() as connection:
            with connection:
                connection.execute(
                    "UPDATE job_leases SET expires_at = ? WHERE job_id = ?",
                    (expired, original_job["id"]),
                )

        recovered_job = claim_due_job()
        self.assertIsNotNone(recovered_job)
        self.assertEqual(original_job["id"], recovered_job["id"])
        self.assertNotEqual(
            original_job["lease_token"],
            recovered_job["lease_token"],
        )
        self.assertEqual(
            original_job["idempotency_key"],
            recovered_job["idempotency_key"],
        )

        # The old worker cannot complete using its stale lease.
        self.assertFalse(
            finish_attempt(
                original_job,
                "success",
                original_result.post_id,
                original_result.url,
            )
        )

        recovered_result = publisher.publish(
            recovered_job["text"],
            recovered_job["idempotency_key"],
        )
        self.assertEqual(original_result, recovered_result)

        self.assertTrue(
            finish_attempt(
                recovered_job,
                "success",
                recovered_result.post_id,
                recovered_result.url,
            )
        )

        self.assertFalse(run_once())

        with database.connect_db() as connection:
            publication_count = connection.execute(
                "SELECT COUNT(*) FROM mock_publications"
            ).fetchone()[0]

            outcomes = connection.execute(
                "SELECT outcome FROM publish_attempts ORDER BY id"
            ).fetchall()

            job_status = connection.execute(
                "SELECT status FROM publish_jobs WHERE id = 1"
            ).fetchone()[0]

            variant_status = connection.execute(
                "SELECT status FROM variants WHERE id = 1"
            ).fetchone()[0]

        self.assertEqual(publication_count, 1)
        self.assertEqual(outcomes, [("interrupted",), ("success",)])
        self.assertEqual(job_status, "published")
        self.assertEqual(variant_status, "published")

    def test_recovery_after_process_exit(self):
        project_root = Path(__file__).resolve().parents[1]

        crash_code = dedent("""
            import os
            import sys
            from pathlib import Path

            from app import database
            from app.publishers.registry import get_publisher
            from app.repositories.worker import claim_due_job

            database.DB_PATH = Path(sys.argv[1])

            job = claim_due_job()
            assert job is not None

            publisher = get_publisher(job["platform"])
            publisher.publish(job["text"], job["idempotency_key"])

            # Exit immediately after publishing, before recording completion.
            os._exit(23)
        """)

        crashed = subprocess.run(
            [
                sys.executable,
                "-c",
                crash_code,
                str(database.DB_PATH),
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(crashed.returncode, 23, crashed.stderr)

        with database.connect_db() as connection:
            outcome = connection.execute(
                "SELECT outcome FROM publish_attempts"
            ).fetchone()[0]
            self.assertEqual(outcome, "started")

            # Advance lease expiry so recovery can run immediately.
            expired = (
                datetime.now(timezone.utc) - timedelta(seconds=1)
            ).isoformat(timespec="microseconds")

            with connection:
                connection.execute(
                    "UPDATE job_leases SET expires_at = ?",
                    (expired,),
                )

        recovery_code = dedent("""
            import sys
            from pathlib import Path

            from app import database
            from app.worker import run_once

            database.DB_PATH = Path(sys.argv[1])

            assert run_once()
            assert not run_once()
        """)

        recovered = subprocess.run(
            [
                sys.executable,
                "-c",
                recovery_code,
                str(database.DB_PATH),
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(recovered.returncode, 0, recovered.stderr)

        with database.connect_db() as connection:
            publication_count = connection.execute(
                "SELECT COUNT(*) FROM mock_publications"
            ).fetchone()[0]

            outcomes = connection.execute(
                "SELECT outcome FROM publish_attempts ORDER BY id"
            ).fetchall()

            job_status = connection.execute(
                "SELECT status FROM publish_jobs WHERE id = 1"
            ).fetchone()[0]

        self.assertEqual(publication_count, 1)
        self.assertEqual(outcomes, [("interrupted",), ("success",)])
        self.assertEqual(job_status, "published")
