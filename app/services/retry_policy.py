from datetime import datetime, timedelta, timezone

MAX_ATTEMPTS = 5
RETRY_WINDOW = timedelta(minutes=30)


class RetryLimitExceeded(RuntimeError):
    pass


def next_retry_at(
    *,
    first_started_at: datetime,
    attempt_count: int,
    requested_delay: int,
    now: datetime | None = None,
) -> datetime:
    now = now or datetime.now(timezone.utc)

    if attempt_count < 1:
        raise ValueError("Attempt count must include the current attempt.")

    if attempt_count >= MAX_ATTEMPTS:
        raise RetryLimitExceeded("Maximum publish attempts reached.")

    backoff_seconds = min(300, 30 * (2 ** (attempt_count - 1)))
    delay_seconds = max(requested_delay, backoff_seconds)

    deadline = first_started_at + RETRY_WINDOW
    remaining_seconds = (deadline - now).total_seconds()

    if delay_seconds >= remaining_seconds:
        raise RetryLimitExceeded(
            "Retry window exceeded. Reconcile before publishing again."
        )

    return now + timedelta(seconds=delay_seconds)