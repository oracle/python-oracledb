# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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
4500 - Module for testing connection parameters.
"""

import base64
import random
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
        params = oracledb.ConnectParams()
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

    def __verify_network_name_attr(self, name):
        """
        Verify that a network name attribute is handled properly in both valid
        and invalid cases.
        """
        cp = oracledb.ConnectParams()
        self.assertEqual(getattr(cp, name), getattr(oracledb.defaults, name))
        for value, ok in [
            ("valid_value", True),
            ("'contains_quotes'", False),
            ('"contains_double_quotes"', False),
            ("contains_opening_paren (", False),
            ("contains_closing_paren )", False),
            ("contains_equals =", False),
            ("contains_trailing_slash\\", False),
        ]:
            args = {}
            args[name] = value
            if ok:
                cp = oracledb.ConnectParams(**args)
                self.assertEqual(getattr(cp, name), value)
            else:
                with self.assertRaisesFullCode("DPY-3029"):
                    oracledb.ConnectParams(**args)

    def test_4500(self):
        "4500 - test simple EasyConnect string parsing with port specified"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host:1578/my_service_name")
        self.assertEqual(params.host, "my_host")
        self.assertEqual(params.port, 1578)
        self.assertEqual(params.service_name, "my_service_name")

    def test_4501(self):
        "4501 - test simple Easy Connect string parsing with no port specified"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host2/my_service_name2")
        self.assertEqual(params.host, "my_host2")
        self.assertEqual(params.port, 1521)
        self.assertEqual(params.service_name, "my_service_name2")

    def test_4502(self):
        "4502 - test simple EasyConnect string parsing with DRCP enabled"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host3.org/my_service_name3:pooled")
        self.assertEqual(params.host, "my_host3.org")
        self.assertEqual(params.service_name, "my_service_name3")
        self.assertEqual(params.server_type, "pooled")
        params.parse_connect_string("my_host3/my_service_name3:ShArEd")
        self.assertEqual(params.server_type, "shared")

    def test_4503(self):
        "4503 - test simple name-value pair format connect string"
        connect_string = """
            (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host4)(PORT=1589))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name4)))"""
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.host, "my_host4")
        self.assertEqual(params.port, 1589)
        self.assertEqual(params.service_name, "my_service_name4")

    def test_4504(self):
        "4504 - test EasyConnect with protocol"
        params = oracledb.ConnectParams()
        params.parse_connect_string("tcps://my_host6/my_service_name6")
        self.assertEqual(params.host, "my_host6")
        self.assertEqual(params.service_name, "my_service_name6")
        self.assertEqual(params.protocol, "tcps")

    def test_4505(self):
        "4505 - test EasyConnect with invalid protocol"
        params = oracledb.ConnectParams()
        with self.assertRaisesFullCode("DPY-4021"):
            params.parse_connect_string(
                "invalid_proto://my_host7/my_service_name7"
            )

    def test_4506(self):
        "4506 - confirm an exception is raised if using ipc protocol"
        connect_string = """
            (DESCRIPTION=(ADDRESS=(PROTOCOL=ipc)(KEY=my_view8))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name8)))"""
        params = oracledb.ConnectParams()
        with self.assertRaisesFullCode("DPY-4021"):
            params.parse_connect_string(connect_string)

    def test_4507(self):
        "4507 - connect descriptor with retry count and retry delay"
        connect_string = """
            (DESCRIPTION=(RETRY_COUNT=6)(RETRY_DELAY=5)
            (ADDRESS=(PROTOCOL=TCP)(HOST=my_host9)(PORT=1593))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name9)))"""
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.retry_count, 6)
        self.assertEqual(params.retry_delay, 5)

    def test_4508(self):
        "4508 - connect descriptor with expire_time setting"
        connect_string = """
            (DESCRIPTION=(EXPIRE_TIME=12)
            (ADDRESS=(PROTOCOL=TCP)(HOST=my_host11)(PORT=1594))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name11)))
        """
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.expire_time, 12)

    def test_4509(self):
        "4509 - connect descriptor with purity parameters"
        for purity in oracledb.Purity:
            if purity is oracledb.Purity.DEFAULT:
                continue
            cclass = f"cclass_4510_{purity.name}"
            connect_string = f"""
                (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host12)(PORT=694))
                (CONNECT_DATA=(SERVICE_NAME=service_4510)
                (POOL_CONNECTION_CLASS={cclass})
                (POOL_PURITY={purity.name})))"""
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            self.assertEqual(params.cclass, cclass)
            self.assertIs(params.purity, purity)
            gen_connect_string = params.get_connect_string()
            gen_params = oracledb.ConnectParams()
            gen_params.parse_connect_string(gen_connect_string)
            self.assertEqual(gen_params.cclass, cclass)
            self.assertIs(gen_params.purity, purity)

    def test_4510(self):
        "4510 - connect descriptor with invalid pool purity"
        connect_string = """
            (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host13)(PORT=695))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name13)
            (POOL_CONNECTION_CLASS=cclass_13)(POOL_PURITY=INVALID)))"""
        params = oracledb.ConnectParams()
        with self.assertRaisesFullCode("DPY-4022"):
            params.parse_connect_string(connect_string)

    def test_4511(self):
        "4511 - connect descriptor with transport connect timeout values"
        connect_string = """
            (DESCRIPTION=(TRANSPORT_CONNECT_TIMEOUT=500 ms)
            (ADDRESS=(PROTOCOL=TCP)(HOST=my_host14)(PORT=695))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name14)))"""
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.tcp_connect_timeout, 0.5)
        connect_string = connect_string.replace("500 ms", "15 SEC")
        params.parse_connect_string(connect_string)
        self.assertEqual(params.tcp_connect_timeout, 15)
        connect_string = connect_string.replace("15 SEC", "5 min")
        params.parse_connect_string(connect_string)
        self.assertEqual(params.tcp_connect_timeout, 300)
        connect_string = connect_string.replace("5 min", "34")
        params.parse_connect_string(connect_string)
        self.assertEqual(params.tcp_connect_timeout, 34)

    def test_4512(self):
        "4512 - test EasyConnect string parsing with no service name specified"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host15:1578/")
        self.assertEqual(params.host, "my_host15")
        self.assertEqual(params.port, 1578)
        self.assertEqual(params.service_name, None)

    def test_4513(self):
        "4513 - test EasyConnect string parsing with port value missing"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host17:/my_service_name17")
        self.assertEqual(params.host, "my_host17")
        self.assertEqual(params.port, 1521)
        self.assertEqual(params.service_name, "my_service_name17")

    def test_4514(self):
        "4514 - test connect descriptor with invalid number"
        params = oracledb.ConnectParams()
        connect_string = """
            (DESCRIPTION=(RETRY_COUNT=wrong)(RETRY_DELAY=5)
            (ADDRESS=(PROTOCOL=TCP)(HOST=my_host18)(PORT=1598))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name18)))"""
        with self.assertRaisesFullCode("DPY-4018"):
            params.parse_connect_string(connect_string)

    def test_4515(self):
        "4515 - test connect descriptor with security options"
        options = [
            ("CN=unknown19a", "/tmp/wallet_loc19a", "On", True),
            ("CN=unknown19b", "/tmp/wallet_loc19b", "False", False),
            ("CN=unknown19c", "/tmp/wallet_loc19c", "Off", False),
            ("CN=unknown19d", "/tmp/wallet_loc19d", "True", True),
            ("CN=unknown19e", "/tmp/wallet_loc19e", "yes", True),
            ("CN=unknown19f", "/tmp/wallet_loc19f", "no", False),
        ]
        for dn, wallet_loc, match_option, match_value in options:
            params = oracledb.ConnectParams()
            connect_string = f"""
                (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host19)(PORT=872))
                (CONNECT_DATA=(SERVICE_NAME=my_service_name19))
                (SECURITY=(SSL_SERVER_CERT_DN="{dn}")
                (SSL_SERVER_DN_MATCH={match_option})
                (MY_WALLET_DIRECTORY="{wallet_loc}")))"""
            params.parse_connect_string(connect_string)
            self.assertEqual(params.ssl_server_cert_dn, dn)
            self.assertEqual(params.wallet_location, wallet_loc)
            self.assertEqual(params.ssl_server_dn_match, match_value)

    def test_4516(self):
        "4516 - test easy connect string with security options"
        options = [
            ("CN=unknown20a", "/tmp/wallet_loc20a", "On", True),
            ("CN=unknown20b", "/tmp/wallet_loc20b", "False", False),
            ("CN=unknown20c", "/tmp/wallet_loc20c", "Off", False),
            ("CN=unknown20d", "/tmp/wallet_loc20d", "True", True),
            ("CN=unknown20e", "/tmp/wallet_loc20e", "yes", True),
            ("CN=unknown20f", "/tmp/wallet_loc20f", "no", False),
        ]
        for dn, wallet_loc, match_option, match_value in options:
            params = oracledb.ConnectParams()
            connect_string = f"""
                my_host20/my_server_name20?
                ssl_server_cert_dn="{dn}"&
                ssl_server_dn_match= {match_option} &
                wallet_location = "{wallet_loc}" """
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            self.assertEqual(params.ssl_server_cert_dn, dn)
            self.assertEqual(params.ssl_server_dn_match, match_value)
            self.assertEqual(params.wallet_location, wallet_loc)

    def test_4517(self):
        "4517 - test easy connect string with description options"
        params = oracledb.ConnectParams()
        connect_string = """
            my_host21/my_server_name21?
            expire_time=5&
            retry_delay=10&
            retry_count=12&
            transport_connect_timeout=2.5"""
        params.parse_connect_string(connect_string)
        self.assertEqual(params.expire_time, 5)
        self.assertEqual(params.retry_delay, 10)
        self.assertEqual(params.retry_count, 12)
        self.assertEqual(params.tcp_connect_timeout, 2.5)

    def test_4518(self):
        "4518 - test easy connect string with invalid parameters"
        params = oracledb.ConnectParams()
        connect_string_prefix = "my_host22/my_server_name22?"
        suffixes = ["expire_time=invalid", "expire_time"]
        for suffix in suffixes:
            with self.assertRaisesFullCode("DPY-4018"):
                params.parse_connect_string(connect_string_prefix + suffix)

    def test_4519(self):
        "4519 - test connect string containing spaces and newlines"
        params = oracledb.ConnectParams()
        connect_string = """
            (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP) \n(HOST=my_host23)\n
            (PORT=1560))(CONNECT_DATA=  (SERVICE_NAME=my_service_name23))
            (SECURITY=(MY_WALLET_DIRECTORY="my wallet dir 23")))"""
        params.parse_connect_string(connect_string)
        self.assertEqual(params.host, "my_host23")
        self.assertEqual(params.port, 1560)
        self.assertEqual(params.service_name, "my_service_name23")
        self.assertEqual(params.wallet_location, "my wallet dir 23")

    def test_4520(self):
        "4520 - test missing configuration directory"
        params = oracledb.ConnectParams(config_dir="/missing")
        with self.assertRaisesFullCode("DPY-4026"):
            params.parse_connect_string("tns_alias")

    def test_4521(self):
        "4521 - test connect string with an address list"
        params = oracledb.ConnectParams()
        connect_string = (
            "(DESCRIPTION=(LOAD_BALANCE=ON)(RETRY_COUNT=5)(RETRY_DELAY=2)"
            "(ADDRESS_LIST=(LOAD_BALANCE=ON)"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=my_host25)(PORT=4521))"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=my_host26)(PORT=4522)))"
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name25)))"
        )
        params.parse_connect_string(connect_string)
        self.assertEqual(params.host, ["my_host25", "my_host26"])
        self.assertEqual(params.port, [4521, 4522])
        self.assertEqual(params.protocol, ["tcp", "tcp"])
        self.assertEqual(params.service_name, "my_service_name25")
        self.assertEqual(params.retry_count, 5)
        self.assertEqual(params.retry_delay, 2)
        self.assertEqual(params.get_connect_string(), connect_string)

    def test_4522(self):
        "4522 - test connect string with multiple address lists"
        params = oracledb.ConnectParams()
        connect_string = """
            (DESCRIPTION=(LOAD_BALANCE=ON)(RETRY_COUNT=5)(RETRY_DELAY=2)
            (ADDRESS_LIST=(LOAD_BALANCE=ON)
            (ADDRESS=(PROTOCOL=tcp)(PORT=1521)(HOST=my_host26))
            (ADDRESS=(PROTOCOL=tcp)(PORT=222)(HOST=my_host27)))
            (ADDRESS_LIST=(LOAD_BALANCE=ON)
            (ADDRESS=(PROTOCOL=tcps)(PORT=5555)(HOST=my_host28))
            (ADDRESS=(PROTOCOL=tcps)(PORT=444)(HOST=my_host29)))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name26)))"""
        params.parse_connect_string(connect_string)
        hosts = ["my_host26", "my_host27", "my_host28", "my_host29"]
        self.assertEqual(params.host, hosts)
        self.assertEqual(params.port, [1521, 222, 5555, 444])
        self.assertEqual(params.protocol, ["tcp", "tcp", "tcps", "tcps"])
        self.assertEqual(params.service_name, "my_service_name26")
        self.assertEqual(params.retry_count, 5)
        self.assertEqual(params.retry_delay, 2)

    def test_4523(self):
        "4523 - test connect string with multiple descriptions"
        params = oracledb.ConnectParams()
        connect_string = """
            (DESCRIPTION_LIST=(FAIL_OVER=ON)(LOAD_BALANCE=OFF)
            (DESCRIPTION=(LOAD_BALANCE=OFF)(RETRY_COUNT=1)(RETRY_DELAY=1)
            (ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(PORT=5001)
            (HOST=my_host30))
            (ADDRESS=(PROTOCOL=tcp)(PORT=1521)(HOST=my_host31)))
            (ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(PORT=5002)
            (HOST=my_host32))
            (ADDRESS=(PROTOCOL=tcp)(PORT=5003)(HOST=my_host33)))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name27)))
            (DESCRIPTION=(LOAD_BALANCE=OFF)(RETRY_COUNT=2)(RETRY_DELAY=3)
            (ADDRESS_LIST = (ADDRESS=(PROTOCOL=tcp)(PORT=5001)
            (HOST=my_host34))
            (ADDRESS=(PROTOCOL=tcp)(PORT=5001)(HOST=my_host35)))
            (ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(PORT=5001)
            (HOST=my_host36))
            (ADDRESS=(PROTOCOL=tcps)(HOST=my_host37)(PORT=1521)))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name28))))"""
        params.parse_connect_string(connect_string)
        hosts = [
            "my_host30",
            "my_host31",
            "my_host32",
            "my_host33",
            "my_host34",
            "my_host35",
            "my_host36",
            "my_host37",
        ]
        ports = [5001, 1521, 5002, 5003, 5001, 5001, 5001, 1521]
        protocols = ["tcp", "tcp", "tcp", "tcp", "tcp", "tcp", "tcp", "tcps"]
        service_names = ["my_service_name27", "my_service_name28"]
        self.assertEqual(params.host, hosts)
        self.assertEqual(params.port, ports)
        self.assertEqual(params.protocol, protocols)
        self.assertEqual(params.service_name, service_names)
        self.assertEqual(params.retry_count, [1, 2])
        self.assertEqual(params.retry_delay, [1, 3])

    def test_4524(self):
        "4524 - test connect strings with https_proxy defined"
        params = oracledb.ConnectParams()
        connect_string = """
            (DESCRIPTION=
            (ADDRESS=(HTTPS_PROXY=proxy_4528a)(HTTPS_PROXY_PORT=4528)
            (PROTOCOL=TCP)(HOST=my_host4528a)(PORT=8528))
            (CONNECT_DATA=(SERVICE_NAME=my_service_name4528a)))"""
        params.parse_connect_string(connect_string)
        self.assertEqual(params.https_proxy, "proxy_4528a")
        self.assertEqual(params.https_proxy_port, 4528)
        connect_string = """
            tcps://my_host_4528b/my_service_name_4528b?
            https_proxy=proxy_4528b&https_proxy_port=9528"""
        params.parse_connect_string(connect_string)
        self.assertEqual(params.https_proxy, "proxy_4528b")
        self.assertEqual(params.https_proxy_port, 9528)

    def test_4525(self):
        "4525 - test connect strings with server_type defined"
        params = oracledb.ConnectParams()
        connect_string = """
            (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host4529)(PORT=4529))
            (CONNECT_DATA=(SERVER=DEDICATED)
            (SERVICE_NAME=my_service_name4529)))"""
        params.parse_connect_string(connect_string)
        self.assertEqual(params.server_type, "dedicated")
        connect_string = connect_string.replace("DEDICATED", "INVALID")
        with self.assertRaisesFullCode("DPY-4028"):
            params.parse_connect_string(connect_string)

    def test_4526(self):
        "4526 - test writable parameters"
        self.__test_writable_parameter("appcontext", [("a", "b", "c")])
        self.__test_writable_parameter("config_dir", "config_dir_4530")
        self.__test_writable_parameter("disable_oob", True)
        self.__test_writable_parameter("edition", "edition_4530")
        self.__test_writable_parameter("events", True)
        self.__test_writable_parameter("matchanytag", True)
        self.__test_writable_parameter("mode", oracledb.AUTH_MODE_SYSDBA)
        self.__test_writable_parameter("shardingkey", [1, 2, 3])
        self.__test_writable_parameter("stmtcachesize", 25)
        self.__test_writable_parameter("supershardingkey", [1, 2, 3])
        self.__test_writable_parameter("tag", "tag_4530")
        self.__test_writable_parameter("debug_jdwp", "host=host;port=4530")
        self.__test_writable_parameter("externalauth", True)
        self.__test_writable_parameter("user", "USER_1")
        self.__test_writable_parameter("proxy_user", "PROXY_USER_1")

    def test_4527(self):
        "4527 - test building connect string with TCP connect timeout"
        host = "my_host4531"
        service_name = "my_service4531"
        options = [
            (25, "25"),
            (120, "2min"),
            (2.5, "2500ms"),
            (3.4328, "3432ms"),
        ]
        for in_val, out_val in options:
            params = oracledb.ConnectParams(
                host=host,
                service_name=service_name,
                tcp_connect_timeout=in_val,
                retry_delay=0,
            )
            tcp_timeout_val = f"(TRANSPORT_CONNECT_TIMEOUT={out_val})"
            connect_string = (
                f"(DESCRIPTION={tcp_timeout_val}"
                "(ADDRESS=(PROTOCOL=tcp)"
                f"(HOST={host})(PORT=1521))(CONNECT_DATA="
                f"(SERVICE_NAME={service_name})))"
            )
            self.assertEqual(params.get_connect_string(), connect_string)

    def test_4528(self):
        "4528 - test EasyConnect with pool parameters"
        options = [
            ("cclass_33a", "self", oracledb.PURITY_SELF),
            ("cclass_33b", "new", oracledb.PURITY_NEW),
        ]
        for cclass, purity_str, purity_int in options:
            connect_string = f"""
                my_host_33/my_service_name_33:pooled?
                pool_connection_class={cclass}&
                pool_purity={purity_str}"""
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            self.assertEqual(params.host, "my_host_33")
            self.assertEqual(params.service_name, "my_service_name_33")
            self.assertEqual(params.port, 1521)
            self.assertEqual(params.server_type, "pooled")
            self.assertEqual(params.cclass, cclass)
            self.assertEqual(params.purity, purity_int)

    def test_4529(self):
        "4529 - test connect descriptor with different containers (small 1st)"
        connect_string = """
            (DESCRIPTION=
                (ADDRESS=(PROTOCOL=tcp)(HOST=host1)(PORT=1521))
                (ADDRESS_LIST=
                    (ADDRESS=(PROTOCOL=tcp)(HOST=host2a)(PORT=1522))
                    (ADDRESS=(PROTOCOL=tcp)(HOST=host2b)(PORT=1523)))
                (ADDRESS=(PROTOCOL=tcp)(HOST=host3)(PORT=1524))
                (CONNECT_DATA=(SERVICE_NAME=my_service_34)))"""
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.host, ["host1", "host2a", "host2b", "host3"])

    def test_4530(self):
        "4530 - test connect descriptor with different containers (small 2nd)"
        connect_string = """
            (DESCRIPTION=
                (ADDRESS_LIST=
                    (ADDRESS=(PROTOCOL=tcp)(HOST=host1a)(PORT=1532))
                    (ADDRESS=(PROTOCOL=tcp)(HOST=host1b)(PORT=1533)))
                (ADDRESS=(PROTOCOL=tcp)(HOST=host2)(PORT=1534))
                (ADDRESS_LIST=
                    (ADDRESS=(PROTOCOL=tcp)(HOST=host3a)(PORT=1535))
                    (ADDRESS=(PROTOCOL=tcp)(HOST=host3b)(PORT=1536)))
                (CONNECT_DATA=(SERVICE_NAME=my_service_34)))"""
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(
            params.host, ["host1a", "host1b", "host2", "host3a", "host3b"]
        )

    def test_4531(self):
        "4531 - test building connect string with source route designation"
        options = [
            ("on", True),
            ("off", False),
            ("true", True),
            ("false", False),
            ("yes", True),
            ("no", False),
        ]

        for in_val, has_section in options:
            connect_string = f"""
                (DESCRIPTION=
                    (RETRY_DELAY=0)
                    (SOURCE_ROUTE={in_val})
                    (ADDRESS=(PROTOCOL=tcp)(HOST=host1)(PORT=1521))
                    (ADDRESS=(PROTOCOL=tcp)(HOST=host2)(PORT=1522))
                    (CONNECT_DATA=(SERVICE_NAME=my_service_35)))"""
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            source_route_clause = "(SOURCE_ROUTE=ON)" if has_section else ""
            connect_string = (
                f"(DESCRIPTION={source_route_clause}"
                f"(ADDRESS_LIST={source_route_clause}"
                "(ADDRESS=(PROTOCOL=tcp)(HOST=host1)(PORT=1521))"
                "(ADDRESS=(PROTOCOL=tcp)(HOST=host2)(PORT=1522)))"
                "(CONNECT_DATA=(SERVICE_NAME=my_service_35)))"
            )
            self.assertEqual(params.get_connect_string(), connect_string)

    def test_4532(self):
        "4532 - test connect parameters which generate no connect string"
        params = oracledb.ConnectParams()
        self.assertEqual(params.get_connect_string(), None)
        params.set(mode=oracledb.SYSDBA)
        self.assertEqual(params.get_connect_string(), None)

    def test_4533(self):
        "4533 - test parsing a DSN with credentials and a connect string"
        params = oracledb.ConnectParams()
        dsn = "my_user4538/my_password4538@localhost:1525/my_service_name"
        user, password, dsn = params.parse_dsn_with_credentials(dsn)
        self.assertEqual(user, "my_user4538")
        self.assertEqual(password, "my_password4538")
        self.assertEqual(dsn, "localhost:1525/my_service_name")

    def test_4534(self):
        "4534 - test parsing a DSN with only credentials"
        params = oracledb.ConnectParams()
        dsn = "my_user4539/my_password4539"
        user, password, dsn = params.parse_dsn_with_credentials(dsn)
        self.assertEqual(user, "my_user4539")
        self.assertEqual(password, "my_password4539")
        self.assertEqual(dsn, None)

    def test_4535(self):
        "4535 - test parsing a DSN with empty credentials"
        for dsn in ("", "/"):
            params = oracledb.ConnectParams()
            user, password, dsn = params.parse_dsn_with_credentials(dsn)
            self.assertEqual(user, None)
            self.assertEqual(password, None)
            self.assertEqual(dsn, None)

    def test_4536(self):
        "4536 - test parsing a DSN with no credentials"
        dsn_in = "my_alias_4561"
        params = oracledb.ConnectParams()
        user, password, dsn_out = params.parse_dsn_with_credentials(dsn_in)
        self.assertEqual(user, None)
        self.assertEqual(password, None)
        self.assertEqual(dsn_out, dsn_in)

    def test_4537(self):
        "4537 - test connect strings with connection_id_prefix defined"
        params = oracledb.ConnectParams()
        connect_string = """
            (DESCRIPTION=
                (ADDRESS=(PROTOCOL=TCP)(HOST=my_host4562a)(PORT=4562))
                (CONNECT_DATA=(CONNECTION_ID_PREFIX=prefix4562a)
                (SERVICE_NAME=my_service_name4562a)))"""
        params.parse_connect_string(connect_string)
        self.assertEqual(params.connection_id_prefix, "prefix4562a")
        params = oracledb.ConnectParams()
        params.set(connection_id_prefix="prefix4562b")
        params.parse_connect_string("my_host4562b/my_service_name_4562b")
        self.assertEqual(params.connection_id_prefix, "prefix4562b")

    def test_4538(self):
        "4538 - test overriding parameters"
        params = oracledb.ConnectParams()
        host = "my_host_4538"
        port = 3578
        service_name = "my_service_name_4538"
        connect_string = f"{host}:{port}/{service_name}"
        params.parse_connect_string(connect_string)
        self.assertEqual(params.service_name, service_name)
        self.assertEqual(params.port, port)
        new_service_name = "new_service_name_4538"
        new_port = 613
        params.set(service_name=new_service_name, port=new_port)
        self.assertEqual(params.service_name, new_service_name)
        self.assertEqual(params.port, new_port)

    def test_4539(self):
        "4539 - test ConnectParams repr()"
        values = [
            ("user", "USER_1"),
            ("proxy_user", "PROXY_USER_1"),
            ("host", "my_host_1"),
            ("port", 1521),
            ("protocol", "tcp"),
            ("https_proxy", "proxy_a"),
            ("https_proxy_port", 4528),
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
            ("ssl_server_cert_dn", "CN=unknown19a"),
            ("wallet_location", "/tmp/wallet_loc1a"),
            ("events", True),
            ("externalauth", True),
            ("mode", oracledb.AUTH_MODE_SYSDBA),
            ("disable_oob", True),
            ("stmtcachesize", 25),
            ("edition", "edition_4"),
            ("tag", "tag4"),
            ("matchanytag", True),
            ("config_dir", "config_dir_4"),
            ("appcontext", [("a", "b", "c")]),
            ("shardingkey", [1, 2, 3]),
            ("supershardingkey", [4]),
            ("debug_jdwp", "host=host;port=4538"),
            ("connection_id_prefix", "prefix4564"),
            ("ssl_context", None),
            ("sdu", 16384),
            ("pool_boundary", "statement"),
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
        params = oracledb.ConnectParams(**dict(values))
        parts = [f"{name}={value!r}" for name, value in values]
        expected_value = f"ConnectParams({', '.join(parts)})"
        self.assertEqual(repr(params), expected_value)
        self.assertIs(params.purity, oracledb.Purity.SELF)
        self.assertIs(params.mode, oracledb.AuthMode.SYSDBA)
        new_values = [
            ("user", "USER_NEW"),
            ("proxy_user", "PROXY_USER_NEW"),
            ("host", "my_host_new"),
            ("port", 1621),
            ("protocol", "tcps"),
            ("https_proxy", "proxy_b"),
            ("https_proxy_port", 4529),
            ("service_name", "my_service_name_new"),
            ("instance_name", "my_instance_name_new"),
            ("sid", "my_sid_new"),
            ("server_type", "pooled"),
            ("cclass", "cclass_new"),
            ("purity", oracledb.PURITY_NEW),
            ("expire_time", 90),
            ("retry_count", 8),
            ("retry_delay", 15),
            ("tcp_connect_timeout", 15.0),
            ("ssl_server_dn_match", True),
            ("ssl_server_cert_dn", "CN=unknown19_new"),
            ("wallet_location", "/tmp/wallet_loc1_new"),
            ("events", False),
            ("externalauth", False),
            ("mode", oracledb.AUTH_MODE_SYSDGD),
            ("disable_oob", False),
            ("stmtcachesize", 35),
            ("edition", "edition_new"),
            ("tag", "tag_new"),
            ("matchanytag", False),
            ("config_dir", "config_dir_new"),
            ("appcontext", [("a", "b", "c"), ("d", "e", "f")]),
            ("shardingkey", [1, 2, 3, 4]),
            ("supershardingkey", [6]),
            ("debug_jdwp", "host=host;port=4638"),
            ("connection_id_prefix", "prefix4664"),
            ("ssl_context", ssl.create_default_context()),
            ("sdu", 32768),
            ("pool_boundary", "transaction"),
            ("use_tcp_fast_open", False),
            ("ssl_version", ssl.TLSVersion.TLSv1_2),
            ("program", "modified_program"),
            ("machine", "modified_machine"),
            ("terminal", "modified_terminal"),
            ("osuser", "modified_osuser"),
            ("driver_name", "modified_driver_name"),
            ("use_sni", False),
            ("thick_mode_dsn_passthrough", False),
            ("extra_auth_params", dict(extra1="X", extra2="Y")),
        ]
        params.set(**dict(new_values))
        parts = [f"{name}={value!r}" for name, value in new_values]
        expected_value = f"ConnectParams({', '.join(parts)})"
        self.assertEqual(repr(params), expected_value)
        cs_values = dict(
            host="my_host_final",
            service_name="my_service_final",
        )
        connect_string = f"{cs_values['host']}/{cs_values['service_name']}"
        params.parse_connect_string(connect_string)
        final_values = [(n, cs_values.get(n, v)) for n, v in new_values]
        parts = [f"{name}={value!r}" for name, value in final_values]
        expected_value = f"ConnectParams({', '.join(parts)})"
        self.assertEqual(repr(params), expected_value)

    def test_4540(self):
        "4540 - connect descriptor with SDU"
        connect_string = """
            (DESCRIPTION=(SDU=65535)(ADDRESS=(PROTOCOL=TCP)
            (HOST=my_host1)(PORT=1589)))"""
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.sdu, 65535)

    def test_4541(self):
        "4541 - test that SDU is set correctly with invalid sizes"
        params = oracledb.ConnectParams()
        params.set(sdu=random.randint(0, 511))
        self.assertEqual(params.sdu, 512)
        params.set(sdu=2097153)
        self.assertEqual(params.sdu, 2097152)

    def test_4542(self):
        "4542 - test empty connection class"
        params = oracledb.ConnectParams()
        self.assertEqual(params.cclass, None)
        params.set(cclass="")
        self.assertEqual(params.cclass, None)

    def test_4543(self):
        "4543 - test easy connect string with protocol specified"
        protocol = "tcp"
        host = "my_host_4568"
        port = 1668
        service_name = "my_service_4568"
        connect_string = f"{protocol}://{host}:{port}/{service_name}"
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.protocol, protocol)
        self.assertEqual(params.host, host)
        self.assertEqual(params.port, port)
        self.assertEqual(params.service_name, service_name)

    def test_4544(self):
        "4544 - calling set() doesn't clear object parameters"
        sharding_key = [1, 2, 3]
        super_sharding_key = [4, 5, 6]
        app_context = [("NAMESPACE", "KEY", "VALUE")]
        ssl_context = ssl.create_default_context()
        params = oracledb.ConnectParams(
            shardingkey=sharding_key,
            supershardingkey=super_sharding_key,
            appcontext=app_context,
            ssl_context=ssl_context,
        )
        self.assertEqual(params.appcontext, app_context)
        self.assertEqual(params.shardingkey, sharding_key)
        self.assertEqual(params.supershardingkey, super_sharding_key)
        self.assertEqual(params.ssl_context, ssl_context)
        user = "user_4571"
        params.set(user=user)
        self.assertEqual(params.user, user)
        self.assertEqual(params.appcontext, app_context)
        self.assertEqual(params.shardingkey, sharding_key)
        self.assertEqual(params.supershardingkey, super_sharding_key)
        self.assertEqual(params.ssl_context, ssl_context)

    def test_4545(self):
        "4545 - test that use_tcp_fast_open is set correctly"
        params = oracledb.ConnectParams()
        params.set(use_tcp_fast_open=True)
        self.assertTrue(params.use_tcp_fast_open)
        params.set(use_tcp_fast_open=False)
        self.assertFalse(params.use_tcp_fast_open)
        params.set(use_tcp_fast_open="True")
        self.assertTrue(params.use_tcp_fast_open)
        params.set(use_tcp_fast_open="False")
        self.assertFalse(params.use_tcp_fast_open)
        params.set(use_tcp_fast_open=None)
        self.assertFalse(params.use_tcp_fast_open)
        params.set(use_tcp_fast_open=1)
        self.assertTrue(params.use_tcp_fast_open)

    def test_4546(self):
        "4546 - test connect descriptor without addresses defined"
        params = oracledb.ConnectParams()
        host = "host_4546"
        port = 4546
        service_name = "service_name_4546"
        ok_container_names = ("DESCRIPTION", "ADDRESS")
        options = [
            ("DESRIPTION", "ADDRESS"),
            ok_container_names,
            ("DESCRIPTION", "ADRESS"),
        ]
        for option in options:
            desc_name, addr_name = option
            connect_string = (
                f"({desc_name}=({addr_name}=(PROTOCOL=TCP)(HOST={host})"
                f"(PORT={port}))(CONNECT_DATA=(SERVICE_NAME={service_name})))"
            )
            params = oracledb.ConnectParams()
            if option == ok_container_names:
                params.parse_connect_string(connect_string)
                self.assertEqual(params.host, host)
                self.assertEqual(params.port, port)
                self.assertEqual(params.service_name, service_name)
            else:
                with self.assertRaisesFullCode("DPY-2049"):
                    params.parse_connect_string(connect_string)

    def test_4547(self):
        "4547 - test simple EasyConnect string parsing with IPv6 address"
        host = "::1"
        port = 4547
        service_name = "service_name_4547"
        connect_string = f"[{host}]:{port}/{service_name}"
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.host, host)
        self.assertEqual(params.port, port)
        self.assertEqual(params.service_name, service_name)

    def test_4548(self):
        "4548 - test easy connect string with multiple hosts, different ports"
        connect_string = (
            "host4548a,host4548b:4548,host4548c,host4548d:4549/"
            "service_name_4548"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(
            params.host, ["host4548a", "host4548b", "host4548c", "host4548d"]
        )
        self.assertEqual(params.port, [4548, 4548, 4549, 4549])
        self.assertEqual(params.service_name, "service_name_4548")

    def test_4549(self):
        "4549 - test easy connect string with multiple address lists"
        connect_string = (
            "host4549a;host4549b,host4549c:4549;host4549d/service_name_4549"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(
            params.host, ["host4549a", "host4549b", "host4549c", "host4549d"]
        )
        self.assertEqual(params.port, [1521, 4549, 4549, 1521])
        self.assertEqual(params.service_name, "service_name_4549")
        expected_conn_string = (
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=host4549a)(PORT=1521))"
            "(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=host4549b)(PORT=4549))"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=host4549c)(PORT=4549)))"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=host4549d)(PORT=1521))"
            "(CONNECT_DATA=(SERVICE_NAME=service_name_4549)))"
        )
        self.assertEqual(params.get_connect_string(), expected_conn_string)

    def test_4550(self):
        "4550 - test connect descriptor with mixed complex and simple data"
        connect_string = (
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=localhost)(PORT=1521))"
            "(CONNECT_DATA=(SERVER=DEDICATED) SERVICE_NAME=orclpdb1))"
        )
        params = oracledb.ConnectParams()
        with self.assertRaisesFullCode("DPY-4017"):
            params.parse_connect_string(connect_string)

    def test_4551(self):
        "4551 - test connect descriptor with simple data for containers"
        container_names = [
            "address",
            "address_list",
            "connect_data",
            "description",
            "description_list",
            "security",
        ]
        for name in container_names:
            with self.subTest(name=name):
                connect_string = f"({name}=5)"
                params = oracledb.ConnectParams()
                with self.assertRaisesFullCode("DPY-4017"):
                    params.parse_connect_string(connect_string)

    def test_4552(self):
        "4552 - test easy connect string with degenerate protocol"
        host = "host_4552"
        port = 4552
        service_name = "service_name_4552"
        connect_string = f"//{host}:{port}/{service_name}"
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.host, host)
        self.assertEqual(params.port, port)
        self.assertEqual(params.service_name, service_name)

    def test_4553(self):
        "4553 - test easy connect string with registered protocol"
        protocol = "proto-test"
        protocol_arg = "args/for/proto4553"
        host = "host_4553"
        service_name = "service_name_4553"
        connect_string = f"{protocol}://{protocol_arg}"

        def hook(passed_protocol, passed_protocol_arg, passed_params):
            self.assertEqual(passed_protocol, protocol)
            self.assertEqual(passed_protocol_arg, protocol_arg)
            new_connect_string = f"{host}/{service_name}"
            passed_params.parse_connect_string(new_connect_string)

        try:
            oracledb.register_protocol(protocol, hook)
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            self.assertEqual(params.host, host)
            self.assertEqual(params.service_name, service_name)
        finally:
            oracledb.register_protocol(protocol, None)

    def test_4554(self):
        "4554 - test parsing a DSN with a protocol specified"
        dsn_in = "my-protocol://some_arguments_to_protocol"
        params = oracledb.ConnectParams()
        user, password, dsn_out = params.parse_dsn_with_credentials(dsn_in)
        self.assertEqual(user, None)
        self.assertEqual(password, None)
        self.assertEqual(dsn_out, dsn_in)

    def test_4555(self):
        "4555 - test program attribute"
        self.__verify_network_name_attr("program")

    def test_4556(self):
        "4556 - test machine attribute"
        self.__verify_network_name_attr("machine")

    def test_4557(self):
        "4557 - test osuser attribute"
        self.__verify_network_name_attr("osuser")

    def test_4558(self):
        "4558 - test terminal attribute"
        params = oracledb.ConnectParams()
        self.assertEqual(params.terminal, oracledb.defaults.terminal)
        value = "myterminal"
        params = oracledb.ConnectParams(terminal=value)
        self.assertEqual(params.terminal, value)

    def test_4559(self):
        "4559 - test driver_name attribute"
        params = oracledb.ConnectParams()
        self.assertEqual(params.driver_name, oracledb.defaults.driver_name)
        value = "newdriver"
        params = oracledb.ConnectParams(driver_name=value)
        self.assertEqual(params.driver_name, value)

    def test_4560(self):
        "4560 - test register_protocol with invalid hook type"

        def hook1(protocol, protocol_arg, params, extra_invalid_param):
            pass

        def hook2(passed_protocol):
            pass

        protocol = "proto-test"
        try:
            for hook in [hook1, hook2]:
                oracledb.register_protocol(protocol, hook)
                params = oracledb.ConnectParams()
                with self.assertRaisesFullCode("DPY-2056"):
                    params.parse_connect_string(f"{protocol}://args")
        finally:
            oracledb.register_protocol(protocol, None)

    def test_4561(self):
        "4561 - test register_protocol with invalid protocol type"
        with self.assertRaises(TypeError):
            oracledb.register_protocol(1, lambda: None)
        with self.assertRaises(TypeError):
            oracledb.register_protocol("proto", 5)

    def test_4562(self):
        "4562 - test removing unregistered protocol"
        with self.assertRaises(KeyError):
            oracledb.register_protocol("unregistered-protocol", None)

    def test_4563(self):
        "4563 - test restoring pre-registered protocols (tcp and tcps)"

        host = "host_4565"
        port = 4565
        service_name = "service_4565"
        user = "user_4565"

        def hook(passed_protocol, passed_protocol_arg, passed_params):
            passed_params.set(user=user)

        for protocol in ["tcp", "tcps"]:
            try:
                oracledb.register_protocol(protocol, hook)
                connect_string = f"{protocol}://{host}:{port}/{service_name}"
                params = oracledb.ConnectParams()
                params.parse_connect_string(connect_string)
                self.assertEqual(params.user, user)
                self.assertEqual(params.service_name, None)
            finally:
                oracledb.register_protocol(protocol, None)
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            self.assertEqual(params.host, host)
            self.assertEqual(params.port, port)
            self.assertEqual(params.service_name, service_name)

    def test_4564(self):
        "4564 - test extended connect strings for ConnectParams"
        test_scenarios = [
            ("cclass", "test_cclass", "test_cclass"),
            ("connection_id_prefix", "cid_prefix", "cid_prefix"),
            ("disable_oob", "true", True),
            ("disable_oob", "off", False),
            ("driver_name", "test_driver_name", "test_driver_name"),
            ("edition", "test_edition", "test_edition"),
            ("events", "on", True),
            ("events", "false", False),
            ("expire_time", "10", 10),
            ("externalauth", "yes", True),
            ("externalauth", "no", False),
            ("https_proxy", "test_proxy", "test_proxy"),
            ("https_proxy_port", "80", 80),
            ("machine", "test_machine", "test_machine"),
            ("machine", "test_machine", "test_machine"),
            ("mode", "SYSDBA", oracledb.AUTH_MODE_SYSDBA),
            ("osuser", "test_osuser", "test_osuser"),
            ("pool_boundary", "statement", "statement"),
            ("program", "test_program", "test_program"),
            ("purity", "NEW", oracledb.PURITY_NEW),
            ("retry_count", "5", 5),
            ("retry_delay", "3", 3),
            ("sdu", "16384", 16384),
            ("ssl_server_cert_dn", "test_dn", "test_dn"),
            ("ssl_server_dn_match", "on", True),
            ("ssl_server_dn_match", "false", False),
            ("stmtcachesize", "25", 25),
            ("tcp_connect_timeout", "15", 15),
            ("terminal", "test_terminal", "test_terminal"),
            ("use_tcp_fast_open", "true", True),
            ("use_tcp_fast_open", "off", False),
            ("wallet_location", "test_location", "test_location"),
        ]
        host = "host_4564"
        service_name = "service_4564"
        for name, str_value, actual_value in test_scenarios:
            conn_string = f"{host}/{service_name}?pyo.{name}={str_value}"
            with self.subTest(name=name, value=str_value):
                params = oracledb.ConnectParams()
                params.parse_connect_string(conn_string)
                self.assertEqual(params.host, host)
                self.assertEqual(params.service_name, service_name)
                self.assertEqual(getattr(params, name), actual_value)

    def test_4565(self):
        "4565 - test set_from_config() with no user and password set"
        user = "user_4565"
        password = test_env.get_random_string()
        options = [
            ("a", user, password),
            ("b", user, None),
            ("c", None, None),
        ]
        for option, user, password in options:
            with self.subTest(option=option):
                host = f"host_4565{option}"
                service_name = f"service_4565{option}"
                connect_string = f"{host}/{service_name}"
                config = dict(connect_descriptor=connect_string)
                if user is not None:
                    config["user"] = user
                if password is not None:
                    config["password"] = dict(
                        type="base64",
                        value=base64.b64encode(password.encode()).decode(),
                    )
                params = oracledb.ConnectParams()
                params.set_from_config(config)
                self.assertEqual(params.host, host)
                self.assertEqual(params.service_name, service_name)
                if user is not None:
                    self.assertEqual(params.user, user)

    def test_4566(self):
        "4566 - test set_from_config() with user and password already set"
        host = "host_4566"
        service_name = "service_4566"
        connect_string = f"{host}/{service_name}"
        user = "user_4566"
        password = test_env.get_random_string()
        config_user = "user_4566_in_config"
        config_password = test_env.get_random_string()
        config = dict(
            connect_descriptor=connect_string,
            user=config_user,
            password=dict(
                type="base64",
                value=base64.b64encode(config_password.encode()).decode(),
            ),
        )
        params = oracledb.ConnectParams(user=user, password=password)
        params.set_from_config(config)
        self.assertEqual(params.host, host)
        self.assertEqual(params.service_name, service_name)
        self.assertEqual(params.user, user)

    def test_4567(self):
        "4567 - test set_from_config() without connect_descriptor"
        params = oracledb.ConnectParams()
        with self.assertRaisesFullCode("DPY-2059"):
            params.set_from_config(dict(connect_descriptor_missing="missing"))

    def test_4568(self):
        "4568 - test set_from_config() with extended parameters"
        host = "host_4566"
        service_name = "service_4566"
        connect_string = f"{host}/{service_name}"
        stmtcachesize = 35
        user = "user_4566"
        password = test_env.get_random_string()
        config = dict(
            connect_descriptor=connect_string,
            user=user,
            password=dict(
                type="base64",
                value=base64.b64encode(password.encode()).decode(),
            ),
            pyo=dict(stmtcachesize=stmtcachesize),
        )
        params = oracledb.ConnectParams(user=user, password=password)
        params.set_from_config(config)
        self.assertEqual(params.host, host)
        self.assertEqual(params.service_name, service_name)
        self.assertEqual(params.user, user)
        self.assertEqual(params.stmtcachesize, stmtcachesize)

    def test_4569(self):
        "4569 - test USE_SNI in connect string"
        options = [("on", True), ("off", False)]
        service_name = "service_4569"
        host = "host_4569"
        port = 4569
        for str_val, val in options:
            easy_connect = f"{host}:{port}/{service_name}?use_sni={str_val}"
            descriptor_part = f"(USE_SNI={str_val.upper()})" if val else ""
            connect_descriptor = (
                f"(DESCRIPTION={descriptor_part}"
                f"(ADDRESS=(PROTOCOL=tcp)(HOST={host})"
                f"(PORT={port}))(CONNECT_DATA=(SERVICE_NAME={service_name})))"
            )
            for connect_string in (easy_connect, connect_descriptor):
                params = oracledb.ConnectParams()
                params.parse_connect_string(connect_string)
                self.assertEqual(params.host, host)
                self.assertEqual(params.port, port)
                self.assertEqual(params.service_name, service_name)
                self.assertEqual(params.use_sni, val)
            self.assertEqual(params.get_connect_string(), connect_descriptor)

    def test_4570(self):
        "4570 - test passing through unrecognized parameters in CONNECT_DATA"
        options = [
            "(SIMPLE_KEY=SIMPLE_VALUE)",
            "(COMPLEX_KEY=(SUB_VALUE_A=5)(SUB_VALUE_B=6))",
            "(COMPLEX_KEY=(SUB_VALUE_A=5)(SUB_VALUE_B=(SUB_SUB_A=6)))",
        ]
        for option in options:
            with self.subTest(option=option):
                connect_string = (
                    "(DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=host4570)"
                    "(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=service4570)"
                    f"{option}))"
                )
                params = oracledb.ConnectParams()
                params.parse_connect_string(connect_string)
                self.assertEqual(params.get_connect_string(), connect_string)

    def test_4571(self):
        "4571 - test INSTANCE_NAME in connect string"
        service_name = "service_4571"
        instance_name = "instance_4571"
        host = "host_4571"
        port = 4571
        easy_connect = f"{host}:{port}/{service_name}/{instance_name}"
        connect_descriptor = (
            f"(DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST={host})(PORT={port}))"
            f"(CONNECT_DATA=(SERVICE_NAME={service_name})"
            f"(INSTANCE_NAME={instance_name})))"
        )
        for connect_string in (easy_connect, connect_descriptor):
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            self.assertEqual(params.service_name, service_name)
            self.assertEqual(params.instance_name, instance_name)
            self.assertEqual(params.host, host)
            self.assertEqual(params.port, port)
            self.assertEqual(params.get_connect_string(), connect_descriptor)

    def test_4572(self):
        "4572 - test passing through unrecognized parameters in SECURITY"
        options = [
            "(SIMPLE_KEY=SIMPLE_VALUE)",
            "(COMPLEX_KEY=(SUB_VALUE_A=23)(SUB_VALUE_B=27))",
            "(COMPLEX_KEY=(SUB_VALUE_A=A)(SUB_VALUE_B=(SUB_SUB_A=B)))",
        ]
        for option in options:
            with self.subTest(option=option):
                connect_string = (
                    "(DESCRIPTION=(ADDRESS=(PROTOCOL=tcps)(HOST=host4572)"
                    "(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=service4572))"
                    f"(SECURITY=(SSL_SERVER_DN_MATCH=ON){option}))"
                )
                params = oracledb.ConnectParams()
                params.parse_connect_string(connect_string)
                self.assertEqual(params.get_connect_string(), connect_string)

    def test_4573(self):
        "4573 - test passing through unrecognized parameters in DESCRIPTION"
        options = [
            "(SIMPLE_KEY=SIMPLE_VALUE)",
            "(COMPLEX_KEY=(SUB_VALUE_1=1)(SUB_VALUE_B=2))",
            "(COMPLEX_KEY=(SUB_VALUE_2=S)(SUB_VALUE_B=(SUB_SUB_A=T)))",
        ]
        for option in options:
            with self.subTest(option=option):
                connect_string = (
                    "(DESCRIPTION_LIST="
                    f"(DESCRIPTION={option}(ADDRESS=(PROTOCOL=tcp)"
                    "(HOST=host4573a)(PORT=1521))"
                    "(CONNECT_DATA=(SERVICE_NAME=service4573)))"
                    f"(DESCRIPTION={option}(ADDRESS=(PROTOCOL=tcp)"
                    "(HOST=host4573b)(PORT=1521))"
                    "(CONNECT_DATA=(SERVICE_NAME=service4573))))"
                )
                params = oracledb.ConnectParams()
                params.parse_connect_string(connect_string)
                self.assertEqual(params.get_connect_string(), connect_string)

    def test_4574(self):
        "4574 - test passing through specific unsupported parameters"
        easy_connect = (
            "host_4574/service_4574?"
            "enable=broken&recv_buf_size=1024&send_buf_size=2048"
        )
        connect_descriptor = (
            "(DESCRIPTION=(ENABLE=broken)(RECV_BUF_SIZE=1024)"
            "(SEND_BUF_SIZE=2048)(ADDRESS=(PROTOCOL=tcp)(HOST=host_4574)"
            "(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=service_4574)))"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(easy_connect)
        self.assertEqual(params.get_connect_string(), connect_descriptor)

    def test_4575(self):
        "4575 - test syntax rule for keywords"
        for value, ok in [
            ("(SIMPLE_KEY=SIMPLE_VALUE)", True),
            ("(KEY_CONTAINS SPACE=SIMPLE_VALUE)", False),
            ("(∆KEY✓🚀=SIMPLE_VALUE)", False),
            ("(§∞ホスト🔑=SIMPLE_VALUE)", False),
            ("(^MY_KEY_NAME=SIMPLE_VALUE)", False),
            ("(KEY_CONTAINS     TAB=SIMPLE_VALUE)", False),
            ("(KEY_CONTAINS_QUOTES_''=SIMPLE_VALUE)", False),
            ("(KEY_CONTAINS'\r'=SIMPLE_VALUE)", False),
            ("(KEY_CONTAINS'\n'=SIMPLE_VALUE)", False),
        ]:
            with self.subTest(value=value):
                connect_string = (
                    "(DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=host4573)"
                    + "(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=service4573)"
                    + f"{value}))"
                )
                if ok:
                    params = oracledb.ConnectParams()
                    params.parse_connect_string(connect_string)
                    self.assertEqual(
                        params.get_connect_string(), connect_string
                    )
                else:
                    with self.assertRaisesFullCode("DPY-4017"):
                        params.parse_connect_string(connect_string)

    def test_4576(self):
        "4576 - test syntax rule for keywords in easy connect string"
        for value, ok in [
            ("simple_key=simple_value", True),
            ("key_contains space=simple_value", False),
            ("∆key✓🚀=simple_value", False),
            ("^my_key_name=simple_value", False),
            ("key_contains      tab=simple_value", False),
            ("key_contains_quotes_''=simple_value", False),
            ("key_contains'r'=simple_value", False),
            ("key_contains'\n'=simple_value", False),
        ]:
            with self.subTest(value=value):
                easy_connect = f"""host4574:1589/service4574?{value}"""
                connect_string_exp = (
                    "(DESCRIPTION="
                    + "(ADDRESS=(PROTOCOL=tcp)(HOST=host4574)(PORT=1589))"
                    + "(CONNECT_DATA=(SERVICE_NAME=service4574)))"
                )
                if ok:
                    params = oracledb.ConnectParams()
                    params.parse_connect_string(easy_connect)
                    self.assertEqual(params.host, "host4574")
                    self.assertEqual(params.port, 1589)
                    self.assertEqual(params.service_name, "service4574")
                    self.assertEqual(
                        params.get_connect_string(), connect_string_exp
                    )
                else:
                    with self.assertRaisesFullCode("DPY-4018"):
                        params.parse_connect_string(easy_connect)

    def test_4577(self):
        "4577 - test for DESCRIPTION_LIST with FAILOVER"
        connect_string = (
            "(DESCRIPTION_LIST=(FAILOVER=OFF)(LOAD_BALANCE=ON)"
            "(DESCRIPTION=(LOAD_BALANCE=ON)(RETRY_COUNT=1)(RETRY_DELAY=1)"
            "(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=my_host30)(PORT=5001))"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=my_host31)(PORT=1521)))"
            "(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=my_host32)(PORT=5002))"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=my_host32)(PORT=5003)))"
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name27)))"
            "(DESCRIPTION=(LOAD_BALANCE=ON)(RETRY_COUNT=2)(RETRY_DELAY=3)"
            "(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=my_host34)(PORT=5002))"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=my_host35)(PORT=5001)))"
            "(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=my_host36)(PORT=5002))"
            "(ADDRESS=(PROTOCOL=tcps)(HOST=my_host37)(PORT=1521)))"
            "(SECURITY=(SSL_SERVER_DN_MATCH=ON))))"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.get_connect_string(), connect_string)

    def test_4578(self):
        "4578 - test for descriptor parameters in connect descriptor"
        options = [
            ("(FAILOVER=on)", ""),
            ("(FAILOVER=off)", "(FAILOVER=OFF)"),
            ("(FAILOVER=true)", ""),
            ("(FAILOVER=false)", "(FAILOVER=OFF)"),
            ("(FAILOVER=yes)", ""),
            ("(FAILOVER=no)", "(FAILOVER=OFF)"),
            ("(FAILOVER=unsupported_value)", "(FAILOVER=OFF)"),
            ("(FAILOVER=1700)", "(FAILOVER=OFF)"),
            ("(ENABLE=broken)", "(ENABLE=broken)"),
            ("(LOAD_BALANCE=on)", "(LOAD_BALANCE=ON)"),
            ("(LOAD_BALANCE=off)", ""),
            ("(LOAD_BALANCE=true)", "(LOAD_BALANCE=ON)"),
            ("(LOAD_BALANCE=false)", ""),
            ("(LOAD_BALANCE=yes)", "(LOAD_BALANCE=ON)"),
            ("(LOAD_BALANCE=no)", ""),
            ("(LOAD_BALANCE=unsupported_value)", ""),
            ("(LOAD_BALANCE=1700)", ""),
            ("(RECV_BUF_SIZE=87300)", "(RECV_BUF_SIZE=87300)"),
            ("(RECV_BUF_SIZE=11784)", "(RECV_BUF_SIZE=11784)"),
            ("(SEND_BUF_SIZE=87300)", "(SEND_BUF_SIZE=87300)"),
            ("(SEND_BUF_SIZE=11784)", "(SEND_BUF_SIZE=11784)"),
            ("(RECV_TIMEOUT=10)", "(RECV_TIMEOUT=10)"),
            ("(RECV_TIMEOUT=10ms)", "(RECV_TIMEOUT=10ms)"),
            ("(RECV_TIMEOUT=10 ms)", "(RECV_TIMEOUT=10 ms)"),
            ("(RECV_TIMEOUT=10 hr)", "(RECV_TIMEOUT=10 hr)"),
            ("(RECV_TIMEOUT=10 min)", "(RECV_TIMEOUT=10 min)"),
            ("(RECV_TIMEOUT=10 sec)", "(RECV_TIMEOUT=10 sec)"),
            ("(COMPRESSION=on)", "(COMPRESSION=on)"),
            ("(COMPRESSION=off)", "(COMPRESSION=off)"),
            (
                "(COMPRESSION=on)(COMPRESSION_LEVELS=(LEVEL=low))",
                "(COMPRESSION=on)(COMPRESSION_LEVELS=(LEVEL=low))",
            ),
            (
                "(COMPRESSION=on)(COMPRESSION_LEVELS=(LEVEL=high))",
                "(COMPRESSION=on)(COMPRESSION_LEVELS=(LEVEL=high))",
            ),
            (
                "(COMPRESSION=on)(COMPRESSION_LEVELS=(LEVEL=wrong))",
                "(COMPRESSION=on)(COMPRESSION_LEVELS=(LEVEL=wrong))",
            ),
        ]

        service_name = "service_4576"
        host1 = "host_4576_1"
        host2 = "host_4576_2"
        port1 = 45761
        port2 = 45762
        for str_val, exp_val in options:
            with self.subTest(str_val=str_val):
                descriptor_part = str_val
                descriptor_part_exp = exp_val
                connect_descriptor = (
                    f"(DESCRIPTION={descriptor_part}(ADDRESS_LIST="
                    f"(ADDRESS=(PROTOCOL=tcp)(HOST={host1})(PORT={port1}))"
                    f"(ADDRESS=(PROTOCOL=tcp)(HOST={host2})(PORT={port2})))"
                    f"(CONNECT_DATA=(SERVICE_NAME={service_name})))"
                )
                params = oracledb.ConnectParams()
                params.parse_connect_string(connect_descriptor)

                connect_descriptor_exp = (
                    f"(DESCRIPTION={descriptor_part_exp}(ADDRESS_LIST="
                    f"(ADDRESS=(PROTOCOL=tcp)(HOST={host1})(PORT={port1}))"
                    f"(ADDRESS=(PROTOCOL=tcp)(HOST={host2})(PORT={port2})))"
                    f"(CONNECT_DATA=(SERVICE_NAME={service_name})))"
                )

                self.assertEqual(params.host, [host1, host2])
                self.assertEqual(params.port, [port1, port2])
                self.assertEqual(params.service_name, service_name)
                self.assertEqual(
                    params.get_connect_string(), connect_descriptor_exp
                )

    def test_4579(self):
        "4579 - test for connect data parameters in connect descriptor"
        options = [
            "(COLOCATION_TAG=ColocationTag4577)",
            "(COLOCATION_TAG=ColocationTag_4577)",
            "(FAILOVER_MODE=(BACKUP=bhost)(TYPE=session)(METHOD=basic))",
            "(FAILOVER_MODE=(BACKUP=bhost)(TYPE=select)(METHOD=preconnect))",
            "(FAILOVER_MODE=(TYPE=select)(METHOD=basic)(RETRIES=2)(DELAY=15))",
            "(HS=ok)",
            "(TUNNEL_SERVICE_NAME=south)",
        ]

        service_name = "service_4577"
        host = "host_4577"
        port = 4577
        for str_val in options:
            with self.subTest(str_val=str_val):
                connect_data_part = str_val
                connect_descriptor = (
                    f"(DESCRIPTION="
                    f"(ADDRESS=(PROTOCOL=tcp)(HOST={host})(PORT={port}))"
                    f"(CONNECT_DATA=(SERVICE_NAME={service_name})"
                    f"{connect_data_part}))"
                )
                params = oracledb.ConnectParams()
                params.parse_connect_string(connect_descriptor)
                self.assertEqual(params.host, host)
                self.assertEqual(params.port, port)
                self.assertEqual(params.service_name, service_name)
                self.assertEqual(
                    params.get_connect_string(), connect_descriptor
                )

    def test_4580(self):
        "4580 - test for security parameters in connect descriptor"

        security_options = {
            # IGNORE_ANO_ENCRYPTION_FOR_TCPS variations
            "(SECURITY=(IGNORE_ANO_ENCRYPTION_FOR_TCPS=TRUE))": (
                "(SECURITY=(SSL_SERVER_DN_MATCH=ON)"
                "(IGNORE_ANO_ENCRYPTION_FOR_TCPS=TRUE))"
            ),
            "(SECURITY=(IGNORE_ANO_ENCRYPTION_FOR_TCPS=FALSE))": (
                "(SECURITY=(SSL_SERVER_DN_MATCH=ON)"
                "(IGNORE_ANO_ENCRYPTION_FOR_TCPS=FALSE))"
            ),
            "(SECURITY=(SSL_SERVER_DN_MATCH=false)"
            "(IGNORE_ANO_ENCRYPTION_FOR_TCPS=FALSE))": (
                "(SECURITY=(IGNORE_ANO_ENCRYPTION_FOR_TCPS=FALSE))"
            ),
            # KERBEROS5_CC_NAME and KERBEROS5_PRINCIPAL variations
            "(SECURITY=(KERBEROS5_CC_NAME=/tmp/krbuser2/krb.cc)"
            "(KERBEROS5_PRINCIPAL=krbprinc2@example.com))": (
                "(SECURITY=(SSL_SERVER_DN_MATCH=ON)"
                "(KERBEROS5_CC_NAME=/tmp/krbuser2/krb.cc)"
                "(KERBEROS5_PRINCIPAL=krbprinc2@example.com))"
            ),
            # SSL_SERVER_CERT_DN and SSL_SERVER_DN_MATCH variations
            "(SECURITY=(SSL_SERVER_DN_MATCH=on)"
            "(SSL_SERVER_CERT_DN=CN=unknown19a)"
            "(MY_WALLET_DIRECTORY=/tmp/wallet_loc19a))": (
                "(SECURITY=(SSL_SERVER_DN_MATCH=ON)"
                "(SSL_SERVER_CERT_DN=CN=unknown19a)"
                "(MY_WALLET_DIRECTORY=/tmp/wallet_loc19a))"
            ),
            "(SECURITY=(SSL_SERVER_DN_MATCH=false)"
            "(SSL_SERVER_CERT_DN=CN=unknown19a)"
            "(MY_WALLET_DIRECTORY=/tmp/wallet_loc19a))": (
                "(SECURITY=(SSL_SERVER_CERT_DN=CN=unknown19a)"
                "(MY_WALLET_DIRECTORY=/tmp/wallet_loc19a))"
            ),
            "(SECURITY=(SSL_SERVER_DN_MATCH=wrong)"
            "(SSL_SERVER_CERT_DN=CN=unknown19a)"
            "(MY_WALLET_DIRECTORY=/tmp/wallet_loc19a))": (
                "(SECURITY=(SSL_SERVER_CERT_DN=CN=unknown19a)"
                "(MY_WALLET_DIRECTORY=/tmp/wallet_loc19a))"
            ),
        }

        service_name = "service_4578"
        host = "host_4578"
        port = 4578
        for str_val, exp_val in security_options.items():
            with self.subTest(str_val=str_val):
                security_part = str_val
                security_part_exp = exp_val
                connect_descriptor = (
                    f"(DESCRIPTION="
                    f"(ADDRESS=(PROTOCOL=tcps)(HOST={host})(PORT={port}))"
                    f"(CONNECT_DATA=(SERVICE_NAME={service_name}))"
                    f"{security_part})"
                )
                params = oracledb.ConnectParams()
                params.parse_connect_string(connect_descriptor)
                connect_descriptor_exp = (
                    f"(DESCRIPTION="
                    f"(ADDRESS=(PROTOCOL=tcps)(HOST={host})(PORT={port}))"
                    f"(CONNECT_DATA=(SERVICE_NAME={service_name}))"
                    f"{security_part_exp})"
                )
                self.assertEqual(params.host, host)
                self.assertEqual(params.port, port)
                self.assertEqual(params.service_name, service_name)
                self.assertEqual(
                    params.get_connect_string(), connect_descriptor_exp
                )

    def test_4581(self):
        "4581 - test for parameters supported in easy connect descriptor"
        options = [
            ("retry_count=3&retry_delay=6", "(RETRY_COUNT=3)(RETRY_DELAY=6)"),
            ("enable=broken", "(ENABLE=broken)"),
            ("failover=on", ""),
            ("failover=off", "(FAILOVER=OFF)"),
            ("failover=true", ""),
            ("failover=false", "(FAILOVER=OFF)"),
            ("failover=yes", ""),
            ("failover=no", "(FAILOVER=OFF)"),
            ("failover=unsupported_value", "(FAILOVER=OFF)"),
            ("failover=1700", "(FAILOVER=OFF)"),
            ("load_balance=on", "(LOAD_BALANCE=ON)"),
            ("load_balance=off", ""),
            ("load_balance=true", "(LOAD_BALANCE=ON)"),
            ("load_balance=false", ""),
            ("load_balance=yes", "(LOAD_BALANCE=ON)"),
            ("load_balance=no", ""),
            ("load_balance=unsupported_value", ""),
            ("load_balance=1700", ""),
            ("recv_buf_size=87300", "(RECV_BUF_SIZE=87300)"),
            ("send_buf_size=11786", "(SEND_BUF_SIZE=11786)"),
            ("sdu=16384", "(SDU=16384)"),
            ("retry_count=6", "(RETRY_COUNT=6)(RETRY_DELAY=1)"),
            ("source_route=on", "(SOURCE_ROUTE=ON)"),
            ("source_route=true", "(SOURCE_ROUTE=ON)"),
            ("source_route=yes", "(SOURCE_ROUTE=ON)"),
            ("source_route=off", ""),
            ("source_route=false", ""),
            ("source_route=no", ""),
            ("source_route=wrong", ""),
            (
                "transport_connect_timeout=100",
                "(TRANSPORT_CONNECT_TIMEOUT=100)",
            ),
            (
                "transport_connect_timeout=500ms",
                "(TRANSPORT_CONNECT_TIMEOUT=500ms)",
            ),
        ]

        service_name = "service_4579"
        host = "host_4579"
        port = 4579
        for str_val, exp_str in options:
            with self.subTest(str_val=str_val):
                descriptor_part = exp_str
                easy_connect = f"""{host}:{port}/{service_name}?{str_val}"""
                connect_descriptor_exp = (
                    f"(DESCRIPTION={descriptor_part}"
                    f"(ADDRESS=(PROTOCOL=tcp)(HOST={host})(PORT={port}))"
                    f"(CONNECT_DATA=(SERVICE_NAME={service_name})))"
                )
                params = oracledb.ConnectParams()
                params.parse_connect_string(easy_connect)
                self.assertEqual(params.host, host)
                self.assertEqual(params.port, port)
                self.assertEqual(params.service_name, service_name)
                self.assertEqual(
                    params.get_connect_string(), connect_descriptor_exp
                )

    def test_4582(self):
        "4582 - test for security parameters in easy connect descriptor"
        service_name = "service_4580"
        srvc_str = (
            "ssl_server_dn_match=true"
            "&ssl_server_cert_dn='cn=sales,cn=OracleContext,"
            "dc=us,dc=example,dc=com'"
            "&wallet_location='/tmp/oracle'"
        )
        host = "host_4580"
        port = 4580
        easy_connect = f"tcps://{host}:{port}/{service_name}?{srvc_str}"
        connect_descriptor_exp = (
            f"(DESCRIPTION="
            f"(ADDRESS=(PROTOCOL=tcps)(HOST={host})"
            f"(PORT={port}))"
            f"(CONNECT_DATA=(SERVICE_NAME={service_name}))"
            "(SECURITY=(SSL_SERVER_DN_MATCH=ON)"
            "(SSL_SERVER_CERT_DN='cn=sales,cn=OracleContext,"
            "dc=us,dc=example,dc=com')"
            "(MY_WALLET_DIRECTORY='/tmp/oracle')))"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(easy_connect)
        self.assertEqual(params.host, host)
        self.assertEqual(params.port, port)
        self.assertEqual(params.service_name, service_name)
        self.assertEqual(params.get_connect_string(), connect_descriptor_exp)

    def test_4583(self):
        "4583 - test for TYPE_OF_SERVICE, RDB_DATABASE, GLOBAL_NAME parameters"
        connect_string = (
            "(DESCRIPTION_LIST="
            "(DESCRIPTION=(TYPE_OF_SERVICE=rdb_database)"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=my_host94_1)(PORT=5002))"
            "(CONNECT_DATA="
            "(SERVICE_NAME=generic)"
            "(RDB_DATABASE=[.mf]mf_personal.rdb)"
            "(GLOBAL_NAME=alpha5)))"
            "(DESCRIPTION=(TYPE_OF_SERVICE=oracle11_database)"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=my_host94_2)(PORT=5003))"
            "(CONNECT_DATA="
            "(SERVICE_NAME=sales.us.example.com))))"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.get_connect_string(), connect_string)


if __name__ == "__main__":
    test_env.run_test_cases()
