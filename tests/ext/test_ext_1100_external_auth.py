# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_extended_config_bool("has_orapki"),
    "extended configuration has_orapki is disabled",
)
@unittest.skipIf(
    test_env.get_is_thin(),
    "thin mode doesn't support external authentication yet",
)
class TestCase(test_env.BaseTestCase):
    alias_name = "ext_test_1100"
    user = "ext_test_1100_user"
    requires_connection = False

    @classmethod
    def _build_sqlnet_config(cls):
        """
        Builds the sqlnet.ora configuration file.
        """
        connect_string = test_env.get_connect_string()
        cls.password = test_env.get_random_string()
        subprocess.run(
            [
                "orapki",
                "wallet",
                "create",
                "-wallet",
                cls.temp_dir.name,
                "-auto_login_only",
            ],
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            [
                "mkstore",
                "-wrl",
                cls.temp_dir.name,
                "-createCredential",
                cls.alias_name,
                cls.user,
                cls.password,
            ],
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            [
                "mkstore",
                "-wrl",
                cls.temp_dir.name,
                "-createCredential",
                connect_string,
                cls.user,
                cls.password,
            ],
            stdout=subprocess.DEVNULL,
        )
        contents = (
            "WALLET_LOCATION=(SOURCE=(METHOD=FILE)(METHOD_DATA="
            + f"(DIRECTORY={cls.temp_dir.name})))\n"
            + "SQLNET.WALLET_OVERRIDE=TRUE"
        )
        file_name = os.path.join(cls.temp_dir.name, "sqlnet.ora")
        with open(file_name, "w") as f:
            f.write(contents)

    @classmethod
    def _build_tnsnames_config(cls):
        """
        Builds the tnsnames.ora configuration file.
        """
        params = oracledb.ConnectParams()
        params.parse_connect_string(test_env.get_connect_string())
        connect_string = params.get_connect_string()
        file_name = os.path.join(cls.temp_dir.name, "tnsnames.ora")
        with open(file_name, "w") as f:
            f.write(f"{cls.alias_name} = {connect_string}")

    @classmethod
    def _build_user(cls):
        """
        Builds the user credentials stored in the supplied wallet.
        """
        admin_conn = test_env.get_admin_connection()
        with admin_conn.cursor() as cursor:
            try:
                cursor.execute(f"drop user {cls.user} cascade")
            except oracledb.DatabaseError:
                pass
            cursor.execute(
                f"create user {cls.user} identified by " + f"{cls.password}"
            )
            cursor.execute(f"grant create session to {cls.user}")

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls._build_sqlnet_config()
        cls._build_tnsnames_config()
        oracledb.init_oracle_client(config_dir=cls.temp_dir.name)
        cls._build_user()

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_ext_1100(self):
        "E1100 - external authentication with tnsnames alias (implicit)"
        with oracledb.connect(dsn=self.alias_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute("select user from dual")
                (user,) = cursor.fetchone()
                self.assertEqual(user, self.user.upper())

    def test_ext_1101(self):
        "E1101 - external authentication with tnsnames alias (explicit)"
        with oracledb.connect(externalauth=True, dsn=self.alias_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute("select user from dual")
                (user,) = cursor.fetchone()
                self.assertEqual(user, self.user.upper())

    def test_ext_1102(self):
        "E1102 - external authentication with connect string (explicit)"
        with oracledb.connect(
            externalauth=True, dsn=test_env.get_connect_string()
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("select user from dual")
                (user,) = cursor.fetchone()
                self.assertEqual(user, self.user.upper())

    def test_ext_1103(self):
        "E1103 - external authentication with tnsnames alias (explicit)"
        pool = oracledb.create_pool(
            externalauth=True, dsn=self.alias_name, homogeneous=False
        )
        with pool.acquire() as conn:
            with conn.cursor() as cursor:
                cursor.execute("select user from dual")
                (user,) = cursor.fetchone()
                self.assertEqual(user, self.user.upper())

    def test_ext_1104(self):
        "E1104 - external authentication with connect string (explicit)"
        pool = oracledb.create_pool(
            externalauth=True,
            homogeneous=False,
            dsn=test_env.get_connect_string(),
        )
        with pool.acquire() as conn:
            with conn.cursor() as cursor:
                cursor.execute("select user from dual")
                (user,) = cursor.fetchone()
                self.assertEqual(user, self.user.upper())


if __name__ == "__main__":
    test_env.run_test_cases()
