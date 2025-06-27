from datetime import datetime, UTC


def now() -> datetime:
    return datetime.now(UTC)
