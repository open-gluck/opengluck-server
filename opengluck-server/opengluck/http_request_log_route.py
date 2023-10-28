import json

from flask import Response

from .http_request_log import get_last_http_requests
from .login import assert_current_request_logged_in
from .server import app


@app.route("/opengluck/last-requests")
def _last_requests():
    assert_current_request_logged_in()
    last_http_requests = get_last_http_requests()
    return Response(json.dumps(last_http_requests))
