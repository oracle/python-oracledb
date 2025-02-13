# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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

# -----------------------------------------------------------------------------
# create_schema.py
#
# Creates users and populates their schemas with the tables and packages
# necessary for running the python-oracledb test suite.
# -----------------------------------------------------------------------------

import drop_schema
import test_env

# connect as administrative user (usually SYSTEM or ADMIN)
conn = test_env.get_admin_connection()

# drop existing users and editions, if applicable
drop_schema.drop_schema(conn)

# create test schemas
print("Creating test schemas...")
test_env.run_sql_script(
    conn,
    "create_schema",
    main_user=test_env.get_main_user(),
    main_password=test_env.get_main_password(),
    proxy_user=test_env.get_proxy_user(),
    proxy_password=test_env.get_proxy_password(),
    edition_name=test_env.get_edition_name(),
)
if test_env.get_server_version() >= (21, 0):
    test_env.run_sql_script(
        conn, "create_schema_21", main_user=test_env.get_main_user()
    )
if test_env.get_server_version() >= (23, 4):
    test_env.run_sql_script(
        conn, "create_schema_23_4", main_user=test_env.get_main_user()
    )
if test_env.get_server_version() >= (23, 5):
    test_env.run_sql_script(
        conn, "create_schema_23_5", main_user=test_env.get_main_user()
    )
if test_env.get_server_version() >= (23, 7):
    test_env.run_sql_script(
        conn, "create_schema_23_7", main_user=test_env.get_main_user()
    )
if test_env.is_on_oracle_cloud(conn):
    test_env.run_sql_script(
        conn, "create_schema_cloud", main_user=test_env.get_main_user()
    )
print("Done.")
