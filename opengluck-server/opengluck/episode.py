"""A module to store change of episodes.

An episode can be reported either:
    - when using a real-time CGM, when a new glucose is uploaded, the episode
      is adjusted accordingly if needed
    - when using a non real-time CGM that does supports episode reporting, the
      episode can be adjusted using a POST API call
"""
import json
import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional, TypedDict, cast

from flask import Response, abort, request
from redis import WatchError

from .cgm import get_current_cgm_properties, set_current_cgm_device_properties
from .config import merge_record_high_threshold, merge_record_low_threshold, tz
from .login import (assert_current_request_logged_in,
                    assert_get_current_request_redis_client)
from .redis import bump_revision
from .server import app
from .webhooks import call_webhooks


class Episode(str, Enum):
    """An episode."""

    unknown = "unknown"
    disconnected = "disconnected"
    error = "error"
    low = "low"
    normal = "normal"
    high = "high"


class EpisodeRecord(TypedDict):
    """An episode record."""

    timestamp: str
    episode: Episode


_key = "episode"


def _member_to_episode_record(member: bytes) -> EpisodeRecord:
    """Convert a member to an episode record."""
    record = json.loads(member.decode("utf-8"))
    return EpisodeRecord(
        timestamp=datetime.fromtimestamp(float(record["ts"]), tz=tz).isoformat(),
        episode=record["episode"],
    )


def get_episodes_after_date(*, after_date: datetime) -> List[EpisodeRecord]:
    """Get the episodes after a given date.

    Args:
        after_date: the date after which to start
    Returns:
        the list of episodes
    """
    redis_client = assert_get_current_request_redis_client()
    ts = int(after_date.timestamp())
    res = redis_client.zrangebyscore(_key, "(" + str(ts), "+inf")
    logging.debug(f"get_episodes_after_date ts={ts}")
    episodes: List[EpisodeRecord] = []
    for member in res:
        episode = _member_to_episode_record(member)
        logging.debug(f" -> episode: {episode}")
        at_ts = datetime.fromisoformat(episode["timestamp"]).timestamp()
        # double check the timestamp is after the date, for some reasons it
        # appears sometimes the record at after_date is still being returned
        # TOOD find why
        if at_ts <= ts:
            logging.debug(" -> skipping at_ts <= ts: {at_ts} <= {ts}")
        else:
            episodes.append(episode)
    return episodes


def get_last_episodes(
    *, last_n: int = 20, until_date: Optional[datetime] = None
) -> List[EpisodeRecord]:
    """Get the latest episodes.

    Args:
        last_n: the number of episodes to retrieve
        until_date: the date until which to retrieve episodes
    """
    redis_client = assert_get_current_request_redis_client()
    if until_date is None:
        res = redis_client.zrevrange(_key, 0, last_n - 1)
    else:
        until_ts = int(until_date.timestamp())
        res = redis_client.zrevrangebyscore(_key, until_ts, 0, start=0, num=last_n)
    episodes: List[EpisodeRecord] = []
    for member in res:
        episodes.append(_member_to_episode_record(member))
    return episodes


def get_current_episode_record(
    until_date: Optional[datetime] = None,
) -> Optional[EpisodeRecord]:
    """Get the current episode."""
    latest_episodes = get_last_episodes(until_date=until_date, last_n=1)
    if not latest_episodes:
        return None
    return latest_episodes[0]


def get_current_episode(until_date: Optional[datetime]) -> Episode:
    """Get the current episode."""
    latest_episodes = get_last_episodes(last_n=1, until_date=until_date)
    if not latest_episodes:
        return Episode.unknown
    return latest_episodes[0]["episode"]


def just_updated_episode(
    *, previous: Optional[EpisodeRecord], current_episode_record: EpisodeRecord
) -> None:
    """Notifies that episode records have been updated.

    This is used to run the episode:changed webhook, providing both previous
    and current records.
    """
    if previous and current_episode_record:
        assert previous["episode"] != current_episode_record["episode"]

    call_webhooks(
        "episode:changed",
        {
            "previous": previous,
            "new": current_episode_record,
            "cgm-properties": get_current_cgm_properties(),
        },
    )


