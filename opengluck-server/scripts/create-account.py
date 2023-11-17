#!/opt/venv/bin/python

import sys

sys.path.append("/app")

import opengluck.login  # noqa: E402

if len(sys.argv) != 3:
    print("Usage: create-account.py <username> <password>")
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]

opengluck.login.create_account(username, password)
