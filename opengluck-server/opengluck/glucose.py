"""A class to read and store glucose data."""
import json
import logging
import time
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import List, Optional, TypedDict

from flask import Response, abort, request

from .cgm import (
    do_we_have_realtime_cgm_data,
    get_current_cgm_properties,
    set_current_cgm_device_properties,
)
from .config import merge_record_high_threshold, merge_record_low_threshold, tz
from .instant_glucose import record_instant_glucose_data
from .login import assert_current_request_logged_in
from .redis import bump_revision, redis_client
from .server import app
from .utils import parse_timestamp
from .webhooks import call_webhooks

# We keep track of the last used scan, so that we don't backtrack in time when
# historic records shifts and we no longer have matching scan records
_key_last_used_scan = "last_used_scan"
_merged_glucose_records_lock = Lock()
_keep_scan_records_apart_duration = 4 * 60 + 50


class GlucoseRecordType(str, Enum):
    """The type of glucose record."""

    historic = "historic"
    scan = "scan"


class GlucoseRecord(TypedDict):
    """A glucose record."""

    timestamp: str
    mgDl: int
    record_type: GlucoseRecordType


def record_glucose_data(
    record_type: GlucoseRecordType,
    timestamp: datetime,
    mgDl: int,
    trigger_episode_changes: bool = True,
) -> None:
    """Record a new glucose reading."""
    # LATER DEPRECATED setting trigger_episode_changes to True is deprecated
    key = _key(record_type)
    ts = str(timestamp.timestamp())
    logging.info(f"Recording glucose data, key={key}, ts={ts}, mgDl={mgDl}")
    res = (
        redis_client.pipeline()
        .zrangebyscore(key, ts, ts)
        .zremrangebyscore(key, ts, ts)
        .zadd(key, {json.dumps({"ts": ts, "mgDl": mgDl}): ts})
        .execute()
    )
    should_bump_revision: bool = True
    if res[0]:
        previous_record_at_timestamp = json.loads(res[0][0].decode("utf-8"))
        if (
            "mgDl" in previous_record_at_timestamp
            and previous_record_at_timestamp["mgDl"] == mgDl
        ):
            logging.info("Duplicate glucose record, not bumping revision")
            should_bump_revision = False
    if should_bump_revision:
        bump_revision()
        call_webhooks(
            f"glucose:new:{record_type.value}",
            {"timestamp": timestamp.isoformat(), "mgDl": mgDl},
        )
    from .episode import get_episode_for_mgdl, insert_episode

    if trigger_episode_changes:
        episode = episode = get_episode_for_mgdl(mgDl)
        logging.debug(
            f"insert_episode for mgDl={mgDl}, episode={episode}, timestamp={timestamp}"
        )
        insert_episode(episode=episode, timestamp=timestamp)


def _member_to_glucose_record(
    record_type: GlucoseRecordType, member: bytes
) -> GlucoseRecord:
    record = json.loads(member.decode("utf-8"))
    return GlucoseRecord(
        timestamp=datetime.fromtimestamp(float(record["ts"]), tz=tz).isoformat(),
        mgDl=record["mgDl"],
        record_type=record_type,
    )


def _key(record_type: GlucoseRecordType) -> str:
    return f"glucose:{record_type.value}"


def get_latest_glucose_records(
    record_type: GlucoseRecordType, last_n: int = 288
) -> List[GlucoseRecord]:
    """Gets the latest last_n records of a given type."""
    records = []
    key = _key(record_type)
    # use zrange to return the last last_n entries ranked by score
    res = redis_client.zrange(key, -last_n, -1)
    for member in res:
        records.append(_member_to_glucose_record(record_type, member))
    records.reverse()
    return records


def get_merged_glucose_records(
    last_n_historic: int = 288, last_n_scan: int = 288
) -> List[GlucoseRecord]:
    """Gets last historic records, and all more recent scan records.

    This is a wrapper around the implementation, with a mutex to make sure that
    we won't run this concurrently.
    """
    with _merged_glucose_records_lock:
        return _get_merged_glucose_records_impl(
            last_n_historic=last_n_historic, last_n_scan=last_n_scan
        )


