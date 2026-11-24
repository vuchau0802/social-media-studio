from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from math import ceil

import httpx


def retry_delay(
    headers: httpx.Headers,
    now: datetime | None = None,
) -> int:
    now = now or datetime.now(timezone.utc)
    delays = []

    retry_after = headers.get("Retry-After")

    if retry_after:
        retry_after = retry_after.strip()

        try:
            if retry_after.isascii() and retry_after.isdecimal():
                delays.append(int(retry_after))
            else:
                retry_at = parsedate_to_datetime(retry_after)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)

                delays.append(ceil((retry_at - now).total_seconds()))
        except (ValueError, TypeError, OverflowError):
            pass

    reset = headers.get("X-RateLimit-Reset")

    if reset:
        try:
            reset_at = datetime.fromisoformat(reset)
            if reset_at.tzinfo is None:
                reset_at = reset_at.replace(tzinfo=timezone.utc)

            delays.append(ceil((reset_at - now).total_seconds()))
        except (ValueError, TypeError, OverflowError):
            pass

    return max(1, max(delays, default=30))