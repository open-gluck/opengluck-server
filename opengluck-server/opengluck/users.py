import json

from flask import Response

from .login import assert_current_request_logged_in
from .redis import redis_client
from .server import app


@app.route("/opengluck/users")
def _list_users():
    assert_current_request_logged_in()
    users = []
    for user in redis_client.hkeys("users"):
        users.append({"login": user.decode("utf-8")})
    return Response(json.dumps(users))


@app.route("/opengluck/users/<login>", methods=["DELETE"])
def _delete_user(login):
    assert_current_request_logged_in()
    redis_client.hdel("users", login)
    return Response(status=204)
