import logging
import time

from app.database import init_db
from app.publishers.registry import get_publisher
from app.repositories.worker import claim_due_job, finish_attempt

logger = logging.getLogger(__name__)


def run_once() -> bool:
    job = claim_due_job()

    if job is None:
        return False

    try:
        publisher = get_publisher(job["platform"])
        result = publisher.publish(
            job["text"],
            job["idempotency_key"],
        )
    except Exception as error:
        recorded = finish_attempt(
            job,
            outcome="failed",
            error=type(error).__name__,
        )
        logger.error(
            "Job %s publish failed with %s. Recorded: %s",
            job["id"],
            type(error).__name__,
            recorded,
        )
        return True

    recorded = finish_attempt(
        job,
        outcome="success",
        post_id=result.post_id,
        url=result.url,
    )

    if recorded:
        logger.info("Job %s published: %s", job["id"], result.url)
    else:
        logger.warning(
            "Job %s lost its lease before completion was recorded.",
            job["id"],
        )

    return True


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    init_db()
    logger.info("Worker started.")

    try:
        while True:
            if not run_once():
                time.sleep(2)
    except KeyboardInterrupt:
        logger.info("Worker stopped.")


if __name__ == "__main__":
    main()