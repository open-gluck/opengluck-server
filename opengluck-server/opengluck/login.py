import json
import logging
import os
import time
import uuid
from typing import Optional

import redis
from flask import Response, abort, g, request

from .redis import get_redis_client
from .server import app  # , cors_headers

_target = os.environ.get("TARGET", "production")

_redis_client_users = get_redis_client(db=0)
_dev_magic_token = "dev-token"
_userdb_key = "userdb"


def do_we_have_any_accounts() -> bool:
    """Check if we already have at least one account."""
    return _redis_client_users.hlen("users") > 0


def migrate_to_multi_user() -> None:
    """Migrate to multi-user."""
    # loop over all keys
    for key in _redis_client_users.scan_iter():
        # skip the users and http_requests key
        if key == b"users" or key == b"http_requests":
            continue
        # is it a token?
        if key.startswith(b"token:"):
            # delete it
            _redis_client_users.delete(key)
        else:
            # move the key to db=1
            _redis_client_users.move(key, 1)


def _get_next_available_db() -> int:
    db = 1
    while True:
        dbuser = _redis_client_users.hget(_userdb_key, f"{db}")
        if dbuser is None:
            return db
        # yield to other threads
        time.sleep(0.0001)
        db += 1


def create_account(login: str, password: str) -> None:
    """Creates an account on redis.

    Args:
        login: The login of the user.
        password: The password of the user.
    """
    previous_user_check = _redis_client_users.hget("users", login)
    if previous_user_check is not None:
        logging.info(f"User {login} already exists")
        abort(409)
    db = _get_next_available_db()
    _redis_client_users.hset(_userdb_key, f"{db}", login)
    _redis_client_users.hset(
        "users", login, json.dumps({"password": password, "db": db})
    )


def delete_account(login: str) -> None:
    """Deletes an account on redis.

    Args:
        login: The login of the user.
    """
    previous_user_check = _redis_client_users.hget("users", login)
    if previous_user_check is None:
        logging.info(f"User {login} does not exists")
        abort(404)
    previous_user_check = json.loads(previous_user_check)
    assert "db" in previous_user_check
    db = previous_user_check["db"]
    assert type(db) == int and db > 0
    redis_client_user = get_redis_client(db=db)
    redis_client_user.flushdb()
    _redis_client_users.hdel("users", login)


def get_token(login: str, password: str, scope: str = "admin") -> str:
    """Returns a token for a user, given its password.

    This works by checking on redis if the account already exists. If yes, its
    value is parsed, and the password is checked. If everything looks good, we
    generate a temporary token that is valid two years, store it on redis, and
    return it.

    Args:
        login: The login of the user.
        password: The password of the user.
        scope: The scope of the token. Defaults to "admin", meaning the user
            will be able to do everything, including creating and deleting
            accounts.
    """
    logging.debug(f"Checking login {login} and password (*hidden*)")

    user = _redis_client_users.hget("users", login)
    if user is None:
        logging.debug("User not found")
        abort(401)

    user_data = json.loads(user)
    if user_data["password"] != password:
        logging.debug("Password does not match")
        abort(401)

    token = uuid.uuid4().hex
    token_data = json.dumps({"login": login, "scope": scope})
    logging.debug(f"User OK, generated token {token}")
    _redis_client_users.setex(f"token:{token}", 2 * 365 * 86400, token_data)
    return token


def get_token_login(token: str) -> Optional[str]:
    """Returns the login for a token.

    Args:
        token: The token to check.
    """
    logging.debug(f"Checking token {token}")
    token_data = _redis_client_users.get(f"token:{token}")
    if token_data is None:
        logging.debug("Token not found")
        return None
    token_data = json.loads(token_data.decode("utf-8"))
    assert "login" in token_data
    login = token_data["login"]
    return login


def get_token_scope(token: str) -> Optional[str]:
    """Returns the scope for a token.

    Args:
        token: The token to check.
    """
    logging.debug(f"Checking token scope {token}")
    token_data = _redis_client_users.get(f"token:{token}")
    if token_data is None:
        logging.debug("Token not found")
        return None
    token_data = json.loads(token_data.decode("utf-8"))
    assert "scope" in token_data
    scope = token_data["scope"]
    return scope


def get_token_user(token: str) -> Optional[str]:
    """Returns the user for a token.

    Args:
        token: The token to check.
    """
    login = get_token_login(token)
    if login is None:
        return None
    user_data = _redis_client_users.hget("users", login)
    if user_data is None:
        logging.debug("User not found for token")
        return None
    return user_data.decode("utf-8")


def get_token_redis_client(token: str) -> redis.Redis:
    """Returns the redis client for a token.

    Args:
        token: The token to check.
    """
    # are we on dev? if so we accept a magic dev token
    if _target == "dev" and token == _dev_magic_token:
        return get_redis_client(db=1)
    user = get_token_user(token)
    if user is None:
        abort(401)
        return
    user_data = json.loads(user)
    assert "db" in user_data
    return get_redis_client(db=user_data["db"])


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
    assert_current_request_is_logged_in_as_admin()
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


def is_current_request_logged_in() -> bool:
    """Checks if the current request is logged in."""
    token = get_current_request_token()
    if token is None:
        return False
    # are we on dev? if so we accept a magic dev token
    if _target == "dev" and get_current_request_token() == _dev_magic_token:
        return True
    if not is_token_valid(token):
        return False
    return True


def assert_current_request_logged_in() -> None:
    """Asserts that the current request is logged in."""
    if not is_current_request_logged_in():
        abort(401)


def assert_current_request_is_logged_in_as_admin() -> None:
    """Asserts that the current request is logged in with an admin scope."""
    if not is_current_request_logged_in():
        abort(401)
    token = get_current_request_token()
    scope = get_token_scope(token)
    if scope != "admin":
        abort(403)


def assert_get_current_request_login() -> str:
    """Asserts and returns the login for the current request."""
    token = get_current_request_token()
    if token is None:
        abort(401)
    login = get_token_login(token)
    if login is None:
        abort(401)
    user_data = _redis_client_users.hget("users", login)
    if user_data is None:
        abort(401)
    return login


def assert_get_current_request_redis_client() -> redis.Redis:
    """Asserts and returns we have a redis client for the current request."""
    if g.get("redis_client") is not None:
        return g.redis_client
    token = get_current_request_token()
    if token is None:
        abort(401)
    if g.get("redis_client") is None:
        g.redis_client = get_token_redis_client(token)
    return g.redis_client


@app.route("/opengluck/validate-auth", methods=["POST"])
def _validate_auth():
    token = get_current_request_token()
    if token is None:
        abort(401)
    user = get_token_user(token)
    return Response(json.dumps({"user": user}), content_type="application/json")
