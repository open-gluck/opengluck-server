"""A class to read and store foods."""
import json
import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional, TypedDict

from flask import Response

from .config import tz
from .login import assert_get_current_request_redis_client
from .redis import bump_revision
from .server import app
from .utils import parse_timestamp
from .webhooks import call_webhooks

_key_set = "food:set"
_key_hash = "food:hash"


class GlucoseSpeed(str, Enum):
    """The speed of glucose absorption."""

    AUTO = "auto"
    CUSTOM = "custom"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"


class PossibleCompressorsValue(TypedDict):
    """A possible compressors value."""

    glucose_speed: GlucoseSpeed
    comp: Optional[float]


class FoodRecord(TypedDict):
    """A food record."""

    id: str
    timestamp: str
    deleted: bool
    name: str
    carbs: Optional[float]
    comps: PossibleCompressorsValue
    record_until: Optional[str]
    remember_recording: bool


@app.route("/opengluck/food", methods=["DELETE"])
def _clear_all_food_records():
    """Delete all food records."""
    redis_client = assert_get_current_request_redis_client()
    redis_client.delete(_key_set)
    bump_revision(redis_client)
    return Response(status=204)


def record_food(
    *,
    id: str,
    timestamp: datetime,
    deleted: bool,
    name: str,
    carbs: Optional[float],
    comps: PossibleCompressorsValue,
    record_until: Optional[datetime],
    remember_recording: bool,
) -> None:
    """Record a food."""
    redis_client = assert_get_current_request_redis_client()
    logging.info(
        f"Recording food, id={id}, timestamp={timestamp}, deleted={deleted},"
        f"name={name}, carbs={carbs}, comps={comps}, "
        f"record_until={record_until}, remember_recording={remember_recording}"
    )
    ts = str(timestamp.timestamp())
    str_record_until = record_until.timestamp() if record_until is not None else None
    value = json.dumps(
        {
            "id": id,
            "ts": ts,
            "deleted": deleted,
            "name": name,
            "carbs": carbs,
            "comps": comps,
            "record_until": str_record_until,
            "remember_recording": remember_recording,
        }
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
        logging.info("Duplicate food, check if we need to bump revision")
        previous_record = _value_to_food_record(res[0])
        if (
            datetime.fromisoformat(previous_record["timestamp"]) == timestamp
            and previous_record["deleted"] == deleted
            and previous_record["name"] == name
            and previous_record["carbs"] == carbs
            and previous_record["comps"] == comps
            and previous_record["record_until"] == record_until
            and previous_record["remember_recording"] == remember_recording
        ):
            logging.info("Duplicate food")
            should_bump_revision = False
    if should_bump_revision:
        bump_revision(redis_client)
        call_webhooks(
            "food:new",
            {
                "id": id,
                "timestamp": timestamp.isoformat(),
                "deleted": deleted,
                "name": name,
                "carbs": carbs,
                "comps": comps,
                "record_until": record_until.isoformat() if record_until else None,
                "remember_recording": remember_recording,
            },
        )


def _value_to_food_record(member: bytes) -> FoodRecord:
    record = json.loads(member.decode("utf-8"))
    return FoodRecord(
        id=record["id"],
        timestamp=datetime.fromtimestamp(float(record["ts"]), tz=tz).isoformat(),
        deleted=record["deleted"],
        name=record["name"],
        carbs=record["carbs"],
        comps=record["comps"],
        record_until=datetime.fromtimestamp(record["record_until"], tz=tz).isoformat()
        if "record_until" in record and record["record_until"]
        else None,
        remember_recording=record["remember_recording"],
    )


def get_latest_food_records(last_n: int = 288) -> List[FoodRecord]:
    """Gets the latest last_n food records."""
    redis_client = assert_get_current_request_redis_client()
    records = []
    # use zrange to return the last last_n entries ranked by score
    res = redis_client.zrange(_key_set, -last_n, -1)
    for id in res:
        value = redis_client.hget(_key_hash, id)
        assert value
        records.append(_value_to_food_record(value))
    records.reverse()
    return records


class InsertFoodRecordsStatus(TypedDict):
    """The response to a food upload."""

    success: bool
    status: str


def insert_food_records(food_records: List[dict]) -> InsertFoodRecordsStatus:
    """Insert food records at once.

    Args:
        food_records: The food records to insert
    Returns:
        the response
    """
    food_records = sorted(
        food_records, key=lambda record: record["timestamp"], reverse=False
    )
    for record in food_records:
        record_food(
            id=record["id"],
            timestamp=parse_timestamp(record["timestamp"]),
            deleted=record["deleted"],
            name=record["name"],
            carbs=record["carbs"] if "carbs" in record else None,
            comps=record["comps"],
            record_until=parse_timestamp(record["record_until"])
            if "record_until" in record and record["record_until"]
            else None,
            remember_recording=record["remember_recording"],
        )
    return InsertFoodRecordsStatus(
        success=True, status=f"added {len(food_records)} record(s)"
    )
