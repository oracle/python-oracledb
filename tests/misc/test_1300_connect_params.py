# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2026, Oracle and/or its affiliates.
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
Module for testing connection parameters.
"""

import base64
import random
import ssl

import oracledb
import pytest


def _test_writable_parameter(name, value):
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
    assert getattr(params, name) == value
    assert getattr(copied_params, name) == orig_value
    args[name] = None
    params.set(**args)
    assert getattr(params, name) == value


def _verify_network_name_attr(test_env, name):
    """
    Verify that a network name attribute is handled properly in both valid
    and invalid cases.
    """
    cp = oracledb.ConnectParams()
    assert getattr(cp, name) == getattr(oracledb.defaults, name)
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
            assert getattr(cp, name) == value
        else:
            with test_env.assert_raises_full_code("DPY-3029"):
                oracledb.ConnectParams(**args)


def test_misc_1300():
    "1300 - test simple EasyConnect string parsing with port specified"
    params = oracledb.ConnectParams()
    params.parse_connect_string("my_host:1578/my_service_name")
    assert params.host == "my_host"
    assert params.port == 1578
    assert params.service_name == "my_service_name"


def test_misc_1301():
    "1301 - test simple Easy Connect string parsing with no port specified"
    params = oracledb.ConnectParams()
    params.parse_connect_string("my_host2/my_service_name2")
    assert params.host == "my_host2"
    assert params.port == 1521
    assert params.service_name == "my_service_name2"


def test_misc_1302():
    "1302 - test simple EasyConnect string parsing with DRCP enabled"
    params = oracledb.ConnectParams()
    params.parse_connect_string("my_host3.org/my_service_name3:pooled")
    assert params.host == "my_host3.org"
    assert params.service_name == "my_service_name3"
    assert params.server_type == "pooled"
    params.parse_connect_string("my_host3/my_service_name3:ShArEd")
    assert params.server_type == "shared"


def test_misc_1303():
    "1303 - test simple name-value pair format connect string"
    connect_string = """
        (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host4)(PORT=1589))
        (CONNECT_DATA=(SERVICE_NAME=my_service_name4)))"""
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.host == "my_host4"
    assert params.port == 1589
    assert params.service_name == "my_service_name4"


def test_misc_1304():
    "1304 - test EasyConnect with protocol"
    params = oracledb.ConnectParams()
    params.parse_connect_string("tcps://my_host6/my_service_name6")
    assert params.host == "my_host6"
    assert params.service_name == "my_service_name6"
    assert params.protocol == "tcps"


def test_misc_1305(test_env):
    "1305 - test EasyConnect with invalid protocol"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-4021"):
        params.parse_connect_string(
            "invalid_proto://my_host7/my_service_name7"
        )


def test_misc_1306(test_env):
    "1306 - confirm an exception is raised if using ipc protocol"
    connect_string = """
        (DESCRIPTION=(ADDRESS=(PROTOCOL=ipc)(KEY=my_view8))
        (CONNECT_DATA=(SERVICE_NAME=my_service_name8)))"""
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-4021"):
        params.parse_connect_string(connect_string)


def test_misc_1307():
    "1307 - connect descriptor with retry count and retry delay"
    connect_string = """
        (DESCRIPTION=(RETRY_COUNT=6)(RETRY_DELAY=5)
        (ADDRESS=(PROTOCOL=TCP)(HOST=my_host9)(PORT=1593))
        (CONNECT_DATA=(SERVICE_NAME=my_service_name9)))"""
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.retry_count == 6
    assert params.retry_delay == 5


def test_misc_1308():
    "1308 - connect descriptor with expire_time setting"
    connect_string = """
        (DESCRIPTION=(EXPIRE_TIME=12)
        (ADDRESS=(PROTOCOL=TCP)(HOST=my_host11)(PORT=1594))
        (CONNECT_DATA=(SERVICE_NAME=my_service_name11)))
    """
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.expire_time == 12


def test_misc_1309():
    "1309 - connect descriptor with purity parameters"
    for purity in oracledb.Purity:
        if purity is oracledb.Purity.DEFAULT:
            continue
        cclass = f"cclass_1309_{purity.name}"
        connect_string = f"""
            (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host12)(PORT=694))
            (CONNECT_DATA=(SERVICE_NAME=service_1309)
            (POOL_CONNECTION_CLASS={cclass})
            (POOL_PURITY={purity.name})))"""
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        assert params.cclass == cclass
        assert params.purity is purity
        gen_connect_string = params.get_connect_string()
        gen_params = oracledb.ConnectParams()
        gen_params.parse_connect_string(gen_connect_string)
        assert gen_params.cclass == cclass
        assert gen_params.purity is purity


def test_misc_1310(test_env):
    "1310 - connect descriptor with invalid pool purity"
    connect_string = """
        (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host13)(PORT=695))
        (CONNECT_DATA=(SERVICE_NAME=my_service_name13)
        (POOL_CONNECTION_CLASS=cclass_13)(POOL_PURITY=INVALID)))"""
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-4022"):
        params.parse_connect_string(connect_string)


def test_misc_1311():
    "1311 - connect descriptor with transport connect timeout values"
    connect_string = """
        (DESCRIPTION=(TRANSPORT_CONNECT_TIMEOUT=500 ms)
        (ADDRESS=(PROTOCOL=TCP)(HOST=my_host14)(PORT=695))
        (CONNECT_DATA=(SERVICE_NAME=my_service_name14)))"""
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.tcp_connect_timeout == 0.5
    connect_string = connect_string.replace("500 ms", "15 SEC")
    params.parse_connect_string(connect_string)
    assert params.tcp_connect_timeout == 15
    connect_string = connect_string.replace("15 SEC", "5 min")
    params.parse_connect_string(connect_string)
    assert params.tcp_connect_timeout == 300
    connect_string = connect_string.replace("5 min", "34")
    params.parse_connect_string(connect_string)
    assert params.tcp_connect_timeout == 34


def test_misc_1312():
    "1312 - test EasyConnect string parsing with no service name specified"
    params = oracledb.ConnectParams()
    params.parse_connect_string("my_host15:1578/")
    assert params.host == "my_host15"
    assert params.port == 1578
    assert params.service_name is None


def test_misc_1313():
    "1313 - test EasyConnect string parsing with port value missing"
    params = oracledb.ConnectParams()
    params.parse_connect_string("my_host17:/my_service_name17")
    assert params.host == "my_host17"
    assert params.port == 1521
    assert params.service_name == "my_service_name17"


def test_misc_1314(test_env):
    "1314 - test connect descriptor with invalid number"
    params = oracledb.ConnectParams()
    connect_string = """
        (DESCRIPTION=(RETRY_COUNT=wrong)(RETRY_DELAY=5)
        (ADDRESS=(PROTOCOL=TCP)(HOST=my_host18)(PORT=1598))
        (CONNECT_DATA=(SERVICE_NAME=my_service_name18)))"""
    with test_env.assert_raises_full_code("DPY-4018"):
        params.parse_connect_string(connect_string)


def test_misc_1315():
    "1315 - test connect descriptor with security options"
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
        assert params.ssl_server_cert_dn == dn
        assert params.wallet_location == wallet_loc
        assert params.ssl_server_dn_match == match_value


def test_misc_1316():
    "1316 - test easy connect string with security options"
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
        assert params.ssl_server_cert_dn == dn
        assert params.ssl_server_dn_match == match_value
        assert params.wallet_location == wallet_loc


def test_misc_1317():
    "1317 - test easy connect string with description options"
    params = oracledb.ConnectParams()
    connect_string = """
        my_host21/my_server_name21?
        expire_time=5&
        retry_delay=10&
        retry_count=12&
        transport_connect_timeout=2.5"""
    params.parse_connect_string(connect_string)
    assert params.expire_time == 5
    assert params.retry_delay == 10
    assert params.retry_count == 12
    assert params.tcp_connect_timeout == 2.5


def test_misc_1318(test_env):
    "1318 - test easy connect string with invalid parameters"
    params = oracledb.ConnectParams()
    connect_string_prefix = "my_host22/my_server_name22?"
    suffixes = ["expire_time=invalid", "expire_time"]
    for suffix in suffixes:
        with test_env.assert_raises_full_code("DPY-4018"):
            params.parse_connect_string(connect_string_prefix + suffix)


def test_misc_1319():
    "1319 - test connect string containing spaces and newlines"
    params = oracledb.ConnectParams()
    connect_string = """
        (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP) \n(HOST=my_host23)\n
        (PORT=1560))(CONNECT_DATA=  (SERVICE_NAME=my_service_name23))
        (SECURITY=(MY_WALLET_DIRECTORY="my wallet dir 23")))"""
    params.parse_connect_string(connect_string)
    assert params.host == "my_host23"
    assert params.port == 1560
    assert params.service_name == "my_service_name23"
    assert params.wallet_location == "my wallet dir 23"


def test_misc_1320(test_env):
    "1320 - test missing configuration directory"
    params = oracledb.ConnectParams(config_dir="/missing")
    with test_env.assert_raises_full_code("DPY-4026"):
        params.parse_connect_string("tns_alias")


def test_misc_1321():
    "1321 - test connect string with an address list"
    params = oracledb.ConnectParams()
    connect_string = (
        "(DESCRIPTION=(LOAD_BALANCE=ON)(RETRY_COUNT=5)(RETRY_DELAY=2)"
        "(ADDRESS_LIST=(LOAD_BALANCE=ON)"
        "(ADDRESS=(PROTOCOL=tcp)(HOST=my_host25)(PORT=1321))"
        "(ADDRESS=(PROTOCOL=tcp)(HOST=my_host26)(PORT=1322)))"
        "(CONNECT_DATA=(SERVICE_NAME=my_service_name25)))"
    )
    params.parse_connect_string(connect_string)
    assert params.host == ["my_host25", "my_host26"]
    assert params.port == [1321, 1322]
    assert params.protocol == ["tcp", "tcp"]
    assert params.service_name == "my_service_name25"
    assert params.retry_count == 5
    assert params.retry_delay == 2
    assert params.get_connect_string() == connect_string


def test_misc_1322():
    "1322 - test connect string with multiple address lists"
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
    assert params.host == hosts
    assert params.port == [1521, 222, 5555, 444]
    assert params.protocol == ["tcp", "tcp", "tcps", "tcps"]
    assert params.service_name == "my_service_name26"
    assert params.retry_count == 5
    assert params.retry_delay == 2


def test_misc_1323():
    "1323 - test connect string with multiple descriptions"
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
    assert params.host == hosts
    assert params.port == ports
    assert params.protocol == protocols
    assert params.service_name == service_names
    assert params.retry_count == [1, 2]
    assert params.retry_delay == [1, 3]


def test_misc_1324():
    "1324 - test connect strings with https_proxy defined"
    params = oracledb.ConnectParams()
    connect_string = """
        (DESCRIPTION=
        (ADDRESS=(HTTPS_PROXY=proxy_1324a)(HTTPS_PROXY_PORT=1324)
        (PROTOCOL=TCP)(HOST=my_host1324a)(PORT=8524))
        (CONNECT_DATA=(SERVICE_NAME=my_service_name1324a)))"""
    params.parse_connect_string(connect_string)
    assert params.https_proxy == "proxy_1324a"
    assert params.https_proxy_port == 1324
    connect_string = """
        tcps://my_host_1324b/my_service_name_1324b?
        https_proxy=proxy_1324b&https_proxy_port=9524"""
    params.parse_connect_string(connect_string)
    assert params.https_proxy == "proxy_1324b"
    assert params.https_proxy_port == 9524


def test_misc_1325(test_env):
    "1325 - test connect strings with server_type defined"
    params = oracledb.ConnectParams()
    connect_string = """
        (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=my_host1325)(PORT=1325))
        (CONNECT_DATA=(SERVER=DEDICATED)
        (SERVICE_NAME=my_service_name1325)))"""
    params.parse_connect_string(connect_string)
    assert params.server_type == "dedicated"
    connect_string = connect_string.replace("DEDICATED", "INVALID")
    with test_env.assert_raises_full_code("DPY-4028"):
        params.parse_connect_string(connect_string)


def test_misc_1326():
    "1326 - test writable parameters"
    _test_writable_parameter("appcontext", [("a", "b", "c")])
    _test_writable_parameter("config_dir", "config_dir_1326")
    _test_writable_parameter("disable_oob", True)
    _test_writable_parameter("edition", "edition_1326")
    _test_writable_parameter("events", True)
    _test_writable_parameter("matchanytag", True)
    _test_writable_parameter("mode", oracledb.AUTH_MODE_SYSDBA)
    _test_writable_parameter("shardingkey", [1, 2, 3])
    _test_writable_parameter("stmtcachesize", 25)
    _test_writable_parameter("supershardingkey", [1, 2, 3])
    _test_writable_parameter("tag", "tag_1326")
    _test_writable_parameter("debug_jdwp", "host=host;port=1326")
    _test_writable_parameter("externalauth", True)
    _test_writable_parameter("user", "USER_1")
    _test_writable_parameter("proxy_user", "PROXY_USER_1")


def test_misc_1327():
    "1327 - test building connect string with TCP connect timeout"
    host = "my_host1327"
    service_name = "my_service1327"
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
        assert params.get_connect_string() == connect_string


def test_misc_1328():
    "1328 - test EasyConnect with pool parameters"
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
        assert params.host == "my_host_33"
        assert params.service_name == "my_service_name_33"
        assert params.port == 1521
        assert params.server_type == "pooled"
        assert params.cclass == cclass
        assert params.purity == purity_int


def test_misc_1329():
    "1329 - test connect descriptor with different containers (small 1st)"
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
    assert params.host == ["host1", "host2a", "host2b", "host3"]


def test_misc_1330():
    "1330 - test connect descriptor with different containers (small 2nd)"
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
    assert params.host == ["host1a", "host1b", "host2", "host3a", "host3b"]


def test_misc_1331():
    "1331 - test building connect string with source route designation"
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
            f"(DESCRIPTION=(ADDRESS_LIST={source_route_clause}"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=host1)(PORT=1521))"
            "(ADDRESS=(PROTOCOL=tcp)(HOST=host2)(PORT=1522)))"
            "(CONNECT_DATA=(SERVICE_NAME=my_service_35)))"
        )
        assert params.get_connect_string() == connect_string


def test_misc_1332():
    "1332 - test connect parameters which generate no connect string"
    params = oracledb.ConnectParams()
    assert params.get_connect_string() is None
    params.set(mode=oracledb.SYSDBA)
    assert params.get_connect_string() is None


def test_misc_1333():
    "1333 - test parsing a DSN with credentials and a connect string"
    params = oracledb.ConnectParams()
    dsn = "my_user1333/my_password1333@localhost:1525/my_service_name"
    user, password, dsn = params.parse_dsn_with_credentials(dsn)
    assert user == "my_user1333"
    assert password == "my_password1333"
    assert dsn == "localhost:1525/my_service_name"


def test_misc_1334():
    "1334 - test parsing a DSN with only credentials"
    params = oracledb.ConnectParams()
    dsn = "my_user1334/my_password1334"
    user, password, dsn = params.parse_dsn_with_credentials(dsn)
    assert user == "my_user1334"
    assert password == "my_password1334"
    assert dsn is None


def test_misc_1335():
    "1335 - test parsing a DSN with empty credentials"
    for dsn in ("", "/"):
        params = oracledb.ConnectParams()
        user, password, dsn = params.parse_dsn_with_credentials(dsn)
        assert user is None
        assert password is None
        assert dsn is None


def test_misc_1336():
    "1336 - test parsing a DSN with no credentials"
    dsn_in = "my_alias_1336"
    params = oracledb.ConnectParams()
    user, password, dsn_out = params.parse_dsn_with_credentials(dsn_in)
    assert user is None
    assert password is None
    assert dsn_out == dsn_in


def test_misc_1337():
    "1337 - test connect strings with connection_id_prefix defined"
    params = oracledb.ConnectParams()
    connect_string = """
        (DESCRIPTION=
            (ADDRESS=(PROTOCOL=TCP)(HOST=my_host1337a)(PORT=1337))
            (CONNECT_DATA=(CONNECTION_ID_PREFIX=prefix1337a)
            (SERVICE_NAME=my_service_name1337a)))"""
    params.parse_connect_string(connect_string)
    assert params.connection_id_prefix == "prefix1337a"
    params = oracledb.ConnectParams()
    params.set(connection_id_prefix="prefix1337b")
    params.parse_connect_string("my_host1337b/my_service_name_1337b")
    assert params.connection_id_prefix == "prefix1337b"


def test_misc_1338():
    "1338 - test overriding parameters"
    params = oracledb.ConnectParams()
    host = "my_host_1338"
    port = 3578
    service_name = "my_service_name_1338"
    connect_string = f"{host}:{port}/{service_name}"
    params.parse_connect_string(connect_string)
    assert params.service_name == service_name
    assert params.port == port
    new_service_name = "new_service_name_1338"
    new_port = 613
    params.set(service_name=new_service_name, port=new_port)
    assert params.service_name == new_service_name
    assert params.port == new_port


def test_misc_1339():
    "1339 - test ConnectParams repr()"
    values = [
        ("user", "USER_1"),
        ("proxy_user", "PROXY_USER_1"),
        ("host", "my_host_1"),
        ("port", 1521),
        ("protocol", "tcp"),
        ("https_proxy", "proxy_a"),
        ("https_proxy_port", 1339),
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
        ("debug_jdwp", "host=host;port=1339"),
        ("connection_id_prefix", "prefix1339"),
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
        ("pool_name", "my_pool"),
        ("on_connect_callback", lambda conn: None),
        ("operation_callback", lambda name, arguments: None),
        ("round_trip_callback", lambda name: None),
        ("transaction_priority", oracledb.TransactionPriority.LOW),
    ]
    params = oracledb.ConnectParams(**dict(values))
    parts = [f"{name}={value!r}" for name, value in values]
    expected_value = f"ConnectParams({', '.join(parts)})"
    assert repr(params) == expected_value
    assert params.purity is oracledb.Purity.SELF
    assert params.mode is oracledb.AuthMode.SYSDBA
    new_values = [
        ("user", "USER_NEW"),
        ("proxy_user", "PROXY_USER_NEW"),
        ("host", "my_host_new"),
        ("port", 1621),
        ("protocol", "tcps"),
        ("https_proxy", "proxy_b"),
        ("https_proxy_port", 1339),
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
        ("pool_name", "my_second_pool"),
        ("on_connect_callback", lambda conn: None),
        ("operation_callback", lambda name, arguments: None),
        ("round_trip_callback", lambda name: None),
        ("transaction_priority", oracledb.TransactionPriority.HIGH),
    ]
    params.set(**dict(new_values))
    parts = [f"{name}={value!r}" for name, value in new_values]
    expected_value = f"ConnectParams({', '.join(parts)})"
    assert repr(params) == expected_value
    cs_values = dict(
        host="my_host_final",
        service_name="my_service_final",
    )
    connect_string = f"{cs_values['host']}/{cs_values['service_name']}"
    params.parse_connect_string(connect_string)
    final_values = [(n, cs_values.get(n, v)) for n, v in new_values]
    parts = [f"{name}={value!r}" for name, value in final_values]
    expected_value = f"ConnectParams({', '.join(parts)})"
    assert repr(params) == expected_value


def test_misc_1340():
    "1340 - connect descriptor with SDU"
    connect_string = """
        (DESCRIPTION=(SDU=65535)(ADDRESS=(PROTOCOL=TCP)
        (HOST=my_host1)(PORT=1589)))"""
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.sdu == 65535


def test_misc_1341():
    "1341 - test that SDU is set correctly with invalid sizes"
    params = oracledb.ConnectParams()
    params.set(sdu=random.randint(0, 511))
    assert params.sdu == 512
    params.set(sdu=2097153)
    assert params.sdu == 2097152


def test_misc_1342():
    "1342 - test empty connection class"
    params = oracledb.ConnectParams()
    assert params.cclass is None
    params.set(cclass="")
    assert params.cclass is None


def test_misc_1343():
    "1343 - test easy connect string with protocol specified"
    protocol = "tcp"
    host = "my_host_1343"
    port = 1668
    service_name = "my_service_1343"
    connect_string = f"{protocol}://{host}:{port}/{service_name}"
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.protocol == protocol
    assert params.host == host
    assert params.port == port
    assert params.service_name == service_name


def test_misc_1344():
    "1344 - calling set() doesn't clear object parameters"
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
    assert params.appcontext == app_context
    assert params.shardingkey == sharding_key
    assert params.supershardingkey == super_sharding_key
    assert params.ssl_context == ssl_context
    user = "user_1344"
    params.set(user=user)
    assert params.user == user
    assert params.appcontext == app_context
    assert params.shardingkey == sharding_key
    assert params.supershardingkey == super_sharding_key
    assert params.ssl_context == ssl_context


def test_misc_1345():
    "1345 - test that use_tcp_fast_open is set correctly"
    params = oracledb.ConnectParams()
    params.set(use_tcp_fast_open=True)
    assert params.use_tcp_fast_open
    params.set(use_tcp_fast_open=False)
    assert not params.use_tcp_fast_open
    params.set(use_tcp_fast_open="True")
    assert params.use_tcp_fast_open
    params.set(use_tcp_fast_open="False")
    assert not params.use_tcp_fast_open
    params.set(use_tcp_fast_open=None)
    assert not params.use_tcp_fast_open
    params.set(use_tcp_fast_open=1)
    assert params.use_tcp_fast_open


def test_misc_1346(test_env):
    "1346 - test connect descriptor without addresses defined"
    params = oracledb.ConnectParams()
    host = "host_1346"
    port = 1346
    service_name = "service_name_1346"
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
            assert params.host == host
            assert params.port == port
            assert params.service_name == service_name
        else:
            with test_env.assert_raises_full_code("DPY-2049"):
                params.parse_connect_string(connect_string)


def test_misc_1347():
    "1347 - test simple EasyConnect string parsing with IPv6 address"
    host = "::1"
    port = 1347
    service_name = "service_name_1347"
    connect_string = f"[{host}]:{port}/{service_name}"
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.host == host
    assert params.port == port
    assert params.service_name == service_name


def test_misc_1348():
    "1348 - test easy connect string with multiple hosts, different ports"
    connect_string = (
        "host1348a,host1348b:1348,host1348c,host1348d:1348/"
        "service_name_1348"
    )
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.host == ["host1348a", "host1348b", "host1348c", "host1348d"]
    assert params.port == [1348, 1348, 1348, 1348]
    assert params.service_name == "service_name_1348"


def test_misc_1349():
    "1349 - test easy connect string with multiple address lists"
    connect_string = (
        "host1349a;host1349b,host1349c:1349;host1349d/service_name_1349"
    )
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.host == ["host1349a", "host1349b", "host1349c", "host1349d"]
    assert params.port == [1521, 1349, 1349, 1521]
    assert params.service_name == "service_name_1349"
    expected_conn_string = (
        "(DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=host1349a)(PORT=1521))"
        "(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=host1349b)(PORT=1349))"
        "(ADDRESS=(PROTOCOL=tcp)(HOST=host1349c)(PORT=1349)))"
        "(ADDRESS=(PROTOCOL=tcp)(HOST=host1349d)(PORT=1521))"
        "(CONNECT_DATA=(SERVICE_NAME=service_name_1349)))"
    )
    assert params.get_connect_string() == expected_conn_string


def test_misc_1350(test_env):
    "1350 - test connect descriptor with mixed complex and simple data"
    connect_string = (
        "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=localhost)(PORT=1521))"
        "(CONNECT_DATA=(SERVER=DEDICATED) SERVICE_NAME=orclpdb1))"
    )
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-4017"):
        params.parse_connect_string(connect_string)


def test_misc_1351(test_env):
    "1351 - test connect descriptor with simple data for containers"
    container_names = [
        "address",
        "address_list",
        "connect_data",
        "description",
        "description_list",
        "security",
    ]
    for name in container_names:
        connect_string = f"({name}=5)"
        params = oracledb.ConnectParams()
        with test_env.assert_raises_full_code("DPY-4017"):
            params.parse_connect_string(connect_string)


def test_misc_1352():
    "1352 - test easy connect string with degenerate protocol"
    host = "host_1352"
    port = 1352
    service_name = "service_name_1352"
    connect_string = f"//{host}:{port}/{service_name}"
    params = oracledb.ConnectParams()
    params.parse_connect_string(connect_string)
    assert params.host == host
    assert params.port == port
    assert params.service_name == service_name


def test_misc_1353():
    "1353 - test easy connect string with registered protocol"
    protocol = "proto-test"
    protocol_arg = "args/for/proto1353"
    host = "host_1353"
    service_name = "service_name_1353"
    connect_string = f"{protocol}://{protocol_arg}"

    def hook(passed_protocol, passed_protocol_arg, passed_params):
        assert passed_protocol == protocol
        assert passed_protocol_arg == protocol_arg
        new_connect_string = f"{host}/{service_name}"
        passed_params.parse_connect_string(new_connect_string)

    try:
        oracledb.register_protocol(protocol, hook)
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        assert params.host == host
        assert params.service_name == service_name
    finally:
        oracledb.register_protocol(protocol, None)


def test_misc_1354():
    "1354 - test parsing a DSN with a protocol specified"
    dsn_in = "my-protocol://some_arguments_to_protocol"
    params = oracledb.ConnectParams()
    user, password, dsn_out = params.parse_dsn_with_credentials(dsn_in)
    assert user is None
    assert password is None
    assert dsn_out == dsn_in


def test_misc_1355(test_env):
    "1355 - test program attribute"
    _verify_network_name_attr(test_env, "program")


def test_misc_1356(test_env):
    "1356 - test machine attribute"
    _verify_network_name_attr(test_env, "machine")


def test_misc_1357(test_env):
    "1357 - test osuser attribute"
    _verify_network_name_attr(test_env, "osuser")


def test_misc_1358():
    "1358 - test terminal attribute"
    params = oracledb.ConnectParams()
    assert params.terminal == oracledb.defaults.terminal
    value = "myterminal"
    params = oracledb.ConnectParams(terminal=value)
    assert params.terminal == value


def test_misc_1359():
    "1359 - test driver_name attribute"
    params = oracledb.ConnectParams()
    assert params.driver_name == oracledb.defaults.driver_name
    value = "newdriver"
    params = oracledb.ConnectParams(driver_name=value)
    assert params.driver_name == value


def test_misc_1360(test_env):
    "1360 - test register_protocol with invalid hook type"

    def hook1(protocol, protocol_arg, params, extra_invalid_param):
        pass

    def hook2(passed_protocol):
        pass

    protocol = "proto-test"
    try:
        for hook in [hook1, hook2]:
            oracledb.register_protocol(protocol, hook)
            params = oracledb.ConnectParams()
            with test_env.assert_raises_full_code("DPY-2056"):
                params.parse_connect_string(f"{protocol}://args")
    finally:
        oracledb.register_protocol(protocol, None)


def test_misc_1361():
    "1361 - test register_protocol with invalid protocol type"
    with pytest.raises(TypeError):
        oracledb.register_protocol(1, lambda: None)
    with pytest.raises(TypeError):
        oracledb.register_protocol("proto", 5)


def test_misc_1362():
    "1362 - test removing unregistered protocol"
    with pytest.raises(KeyError):
        oracledb.register_protocol("unregistered-protocol", None)


def test_misc_1363():
    "1363 - test restoring pre-registered protocols (tcp and tcps)"

    host = "host_1363"
    port = 1363
    service_name = "service_1363"
    user = "user_1363"

    def hook(passed_protocol, passed_protocol_arg, passed_params):
        passed_params.set(user=user)

    for protocol in ["tcp", "tcps"]:
        try:
            oracledb.register_protocol(protocol, hook)
            connect_string = f"{protocol}://{host}:{port}/{service_name}"
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            assert params.user == user
            assert params.service_name is None
        finally:
            oracledb.register_protocol(protocol, None)
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        assert params.host == host
        assert params.port == port
        assert params.service_name == service_name


def test_misc_1364():
    "1364 - test extended connect strings for ConnectParams"
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
    host = "host_1364"
    service_name = "service_1364"
    for name, str_value, actual_value in test_scenarios:
        conn_string = f"{host}/{service_name}?pyo.{name}={str_value}"
        params = oracledb.ConnectParams()
        params.parse_connect_string(conn_string)
        assert params.host == host
        assert params.service_name == service_name
        assert getattr(params, name) == actual_value


@pytest.mark.filterwarnings("ignore:base64 encoded")
def test_misc_1365(test_env):
    "1365 - test set_from_config() with no user and password set"
    user = "user_1365"
    password = test_env.get_random_string()
    options = [
        ("a", user, password),
        ("b", user, None),
        ("c", None, None),
    ]
    for option, user, password in options:
        host = f"host_1365{option}"
        service_name = f"service_1365{option}"
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
        assert params.host == host
        assert params.service_name == service_name
        if user is not None:
            assert params.user == user


def test_misc_1366(test_env):
    "1366 - test set_from_config() with user and password already set"
    host = "host_1366"
    service_name = "service_1366"
    connect_string = f"{host}/{service_name}"
    user = "user_1366"
    password = test_env.get_random_string()
    config_user = "user_1366_in_config"
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
    assert params.host == host
    assert params.service_name == service_name
    assert params.user == user


def test_misc_1367(test_env):
    "1367 - test set_from_config() without connect_descriptor"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2059"):
        params.set_from_config(dict(connect_descriptor_missing="missing"))


def test_misc_1368(test_env):
    "1368 - test set_from_config() with extended parameters"
    host = "host_1368"
    service_name = "service_1368"
    connect_string = f"{host}/{service_name}"
    stmtcachesize = 35
    user = "user_1368"
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
    assert params.host == host
    assert params.service_name == service_name
    assert params.user == user
    assert params.stmtcachesize == stmtcachesize


def test_misc_1369():
    "1369 - test USE_SNI in connect string"
    options = [("on", True), ("off", False)]
    service_name = "service_1369"
    host = "host_1369"
    port = 1369
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
            assert params.host == host
            assert params.port == port
            assert params.service_name == service_name
            assert params.use_sni == val
        assert params.get_connect_string() == connect_descriptor


def test_misc_1370():
    "1370 - test passing through unrecognized parameters in CONNECT_DATA"
    options = [
        "(SIMPLE_KEY=SIMPLE_VALUE)",
        "(COMPLEX_KEY=(SUB_VALUE_A=5)(SUB_VALUE_B=6))",
        "(COMPLEX_KEY=(SUB_VALUE_A=5)(SUB_VALUE_B=(SUB_SUB_A=6)))",
    ]
    for option in options:
        connect_string = (
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=host1370)"
            "(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=service1370)"
            f"{option}))"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        assert params.get_connect_string() == connect_string


def test_misc_1371():
    "1371 - test INSTANCE_NAME in connect string"
    service_name = "service_1371"
    instance_name = "instance_1371"
    host = "host_1371"
    port = 1371
    easy_connect = f"{host}:{port}/{service_name}/{instance_name}"
    connect_descriptor = (
        f"(DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST={host})(PORT={port}))"
        f"(CONNECT_DATA=(SERVICE_NAME={service_name})"
        f"(INSTANCE_NAME={instance_name})))"
    )
    for connect_string in (easy_connect, connect_descriptor):
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        assert params.service_name == service_name
        assert params.instance_name == instance_name
        assert params.host == host
        assert params.port == port
        assert params.get_connect_string() == connect_descriptor


def test_misc_1372():
    "1372 - test passing through unrecognized parameters in SECURITY"
    options = [
        "(SIMPLE_KEY=SIMPLE_VALUE)",
        "(COMPLEX_KEY=(SUB_VALUE_A=23)(SUB_VALUE_B=27))",
        "(COMPLEX_KEY=(SUB_VALUE_A=A)(SUB_VALUE_B=(SUB_SUB_A=B)))",
    ]
    for option in options:
        connect_string = (
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=tcps)(HOST=host1372)"
            "(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=service1372))"
            f"(SECURITY=(SSL_SERVER_DN_MATCH=ON){option}))"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        assert params.get_connect_string() == connect_string


def test_misc_1373():
    "1373 - test passing through unrecognized parameters in DESCRIPTION"
    options = [
        "(SIMPLE_KEY=SIMPLE_VALUE)",
        "(COMPLEX_KEY=(SUB_VALUE_1=1)(SUB_VALUE_B=2))",
        "(COMPLEX_KEY=(SUB_VALUE_2=S)(SUB_VALUE_B=(SUB_SUB_A=T)))",
    ]
    for option in options:
        connect_string = (
            "(DESCRIPTION_LIST="
            f"(DESCRIPTION={option}(ADDRESS=(PROTOCOL=tcp)"
            "(HOST=host1373a)(PORT=1521))"
            "(CONNECT_DATA=(SERVICE_NAME=service1373)))"
            f"(DESCRIPTION={option}(ADDRESS=(PROTOCOL=tcp)"
            "(HOST=host1373b)(PORT=1521))"
            "(CONNECT_DATA=(SERVICE_NAME=service1373))))"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_string)
        assert params.get_connect_string() == connect_string


def test_misc_1374():
    "1374 - test passing through specific unsupported parameters"
    easy_connect = (
        "host_1374/service_1374?"
        "enable=broken&recv_buf_size=1024&send_buf_size=2048"
    )
    connect_descriptor = (
        "(DESCRIPTION=(ENABLE=broken)(RECV_BUF_SIZE=1024)"
        "(SEND_BUF_SIZE=2048)(ADDRESS=(PROTOCOL=tcp)(HOST=host_1374)"
        "(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=service_1374)))"
    )
    params = oracledb.ConnectParams()
    params.parse_connect_string(easy_connect)
    assert params.get_connect_string() == connect_descriptor


def test_misc_1375(test_env):
    "1375 - test syntax rule for keywords"
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
        connect_string = (
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=host1375)"
            + "(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=service1375)"
            + f"{value}))"
        )
        if ok:
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            assert params.get_connect_string() == connect_string
        else:
            with test_env.assert_raises_full_code("DPY-4017"):
                params.parse_connect_string(connect_string)


def test_misc_1376(test_env):
    "1376 - test syntax rule for keywords in easy connect string"
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
        easy_connect = f"""host1376:1589/service1376?{value}"""
        connect_string_exp = (
            "(DESCRIPTION="
            + "(ADDRESS=(PROTOCOL=tcp)(HOST=host1376)(PORT=1589))"
            + "(CONNECT_DATA=(SERVICE_NAME=service1376)))"
        )
        if ok:
            params = oracledb.ConnectParams()
            params.parse_connect_string(easy_connect)
            assert params.host == "host1376"
            assert params.port == 1589
            assert params.service_name == "service1376"
            assert params.get_connect_string() == connect_string_exp
        else:
            with test_env.assert_raises_full_code("DPY-4018"):
                params.parse_connect_string(easy_connect)


def test_misc_1377():
    "1377 - test for DESCRIPTION_LIST with FAILOVER"
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
    assert params.get_connect_string() == connect_string


def test_misc_1378():
    "1378 - test for descriptor parameters in connect descriptor"
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

    service_name = "service_1378"
    host1 = "host_1378_1"
    host2 = "host_1378_2"
    port1 = 13781
    port2 = 13782
    for str_val, exp_val in options:
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

        assert params.host == [host1, host2]
        assert params.port == [port1, port2]
        assert params.service_name == service_name
        assert params.get_connect_string() == connect_descriptor_exp


def test_misc_1379():
    "1379 - test for connect data parameters in connect descriptor"
    options = [
        "(COLOCATION_TAG=ColocationTag1379)",
        "(COLOCATION_TAG=ColocationTag_1379)",
        "(FAILOVER_MODE=(BACKUP=bhost)(TYPE=session)(METHOD=basic))",
        "(FAILOVER_MODE=(BACKUP=bhost)(TYPE=select)(METHOD=preconnect))",
        "(FAILOVER_MODE=(TYPE=select)(METHOD=basic)(RETRIES=2)(DELAY=15))",
        "(HS=ok)",
        "(TUNNEL_SERVICE_NAME=south)",
        "(POOL_NAME=pool_name_1379)",
    ]

    service_name = "service_1379"
    host = "host_1379"
    port = 1379
    for str_val in options:
        connect_data_part = str_val
        connect_descriptor = (
            f"(DESCRIPTION="
            f"(ADDRESS=(PROTOCOL=tcp)(HOST={host})(PORT={port}))"
            f"(CONNECT_DATA=(SERVICE_NAME={service_name})"
            f"{connect_data_part}))"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(connect_descriptor)
        assert params.host == host
        assert params.port == port
        assert params.service_name == service_name
        assert params.get_connect_string() == connect_descriptor


def test_misc_1380():
    "1380 - test for security parameters in connect descriptor"

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

    service_name = "service_1380"
    host = "host_1380"
    port = 1380
    for str_val, exp_val in security_options.items():
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
        assert params.host == host
        assert params.port == port
        assert params.service_name == service_name
        assert params.get_connect_string() == connect_descriptor_exp


def test_misc_1381():
    "1381 - test for parameters supported in easy connect descriptor"
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

    service_name = "service_1381"
    host = "host_1381"
    port = 1381
    for str_val, exp_str in options:
        descriptor_part = exp_str
        easy_connect = f"""{host}:{port}/{service_name}?{str_val}"""
        connect_descriptor_exp = (
            f"(DESCRIPTION={descriptor_part}"
            f"(ADDRESS=(PROTOCOL=tcp)(HOST={host})(PORT={port}))"
            f"(CONNECT_DATA=(SERVICE_NAME={service_name})))"
        )
        params = oracledb.ConnectParams()
        params.parse_connect_string(easy_connect)
        assert params.host == host
        assert params.port == port
        assert params.service_name == service_name
        assert params.get_connect_string() == connect_descriptor_exp


def test_misc_1382():
    "1382 - test for security parameters in easy connect descriptor"
    service_name = "service_1382"
    srvc_str = (
        "ssl_server_dn_match=true"
        "&ssl_server_cert_dn='cn=sales,cn=OracleContext,"
        "dc=us,dc=example,dc=com'"
        "&wallet_location='/tmp/oracle'"
    )
    host = "host_1382"
    port = 1382
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
    assert params.host == host
    assert params.port == port
    assert params.service_name == service_name
    assert params.get_connect_string() == connect_descriptor_exp


def test_misc_1383():
    "1383 - test for TYPE_OF_SERVICE, RDB_DATABASE, GLOBAL_NAME parameters"
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
    assert params.get_connect_string() == connect_string


@pytest.mark.parametrize(
    "attr_name,value",
    [
        ("user", "USER_1"),
        ("proxy_user", "PROXY_USER_1"),
        ("password", "dummy_password"),
        ("newpassword", "dummy_new_password"),
        ("wallet_password", "dummy_wallet_password"),
        ("access_token", lambda: "dummy_token"),
        ("host", "my_host_1"),
        ("port", 1584),
        ("protocol", "tcps"),
        ("https_proxy", "proxy_a"),
        ("https_proxy_port", 1384),
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
        ("debug_jdwp", "host=host;port=1384"),
        ("connection_id_prefix", "prefix1384"),
        ("ssl_context", ssl.create_default_context()),
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
        ("pool_name", "my_pool"),
        ("on_connect_callback", lambda conn: None),
        ("operation_callback", lambda name, arguments: None),
        ("round_trip_callback", lambda name: None),
        ("transaction_priority", oracledb.TransactionPriority.MEDIUM),
    ],
)
def test_misc_1384(attr_name, value):
    "1384 - test ConnectParams __eq__()"
    params = oracledb.ConnectParams()
    other_params = oracledb.ConnectParams()
    assert other_params == params
    dict_args = {}
    dict_args[attr_name] = value
    other_params.set(**dict_args)
    assert other_params != params
    params.set(**dict_args)
    assert other_params == params


def test_misc_1385():
    "1385 - test callback parameters"

    def on_connect_callback(connection):
        pass

    def operation_callback(name, arguments):
        pass

    def round_trip_callback(name):
        pass

    params = oracledb.ConnectParams()
    assert params.on_connect_callback is None
    assert params.operation_callback is None
    assert params.round_trip_callback is None
    params.set(
        on_connect_callback=on_connect_callback,
        operation_callback=operation_callback,
        round_trip_callback=round_trip_callback,
    )
    copied_params = params.copy()
    assert copied_params.on_connect_callback is on_connect_callback
    assert copied_params.operation_callback is operation_callback
    assert copied_params.round_trip_callback is round_trip_callback
    for name in (
        "on_connect_callback",
        "operation_callback",
        "round_trip_callback",
    ):
        params.set(**{name: None})
        assert getattr(params, name) is None
        with pytest.raises(oracledb.ProgrammingError) as exc_info:
            oracledb.ConnectParams(**{name: 1})
        assert exc_info.value.args[0].full_code == "DPY-2070"
