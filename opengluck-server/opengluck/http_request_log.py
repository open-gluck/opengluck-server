import json
from typing import List

from flask import request

from .redis import redis_client

_MAX_ITEMS = 500


def log_request_to_redis():
    """Log the current request to redis."""
    method = request.method
    path = request.path
    query_string = request.query_string.decode("utf-8")
    if query_string:
        path = f"{request.path}?{query_string}"
    headers = str(request.headers)
    body = request.get_data().decode("utf-8")
    redis_client.lpush(
        "http_requests",
        json.dumps({"method": method, "path": path, "headers": headers, "body": body}),
    )
    redis_client.ltrim("http_requests", 0, _MAX_ITEMS)


def get_last_http_requests() -> List[dict]:
    """Get the last http requests."""
    last_requests = []
    for last_request in redis_client.lrange("http_requests", 0, _MAX_ITEMS):
        last_requests.append(json.loads(last_request.decode("utf-8")))
    return last_requests
