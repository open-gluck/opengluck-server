import json
import logging
import os
from datetime import datetime
from threading import Thread
from typing import Any
from uuid import uuid4

import requests
from flask import Response, request
from requests.adapters import HTTPAdapter, Retry

from .jmespath import do_record_match_filter
from .login import (assert_current_request_is_logged_in_as_admin,
                    assert_get_current_request_login,
                    assert_get_current_request_redis_client)
from .server import app

_MAX_ITEMS = 100
_WEBHOOK_TIMEOUT = 2

_s = requests.Session()

retries = Retry(total=0, backoff_factor=1, status_forcelist=[500, 502, 503, 504])

_s.mount("http://", HTTPAdapter(max_retries=retries))
_s.mount("https://", HTTPAdapter(max_retries=retries))


@app.route("/opengluck/webhooks/<webhook>")
def _get_webhook(webhook):
    redis_client = assert_get_current_request_redis_client()
    webhooks = []
    for key, value in redis_client.hgetall(f"webhooks:{webhook}").items():
        webhooks.append(
            {"id": key.decode("utf-8"), **json.loads(value.decode("utf-8"))}
        )
    return Response(json.dumps(webhooks))


@app.route("/opengluck/webhooks/<webhook>", methods=["PUT"])
def _create_webhook(webhook):
    redis_client = assert_get_current_request_redis_client()
    assert_current_request_is_logged_in_as_admin()
    data = request.get_json()

    id = str(uuid4())
    redis_client.hset(f"webhooks:{webhook}", id, json.dumps(data))
    return Response(status=204)


@app.route("/opengluck/webhooks/<webhook>", methods=["DELETE"])
def _delete_webhook(webhook):
    redis_client = assert_get_current_request_redis_client()

    redis_client.delete(f"webhooks:{webhook}")
    redis_client.delete(f"last-webhooks:{webhook}")
    return Response(status=204)


@app.route("/opengluck/webhooks/<webhook>/<id>", methods=["DELETE"])
def _delete_webhook_id(webhook, id):
    redis_client = assert_get_current_request_redis_client()

    redis_client.hdel(f"webhooks:{webhook}", id)
    return Response(status=204)


@app.route("/opengluck/webhooks/<webhook>/last")
def _get_last_webhooks(webhook):
    redis_client = assert_get_current_request_redis_client()
    filter = request.args.get("filter", "")
    last_n = int(request.args.get("last_n", _MAX_ITEMS))

    last_webhooks = []
    for last_webhook in redis_client.lrange(f"last-webhooks:{webhook}", 0, last_n - 1):
        record = json.loads(last_webhook.decode("utf-8"))
        try:
            does_match = do_record_match_filter(record["data"], filter)
        except Exception as e:
            return Response(str(e), status=400)
        if does_match:
            last_webhooks.append(record)
    return Response(json.dumps(last_webhooks), content_type="application/json")


def _call_webhook(id: str, webhook: dict, data: Any):
    """Call the given webhook."""
    url = webhook["url"]
    filter = webhook.get("filter", "")
    include_last = webhook.get("include_last", False)
    login = assert_get_current_request_login()
    if do_record_match_filter(data, filter):

        logging.info(f"Calling webhook {url}")

        if include_last:
            from .last import get_last

            last = get_last()
            data = {"data": data, "last": last}
        try:
            _s.request(
                "POST",
                url,
                data=json.dumps(data),
                headers={
                    "content-type": "application/json",
                    "x-opengluck-login": login,
                },
                allow_redirects=False,
                timeout=_WEBHOOK_TIMEOUT,
            )
        except Exception as e:
            logging.debug(f"Calling webhook {url} failed: {e}")


def call_webhooks(webhook: str, data: Any):
    """Call all webhooks for the given webhook name."""
    redis_client = assert_get_current_request_redis_client()

    def _impl():
        for key, value in redis_client.hgetall(f"webhooks:{webhook}").items():
            id = key.decode("utf-8")
            webhook_value: dict = json.loads(value.decode("utf-8"))
            _call_webhook(id, webhook_value, data)

        redis_client.lpush(
            f"last-webhooks:{webhook}",
            json.dumps({"date": datetime.now().isoformat(), "data": data}),
        )
        redis_client.ltrim(f"last-webhooks:{webhook}", 0, _MAX_ITEMS)

    if os.environ.get("PYTEST_CURRENT_TEST"):
        # when running from pytest, do not use threads so we can retrieve
        # webhooks synchronously
        _impl()
    else:
        Thread(target=_impl).start()
