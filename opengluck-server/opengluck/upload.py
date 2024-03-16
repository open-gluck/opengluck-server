"""A module to handle upload of various items in a transaction.

This is required because we don't want partial upload to trigger episodes changes.
"""
import json
import logging
from datetime import datetime
from multiprocessing import Lock

from flask import Response, abort, request

from .episode import (get_current_episode_record, get_episode_for_mgdl,
                      get_episodes_after_date, insert_episode, insert_episodes,
                      just_updated_episode)
from .food import insert_food_records
from .glucose import (get_current_glucose_record,
                      get_last_just_updated_glucose_at, insert_glucose_records,
                      just_updated_glucose, keep_scan_records_apart_duration,
                      set_current_cgm_device_properties)
from .insulin import insert_insulin_records
from .login import (assert_current_request_logged_in,
                    assert_get_current_request_redis_client)
from .low import insert_low_records
from .redis import get_revision
from .server import app

_lock = Lock()


@app.route("/opengluck/upload", methods=["POST"])
def _upload_data_data():
    redis_client = assert_get_current_request_redis_client()
    with _lock:
        assert_current_request_logged_in()
        body = request.get_json()
        if not body:
            abort(400)
        logging.debug(f"(upload) start with body: {body}")

        current_cgm_device_properties = body.get("current-cgm-device-properties", None)
        device = body.get("device", None)
        glucose_records = body.get("glucose-records", None)
        low_records = body.get("low-records", None)
        food_records = body.get("food-records", None)
        insulin_records = body.get("insulin-records", None)
        episodes = body.get("episodes", None)
        logging.debug(
            "(upload) current_cgm_device_properties: %s",
            json.dumps(current_cgm_device_properties),
        )
        logging.debug("(upload) device: %s", json.dumps(device))
        logging.debug("(upload) glucose_records: %s", json.dumps(glucose_records))
        logging.debug("(upload) episodes: %s", json.dumps(episodes))

        if current_cgm_device_properties is not None:
            set_current_cgm_device_properties(current_cgm_device_properties)

        # archive the current glucose/episode records
        previous_current_glucose_record = get_current_glucose_record()
        previous_current_episode_record = get_current_episode_record()
        logging.debug(
            "(upload) previous_current_episode_record: %s",
            previous_current_episode_record,
        )

        # proceed with upload
        response = dict()
        if glucose_records:
            logging.debug(f"(upload) insert_glucose_records: {glucose_records}")
            response["glucose-records"] = insert_glucose_records(
                glucose_records, device=device
            )
            # check if the current glucose record has changed
            current_glucose_record = get_current_glucose_record()
            last_just_updated_glucose_at = get_last_just_updated_glucose_at()
            last_just_updated_glucose_is_old = (
                last_just_updated_glucose_at is not None
                and current_glucose_record
                and (
                    last_just_updated_glucose_at.timestamp()
                    < datetime.fromisoformat(
                        current_glucose_record["timestamp"]
                    ).timestamp()
                    - keep_scan_records_apart_duration
                )
            )
            if current_glucose_record is not None and (
                previous_current_glucose_record is None
                or previous_current_glucose_record["mgDl"]
                != current_glucose_record["mgDl"]
                or last_just_updated_glucose_is_old
            ):
                if (
                    current_glucose_record is not None
                    and previous_current_glucose_record is not None
                    and datetime.fromisoformat(
                        previous_current_glucose_record["timestamp"]
                    )
                    > datetime.fromisoformat(current_glucose_record["timestamp"])
                ):
                    logging.error(
                        "Found mismatched timestamps for glucose record change, "
                        + "previous=%s, current=%s",
                        previous_current_glucose_record,
                        current_glucose_record,
                    )
                just_updated_glucose(
                    previous=previous_current_glucose_record,
                    current_glucose_record=current_glucose_record,
                )
                # get the current glucose record
                current_glucose_record = get_current_glucose_record()
                if current_glucose_record:
                    episode = episode = get_episode_for_mgdl(
                        current_glucose_record["mgDl"]
                    )
                    logging.debug(
                        "(upload) insert_episode for "
                        + f"mgDl={current_glucose_record['mgDl']}, "
                        + f"episode={episode}, "
                        + f"timestamp={current_glucose_record['timestamp']}"
                    )
                    insert_episode(
                        episode=episode,
                        timestamp=datetime.fromisoformat(
                            current_glucose_record["timestamp"]
                        ),
                        trigger_episode_changes=False,
                    )
        if low_records:
            logging.debug(f"(upload) insert_low_records: {low_records}")
            response["low-records"] = insert_low_records(low_records)
        if insulin_records:
            logging.debug(f"(upload) insert_insulin_records: {insulin_records}")
            response["insulin-records"] = insert_insulin_records(insulin_records)
        if episodes:
            logging.debug(f"(upload) insert_episodes: {episodes}")
            response["episodes"] = insert_episodes(episodes)
        if food_records:
            logging.debug(f"(upload) insert_food_records: {food_records}")
            response["food-records"] = insert_food_records(food_records)

        # For debugging purposes only: log the list of new episodes that were
        # uploaded by this transaction
        new_episodes = get_episodes_after_date(
            after_date=datetime.fromisoformat(
                previous_current_episode_record["timestamp"]
            )
            if previous_current_episode_record
            else datetime(1970, 1, 1)
        )
        logging.debug(f"(upload) found new episodes: {new_episodes}")

        new_current_episode_record = get_current_episode_record()
        if new_current_episode_record != previous_current_episode_record:
            if (
                new_current_episode_record
                and previous_current_episode_record
                and datetime.fromisoformat(new_current_episode_record["timestamp"])
                < datetime.fromisoformat(previous_current_episode_record["timestamp"])
            ):
                logging.debug(
                    "(upload) new_current_episode_record is older than previous; it "
                    + "was replaced by an earlier one in which case we do not "
                    + "want to trigger the webhook"
                )
            elif new_current_episode_record:
                if (
                    previous_current_episode_record
                    and new_current_episode_record["episode"]
                    == previous_current_episode_record["episode"]
                ):
                    logging.debug(
                        "(upload) episode did not change, "
                        + f"skip notify webhook for {new_current_episode_record}"
                    )
                else:
                    logging.debug(
                        "(upload) triggering episode:changed, "
                        + f"new={new_current_episode_record}"
                    )
                    just_updated_episode(
                        previous=previous_current_episode_record,
                        current_episode_record=new_current_episode_record,
                    )

        logging.debug("(upload) done")
        response["revision"] = get_revision(redis_client)
        return Response(json.dumps(response), mimetype="application/json")