def _get_merged_glucose_records_impl(
    last_n_historic: int = 288, last_n_scan: int = 288
) -> List[GlucoseRecord]:
    """Gets last historic records, and all more recent scan records."""
    records_historic = get_latest_glucose_records(
        GlucoseRecordType.historic, last_n=last_n_historic
    )
    if len(records_historic) == 0:
        # no historic records, return all scan records
        return get_latest_glucose_records(
            GlucoseRecordType.scan, last_n=last_n_historic
        )
    last_historic_ts = datetime.fromisoformat(
        records_historic[0]["timestamp"]
    ).timestamp()
    last_used_scan = datetime.fromisoformat(
        (redis_client.get(_key_last_used_scan) or b"1970-01-01T00:00:00Z").decode()
    )
    logging.debug("last_used_scan=%s", last_used_scan)
    last_used_scan_ts = last_used_scan.timestamp()

    res = redis_client.zrangebyscore(
        _key(GlucoseRecordType.scan), f"({last_historic_ts}", "+inf"
    )
    records_scan = []
    for member in res:
        records_scan.append(_member_to_glucose_record(GlucoseRecordType.scan, member))

    # keep the last scan record, we'll check if it crosses with the current
    # last, and add it back if it does
    last_scan_record: Optional[GlucoseRecord] = None
    if len(records_scan) > 0:
        last_scan_record = records_scan[-1]
    logging.debug(f"last_scan_record={last_scan_record}")

    has_cgm_realtime_data = do_we_have_realtime_cgm_data()
    logging.debug(f"has_cgm_realtime_data={has_cgm_realtime_data}")

    # keep only records around 4 minutes 50 seconds apart the last historic
    # record
    if not has_cgm_realtime_data:
        logging.info("No realtime CGM data, keeping all scan records")
        records_scan_filtered = []
    else:
        # keep all records that are at least 5 minutes apart from the last,
        # plus also the last scan record the we used
        base_ts = last_historic_ts
        records_scan_filtered = []
        for record in records_scan:
            cur_ts = datetime.fromisoformat(record["timestamp"]).timestamp()
            if (
                cur_ts - base_ts >= _keep_scan_records_apart_duration
                or cur_ts == last_used_scan_ts
            ):
                records_scan_filtered.append(record)
                base_ts = cur_ts
    if len(records_scan_filtered) > 0:
        records_scan = records_scan_filtered
    # elif len(records_scan) > 0:
    #    # no records around 5 minutes apart, keep the last one
    #    records_scan.reverse()
    #    records_scan = [records_scan[0]]
    records_scan.reverse()

    results = records_scan + records_historic

    if len(results) > 0 and last_scan_record is not None:
        # we do have some records, and we also have a scan record
        last_returned_record = results[0]
        logging.debug(f"last_returned_record={last_returned_record}")
        if datetime.fromisoformat(
            last_scan_record["timestamp"]
        ) != datetime.fromisoformat(last_returned_record["timestamp"]):
            # we have an additional scan record
            # check if maybe these records cross with any user configuration
            crosses = False
            if last_scan_record["mgDl"] < merge_record_low_threshold:
                crosses = True
            elif (
                last_scan_record["mgDl"] >= merge_record_high_threshold
                and last_returned_record["mgDl"] < merge_record_high_threshold
            ):
                # note: we only consider a record to be “crossing high" when it
                # reachs a threshold above the limit under some circonstances,
                # the next scan might be lower than the limit, hence not
                # pushing the result, until it is naturaly pushed by the next
                # valid scan -- this might delay the notification that we're no
                # longer high by a few minutes, but that's okay
                crosses = True
            logging.debug(
                f"last_scan_mgdl={last_scan_record['mgDl']} "
                + f"last_returned_mgdl={last_returned_record['mgDl']} crosses={crosses}"
            )
            if crosses:
                results.insert(0, last_scan_record)

    # update the value of the last scan record
    new_scans = [record for record in results if record["record_type"] == "scan"]
    if new_scans and new_scans[0]:
        new_last_used_scan = new_scans[0]["timestamp"]
        if datetime.fromisoformat(new_last_used_scan) > last_used_scan:
            redis_client.set(_key_last_used_scan, new_last_used_scan)

    return results


def get_current_glucose_record() -> Optional[GlucoseRecord]:
    """Gets the current glucose record."""
    records = get_merged_glucose_records()
    if len(records) == 0:
        return None
    return records[0]


class InsertGlucoseRecordsStatus(TypedDict):
    """The response to a glucoses upload."""

    success: bool
    status: str


def insert_glucose_records(
    glucose_records: List[dict], *, device: Optional[dict]
) -> InsertGlucoseRecordsStatus:
    """Insert glucose records at once.

    Args:
        glucose_records: the glucose records to insert
        device: the current device
    Returns:
        the response
    """
    glucose_records = sorted(
        glucose_records, key=lambda record: record["timestamp"], reverse=False
    )
    for record in glucose_records:
        if _get_record_type(record) != "historic":
            continue
        record_glucose_data(
            GlucoseRecordType.historic,
            parse_timestamp(record["timestamp"]),
            record["mgDl"],
            trigger_episode_changes=False,
        )
    if device is not None:
        model_name = device["model_name"]
        device_id = device["device_id"]
    else:
        model_name = "Unknown"
        device_id = "00000000-0000-0000-0000-000000000000"
    for record in glucose_records:
        if _get_record_type(record) != "scan":
            continue
        record_glucose_data(
            GlucoseRecordType.scan,
            parse_timestamp(record["timestamp"]),
            record["mgDl"],
            trigger_episode_changes=False,
        )
        record_instant_glucose_data(
            parse_timestamp(record["timestamp"]),
            record["mgDl"],
            model_name=record.get("model_name", model_name),
            device_id=record.get("device_id", device_id),
        )
    return InsertGlucoseRecordsStatus(
        success=True, status=f"added {len(glucose_records)} record(s)"
    )


