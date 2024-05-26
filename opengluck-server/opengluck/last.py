import json
import logging
import time
from typing import List

from flask import Response, request

from opengluck.instant_glucose import (InstantGlucoseRecord,
                                       get_latest_instant_glucose_records)

from .food import FoodRecord, get_latest_food_records
from .glucose import (GlucoseRecord, GlucoseRecordType,
                      get_latest_glucose_records, get_merged_glucose_records)
from .insulin import InsulinRecord, get_latest_insulin_records
from .login import (assert_current_request_logged_in,
                    assert_get_current_request_redis_client)
from .low import LowRecord, get_latest_low_records
from .redis import get_revision
from .server import app
from .utils import parse_timestamp


def _get_latest_glucose_records(
    *, record_type: str, last_n: int, max_duration: int
) -> List[GlucoseRecord]:
    if record_type:
        records = get_latest_glucose_records(
            GlucoseRecordType(record_type), last_n=last_n
        )
    else:
        records = get_merged_glucose_records(last_n_historic=last_n, last_n_scan=last_n)
    min_timestamp = time.time() - max_duration
    records = [
        record
        for record in records
        if parse_timestamp(record["timestamp"]).timestamp() > min_timestamp
    ]
    return records


def _get_food_records(max_duration: int) -> List[FoodRecord]:
    min_timestamp = time.time() - max_duration
    records = get_latest_food_records()
    records = [
        record
        for record in records
        if parse_timestamp(record["timestamp"]).timestamp() > min_timestamp
    ]
    return records


def _get_low_records(max_duration: int) -> List[LowRecord]:
    min_timestamp = time.time() - max_duration
    records = get_latest_low_records()
    records = [
        record
        for record in records
        if parse_timestamp(record["timestamp"]).timestamp() > min_timestamp
    ]
    return records


def _get_insulin_records(max_duration: int) -> List[InsulinRecord]:
    min_timestamp = time.time() - max_duration
    records = get_latest_insulin_records()
    records = [
        record
        for record in records
        if parse_timestamp(record["timestamp"]).timestamp() > min_timestamp
    ]
    return records


def _get_instant_glucose_records(max_duration: int) -> List[InstantGlucoseRecord]:
    min_timestamp = time.time() - max_duration
    records = get_latest_instant_glucose_records(last_n=5)
    records = [
        record
        for record in records
        if parse_timestamp(record["timestamp"]).timestamp() > min_timestamp
    ]
    return records


@app.route("/opengluck/glucose/last")
def _get_glucose_last_route():
    # TODO LEGACY this is a legacy route and should be removed
    assert_current_request_logged_in()
    record_type = request.args.get("type", "")
    last_n = int(request.args.get("last_n", "288"))
    max_duration = int(request.args.get("max_duration", 7 * 60 * 60))
    records = _get_latest_glucose_records(
        record_type=record_type, last_n=last_n, max_duration=max_duration
    )
    return Response(json.dumps(records))


def get_last(
    *, record_type: str = "", last_n_glucose: int = 288, max_duration: int = 7 * 60 * 60
):
    """Returns the last records."""
    glucose_records = _get_latest_glucose_records(
        record_type=record_type, last_n=last_n_glucose, max_duration=max_duration
    )
    low_records = _get_low_records(max_duration=max_duration)
    food_records = _get_food_records(max_duration=max_duration)
    insulin_records = _get_insulin_records(max_duration=max_duration)
    instant_glucose_records = _get_instant_glucose_records(max_duration=max_duration)
    return {
        "glucose-records": glucose_records,
        "low-records": low_records,
        "insulin-records": insulin_records,
        "food-records": food_records,
        "instant-glucose-records": instant_glucose_records,
    }


@app.route("/opengluck/last")
def _get_last_route():
    redis_client = assert_get_current_request_redis_client()

    revision = get_revision(redis_client)
    if_none_match = request.headers.get("if-none-match")
    if if_none_match is not None and if_none_match == str(revision):
        logging.debug("Sending 304")
        return Response(status=304)

    record_type = request.args.get("type", "")
    last_n_glucose = int(request.args.get("last_n_glucose", "288"))
    max_duration = int(request.args.get("max_duration", 7 * 60 * 60))
    last = get_last(
        record_type=record_type,
        last_n_glucose=last_n_glucose,
        max_duration=max_duration,
    )
    return Response(
        json.dumps(
            {
                "revision": revision,
                **last,
            }
        ),
        headers={"content-type": "application/json", "etag": revision},
    )
