"""A module to manage third-party userdata.

This is useful when using OpenGlück with other apps. You can store and retrive
values, and subscribe to changes using webhooks.
"""
import json
from typing import Any, Optional

from flask import Response, request

from .login import assert_get_current_request_redis_client
from .server import app
from .webhooks import call_webhooks

_MAX_ITEMS = 1000


def _get_redis_key(key: str) -> str:
    """Get the redis key for a userdata key."""
    return f"userdata:{key}"


@app.route("/opengluck/userdata/<key>", methods=["PUT"])
def _set_userdata(key):
    """Set a value in the userdata."""
    redis_client = assert_get_current_request_redis_client()

    value = request.get_data()

    if key is None or value is None:
        return Response("Missing key or value", status=400)

    redis_client.set(_get_redis_key(key), value)
    content_type = request.headers.get("Content-Type")
    if content_type is not None and content_type.startswith("application/json"):
        call_webhooks("userdata:set", {"key": key, "value": json.loads(value)})
    else:
        call_webhooks("userdata:set", {"key": key})

    return Response("", status=201)


@app.route("/opengluck/userdata/<key>", methods=["DELETE"])
def _delete_userdata(key):
    """Delete a userdata."""
    redis_client = assert_get_current_request_redis_client()

    if key is None:
        return Response("Missing key or value", status=400)

    redis_client.delete(_get_redis_key(key))
    return Response("", status=204)


def set_userdata(key: str, value: Any) -> None:
    """Set a value in the userdata."""
    redis_client = assert_get_current_request_redis_client()
    redis_client.set(_get_redis_key(key), json.dumps(value))
    call_webhooks("userdata:set", {"key": key, "value": value})


def get_userdata(key) -> Optional[Any]:
    """Get a value from the userdata."""
    redis_client = assert_get_current_request_redis_client()
    value = redis_client.get(_get_redis_key(key))

    if value is None:
        return None
    result = json.loads(value)
    return result


@app.route("/opengluck/userdata/<key>")
def _get_userdata(key):
    """Get a value from the userdata."""
    redis_client = assert_get_current_request_redis_client()

    value = redis_client.get(_get_redis_key(key))

    if value is None:
        return Response("Not found", status=404)

    return Response(value, content_type="application/octet-stream")


@app.route("/opengluck/userdata/<key>/lpush", methods=["PUT"])
def _lpush_userdata(key):
    """Push a value in front of a userdata list."""
    redis_client = assert_get_current_request_redis_client()

    value = request.get_data()

    if key is None or value is None:
        return Response("Missing key or value", status=400)

    content_type = request.headers.get("Content-Type")
    assert content_type is not None and content_type.startswith("application/json")

    redis_client.lpush(_get_redis_key(key), value)
    redis_client.ltrim(_get_redis_key(key), 0, _MAX_ITEMS)
    call_webhooks("userdata:lpush", {"key": key, "value": json.loads(value)})

    return Response("", status=201)


@app.route("/opengluck/userdata/<key>/lrange", methods=["GET"])
def _lrange_userdata(key):
    """Reads value in front from a userdata list."""
    redis_client = assert_get_current_request_redis_client()

    value = request.get_data()
    start = int(request.args.get("start", "0"))
    end = int(request.args.get("end", _MAX_ITEMS))

    if key is None or value is None:
        return Response("Missing key or value", status=400)

    result = []
    for item in redis_client.lrange(_get_redis_key(key), start, end):
        result.append(json.loads(item))
    return Response(json.dumps(result), content_type="application/json")


@app.route("/opengluck/userdata", methods=["GET"])
def _list_userdata():
    """Gets a list of current userdata."""
    redis_client = assert_get_current_request_redis_client()

    result = []
    for key in redis_client.scan_iter("userdata:*"):
        key_type = redis_client.type(key).decode()
        if key_type == "list":
            userdata_type = "list"
        elif key_type == "string":
            userdata_type = "string"
        elif key_type == "zset":
            userdata_type = "zset"
        else:
            userdata_type = f"unknown:{key_type}"
        result.append({"name": (key[9:]).decode(), "type": userdata_type})

    return Response(json.dumps(result), content_type="application/json")


@app.route("/opengluck/userdata/<key>/zadd", methods=["PUT"])
def _zset_userdata(key):
    """Adds a value to a sorted set."""
    redis_client = assert_get_current_request_redis_client()

    score = request.args.get("score")
    member = request.args.get("member")

    if not member or score is None or not float(score):
        return Response("Missing key or value", status=400)
    score = float(score)

    redis_client.zadd(_get_redis_key(key), {member: score})
    call_webhooks("userdata:zadd", {"key": key, "score": score, "member": member})

    return Response("", status=201)


@app.route("/opengluck/userdata/<key>/zrange", methods=["GET"])
def _zrange_userdata(key):
    """Adds a value to a sorted set."""
    redis_client = assert_get_current_request_redis_client()

    start = int(request.args.get("start", 0))
    end = int(request.args.get("end", 99))

    res = redis_client.zrange(_get_redis_key(key), start, end, desc=True)
    res = [res.decode() for res in res]

    return Response(json.dumps(res), content_type="application/json")