def just_updated_glucose(
    *, previous: Optional[GlucoseRecord], current_glucose_record: GlucoseRecord
) -> None:
    """Notifies that glucose records have been updated.

    This is used to run the glucose:changed webhook, providing both previous
    and current records.
    """
    call_webhooks(
        "glucose:changed",
        {
            "previous": previous,
            "new": current_glucose_record,
            "cgm-properties": get_current_cgm_properties(),
        },
    )


@app.route("/opengluck/glucose", methods=["DELETE"])
def _clear_all_glucose_records():
    """Delete all glucose records."""
    assert_current_request_logged_in()
    redis_client.delete(_key(GlucoseRecordType.historic))
    redis_client.delete(_key(GlucoseRecordType.scan))
    redis_client.delete(_key_last_used_scan)
    bump_revision()
    return Response(status=204)


@app.route("/opengluck/glucose/last")
def _get_latest_glucose_data():
    assert_current_request_logged_in()
    record_type = request.args.get("type", "")
    last_n = int(request.args.get("last_n", "288"))
    max_duration = int(request.args.get("max_duration", 7 * 60 * 60))
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
    return Response(json.dumps(records))


def _get_record_type(record: dict) -> str:
    if "type" in record:
        return record["type"]
    else:
        return record["record_type"]


@app.route("/opengluck/glucose/upload", methods=["GET", "POST"])
def _upload_glucose_data():
    # decode the POST payload as an array of glucose records
    # LATER DEPRECATED this route is deprecated
    print("Uploading glucose data")
    assert_current_request_logged_in()
    body = request.get_json()
    current_cgm_device_properties = None
    if isinstance(body, dict):
        records = body.get("records", [])
        if "current-cgm-device-properties" in body:
            current_cgm_device_properties = body["current-cgm-device-properties"]
    else:
        records = body

    if not isinstance(records, list):
        return abort(400)
    records = sorted(records, key=lambda record: record["timestamp"], reverse=False)

    if current_cgm_device_properties is not None:
        set_current_cgm_device_properties(current_cgm_device_properties)

    previous_current_glucose_record = get_current_glucose_record()

    for record in records:
        if _get_record_type(record) != "historic":
            continue
        record_glucose_data(
            GlucoseRecordType.historic,
            parse_timestamp(record["timestamp"]),
            record["mgDl"],
        )
    for record in records:
        if _get_record_type(record) != "scan":
            continue
        record_glucose_data(
            GlucoseRecordType.scan,
            parse_timestamp(record["timestamp"]),
            record["mgDl"],
        )
    current_glucose_record = get_current_glucose_record()
    assert current_glucose_record is not None
    if (
        previous_current_glucose_record is None
        or previous_current_glucose_record["mgDl"] != current_glucose_record["mgDl"]
    ):
        just_updated_glucose(
            previous=previous_current_glucose_record,
            current_glucose_record=current_glucose_record,
        )
    return Response(
        json.dumps({"success": True, "status": f"added {len(records)} record(s)"})
    )


def find_glucose_records(
    record_type: GlucoseRecordType, from_date: datetime, to_date: datetime
) -> List[GlucoseRecord]:
    """Find glucose records in the given time range."""
    from_ts = from_date.timestamp()
    to_ts = to_date.timestamp()
    key = _key(record_type)
    from_ts = from_date.timestamp()
    to_ts = to_date.timestamp()
    result = []
    logging.debug(f"Finding records for key {key} between {from_ts} and {to_ts}")
    for member in redis_client.zrangebyscore(key, from_ts, to_ts):
        result.append(_member_to_glucose_record(record_type, member))
    logging.debug(f"Found {len(result)} record(s)")
    return result


@app.route("/opengluck/glucose/find")
def _find_glucose_records():
    assert_current_request_logged_in()
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    if from_date is None or to_date is None:
        return abort(400)
    record_type = GlucoseRecordType(request.args.get("type", "historic"))
    records = find_glucose_records(
        record_type, parse_timestamp(from_date), parse_timestamp(to_date)
    )
    return Response(json.dumps(records), content_type="application/json")
