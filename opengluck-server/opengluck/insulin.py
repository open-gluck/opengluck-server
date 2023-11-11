"""A class to read and store insulin units."""
import json
import logging
from datetime import datetime
from typing import List, TypedDict

from flask import Response

from .config import tz
from .login import assert_get_current_request_redis_client
from .redis import bump_revision
from .server import app
from .utils import parse_timestamp
from .webhooks import call_webhooks

_key_set = "insulin:set"
_key_hash = "insulin:hash"


class InsulinRecord(TypedDict):
    """An insulin record."""

    id: str
    timestamp: str
    units: int
    deleted: bool


@app.route("/opengluck/insulin", methods=["DELETE"])
def _clear_all_insulin_records():
    """Delete all insulin records."""
    redis_client = assert_get_current_request_redis_client()
    redis_client.delete(_key_set)
    bump_revision(redis_client)
    return Response(status=204)


def record_insulin(*, id: str, timestamp: datetime, units: int, deleted: bool) -> None:
    """Record an insulin unit."""
    redis_client = assert_get_current_request_redis_client()
    logging.info(
        f"Recording insulin unit, id={id}, timestamp={timestamp}, units={units}, "
        + f"deleted={deleted}"
    )
    ts = str(timestamp.timestamp())
    value = json.dumps({"id": id, "ts": ts, "units": units, "deleted": deleted})
    res = (
        redis_client.pipeline()
        .hget(_key_hash, id)
        .zadd(_key_set, {id: ts})
        .hset(_key_hash, id, value)
        .execute()
    )
    should_bump_revision: bool = True
    if res[0] is not None:
        logging.info("Duplicate insulin units, check if we need to bump revision")
        previous_record = _value_to_insulin_record(res[0])
        if (
            datetime.fromisoformat(previous_record["timestamp"]) == timestamp
            and previous_record["units"] == units
            and previous_record["deleted"] == deleted
        ):
            logging.info("Duplicate insulin units")
            should_bump_revision = False
    if should_bump_revision:
        bump_revision(redis_client)
        call_webhooks(
            "insulin:new",
            {
                "id": id,
                "timestamp": timestamp.isoformat(),
                "units": units,
                "deleted": deleted,
            },
        )


def _value_to_insulin_record(member: bytes) -> InsulinRecord:
    record = json.loads(member.decode("utf-8"))
    return InsulinRecord(
        id=record["id"],
        timestamp=datetime.fromtimestamp(float(record["ts"]), tz=tz).isoformat(),
        units=record["units"],
        deleted=record["deleted"],
    )


def get_latest_insulin_records(last_n: int = 288) -> List[InsulinRecord]:
    """Gets the latest last_n insulin records."""
    redis_client = assert_get_current_request_redis_client()
    records = []
    # use zrange to return the last last_n entries ranked by score
    res = redis_client.zrange(_key_set, -last_n, -1)
    for id in res:
        value = redis_client.hget(_key_hash, id)
        assert value
        records.append(_value_to_insulin_record(value))
    records.reverse()
    return records


class InsertInsulinRecordsStatus(TypedDict):
    """The response to an insulin upload."""

    success: bool
    status: str


def insert_insulin_records(insulin_records: List[dict]) -> InsertInsulinRecordsStatus:
    """Insert insulin records at once.

    Args:
        insulin_records: The insulin records to insert
    Returns:
        the response
    """
    insulin_records = sorted(
        insulin_records, key=lambda record: record["timestamp"], reverse=False
    )
    for record in insulin_records:
        record_insulin(
            id=record["id"],
            timestamp=parse_timestamp(record["timestamp"]),
            units=record["units"],
            deleted=record["deleted"],
        )
    return InsertInsulinRecordsStatus(
        success=True, status=f"added {len(insulin_records)} record(s)"
    )


def find_insulin_records(from_date: datetime, to_date: datetime) -> List[InsulinRecord]:
    """Find insulin records in the given time range."""
    redis_client = assert_get_current_request_redis_client()
    from_ts = from_date.timestamp()
    to_ts = to_date.timestamp()
    from_ts = from_date.timestamp()
    to_ts = to_date.timestamp()
    result = []
    logging.debug(f"Finding insulin records between {from_ts} and {to_ts}")
    for id in redis_client.zrangebyscore(_key_set, from_ts, to_ts):
        value = redis_client.hget(_key_hash, id)
        assert value
        result.append(_value_to_insulin_record(value))
    result.reverse()
    logging.debug(f"Found {len(result)} record(s)")
    return result
