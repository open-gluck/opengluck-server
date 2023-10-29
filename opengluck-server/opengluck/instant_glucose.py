"""A class to read and store instant glucose data."""
import json
import logging
from datetime import datetime
from typing import List, TypedDict

from flask import Response, abort, request
from redis import WatchError

from .config import tz
from .login import assert_current_request_logged_in
from .redis import bump_revision, redis_client
from .server import app
from .utils import parse_timestamp

_key = "instant_glucose"


class InstantGlucoseRecord(TypedDict):
    """An instantglucose record."""

    timestamp: str
    mgDl: int
    model_name: str
    device_id: str


def record_instant_glucose_data(
    timestamp: datetime,
    mgDl: int,
    model_name: str,
    device_id: str,
) -> None:
    """Record a new instant glucose reading."""
    ts = str(timestamp.timestamp())

    # find all records with the same timestamp, and check if they are for the same device
    # if so, update the record, otherwise, add a new record
    # this is to handle the case where the same device is used to record multiple models
    # e.g. a Libre 2 and a Libre 3
    while True:
        try:
            p = redis_client.pipeline()
            p.watch(_key)
            prev_records = redis_client.zrangebyscore(_key, ts, ts)
            for prev_record in prev_records:
                prev_record = _member_to_instant_glucose_record(prev_record)
                if (
                    prev_record["model_name"] == model_name
                    and prev_record["device_id"] == device_id
                ):
                    logging.debug(
                        f"Found existing record for {model_name} {device_id} at {ts}, "
                        + "deleting old"
                    )
                    p.zremrangebyscore(_key, ts, ts)
            logging.info(f"Recording instant glucose data, ts={ts}, mgDl={mgDl}")
            p.unwatch()
            p.zadd(
                _key,
                {
                    json.dumps(
                        {
                            "ts": ts,
                            "mgDl": mgDl,
                            "model_name": model_name,
                            "device_id": device_id,
                        }
                    ): ts
                },
            )
            p.execute()
            break
        except WatchError:
            logging.debug("WatchError, will retry")
            pass


def _member_to_instant_glucose_record(member: bytes) -> InstantGlucoseRecord:
    record = json.loads(member.decode("utf-8"))
    return InstantGlucoseRecord(
        timestamp=datetime.fromtimestamp(float(record["ts"]), tz=tz).isoformat(),
        mgDl=record["mgDl"],
        model_name=record["model_name"],
        device_id=record["device_id"],
    )


def get_latest_instant_glucose_records(
    last_n: int = 24 * 60,
) -> List[InstantGlucoseRecord]:
    """Gets the latest last_n instant glucose record."""
    records = []
    # use zrange to return the last last_n entries ranked by score
    res = redis_client.zrange(_key, -last_n, -1)
    for member in res:
        records.append(_member_to_instant_glucose_record(member))
    records.reverse()
    return records


def find_instant_glucose_records(from_date: datetime, to_date: datetime):
    """Find the instance glucose records in the given time range."""
    from_ts = from_date.timestamp()
    to_ts = to_date.timestamp()
    result = []
    logging.debug(f"Finding instant glucose records between {from_ts} and {to_ts}")
    for member in redis_client.zrangebyscore(_key, from_ts, to_ts):
        result.append(_member_to_instant_glucose_record(member))
    logging.debug(f"Found {len(result)} record(s)")
    return result


class InsertInstantGlucoseRecordsStatus(TypedDict):
    """The response to a glucoses upload."""

    success: bool
    status: str


def insert_instant_glucose_records(
    instant_glucose_records: List[dict],
) -> InsertInstantGlucoseRecordsStatus:
    """Insert instant glucose records at once.

    Args:
        instant_glucose_records: the instant glucose records to insert
    Returns:
        the response
    """
    instant_glucose_records = sorted(
        instant_glucose_records, key=lambda record: record["timestamp"], reverse=False
    )
    for record in instant_glucose_records:
        record_instant_glucose_data(
            parse_timestamp(record["timestamp"]),
            record["mgDl"],
            record["model_name"],
            record["device_id"],
        )
    return InsertInstantGlucoseRecordsStatus(
        success=True, status=f"added {len(instant_glucose_records)} record(s)"
    )


@app.route("/opengluck/instant-glucose", methods=["DELETE"])
def _clear_all_instant_glucose_records():
    """Delete all instant glucose records."""
    assert_current_request_logged_in()
    redis_client.delete(_key)
    bump_revision()
    return Response(status=204)


@app.route("/opengluck/instant-glucose/last")
def _get_latest_instant_glucose_data():
    assert_current_request_logged_in()
    last_n = int(request.args.get("last_n", "288"))
    records = get_latest_instant_glucose_records(last_n=last_n)
    return Response(json.dumps(records), content_type="application/json")


@app.route("/opengluck/instant-glucose/upload", methods=["GET", "POST"])
def _upload_instant_glucose_data():
    # decode the POST payload as an array of glucose records
    logging.info("Uploading instant glucose data")
    assert_current_request_logged_in()
    body = request.get_json()
    records = body.get("instant-glucose-records", [])
    status = insert_instant_glucose_records(records)
    return Response(
        json.dumps({"success": True, "status": status["status"]}),
        content_type="application/json",
    )


@app.route("/opengluck/instant-glucose/download")
def _download_instant_glucose_data():
    assert_current_request_logged_in()
    last_n = int(request.args.get("last_n", "288"))
    rows = []
    records = get_latest_instant_glucose_records(last_n=last_n)
    if not records:
        logging.info("No instant glucose records found, not augmenting")
    else:
        for record in records:
            rows.append(
                f"{record['timestamp']},{record['model_name']},"
                + f"{record['device_id']},{record['mgDl']},"
            )
        min_timestamp: datetime = min(
            [parse_timestamp(record["timestamp"]) for record in records]
        )
        max_timestamp: datetime = max(
            [parse_timestamp(record["timestamp"]) for record in records]
        )
        # remove 5m from min_timestamp and add 5m to max_timestamp
        min_timestamp = datetime.fromtimestamp(min_timestamp.timestamp() - 300, tz=tz)
        max_timestamp = datetime.fromtimestamp(max_timestamp.timestamp() + 300, tz=tz)
        logging.info(
            f"Augmenting with glucose records between {min_timestamp} "
            + f"and {max_timestamp}"
        )
        from .glucose import GlucoseRecordType, find_glucose_records

        historic_records = find_glucose_records(
            GlucoseRecordType.historic, min_timestamp, max_timestamp
        )
        for historic_record in historic_records:
            rows.append(f"{historic_record['timestamp']},,,,{historic_record['mgDl']},")

    rows.sort(key=lambda row: row.split(",")[0])
    rows = ["timestamp,model_name,device_id,instant,historic"] + rows
    return Response("\n".join(rows), content_type="text/csv; charset=utf-8")


@app.route("/opengluck/instant-glucose/find")
def _find_instant_glucose_data():
    assert_current_request_logged_in()
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    if from_date is None or to_date is None:
        return abort(400)
    records = find_instant_glucose_records(
        parse_timestamp(from_date), parse_timestamp(to_date)
    )
    return Response(json.dumps(records), content_type="application/json")
