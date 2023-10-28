from datetime import datetime


def parse_timestamp(timestamp: str) -> datetime:
    """Converts a timestamp to a datetime object."""
    return datetime.fromisoformat(timestamp)


def timestamp_since_epoch(timestamp: str) -> float:
    """Returns the number of seconds since the epoch."""
    return parse_timestamp(timestamp).timestamp()
