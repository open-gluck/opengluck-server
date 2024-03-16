"""A class to retrieve HbA1c values."""
import json
from datetime import timedelta
from typing import List, Optional, TypedDict

from flask import Response, abort, request

from opengluck.glucose import (GlucoseRecord, GlucoseRecordType,
                               find_glucose_records)

from .server import app
from .utils import parse_timestamp

_smoothe_glucose_for_at_most_seconds = 60 * 60


class HbA1cResult(TypedDict):
    """The HbA1c result."""

    from_date: str
    to_date: str
    hba1c: Optional[float]


def _calculate_hba1c(glucose_records: List[GlucoseRecord]) -> Optional[float]:
    """Calculate the HbA1c value."""
    if len(glucose_records) == 0:
        return None
    # sort the records by timestamp
    glucose_records = sorted(glucose_records, key=lambda r: r["timestamp"])
    values: List[float] = []
    last_record = glucose_records.pop(0)
    values.append(last_record["mgDl"])
    for record in glucose_records:
        record_ts = parse_timestamp(record["timestamp"])
        elapsed = record_ts - parse_timestamp(last_record["timestamp"])
        delta_seconds = elapsed.total_seconds()
        if delta_seconds > _smoothe_glucose_for_at_most_seconds:
            values.append(record["mgDl"])
            continue
        delta_mgDl = record["mgDl"] - last_record["mgDl"]
        current_ts = parse_timestamp(last_record["timestamp"]) + timedelta(minutes=1)
        i = 1
        while current_ts <= record_ts:
            current_mgdl = last_record["mgDl"] + delta_mgDl * i / (delta_seconds / 60)
            values.append(current_mgdl)
            current_ts += timedelta(minutes=1)
            i += 1

        last_record = record
    print(values)
    avg_mgdl = sum(values) / len(values)
    return (avg_mgdl + 46.7) / 28.7


@app.route("/opengluck/hba1c", methods=["POST"])
def _record_hba1c():
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    if from_date is None or to_date is None:
        return abort(400)
    from_ts = parse_timestamp(from_date)
    to_ts = parse_timestamp(to_date)

    glucose_records = find_glucose_records(GlucoseRecordType.historic, from_ts, to_ts)
    hbA1c = _calculate_hba1c(glucose_records)

    return Response(
        json.dumps(
            HbA1cResult(
                from_date=from_ts.isoformat(), to_date=to_ts.isoformat(), hba1c=hbA1c
            )
        ),
        status=200,
    )
