import json
import logging

from flask import Response, request

from .cgm import do_we_have_realtime_cgm_data
from .episode import get_current_episode_record
from .glucose import (GlucoseRecordType, get_latest_glucose_records,
                      get_merged_glucose_records)
from .login import assert_get_current_request_redis_client
from .redis import get_revision
from .server import app
from .utils import parse_timestamp


@app.route("/opengluck/glucose/current")
def _get_current_glucose_data():
    # TODO LEGACY this is a legacy route and should be removed
    return _handle_get_current(
        current_glucose_record_field_name="current",
        last_historic_field_name="last_historic",
    )


@app.route("/opengluck/current")
def _get_current_data():
    return _handle_get_current(
        current_glucose_record_field_name="current_glucose_record",
        last_historic_field_name="last_historic_glucose_record",
    )


def _handle_get_current(
    *, current_glucose_record_field_name: str, last_historic_field_name: str
):
    redis_client = assert_get_current_request_redis_client()

    revision = get_revision(redis_client)
    if_none_match = request.headers.get("if-none-match")
    if if_none_match is not None and if_none_match == str(revision):
        logging.debug("Sending 304")
        return Response(status=304)

    has_cgm_real_time_data = do_we_have_realtime_cgm_data()

    records = get_merged_glucose_records()
    records = records[:2]
    historic_records = get_latest_glucose_records(GlucoseRecordType.historic, last_n=2)

    if len(records) > 0:
        last_historic = historic_records[0] if len(historic_records) > 0 else None
        if last_historic is not None and parse_timestamp(
            last_historic["timestamp"]
        ) == parse_timestamp(records[0]["timestamp"]):
            last_historic = historic_records[1] if len(historic_records) > 1 else None

        current_episode_record = get_current_episode_record()
        return Response(
            json.dumps(
                {
                    current_glucose_record_field_name: records[0],
                    last_historic_field_name: last_historic,
                    "current_episode": current_episode_record["episode"]
                    if current_episode_record is not None
                    else None,
                    "current_episode_timestamp": current_episode_record["timestamp"]
                    if current_episode_record is not None
                    else None,
                    "has_cgm_real_time_data": has_cgm_real_time_data,
                    "revision": revision,
                }
            ),
            headers={"content-type": "application/json", "etag": revision},
        )
    else:
        return Response(
            json.dumps(
                {
                    current_glucose_record_field_name: None,
                    last_historic_field_name: None,
                    "current_episode": None,
                    "current_episode_timestamp": None,
                    "has_cgm_real_time_data": has_cgm_real_time_data,
                    "revision": revision,
                }
            ),
            headers={"content-type": "application/json"},
        )
