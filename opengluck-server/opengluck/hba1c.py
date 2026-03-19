"""A class to retrieve HbA1c values."""
import json
import math
from datetime import timedelta
from typing import List, Optional, TypedDict

from flask import Response, abort, request

from opengluck.glucose import (GlucoseRecord, GlucoseRecordType,
                               find_glucose_records)

from .server import app
from .utils import parse_timestamp

_smoothe_glucose_for_at_most_seconds = 60 * 60


class HbA1cStats(TypedDict):
    """The calculated HbA1c statistics."""

    hba1c: float
    avg_mgdl: float
    cv: float


class HbA1cResult(TypedDict):
    """The HbA1c result."""

    from_date: str
    to_date: str
    hba1c: Optional[float]
    avg_mgdl: Optional[float]
    cv: Optional[float]


def _calculate_hba1c(glucose_records: List[GlucoseRecord]) -> Optional[HbA1cStats]:
    """Calculate the HbA1c value, average mg/dL, and coefficient of variation."""
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
    avg_mgdl = sum(values) / len(values)
    hba1c = (avg_mgdl + 46.7) / 28.7
    std_dev = math.sqrt(sum((v - avg_mgdl) ** 2 for v in values) / len(values))
    cv = (std_dev / avg_mgdl) * 100 if avg_mgdl != 0 else 0
    return HbA1cStats(hba1c=hba1c, avg_mgdl=avg_mgdl, cv=cv)


@app.route("/opengluck/hba1c", methods=["POST"])
def _record_hba1c():
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    if from_date is None or to_date is None:
        return abort(400)
    from_ts = parse_timestamp(from_date)
    to_ts = parse_timestamp(to_date)

    glucose_records = find_glucose_records(GlucoseRecordType.historic, from_ts, to_ts)
    stats = _calculate_hba1c(glucose_records)

    return Response(
        json.dumps(
            HbA1cResult(
                from_date=from_ts.isoformat(),
                to_date=to_ts.isoformat(),
                hba1c=stats["hba1c"] if stats else None,
                avg_mgdl=stats["avg_mgdl"] if stats else None,
                cv=stats["cv"] if stats else None,
            )
        ),
        status=200,
    )
