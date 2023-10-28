"""A class to read and store lows."""
import json
import logging
from datetime import datetime
from typing import List, TypedDict

from flask import Response

from .config import tz
from .login import assert_current_request_logged_in
from .redis import bump_revision, redis_client
from .server import app
from .utils import parse_timestamp
from .webhooks import call_webhooks

_key_set = "low:set"
_key_hash = "low:hash"


class LowRecord(TypedDict):
    """A low record."""

    id: str
    timestamp: str
    sugar_in_grams: float
    deleted: bool


@app.route("/opengluck/low", methods=["DELETE"])
def _clear_all_low_records():
    """Delete all low records."""
    assert_current_request_logged_in()
    redis_client.delete(_key_set)
    bump_revision()
    return Response(status=204)


def record_low(
    *, id: str, timestamp: datetime, sugar_in_grams: float, deleted: bool
) -> None:
    """Record a low."""
    logging.info(
        f"Recording low, id={id}, timestamp={timestamp}, "
        + f"sugar_in_grams={sugar_in_grams}, deleted={deleted}"
    )
    ts = str(timestamp.timestamp())
    value = json.dumps(
        {"id": id, "ts": ts, "sugar_in_grams": sugar_in_grams, "deleted": deleted}
    )
    res = (
        redis_client.pipeline()
        .hget(_key_hash, id)
        .zadd(_key_set, {id: ts})
        .hset(_key_hash, id, value)
        .execute()
    )
    should_bump_revision: bool = True
    if res[0] is not None:
        logging.info("Duplicate low, check if we need to bump revision")
        previous_record = _value_to_low_record(res[0])
        if (
            datetime.fromisoformat(previous_record["timestamp"]) == timestamp
            and previous_record["sugar_in_grams"] == sugar_in_grams
            and previous_record["deleted"] == deleted
        ):
            logging.info("Duplicate low sugar")
            should_bump_revision = False
    if should_bump_revision:
        bump_revision()
        call_webhooks(
            "low:new",
            {
                "id": id,
                "timestamp": timestamp.isoformat(),
                "sugar_in_grams": sugar_in_grams,
                "deleted": deleted,
            },
        )


def _value_to_low_record(member: bytes) -> LowRecord:
    record = json.loads(member.decode("utf-8"))
    return LowRecord(
        id=record["id"],
        timestamp=datetime.fromtimestamp(float(record["ts"]), tz=tz).isoformat(),
        sugar_in_grams=record["sugar_in_grams"],
        deleted=record["deleted"],
    )


def get_latest_low_records(last_n: int = 288) -> List[LowRecord]:
    """Gets the latest last_n low records."""
    records = []
    # use zrange to return the last last_n entries ranked by score
    res = redis_client.zrange(_key_set, -last_n, -1)
    for id in res:
        value = redis_client.hget(_key_hash, id)
        assert value
        records.append(_value_to_low_record(value))
    records.reverse()
    return records


class InsertLowRecordsStatus(TypedDict):
    """The response to a low upload."""

    success: bool
    status: str


def insert_low_records(low_records: List[dict]) -> InsertLowRecordsStatus:
    """Insert low records at once.

    Args:
        low_records: The low records to insert
    Returns:
        the response
    """
    low_records = sorted(
        low_records, key=lambda record: record["timestamp"], reverse=False
    )
    for record in low_records:
        record_low(
            id=record["id"],
            timestamp=parse_timestamp(record["timestamp"]),
            sugar_in_grams=record["sugar_in_grams"],
            deleted=record["deleted"],
        )
    return InsertLowRecordsStatus(
        success=True, status=f"added {len(low_records)} record(s)"
    )