class InsertEpisodeStatus(str, Enum):
    """The status of inserting an episode."""

    inserted = "inserted"
    replaced = "replaced"
    duplicate = "duplicate"


def insert_episode(
    *, episode: Episode, timestamp: datetime, trigger_episode_changes: bool = True
) -> InsertEpisodeStatus:
    """Insert an episode."""
    redis_client = assert_get_current_request_redis_client()
    # LATER DEPRECATED setting trigger_episode_changes to True is deprecated
    timestamp = datetime.fromtimestamp(timestamp.timestamp(), tz=tz)
    ts = str(timestamp.timestamp())
    previous_episode_record = None
    previous_current_episode_record = get_current_episode_record()
    while True:
        try:
            p = redis_client.pipeline()
            p.watch(_key)
            previous_episode_record = get_current_episode_record(until_date=timestamp)
            logging.debug(f"Current episode record: {previous_episode_record}")
            previous_episode = (
                previous_episode_record["episode"]
                if previous_episode_record
                else Episode.unknown
            )
            logging.debug(
                f"Will try insert episode {episode} at timestamp {timestamp}, ts {ts}, "
                + f"current episode: {previous_episode}"
            )
            if previous_episode == episode:
                logging.debug(" -> duplicate")
                status = InsertEpisodeStatus.duplicate
            else:
                # is the same episode happening just later? if so, we need to
                # delete the later episode, and correctly record that it
                # started earlier than we thought
                res = redis_client.zrangebyscore(
                    _key, ts, "+inf", start=0, num=1, withscores=True
                )
                following_score = None
                status = InsertEpisodeStatus.inserted
                if res:
                    (following_episode, following_score) = res[0]
                    logging.debug(f" -> following episode {following_episode}")
                    following_episode = _member_to_episode_record(following_episode)
                    logging.debug(
                        f"check if {following_episode['episode']} == {episode}"
                    )
                    if following_episode["episode"] == episode:
                        logging.debug(
                            " -> same episode happening later, will delete later "
                            + f"episode {following_episode} "
                            + f"with score {following_score}"
                        )
                        status = InsertEpisodeStatus.replaced
                if status == InsertEpisodeStatus.inserted:
                    logging.debug(" -> new episode")
                else:
                    logging.debug(" -> replaced episode")

                p.zremrangebyscore(_key, ts, ts)
                p.multi()
                p.zadd(_key, {json.dumps({"ts": ts, "episode": episode}): ts})
                if status == InsertEpisodeStatus.replaced:
                    assert following_score
                    p.zremrangebyscore(_key, following_score, following_score)

            p.execute()
            bump_revision(redis_client)
            if trigger_episode_changes:
                new_current_episode_record = get_current_episode_record()
                if new_current_episode_record != previous_current_episode_record:
                    if (
                        new_current_episode_record
                        and previous_current_episode_record
                        and datetime.fromisoformat(
                            new_current_episode_record["timestamp"]
                        )
                        < datetime.fromisoformat(
                            previous_current_episode_record["timestamp"]
                        )
                    ):
                        logging.debug(
                            "new_current_episode_record is older than previous; it "
                            + "was replaced by an earlier one in which case we do not "
                            + "want to trigger the webhook"
                        )
                    else:
                        just_updated_episode(
                            previous=previous_episode_record,
                            current_episode_record=EpisodeRecord(
                                timestamp=timestamp.isoformat(), episode=episode
                            ),
                        )
            return status
            break
        except WatchError:
            logging.debug("WatchError, will retry")
            continue


@app.route("/opengluck/episode", methods=["DELETE"])
def _clear_all_episodes():
    """Delete all episodes."""
    redis_client = assert_get_current_request_redis_client()
    redis_client.delete(_key)
    bump_revision(redis_client)
    return Response(status=204)


@app.route("/opengluck/episode/current", methods=["GET"])
def _get_current_episode_api():
    """Get the current episode."""
    assert_current_request_logged_in()
    until_date = request.args.get("until_date", None)
    if until_date is not None:
        until_date = datetime.fromisoformat(until_date)
    return Response(
        json.dumps(get_current_episode_record(until_date=until_date)),
        content_type="application/json",
    )


