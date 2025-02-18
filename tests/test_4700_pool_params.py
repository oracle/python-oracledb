# -----------------------------------------------------------------------------
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
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
4700 - Module for testing pool parameters.
"""

import ssl

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    requires_connection = False

    def __test_writable_parameter(self, name, value):
        """
        Tests that a writable parameter can be written to and the modified
        value read back successfully.
        """
        params = oracledb.PoolParams()
        orig_value = getattr(params, name)
        copied_params = params.copy()
        args = {}
        args[name] = value
        params.set(**args)
        self.assertEqual(getattr(params, name), value)
        self.assertEqual(getattr(copied_params, name), orig_value)
        args[name] = None
        params.set(**args)
        self.assertEqual(getattr(params, name), value)

    def test_4700(self):
        "4700 - test writable parameters"
        self.__test_writable_parameter("min", 8)
        self.__test_writable_parameter("max", 12)
        self.__test_writable_parameter("increment", 2)
        self.__test_writable_parameter("connectiontype", oracledb.Connection)
        self.__test_writable_parameter("getmode", oracledb.POOL_GETMODE_NOWAIT)
        self.__test_writable_parameter("homogeneous", False)
        self.__test_writable_parameter("timeout", 25)
        self.__test_writable_parameter("wait_timeout", 45)
        self.__test_writable_parameter("max_lifetime_session", 65)
        self.__test_writable_parameter("session_callback", lambda c: None)
        self.__test_writable_parameter("max_sessions_per_shard", 5)
        self.__test_writable_parameter("soda_metadata_cache", True)
        self.__test_writable_parameter("ping_interval", 20)
        self.__test_writable_parameter("ping_timeout", 3000)

    def test_4701(self):
        "4701 - test PoolParams repr()"
        values = [
            ("min", 3),
            ("max", 10),
            ("increment", 4),
            ("connectiontype", oracledb.Connection),
            ("getmode", oracledb.POOL_GETMODE_WAIT),
            ("homogeneous", True),
            ("timeout", 60),
            ("wait_timeout", 20),
            ("max_lifetime_session", 80),
            ("session_callback", lambda c: None),
            ("max_sessions_per_shard", 4),
            ("soda_metadata_cache", False),
            ("ping_interval", 50),
            ("ping_timeout", 2500),
            ("user", test_env.get_main_user()),
            ("proxy_user", test_env.get_proxy_user()),
            ("host", "my_host1"),
            ("port", 1522),
            ("protocol", "tcp"),
            ("https_proxy", "proxy_4701"),
            ("https_proxy_port", 4701),
            ("service_name", "my_service_name1"),
            ("instance_name", "my_instance_name"),
            ("sid", "my_sid1"),
            ("server_type", "dedicated"),
            ("cclass", "cclass_1"),
            ("purity", oracledb.PURITY_SELF),
            ("expire_time", 60),
            ("retry_count", 6),
            ("retry_delay", 10),
            ("tcp_connect_timeout", 40.0),
            ("ssl_server_dn_match", False),
            ("ssl_server_cert_dn", "CN=unknown4701a"),
            ("wallet_location", "/tmp/wallet_loc1a"),
            ("events", True),
            ("externalauth", True),
            ("mode", oracledb.AUTH_MODE_SYSDBA),
            ("disable_oob", True),
            ("stmtcachesize", 25),
            ("edition", "edition_4701"),
            ("tag", "tag4701"),
            ("matchanytag", True),
            ("config_dir", "config_dir_4701"),
            ("appcontext", [("a", "b", "c")]),
            ("shardingkey", [1, 2, 3]),
            ("supershardingkey", [4]),
            ("debug_jdwp", "host=host;port=1523"),
            ("connection_id_prefix", "prefix4701"),
            ("ssl_context", None),
            ("sdu", 16384),
            ("pool_boundary", "transaction"),
            ("use_tcp_fast_open", True),
            ("ssl_version", ssl.TLSVersion.TLSv1_2),
            ("program", "my_program"),
            ("machine", "my_machine"),
            ("terminal", "my_terminal"),
            ("osuser", "me"),
            ("driver_name", "custom_driver"),
            ("use_sni", True),
            ("thick_mode_dsn_passthrough", True),
            ("extra_auth_params", dict(extra1="A", extra2="B")),
        ]
        params = oracledb.PoolParams(**dict(values))
        parts = [f"{name}={value!r}" for name, value in values]
        expected_value = f"PoolParams({', '.join(parts)})"
        self.assertEqual(repr(params), expected_value)
        self.assertIs(params.getmode, oracledb.PoolGetMode.WAIT)

    def test_4702(self):
        "4702 - test extended connect strings for ConnectParams"
        test_scenarios = [
            ("getmode", "NOWAIT", oracledb.POOL_GETMODE_NOWAIT),
            ("homogeneous", "true", True),
            ("homogeneous", "false", False),
            ("increment", "2", 2),
            ("max", "50", 50),
            ("max_lifetime_session", "6000", 6000),
            ("max_sessions_per_shard", "5", 5),
            ("min", "3", 3),
            ("ping_interval", "-1", -1),
            ("ping_timeout", "2500", 2500),
            ("homogeneous", "on", True),
            ("homogeneous", "off", False),
            ("timeout", "3000", 3000),
            ("wait_timeout", "300", 300),
        ]
        host = "host_4702"
        service_name = "service_4702"
        for name, str_value, actual_value in test_scenarios:
            conn_string = f"{host}/{service_name}?pyo.{name}={str_value}"
            with self.subTest(name=name, value=str_value):
                params = oracledb.PoolParams()
                params.parse_connect_string(conn_string)
                self.assertEqual(params.host, host)
                self.assertEqual(params.service_name, service_name)
                self.assertEqual(getattr(params, name), actual_value)


if __name__ == "__main__":
    test_env.run_test_cases()
