import json

from flask import Response
from opengluck.login import assert_current_request_is_logged_in_as_admin

from .redis import get_redis_client
from .server import app

_redis_client_zero = get_redis_client(db=0)


@app.route("/opengluck/users")
def _list_users():
    assert_current_request_is_logged_in_as_admin()
    users = []
    for user in _redis_client_zero.hkeys("users"):
        users.append({"login": user.decode("utf-8")})
    return Response(json.dumps(users))


@app.route("/opengluck/users/<login>", methods=["DELETE"])
def _delete_user(login):
    assert_current_request_is_logged_in_as_admin()
    _redis_client_zero.hdel("users", login)
    return Response(status=204)
