"""Main server module."""
import json
import logging
import random
import sys

from flask import Flask, Response, request
from flask_cors import CORS

from .http_request_log import log_request_to_redis
from .redis import get_revision, get_revision_changed_at

app = Flask("OpenGlück")

cors = CORS(app, resources={r"/opengluck/*": {"origins": "*"}})


def is_app_request() -> bool:
    """Check if the current request is an app request."""
    return request.path.startswith("/opengluck")


def _process_request():
    log_request_to_redis()
    from opengluck.login import is_current_request_logged_in_as_admin

    from .webhooks import call_webhooks

    try:
        data = request.get_json()
    except Exception:
        data = request.get_data().decode("utf-8")
        if len(data) == 0:
            data = None
    payload = {
        "method": request.method,
        "path": request.path,
        "headers": dict(request.headers),
        "cookies": dict(request.cookies),
        "data": data,
    }

    if is_current_request_logged_in_as_admin():
        call_webhooks("app_request", payload)


@app.before_request
def _prevent_recursive_calls():
    # check if we have a x-opengluck-login header
    # if so, this call is the result of a webhook call and we should stop further processing to avoid infinite loops
    if "x-opengluck-login" in request.headers:
        return Response(status=423)

@app.before_request
def _log_request():
    _process_request()


@app.route("/opengluck/ping")
def _ping():
    from .login import assert_current_request_logged_in

    assert_current_request_logged_in()
    return "pong"


@app.route("/opengluck/random")
def _random():
    return Response(json.dumps({"random": random.random()}), content_type="application/json")

@app.route("/opengluck/revision")
def _get_revision_info():
    from .login import assert_get_current_request_redis_client

    redis_client = assert_get_current_request_redis_client()
    revision = get_revision(redis_client)
    revision_changed_at = get_revision_changed_at(redis_client)
    return Response(
        status=200,
        response=json.dumps(
            {"revision": revision, "revision_changed_at": revision_changed_at}
        ),
        content_type="application/json",
    )


if __name__ == "__main__":

    logging.info("Starting OpenGlück server")
    app.run()


def check():
    """Check that we can run the server.

    This is used by the build script, to check that deps were successfully installed
    it happened we had an issue at one point where flask did not
    correctly pinned its dependancies and the server failed to start
    """
    logging.info("Server check OK")
    sys.exit(0)
