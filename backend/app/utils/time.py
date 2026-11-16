"""Time helpers.

Audit timestamps (created_at, updated_at, completed_at, resolved_at, ...) are stored as
naive UTC and serialised with an explicit UTC offset so browsers in any timezone show
the right local time. User-entered appointment times (scheduled_at) are wall-clock
times and are kept as entered.
"""
from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc_iso(v: datetime | None) -> str | None:
    if v is None:
        return None
    if v.tzinfo is None:
        v = v.replace(tzinfo=timezone.utc)
    return v.isoformat()


UTCDateTime = Annotated[datetime, PlainSerializer(to_utc_iso, return_type=str)]
