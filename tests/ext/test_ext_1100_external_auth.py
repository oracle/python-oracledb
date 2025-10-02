# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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

"""
E1100 - Module for testing external authentication. This requires access to the
orapki executable found in a full database installation and will create and
drop users in the database. The tests here will only run if the has_orapki
value is enabled and, due to limitations in how the Oracle Client libraries
work, can only be run by itself.
"""

import os
import subprocess
import tempfile

import oracledb
import pytest

ALIAS_NAME = "ext_test_1100"
USER = "ext_test_1100_user"


@pytest.fixture(scope="module")
def config(sqlnet_config, tnsnames_config, setup_user):
    """
    Builds the configuration used for the tests in this module. Note that if
    the Oracle Client libraries have already been initialized then all of these
    tests will be skipped.
    """
    pass


@pytest.fixture(scope="module")
def config_dir():
    """
    Returns the directory where the configuration will be stored.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(scope="module")
def setup_user(config_dir, test_env, user_password):
    """
    Builds the user credentials stored in the supplied wallet.
    """
    oracledb.init_oracle_client(config_dir=config_dir)
    admin_conn = test_env.get_admin_connection()
    with admin_conn.cursor() as cursor:
        try:
            cursor.execute(f"drop user {USER} cascade")
        except oracledb.DatabaseError:
            pass
        cursor.execute(
            f"create user {USER} identified by " + f"{user_password}"
        )
        cursor.execute(f"grant create session to {USER}")


@pytest.fixture(scope="module")
def sqlnet_config(config_dir, test_env, user_password):
    """
    Builds the SQL*Net configuration file.
    """
    if not test_env.use_thick_mode:
        pytest.skip("requires thick mode")
    elif not oracledb.is_thin_mode():
        pytest.skip("must be run separately from all other tests")
    subprocess.run(
        [
            "orapki",
            "wallet",
            "create",
            "-wallet",
            config_dir,
            "-auto_login_only",
        ],
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "mkstore",
            "-wrl",
            config_dir,
            "-createCredential",
            ALIAS_NAME,
            USER,
            user_password,
        ],
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "mkstore",
            "-wrl",
            config_dir,
            "-createCredential",
            test_env.connect_string,
            USER,
            user_password,
        ],
        stdout=subprocess.DEVNULL,
    )
    contents = (
        "WALLET_LOCATION=(SOURCE=(METHOD=FILE)(METHOD_DATA="
        + f"(DIRECTORY={config_dir})))\n"
        + "SQLNET.WALLET_OVERRIDE=TRUE"
    )
    file_name = os.path.join(config_dir, "sqlnet.ora")
    with open(file_name, "w") as f:
        f.write(contents)


@pytest.fixture(scope="module")
def tnsnames_config(config_dir, test_env):
    """
    Builds the tnsnames.ora configuration file.
    """
    params = oracledb.ConnectParams()
    params.parse_connect_string(test_env.connect_string)
    connect_string = params.get_connect_string()
    file_name = os.path.join(config_dir, "tnsnames.ora")
    with open(file_name, "w") as f:
        f.write(f"{ALIAS_NAME} = {connect_string}")


@pytest.fixture(scope="module")
def user_password(test_env):
    return test_env.get_random_string()


@pytest.fixture(autouse=True)
def module_checks(skip_unless_thick_mode, skip_unless_has_orapki, config):
    pass


def test_ext_1100():
    "E1100 - external authentication with tnsnames alias (implicit)"
    with oracledb.connect(dsn=ALIAS_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            assert user == USER.upper()


def test_ext_1101():
    "E1101 - external authentication with tnsnames alias (explicit)"
    with oracledb.connect(externalauth=True, dsn=ALIAS_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            assert user == USER.upper()


def test_ext_1102(test_env):
    "E1102 - external authentication with connect string (explicit)"
    with oracledb.connect(
        externalauth=True, dsn=test_env.connect_string
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            assert user == USER.upper()


def test_ext_1103():
    "E1103 - external authentication with tnsnames alias (explicit)"
    pool = oracledb.create_pool(
        externalauth=True, dsn=ALIAS_NAME, homogeneous=False
    )
    with pool.acquire() as conn:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            assert user == USER.upper()


def test_ext_1104(test_env):
    "E1104 - external authentication with connect string (explicit)"
    pool = oracledb.create_pool(
        externalauth=True,
        homogeneous=False,
        dsn=test_env.connect_string,
    )
    with pool.acquire() as conn:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            assert user == USER.upper()
