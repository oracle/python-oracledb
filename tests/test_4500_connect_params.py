#------------------------------------------------------------------------------
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
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
#------------------------------------------------------------------------------

"""
4500 - Module for testing connection parameters.
"""

import os
import tempfile

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

    def test_4500_simple_easy_connect_with_port(self):
        "4500 - test simple EasyConnect string parsing with port specified"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host:1578/my_service_name")
        self.assertEqual(params.host, "my_host")
        self.assertEqual(params.port, 1578)
        self.assertEqual(params.service_name, "my_service_name")

    def test_4501_simple_easy_connect_without_port(self):
        "4501 - test simple Easy Connect string parsing with no port specified"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host2/my_service_name2")
        self.assertEqual(params.host, "my_host2")
        self.assertEqual(params.port, 1521)
        self.assertEqual(params.service_name, "my_service_name2")

    def test_4502_simple_easy_connect_with_server_type(self):
        "4502 - test simple EasyConnect string parsing with DRCP enabled"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host3.org/my_service_name3:pooled")
        self.assertEqual(params.host, "my_host3.org")
        self.assertEqual(params.service_name, "my_service_name3")
        self.assertEqual(params.server_type, "pooled")
        params.parse_connect_string("my_host3/my_service_name3:ShArEd")
        self.assertEqual(params.server_type, "shared")

    def test_4503_simple_connect_descriptor(self):
        "4503 - test simple name-value pair format connect string"
        connect_string = \
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host4)(PORT=1589))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name4)))"
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.host, "my_host4")
        self.assertEqual(params.port, 1589)
        self.assertEqual(params.service_name, "my_service_name4")

    def test_4504_search_tnsnames(self):
        "4504 - test simple tnsnames entry"
        connect_string = \
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host5)(PORT=1624))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name5)))"
        alias = "tns_alias = " + connect_string
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write(alias)
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string("tns_alias")
        self.assertEqual(params.host, "my_host5")
        self.assertEqual(params.port, 1624)
        self.assertEqual(params.service_name, "my_service_name5")

    def test_4505_easy_connect_with_protocol(self):
        "4505 - test EasyConnect with protocol"
        params = oracledb.ConnectParams()
        params.parse_connect_string("tcps://my_host6/my_service_name6")
        self.assertEqual(params.host, "my_host6")
        self.assertEqual(params.service_name, "my_service_name6")
        self.assertEqual(params.protocol, "tcps")

    def test_4506_easy_connect_with_invalid_protocol(self):
        "4506 - test EasyConnect with invalid protocol"
        params = oracledb.ConnectParams()
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4021:",
                               params.parse_connect_string,
                               "invalid_proto://my_host7/my_service_name7")

    def test_4507_exception_on_ipc_protocol(self):
        "4507 - confirm an exception is raised if using ipc protocol"
        connect_string = \
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=ipc)(KEY=my_view8))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name8)))"
        params = oracledb.ConnectParams()
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4021:",
                               params.parse_connect_string, connect_string)

    def test_4508_retry_count_and_delay(self):
        "4508 - connect descriptor with retry count and retry delay"
        connect_string = \
            "(DESCRIPTION=(RETRY_COUNT=6)(RETRY_DELAY=5)" \
            "(ADDRESS=(PROTOCOL=TCP)(HOST=my_host9)(PORT=1593))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name9)))"
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.retry_count, 6)
        self.assertEqual(params.retry_delay, 5)

    def test_4509_connect_descriptor_expire_time(self):
        "4509 - connect descriptor with expire_time setting"
        connect_string = \
            "(DESCRIPTION=(EXPIRE_TIME=12)" \
            "(ADDRESS=(PROTOCOL=TCP)(HOST=my_host11)(PORT=1594))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name11)))"
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.expire_time, 12)

    def test_4510_pool_parameters(self):
        "4510 - connect descriptor with pool parameters"
        connect_string = \
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host12)(PORT=694))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name12)" \
            "(POOL_CONNECTION_CLASS=cclass_12)(POOL_PURITY=SELF)))"
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        self.assertEqual(params.cclass, "cclass_12")
        self.assertEqual(params.purity, oracledb.PURITY_SELF)
        connect_string = connect_string.replace("SELF", "NEW")
        params.parse_connect_string(connect_string)
        self.assertEqual(params.purity, oracledb.PURITY_NEW)

    def test_4511_invalid_pool_purity(self):
        "4511 - connect descriptor with invalid pool purity"
        connect_string = \
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host13)(PORT=695))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name13)" \
            "(POOL_CONNECTION_CLASS=cclass_13)(POOL_PURITY=INVALID)))"
        params = oracledb.ConnectParams()
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4022:",
                               params.parse_connect_string, connect_string)

    def test_4512_tcp_connect_timeout(self):
        "4512 - connect descriptor with transport connect timeout values"
        connect_string = \
            "(DESCRIPTION=(TRANSPORT_CONNECT_TIMEOUT=500 ms)" \
            "(ADDRESS=(PROTOCOL=TCP)(HOST=my_host14)(PORT=695))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name14)))"
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

    def test_4513_easy_connect_without_service_name(self):
        "4513 - test EasyConnect string parsing with no service name specified"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host15:1578/")
        self.assertEqual(params.host, "my_host15")
        self.assertEqual(params.port, 1578)
        self.assertEqual(params.service_name, "")

    def test_4514_missing_entry_in_tnsnames(self):
        "4514 - test missing entry in tnsnames"
        with tempfile.TemporaryDirectory() as temp_dir:
            params = oracledb.ConnectParams(config_dir=temp_dir)
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write("# no entries")
            self.assertRaisesRegex(oracledb.DatabaseError, "DPY-4000",
                                   params.parse_connect_string, "tns_alias")

    def test_4515_easy_connect_with_port_missing(self):
        "4515 - test EasyConnect string parsing with port value missing"
        params = oracledb.ConnectParams()
        params.parse_connect_string("my_host17:/my_service_name17")
        self.assertEqual(params.host, "my_host17")
        self.assertEqual(params.port, 1521)
        self.assertEqual(params.service_name, "my_service_name17")

    def test_4516_invalid_number_in_connect_string(self):
        "4516 - test connect descriptor with invalid number"
        params = oracledb.ConnectParams()
        connect_string = \
            "(DESCRIPTION=(RETRY_COUNT=wrong)(RETRY_DELAY=5)" \
            "(ADDRESS=(PROTOCOL=TCP)(HOST=my_host18)(PORT=1598))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name18)))"
        self.assertRaisesRegex(oracledb.DatabaseError, "DPY-4018",
                               params.parse_connect_string, connect_string)

    def test_4517_security_options(self):
        "4517 - test connect descriptor with security options"
        options = [
            ("CN=unknown19a", "/tmp/wallet_loc19a", "On", True),
            ("CN=unknown19b", "/tmp/wallet_loc19b", "False", False),
            ("CN=unknown19c", "/tmp/wallet_loc19c", "Off", False),
            ("CN=unknown19d", "/tmp/wallet_loc19d", "True", True),
            ("CN=unknown19e", "/tmp/wallet_loc19e", "yes", True),
            ("CN=unknown19f", "/tmp/wallet_loc19f", "no", False)
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

    def test_4518_easy_connect_security_options(self):
        "4518 - test easy connect string with security options"
        options = [
            ("CN=unknown20a", "/tmp/wallet_loc20a", "On", True),
            ("CN=unknown20b", "/tmp/wallet_loc20b", "False", False),
            ("CN=unknown20c", "/tmp/wallet_loc20c", "Off", False),
            ("CN=unknown20d", "/tmp/wallet_loc20d", "True", True),
            ("CN=unknown20e", "/tmp/wallet_loc20e", "yes", True),
            ("CN=unknown20f", "/tmp/wallet_loc20f", "no", False)
        ]
        for dn, wallet_loc, match_option, match_value in options:
            params = oracledb.ConnectParams()
            connect_string = f'''
                my_host20/my_server_name20?
                ssl_server_cert_dn="{dn}"&
                ssl_server_dn_match= {match_option} &
                wallet_location = "{wallet_loc}"'''
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            self.assertEqual(params.ssl_server_cert_dn, dn)
            self.assertEqual(params.ssl_server_dn_match, match_value)
            self.assertEqual(params.wallet_location, wallet_loc)

    def test_4519_easy_connect_description_options(self):
        "4519 - test easy connect string with description options"
        params = oracledb.ConnectParams()
        connect_string = 'my_host21/my_server_name21?' \
            'expire_time=5&' \
            'retry_delay=10&' \
            'retry_count=12&' \
            'transport_connect_timeout=2.5'
        params.parse_connect_string(connect_string)
        self.assertEqual(params.expire_time, 5)
        self.assertEqual(params.retry_delay, 10)
        self.assertEqual(params.retry_count, 12)
        self.assertEqual(params.tcp_connect_timeout, 2.5)

    def test_4520_easy_connect_invalid_parameters(self):
        "4520 - test easy connect string with invalid parameters"
        params = oracledb.ConnectParams()
        connect_string_prefix = 'my_host22/my_server_name22?'
        suffixes = [
            'expire_time=invalid',
            'expire_time'
        ]
        for suffix in suffixes:
            self.assertRaisesRegex(oracledb.DatabaseError, "DPY-4018",
                                   params.parse_connect_string,
                                   connect_string_prefix + suffix)

    def test_4521_connect_string_with_newlines_and_spaces(self):
        "4521 - test connect string containing spaces and newlines"
        params = oracledb.ConnectParams()
        connect_string = \
            '(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP) \n(HOST=my_host23)\n' \
            '(PORT=1560))(CONNECT_DATA=  (SERVICE_NAME=my_service_name23))' \
            '(SECURITY=(MY_WALLET_DIRECTORY="my wallet dir 23")))'
        params.parse_connect_string(connect_string)
        self.assertEqual(params.host, "my_host23")
        self.assertEqual(params.port, 1560)
        self.assertEqual(params.service_name, "my_service_name23")
        self.assertEqual(params.wallet_location, "my wallet dir 23")

    def test_4522_missing_tnsnames(self):
        "4522 - test missing tnsnames.ora in configuration directory"
        with tempfile.TemporaryDirectory() as temp_dir:
            params = oracledb.ConnectParams(config_dir=temp_dir)
            self.assertRaisesRegex(oracledb.DatabaseError, "DPY-4026:",
                                   params.parse_connect_string, "tns_alias")

    def test_4523_missing_config_dir(self):
        "4523 - test missing configuration directory"
        params = oracledb.ConnectParams(config_dir="/missing")
        self.assertRaisesRegex(oracledb.DatabaseError, "DPY-4026:",
                               params.parse_connect_string, "tns_alias")

    def test_4524_invalid_entries_in_tnsnames(self):
        "4524 - test tnsnames.ora with invalid entries"
        connect_string = \
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host24)(PORT=1148))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name24)))"
        alias = f"tns_alias24 = {connect_string}"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                print("invalid_alias = something to ignore", file=f)
                print("some garbage data which should be ignored", file=f)
                print(alias, file=f)
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string("tns_alias24")
        self.assertEqual(params.host, "my_host24")
        self.assertEqual(params.port, 1148)
        self.assertEqual(params.service_name, "my_service_name24")

    def test_4525_single_address_list(self):
        "4525 - test connect string with an address list"
        params = oracledb.ConnectParams()
        connect_string = \
            '(DESCRIPTION=(LOAD_BALANCE=ON)(RETRY_COUNT=5)(RETRY_DELAY=2)'  \
            '(ADDRESS_LIST=(LOAD_BALANCE=ON)' \
            '(ADDRESS=(PROTOCOL=tcp)(PORT=1521)(HOST=my_host25))' \
            '(ADDRESS=(PROTOCOL=tcps)(PORT=222)(HOST=my_host26)))' \
            '(CONNECT_DATA=(SERVICE_NAME=my_service_name25)))'
        params.parse_connect_string(connect_string)
        self.assertEqual(params.host, ["my_host25", "my_host26"])
        self.assertEqual(params.port, [1521, 222])
        self.assertEqual(params.protocol, ["tcp", "tcps"])
        self.assertEqual(params.service_name, "my_service_name25")
        self.assertEqual(params.retry_count, 5)
        self.assertEqual(params.retry_delay, 2)

    def test_4526_multiple_address_lists(self):
        "4526 - test connect string with multiple address lists"
        params = oracledb.ConnectParams()
        connect_string = \
            '(DESCRIPTION=(LOAD_BALANCE=ON)(RETRY_COUNT=5)(RETRY_DELAY=2)'  \
            '(ADDRESS_LIST=(LOAD_BALANCE=ON)' \
            '(ADDRESS=(PROTOCOL=tcp)(PORT=1521)(HOST=my_host26))' \
            '(ADDRESS=(PROTOCOL=tcp)(PORT=222)(HOST=my_host27)))' \
            '(ADDRESS_LIST=(LOAD_BALANCE=ON)' \
            '(ADDRESS=(PROTOCOL=tcps)(PORT=5555)(HOST=my_host28))' \
            '(ADDRESS=(PROTOCOL=tcps)(PORT=444)(HOST=my_host29)))' \
            '(CONNECT_DATA=(SERVICE_NAME=my_service_name26)))'
        params.parse_connect_string(connect_string)
        hosts = ["my_host26", "my_host27", "my_host28", "my_host29"]
        self.assertEqual(params.host, hosts)
        self.assertEqual(params.port, [1521, 222, 5555, 444])
        self.assertEqual(params.protocol, ["tcp", "tcp", "tcps", "tcps"])
        self.assertEqual(params.service_name, "my_service_name26")
        self.assertEqual(params.retry_count, 5)
        self.assertEqual(params.retry_delay, 2)

    def test_4527_multiple_descriptions(self):
        "4527 - test connect string with multiple descriptions"
        params = oracledb.ConnectParams()
        connect_string = \
            '(DESCRIPTION_LIST=(FAIL_OVER=ON)(LOAD_BALANCE=OFF)' \
            '(DESCRIPTION=(LOAD_BALANCE=OFF)(RETRY_COUNT=1)(RETRY_DELAY=1)' \
            '(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(PORT=5001)' \
            '(HOST=my_host30))' \
            '(ADDRESS=(PROTOCOL=tcp)(PORT=1521)(HOST=my_host31)))' \
            '(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(PORT=5002) ' \
            '(HOST=my_host32))' \
            '(ADDRESS=(PROTOCOL=tcp)(PORT=5003)(HOST=my_host33)))' \
            '(CONNECT_DATA=(SERVICE_NAME=my_service_name27)))' \
            '(DESCRIPTION=(LOAD_BALANCE=OFF)(RETRY_COUNT=2)(RETRY_DELAY=3)' \
            '(ADDRESS_LIST = (ADDRESS=(PROTOCOL=tcp)(PORT=5001)' \
            '(HOST=my_host34))' \
            '(ADDRESS=(PROTOCOL=tcp)(PORT=5001)(HOST=my_host35)))' \
            '(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(PORT=5001)' \
            '(HOST=my_host36))' \
            '(ADDRESS=(PROTOCOL=tcps)(HOST=my_host37)(PORT=1521)))' \
            '(CONNECT_DATA=(SERVICE_NAME=my_service_name28))))'
        params.parse_connect_string(connect_string)
        hosts = ["my_host30", "my_host31", "my_host32", "my_host33", \
                 "my_host34", "my_host35", "my_host36", "my_host37"]
        ports = [5001, 1521, 5002, 5003, 5001, 5001, 5001, 1521]
        protocols = ["tcp", "tcp", "tcp", "tcp", "tcp", "tcp", "tcp", "tcps"]
        service_names = ["my_service_name27", "my_service_name28"]
        self.assertEqual(params.host, hosts)
        self.assertEqual(params.port, ports)
        self.assertEqual(params.protocol, protocols)
        self.assertEqual(params.service_name, service_names)
        self.assertEqual(params.retry_count, [1, 2])
        self.assertEqual(params.retry_delay, [1, 3])

    def test_4528_https_proxy(self):
        "4528 - test connect strings with https_proxy defined"
        params = oracledb.ConnectParams()
        connect_string = \
            "(DESCRIPTION=" \
            "(ADDRESS=(HTTPS_PROXY=proxy_4528a)(HTTPS_PROXY_PORT=4528)" \
            "(PROTOCOL=TCP)(HOST=my_host4528a)(PORT=8528))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name4528a)))"
        params.parse_connect_string(connect_string)
        self.assertEqual(params.https_proxy, "proxy_4528a")
        self.assertEqual(params.https_proxy_port, 4528)
        connect_string = "tcps://my_host_4528b/my_service_name_4528b?" \
                "https_proxy=proxy_4528b&https_proxy_port=9528"
        params.parse_connect_string(connect_string)
        self.assertEqual(params.https_proxy, "proxy_4528b")
        self.assertEqual(params.https_proxy_port, 9528)

    def test_4529_server_type(self):
        "4529 - test connect strings with server_type defined"
        params = oracledb.ConnectParams()
        connect_string = \
            "(DESCRIPTION=" \
            "(ADDRESS=(PROTOCOL=TCP)(HOST=my_host4529)(PORT=4529))" \
            "(CONNECT_DATA=(SERVER=DEDICATED)" \
            "(SERVICE_NAME=my_service_name4529)))"
        params.parse_connect_string(connect_string)
        self.assertEqual(params.server_type, "dedicated")
        connect_string = connect_string.replace("DEDICATED", "INVALID")
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4028:",
                               params.parse_connect_string, connect_string)

    def test_4530_writable_params(self):
        "4530 - test writable parameters"
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

    def test_4531_build_connect_string_with_tcp_connect_timeout(self):
        "4531 - test building connect string with TCP connect timeout"
        host = "my_host4531"
        service_name = "my_service4531"
        options = [
            (25, "25"),
            (120, "2min"),
            (2.5, "2500ms"),
            (3.4328, "3432ms")
        ]
        for in_val, out_val in options:
            params = oracledb.ConnectParams(host=host,
                                            service_name=service_name,
                                            tcp_connect_timeout=in_val)
            tcp_timeout_val = f"(TRANSPORT_CONNECT_TIMEOUT={out_val})"
            connect_string = f"(DESCRIPTION={tcp_timeout_val}" + \
                             f"(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)" + \
                             f"(HOST={host})(PORT=1521)))(CONNECT_DATA=" + \
                             f"(SERVICE_NAME={service_name}))" + \
                             f"(SECURITY=(SSL_SERVER_DN_MATCH=True)))"
            self.assertEqual(params.get_connect_string(), connect_string)

    def test_4532_multiple_alias_entry_tnsnames(self):
        "4532 - test tnsnames.ora with multiple aliases on one line"
        connect_string = \
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host32)(PORT=1132))" \
            "(CONNECT_DATA=(SERVICE_NAME=my_service_name32)))"
        aliases = f"tns_alias32a,tns_alias32b = {connect_string}"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                print(aliases, file=f)
            params = oracledb.ConnectParams(config_dir=temp_dir)
            for name in ("tns_alias32a", "tns_alias32b"):
                params.parse_connect_string(name)
                self.assertEqual(params.host, "my_host32")
                self.assertEqual(params.port, 1132)
                self.assertEqual(params.service_name, "my_service_name32")

if __name__ == "__main__":
    test_env.run_test_cases()
