# -----------------------------------------------------------------------------
# drcp_query.py (Section 2.4 and 2.5)
# Query DRCP pool statistics
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Copyright (c) 2022, 2025, Oracle and/or its affiliates. All rights reserved.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

import oracledb
import getpass
import os

# default values
PYTHON_SYS_USER = "SYSTEM"
PYTHON_DRCP_CONNECT_STRING = "localhost/free"

# dictionary containing all parameters; these are acquired as needed by the
# methods below (which should be used instead of consulting this dictionary
# directly) and then stored so that a value is not requested more than once
PARAMETERS = {}


def get_value(name, label, default_value=""):
    value = PARAMETERS.get(name)
    if value is not None:
        return value
    value = os.environ.get(name)
    if value is None:
        if default_value:
            label += " [%s]" % default_value
        label += ": "
        if default_value:
            value = input(label).strip()
        else:
            value = getpass.getpass(label)
        if not value:
            value = default_value
    PARAMETERS[name] = value
    return value


def get_main_user():
    return get_value(
        "user",
        "Enter the privileged user with access to DRCP views",
        PYTHON_SYS_USER,
    )


def get_main_password():
    return get_value("pw", "Enter the Password for %s" % get_main_user())


def get_drcp_connect_string():
    connect_string = get_value(
        "DRCP_CONNECT_STRING",
        "Enter the connect string to access the DRCP views",
        PYTHON_DRCP_CONNECT_STRING,
    )
    return connect_string


drcp_user = get_main_user()
drcp_password = get_main_password()
drcp_connect_string = get_drcp_connect_string()

con = oracledb.connect(
    user=drcp_user, password=drcp_password, dsn=drcp_connect_string
)
cur = con.cursor()
# looking at the pool stats of the DRCP Connection
print("\nLooking at DRCP Pool statistics...\n")
cur.execute(
    "select cclass_name, num_requests, num_hits, num_misses "
    "from v$cpool_cc_stats"
)
res = cur.fetchall()

print("(CCLASS_NAME, NUM_REQUESTS, NUM_HITS, NUM_MISSES)")
print("-------------------------------------------------")
for row in res:
    print(row)
print("Done.")
