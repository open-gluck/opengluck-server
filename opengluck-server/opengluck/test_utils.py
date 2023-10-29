from datetime import datetime, timedelta, timezone

from .utils import parse_timestamp, timestamp_since_epoch


def test_parse_timestamp():
    assert parse_timestamp("2023-03-17T23:52:13.000+01:00") == datetime(
        2023, 3, 17, 23, 52, 13, tzinfo=timezone(timedelta(hours=1))
    )


def test_timestamp_since_epoch():
    assert timestamp_since_epoch("2023-03-17T23:52:13.000+01:00") == 1679093533
