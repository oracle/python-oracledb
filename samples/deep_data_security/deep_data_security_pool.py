# -----------------------------------------------------------------------------
# Copyright (c) 2026, Oracle and/or its affiliates.
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
# deep_data_security_pool.py
#
# Demonstrates Deep Data Security usage with python-oracledb connection pooling
# and Microsoft Entra ID tokens. The sample shows session context before and
# after setting end-user identity so row-level security behavior can be
# observed.
#
# For setup and run instructions, see README.md in this directory.
# -----------------------------------------------------------------------------

import getpass
import os
import sys

import msal
import oracledb
import oracledb.plugins.end_user_sec_provider as provider

# Add the parent "samples" directory to Python import path
SAMPLES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SAMPLES_DIR)

import sample_env  # noqa

# Azure App client ID used for user token acquisition
AZURE_USER_CLIENT_ID = os.environ.get("AZURE_USER_CLIENT_ID")
# Microsoft Entra authority URL (for example:
# https://login.microsoftonline.com/<tenant-id>)
AZURE_USER_AUTHORITY = os.environ.get("AZURE_USER_AUTHORITY")
# Scope/audience requested for database token flow
AZURE_USER_SCOPES = os.environ.get("AZURE_USER_SCOPES")

# Azure App client ID used for db token acquisition
AZURE_DB_CLIENT_ID = os.environ.get("AZURE_DB_CLIENT_ID")
# Azure client secret associated with AZURE_CLIENT_ID
AZURE_DB_CLIENT_CREDENTIAL = os.environ.get("AZURE_DB_CLIENT_CREDENTIAL")
# Microsoft Entra authority URL (for example:
# https://login.microsoftonline.com/<tenant-id>)
AZURE_DB_AUTHORITY = os.environ.get("AZURE_DB_AUTHORITY")
# Scope/audience requested for database token flow
AZURE_DB_SCOPES = os.environ.get("AZURE_DB_SCOPES")

# Azure username required for getting token
AZURE_USERNAME = os.environ.get("AZURE_USERNAME")
# Azure password required for getting token
AZURE_PASSWORD = getpass.getpass("Azure User Password: ")


def _get_end_user_identity():

    app = msal.PublicClientApplication(
        AZURE_USER_CLIENT_ID,
        authority=AZURE_USER_AUTHORITY,
    )

    result = app.acquire_token_by_username_password(
        username=AZURE_USERNAME,
        password=AZURE_PASSWORD,
        scopes=[AZURE_USER_SCOPES],
    )

    access_token = result.get("access_token")
    if access_token:
        return access_token

    error = result.get("error", "unknown_error")
    description = result.get(
        "error_description", "No error description returned"
    )
    raise RuntimeError(
        f"Failed to acquire end-user token: {error}. {description}"
    )


def _validate_required_env_vars():
    required = {
        "AZURE_USER_CLIENT_ID": AZURE_USER_CLIENT_ID,
        "AZURE_USER_AUTHORITY": AZURE_USER_AUTHORITY,
        "AZURE_USER_SCOPES": AZURE_USER_SCOPES,
        "AZURE_USERNAME": AZURE_USERNAME,
        "AZURE_DB_CLIENT_ID": AZURE_DB_CLIENT_ID,
        "AZURE_DB_CLIENT_CREDENTIAL": AZURE_DB_CLIENT_CREDENTIAL,
        "AZURE_DB_AUTHORITY": AZURE_DB_AUTHORITY,
        "AZURE_DB_SCOPES": AZURE_DB_SCOPES,
    }

    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing required azure configuration env vars: "
            + ", ".join(missing)
        )


def query(conn):

    # --------------------------------------------------------
    # Query contexts
    # --------------------------------------------------------
    query = """
        select sys_context('userenv', 'current_user'),
               xs_sys_context('xs$session', 'username')
    """

    print("\n-- Read contexts through DB query")
    with conn.cursor() as cursor:
        cursor.execute(query)
        current_user, xs_user = cursor.fetchone()

        print(
            "Current user sys_context('userenv', 'current_user') =",
            current_user,
        )
        print(
            "XS session user xs_sys_context('xs$session', 'username') =",
            xs_user,
        )

    # ---------------------------------------------------------------
    # Sample query on hr.employees; this is expected to fail when the
    # end security context is not applied
    # ---------------------------------------------------------------
    print("\n-- Sample DB query on table hr.employees")

    try:
        with conn.cursor() as cursor:
            cursor.execute("select count(*) from hr.employees")

            (count,) = cursor.fetchone()
            print("Count of records in hr.employees =", count, "\n")

        # Print contents of rows
        query = "select DEPARTMENT_ID, FIRST_NAME, SSN from hr.employees"

        with conn.cursor() as cursor:
            cursor.execute(query)

            for dept_id, first_name, ssn in cursor:
                print(
                    f"Dept ID: {dept_id}, First Name: {first_name}, SSN: {ssn}"
                )
    except Exception as e:
        print(e)


def print_sec_ctx_tok(connection):
    # 1. Query ORA_END_USER_CONTEXT.USERNAME
    with connection.cursor() as cursor:
        cursor.execute("select ORA_END_USER_CONTEXT.USERNAME")
        (user_name,) = cursor.fetchone()
        print("ORA_END_USER_CONTEXT username is", user_name)

    # 2. Query ORA_END_USER_CONTEXT."USER".TOKEN.iss
    with connection.cursor() as cursor:
        cursor.execute('select ORA_END_USER_CONTEXT."USER".TOKEN.iss')
        (user_token_iss,) = cursor.fetchone()
        print("ORA_END_USER_CONTEXT user token iss =", user_token_iss)


def print_xs_session_info(connection):

    # ---------------------------------------------------------------
    # First: Query xs$session username
    # ---------------------------------------------------------------
    with connection.cursor() as cursor:
        cursor.execute("select xs_sys_context('xs$session','username')")
        (xs_user_name,) = cursor.fetchone()
        print("xs$session username is " + str(xs_user_name))


def main():

    _validate_required_env_vars()
    end_user_identity = _get_end_user_identity()

    pool = oracledb.create_pool(
        user=sample_env.get_main_user(),
        password=sample_env.get_main_password(),
        dsn=sample_env.get_connect_string(),
        params=sample_env.get_pool_params(),
        extra_auth_params={
            "end_user_sec_params": {
                "spi_type": "azure_tokens",
                "auth_flow": "client_credentials",
                "client_id": AZURE_DB_CLIENT_ID,
                "client_credential": AZURE_DB_CLIENT_CREDENTIAL,
                "authority": AZURE_DB_AUTHORITY,
                "scopes": AZURE_DB_SCOPES,
            }
        },
    )

    print("x" * 20, "Before setting the context", "x" * 20, "\n")

    with pool.acquire() as connection:
        print_xs_session_info(connection)
        print_sec_ctx_tok(connection)
        query(connection)

    input("press enter to set the context")

    provider.set_end_user_identity(end_user_identity)

    print("x" * 20, "After setting the context", "x" * 20, "\n")

    with pool.acquire() as connection:
        print_xs_session_info(connection)
        print_sec_ctx_tok(connection)
        query(connection)


main()
