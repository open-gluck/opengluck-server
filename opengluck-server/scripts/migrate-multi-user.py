#!/opt/venv/bin/python

import sys

sys.path.append("/app")

import opengluck.login  # noqa: E402

# This script is used to migrate OpenGlück from a single to a multi-user architecture.
# It will move all keys to db=1.
#
# You will need to further manually:
# - delete all emitted token
# - adjust the users key
# - create the userdb key: HSET userdb 1 <your-login>
opengluck.login.migrate_to_multi_user()
