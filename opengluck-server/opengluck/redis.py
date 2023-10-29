"""The redis client."""
import datetime
import os

import redis

_redis_port = int(os.environ.get("REDIS_PORT", 6379))
redis_client = redis.Redis(host="localhost", port=_redis_port, db=0)


def bump_revision() -> None:
    """Bump the revision number."""
    p = redis_client.pipeline()
    p.incr("revision")
    p.set("revision_changed_at", datetime.datetime.utcnow().isoformat())
    p.execute()


def get_revision() -> int:
    """Get the current revision number."""
    return int(redis_client.get("revision") or -1)


def get_revision_changed_at() -> str:
    """Get the date when the revision was changed."""
    revision_changed_at = redis_client.get("revision_changed_at")
    if not revision_changed_at:
        return datetime.datetime(1970, 1, 1, 0, 0, 0, 0).isoformat()
    return revision_changed_at.decode("utf-8")