@app.route("/opengluck/episode", methods=["GET"])
def _get_episode_api():
    """Get the current episode."""
    assert_current_request_logged_in()
    until_date = request.args.get("until_date", None)
    if until_date is not None:
        until_date = datetime.fromisoformat(until_date)
    return Response(get_current_episode(until_date=until_date), mimetype="text/plain")


@app.route("/opengluck/episode/last", methods=["GET"])
def _get_last_episodes_api():
    """Get the last episodes."""
    assert_current_request_logged_in()
    last_n = int(request.args.get("last_n", 20))
    until_date = request.args.get("until_date", None)
    if until_date is not None:
        until_date = datetime.fromisoformat(until_date)
    last_episodes = get_last_episodes(last_n=last_n, until_date=until_date)
    return Response(json.dumps(last_episodes), mimetype="application/json")


class InsertEpisodesStatus(TypedDict):
    """The response to an episodes upload."""

    success: bool
    status: str
    nb_inserted: int
    nb_replaced: int
    nb_duplicates: int


def insert_episodes(
    episodes: List[EpisodeRecord],
) -> InsertEpisodesStatus:
    """Insert episode records at once.

    Args:
        episodes: the episode records to insert
    Returns:
        the response
    """
    episodes = sorted(episodes, key=lambda e: e["timestamp"])
    nb_duplicates = 0
    nb_inserted = 0
    nb_replaced = 0
    for episode in episodes:
        timestamp = datetime.fromisoformat(episode["timestamp"])
        status = insert_episode(
            episode=episode["episode"],
            timestamp=timestamp,
            trigger_episode_changes=False,
        )
        if status == InsertEpisodeStatus.duplicate:
            nb_duplicates += 1
        elif status == InsertEpisodeStatus.inserted:
            nb_inserted += 1
        elif status == InsertEpisodeStatus.replaced:
            nb_replaced += 1
        else:
            raise ValueError(f"unexpected status: {status}")
    return InsertEpisodesStatus(
        success=True,
        status=f"added {nb_inserted} record(s), "
        f"replaced {nb_replaced} record(s), " + f"skipped {nb_duplicates} duplicate(s)",
        nb_inserted=nb_inserted,
        nb_replaced=nb_replaced,
        nb_duplicates=nb_duplicates,
    )


@app.route("/opengluck/episode/upload", methods=["POST"])
def _set_episode_api():
    """Inserts a list of episodes, skipping duplicates."""
    # LATER DEPRECATED this route is deprecated
    assert_current_request_logged_in()
    body = request.get_json()
    if not body or not isinstance(body, dict):
        abort(400)
    episodes = cast(List[EpisodeRecord], body["episodes"])
    current_cgm_device_properties = body.get("current-cgm-device-properties", None)
    if current_cgm_device_properties is not None:
        set_current_cgm_device_properties(current_cgm_device_properties)
    episodes = sorted(episodes, key=lambda e: e["timestamp"])
    nb_duplicates = 0
    nb_inserted = 0
    nb_replaced = 0
    for episode in episodes:
        timestamp = datetime.fromisoformat(episode["timestamp"])
        status = insert_episode(episode=episode["episode"], timestamp=timestamp)
        if status == InsertEpisodeStatus.duplicate:
            nb_duplicates += 1
        elif status == InsertEpisodeStatus.inserted:
            nb_inserted += 1
        elif status == InsertEpisodeStatus.replaced:
            nb_replaced += 1
        else:
            raise ValueError(f"unexpected status: {status}")
    return Response(
        json.dumps(
            {
                "success": True,
                "status": (
                    f"added {nb_inserted} record(s), "
                    f"replaced {nb_replaced} record(s), "
                    + f"skipped {nb_duplicates} duplicate(s)"
                ),
                "nb_inserted": nb_inserted,
                "nb_replaced": nb_replaced,
                "nb_duplicates": nb_duplicates,
            }
        ),
        content_type="application/json",
    )


def get_episode_for_mgdl(mgdl: int) -> Episode:
    """Get the episode for a given mg/dL value."""
    if mgdl < merge_record_low_threshold:
        return Episode.low
    elif mgdl >= merge_record_high_threshold:
        return Episode.high
    else:
        return Episode.normal
