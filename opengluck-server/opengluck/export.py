import json
from datetime import datetime
from enum import Enum
from typing import List

from flask import Response, request

from .glucose import GlucoseRecord, GlucoseRecordType, find_glucose_records
from .insulin import InsulinRecord, find_insulin_records
from .login import assert_current_request_logged_in
from .server import app


class _ExportType(str, Enum):
    json = "json"
    swift = "swift"


def _export_swift(
    *,
    glucose_records: List[GlucoseRecord],
    insulin_records: List[InsulinRecord],
    to_date: datetime,
) -> Response:
    # result is a text that looks like:
    #      static let sample = CarbsSample(
    #        id: "sample",
    #        name: "Sample",
    #        expectedUnits: 0,
    #        expectedCarbsInGrams: nil,
    #        foodTimestamp: iso2date("2022-12-23T13:25:00+01:00"),
    #        data: Data(records: [
    #          InsulinRecord(timestamp: iso2date("2022-12-22T12:17:00+01:00"), units: 1),
    #        ]),
    #        glucoseData: GlucoseData(records: [
    #            GlucoseRecord(timestamp: iso2date("2022-12-22T13:20:00+01:00"), mgDl: 165),
    #        ]),
    #     ])
    result = f"""static let sample = CarbsSample(
    id: "sample",
    name: "Sample",
    expectedUnits: 0,
    expectedCarbsInGrams: nil,
    foodTimestamp: iso2date("{to_date.isoformat(timespec='seconds')}"),
    data: Data(records: ["""
    for insulin_record in insulin_records:
        timestamp = datetime.fromisoformat(insulin_record["timestamp"]).isoformat(
            timespec="seconds"
        )
        units = insulin_record["units"]
        result += f"""
        InsulinRecord(timestamp: iso2date("{timestamp}"), units: {units}),"""
    result += """
    ]),
    glucoseData: GlucoseData(records: ["""
    for glucose_record in glucose_records:
        timestamp = datetime.fromisoformat(glucose_record["timestamp"]).isoformat(
            timespec="seconds"
        )
        mg_dl = glucose_record["mgDl"]
        result += f"""
        GlucoseRecord(timestamp: iso2date("{timestamp}"), mgDl: {mg_dl}),"""
    result += """
    ])
)
    """
    return Response(result, mimetype="text/plain")


def _export_json(
    *, glucose_records: List[GlucoseRecord], insulin_records: List[InsulinRecord]
) -> Response:
    return Response(
        json.dumps(
            {
                "glucose": glucose_records,
                "insulin": insulin_records,
            }
        ),
        mimetype="application/json",
    )


@app.route("/opengluck/export", methods=["POST"])
def _export_route():
    assert_current_request_logged_in()

    assert request.json
    from_date = datetime.fromisoformat(request.json.get("from", ""))
    to_date = datetime.fromisoformat(request.json.get("to", ""))
    type = request.json.get("type", "")

    glucose_records = find_glucose_records(
        from_date=from_date, to_date=to_date, record_type=GlucoseRecordType.historic
    )

    insulin_records = find_insulin_records(from_date=from_date, to_date=to_date)

    if type == _ExportType.swift:
        return _export_swift(
            glucose_records=glucose_records,
            insulin_records=insulin_records,
            to_date=to_date,
        )
    elif type == _ExportType.json:
        return _export_json(
            glucose_records=glucose_records, insulin_records=insulin_records
        )
    else:
        return Response(status=400, response="Invalid export type")
