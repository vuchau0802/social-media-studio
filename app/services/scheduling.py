from datetime import datetime, timezone

from app.repositories.jobs import insert_job


def schedule_variant(variant_id: int, scheduled_at: datetime) -> dict:
    if scheduled_at.tzinfo is None or scheduled_at.utcoffset() is None:
        raise ValueError("Publish time must include a timezone.")

    scheduled_utc = scheduled_at.astimezone(timezone.utc)

    if scheduled_utc <= datetime.now(timezone.utc):
        raise ValueError("Publish time must be in the future.")

    return insert_job(
        variant_id,
        scheduled_utc.isoformat(timespec="microseconds"),
    )