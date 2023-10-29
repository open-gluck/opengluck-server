import json
import logging
import os
import uuid
from typing import Optional

from flask import Response, abort, request

from .redis import redis_client
from .server import app  # , cors_headers

_target = os.environ.get("TARGET", "production")


def do_we_have_any_accounts() -> bool:
    """Check if we already have at least one account."""
    return redis_client.hlen("users") > 0


def create_account(login: str, password: str) -> None:
    """Creates an account on redis.

    Args:
        login: The login of the user.
        password: The password of the user.
    """
    redis_client.hset("users", login, json.dumps({"password": password}))


def get_token(login: str, password: str) -> str:
    """Returns a token for a user, given its password.

    This works by checking on redis if the account already exists. If yes, its
    value is parsed, and the password is checked. If everything looks good, we
    generate a temporary token that is valid two years, store it on redis, and
    return it.
    """
    logging.debug(f"Checking login {login} and password (*hidden*)")

    user = redis_client.hget("users", login)
    if user is None:
        logging.debug("User not found")
        abort(401)

    user_data = json.loads(user)
    if user_data["password"] != password:
        logging.debug("Password does not match")
        abort(401)

    token = uuid.uuid4().hex
    logging.debug(f"User OK, generated token {token}")
    redis_client.setex(f"token:{token}", 2 * 365 * 86400, user)
    return token


def get_token_user(token: str) -> Optional[str]:
    """Returns the user for a token.

    Args:
        token: The token to check.
    """
    logging.debug(f"Checking token {token}")
    user = redis_client.get(f"token:{token}")
    if user is None:
        logging.debug("Token not found")
        return None
    return user.decode("utf-8")


def is_token_valid(token: str) -> bool:
    """Checks if a token is valid.

    Args:
        token: The token to check.
    """
    return get_token_user(token) is not None


@app.route("/opengluck/check-accounts")
def _check_accounts():
    return Response(json.dumps(do_we_have_any_accounts()))


@app.route("/opengluck/create-account", methods=["POST"])
def _create_account():
    data = request.get_json()
    token = create_account(data["login"], data["password"])

    return Response(json.dumps({"token": token}))


@app.route("/opengluck/login", methods=["POST"])
def _login():
    data = request.get_json()
    token = get_token(data["login"], data["password"])

    return Response(json.dumps({"token": token}), content_type="application/json")


def get_current_request_token() -> Optional[str]:
    """Returns the token from the current request."""
    authorization = request.headers.get("Authorization")
    if authorization is None:
        return None
    return authorization.split(" ")[1]


def assert_current_request_logged_in() -> None:
    """Asserts that the current request is logged in."""
    token = get_current_request_token()
    if token is None:
        abort(401)
    # are we on dev? if so we accept a magic dev token
    if _target == "dev" and get_current_request_token() == "dev-token":
        return
    if not is_token_valid(token):
        abort(401)


@app.route("/opengluck/validate-auth", methods=["POST"])
def _validate_auth():
    token = get_current_request_token()
    if token is None:
        abort(401)
    user = get_token_user(token)
    return Response(json.dumps({"user": user}))
