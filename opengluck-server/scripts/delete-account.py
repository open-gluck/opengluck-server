#!/opt/venv/bin/python

import sys

sys.path.append("/app")

import opengluck.login  # noqa: E402

if len(sys.argv) != 2:
    print("Usage: delete-account.py <username>")
    sys.exit(1)

username = sys.argv[1]

opengluck.login.delete_account(username)
