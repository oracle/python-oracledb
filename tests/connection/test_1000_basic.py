# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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
Module for testing basic connection funcationality
"""

import random
import string
import threading
import time

import oracledb
import pytest


def _verify_connect_arg(test_env, arg_name, arg_value, sql):
    """
    Verifies an argument passed during connect() matches the value actually
    used by the connection.
    """
    args = {}
    args[arg_name] = arg_value
    with test_env.get_connection(**args) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        (fetched_value,) = cursor.fetchone()
        assert fetched_value == arg_value


def test_connection_1000(test_env, conn):
    "1000 - simple connection to database"
    assert conn.username == test_env.main_user
    assert conn.dsn == test_env.connect_string
    assert conn.thin == (not test_env.use_thick_mode)


def test_connection_1001(skip_if_drcp, test_env):
    "1001 - test use of application context"
    namespace = "CLIENTCONTEXT"
    app_context_entries = [
        (namespace, "ATTR1", "VALUE1"),
        (namespace, "ATTR2", "VALUE2"),
        (namespace, "ATTR3", "VALUE3"),
    ]
    with test_env.get_connection(appcontext=app_context_entries) as conn:
        cursor = conn.cursor()
        for namespace, name, value in app_context_entries:
            cursor.execute(
                "select sys_context(:1, :2) from dual", (namespace, name)
            )
            (actual_value,) = cursor.fetchone()
            assert actual_value == value


def test_connection_1002(test_env):
    "1002 - test invalid use of application context"
    with pytest.raises(TypeError):
        test_env.get_connection(appcontext=[("userenv", "action")])
    with pytest.raises(ValueError):
        test_env.get_connection(appcontext=[("", "action", "value")])
    with pytest.raises(ValueError):
        test_env.get_connection(appcontext=[("userenv", "x" * 129, "value")])
    with pytest.raises(ValueError):
        test_env.get_connection(appcontext=[("userenv", "action", "x" * 4001)])


def test_connection_1003(conn, test_env):
    "1003 - test connection end-to-end tracing attributes"

    # determine the list of attributes to check
    attributes_to_check = []
    if not test_env.is_on_oracle_cloud:
        sql = """select dbop_name from v$sql_monitor
                 where sid = sys_context('userenv', 'sid')
                 and status = 'EXECUTING'"""
        attributes_to_check.append(("dbop", "oracledb_dbop", sql))
    sql = "select sys_context('userenv', 'action') from dual"
    attributes_to_check.append(("action", "oracledb_Action", sql))
    attributes_to_check.append(("action", None, sql))
    sql = "select sys_context('userenv', 'module') from dual"
    attributes_to_check.append(("module", "oracledb_Module", sql))
    attributes_to_check.append(("module", None, sql))
    sql = "select sys_context('userenv', 'client_info') from dual"
    attributes_to_check.append(("clientinfo", "oracledb_cinfo", sql))
    attributes_to_check.append(("clientinfo", None, sql))
    sql = "select sys_context('userenv', 'client_identifier') from dual"
    attributes_to_check.append(("client_identifier", "oracledb_cid", sql))
    attributes_to_check.append(("client_identifier", None, sql))
    if not conn.thin:
        sql = """select ecid from v$session
                 where sid = sys_context('userenv', 'sid')"""
        attributes_to_check.append(("econtext_id", "oracledb_ecid", sql))
        attributes_to_check.append(("econtext_id", None, sql))

    # check each of the scenarios
    for attr_name, value, sql in attributes_to_check:
        setattr(conn, attr_name, value)
        with conn.cursor() as cursor:
            cursor.execute(sql)
            (result,) = cursor.fetchone()
        assert result == value


def test_connection_1004(test_env):
    "1004 - test use of autocommit"
    with (
        test_env.get_connection() as conn,
        test_env.get_connection() as other_conn,
    ):
        cursor = conn.cursor()
        other_cursor = other_conn.cursor()
        cursor.execute("truncate table TestTempTable")
        cursor.execute("insert into TestTempTable (IntCol) values (1)")
        other_cursor.execute("select IntCol from TestTempTable")
        assert other_cursor.fetchall() == []
        conn.autocommit = True
        cursor.execute("insert into TestTempTable (IntCol) values (2)")
        other_cursor.execute(
            "select IntCol from TestTempTable order by IntCol"
        )
        assert other_cursor.fetchall() == [(1,), (2,)]


def test_connection_1005(test_env):
    "1005 - connection to database with bad connect string"
    with test_env.assert_raises_full_code(
        "DPY-4000", "DPY-4026", "DPY-4027", "ORA-12154"
    ):
        oracledb.connect("not a valid connect string!!")
    with test_env.assert_raises_full_code("DPY-4000", "DPY-4001"):
        dsn = f"{test_env.main_user}@{test_env.connect_string}"
        oracledb.connect(dsn)


def test_connection_1006(test_env):
    "1006 - connection to database with bad password"
    with test_env.assert_raises_full_code("ORA-01017"):
        test_env.get_connection(password=test_env.main_password + "X")


def test_connection_1007(skip_if_drcp, conn, test_env):
    "1007 - test changing password"
    if test_env.is_on_oracle_cloud:
        pytest.skip("passwords on Oracle Cloud are strictly controlled")
    sys_random = random.SystemRandom()
    new_password = "".join(
        sys_random.choice(string.ascii_letters) for i in range(20)
    )
    conn.changepassword(test_env.main_password, new_password)
    with test_env.get_connection(password=new_password) as conn:
        conn.changepassword(new_password, test_env.main_password)


def test_connection_1008(skip_if_drcp, conn, test_env):
    "1008 - test changing password to an invalid value"
    if test_env.is_on_oracle_cloud:
        pytest.skip("passwords on Oracle Cloud are strictly controlled")
    new_password = "1" * 1500
    with test_env.assert_raises_full_code("ORA-01017", "ORA-00988"):
        conn.changepassword(test_env.main_password, new_password)
    with test_env.assert_raises_full_code(
        "ORA-01017", "ORA-00988", "ORA-28008"
    ):
        conn.changepassword("incorrect old password", new_password)


def test_connection_1009(skip_if_drcp, conn, test_env):
    "1009 - test connecting with password containing / and @ symbols"
    if test_env.is_on_oracle_cloud:
        pytest.skip("passwords on Oracle Cloud are strictly controlled")
    sys_random = random.SystemRandom()
    chars = list(sys_random.choice(string.ascii_letters) for i in range(20))
    chars[4] = "/"
    chars[8] = "@"
    new_password = "".join(chars)
    conn.changepassword(test_env.main_password, new_password)
    try:
        with test_env.get_connection(password=new_password):
            pass
    finally:
        conn.changepassword(new_password, test_env.main_password)


def test_connection_1010(conn, test_env):
    "1010 - confirm an exception is raised after closing a connection"
    conn.close()
    with test_env.assert_raises_full_code("DPY-1001"):
        conn.rollback()


def test_connection_1011(skip_unless_thick_mode, conn, test_env):
    "1011 - test creating a connection using a handle"
    cursor = conn.cursor()
    cursor.execute("truncate table TestTempTable")
    int_value = random.randint(1, 32768)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:val, null)
        """,
        val=int_value,
    )
    conn2 = oracledb.connect(handle=conn.handle)
    cursor = conn2.cursor()
    cursor.execute("select IntCol from TestTempTable")
    (fetched_int_value,) = cursor.fetchone()
    assert fetched_int_value == int_value

    cursor.close()
    with test_env.assert_raises_full_code("DPI-1034"):
        conn2.close()
    conn.close()


def test_connection_1012(conn):
    "1012 - connection version is a string"
    assert isinstance(conn.version, str)


def test_connection_1013(test_env):
    "1013 - connection rolls back before close"
    with (
        test_env.get_connection() as conn,
        test_env.get_connection() as other_conn,
    ):
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        other_cursor = other_conn.cursor()
        other_cursor.execute("insert into TestTempTable (IntCol) values (1)")
        other_cursor.close()
        other_conn.close()
        cursor.execute("select count(*) from TestTempTable")
        (count,) = cursor.fetchone()
        assert count == 0


def test_connection_1014(test_env):
    "1014 - connection rolls back before destruction"
    with (
        test_env.get_connection() as conn,
        test_env.get_connection() as other_conn,
    ):
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        other_cursor = other_conn.cursor()
        other_cursor.execute("insert into TestTempTable (IntCol) values (1)")
        del other_cursor
        del other_conn
        cursor.execute("select count(*) from TestTempTable")
        (count,) = cursor.fetchone()
        assert count == 0


def test_connection_1015(test_env):
    "1015 - multiple connections to database with multiple threads"

    def connect_and_drop():
        with test_env.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("select count(*) from TestNumbers")
            (count,) = cursor.fetchone()
            assert count == 10

    threads = []
    for i in range(20):
        thread = threading.Thread(None, connect_and_drop)
        threads.append(thread)
        thread.start()
        time.sleep(0.1)
    for thread in threads:
        thread.join()


def test_connection_1016(conn, test_env):
    "1016 - test string format of connection"
    expected_value = (
        "<oracledb.Connection to "
        f"{test_env.main_user}@{test_env.connect_string}>"
    )
    assert str(conn) == expected_value


def test_connection_1017(test_env):
    "1017 - test context manager - close"
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        cursor.execute("insert into TestTempTable (IntCol) values (1)")
        conn.commit()
        cursor.execute("insert into TestTempTable (IntCol) values (2)")
    with test_env.assert_raises_full_code("DPY-1001"):
        conn.ping()
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("select count(*) from TestTempTable")
        (count,) = cursor.fetchone()
        assert count == 1


def test_connection_1018(conn, test_env):
    "1018 - test connection attribute values"
    assert conn.ltxid == b""
    assert not conn.autocommit
    conn.autocommit = True
    assert conn.autocommit
    assert conn.current_schema is None
    conn.current_schema = "system"
    assert conn.current_schema == "system"
    assert conn.edition is None
    conn.external_name = "test_external"
    assert conn.external_name == "test_external"
    conn.internal_name = "test_internal"
    assert conn.internal_name == "test_internal"
    if conn.max_identifier_length is not None:
        assert isinstance(conn.max_identifier_length, int)
    conn.stmtcachesize = 30
    assert conn.stmtcachesize == 30
    with pytest.raises(TypeError):
        conn.stmtcachesize = "value"
    assert conn.warning is None


def test_connection_1019(conn, test_env):
    "1019 - test closed connection attribute values"
    conn.close()
    attr_names = [
        "current_schema",
        "edition",
        "external_name",
        "internal_name",
        "ltxid",
        "stmtcachesize",
        "warning",
    ]
    for name in attr_names:
        with test_env.assert_raises_full_code("DPY-1001"):
            getattr(conn, name)


def test_connection_1020(conn, round_trip_checker):
    "1020 - test connection ping makes a round trip"
    conn.ping()
    assert round_trip_checker.get_value() == 1


def test_connection_1021(skip_unless_thick_mode, conn):
    "1021 - test begin, prepare, cancel transaction"
    cursor = conn.cursor()
    cursor.execute("truncate table TestTempTable")
    conn.begin(10, "trxnId", "branchId")
    assert not conn.prepare()
    conn.begin(10, "trxnId", "branchId")
    cursor.execute("""
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'tesName')
        """)
    assert conn.prepare()
    conn.cancel()
    conn.rollback()
    cursor.execute("select count(*) from TestTempTable")
    (count,) = cursor.fetchone()
    assert count == 0


def test_connection_1022(skip_unless_thick_mode, conn):
    "1022 - test multiple transactions on the same connection"
    with conn.cursor() as cursor:
        cursor.execute("truncate table TestTempTable")

    id_ = random.randint(0, 2**128)
    xid = (0x1234, "%032x" % id_, "%032x" % 9)
    conn.begin(*xid)
    with conn.cursor() as cursor:
        cursor.execute("""
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'tesName')
            """)
        assert conn.prepare()
        conn.commit()

    for begin_trans in (True, False):
        val = 3
        if begin_trans:
            conn.begin()
            val = 2
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:int_val, 'tesName')
                """,
                int_val=val,
            )
            conn.commit()

    expected_rows = [(1, "tesName"), (2, "tesName"), (3, "tesName")]
    with conn.cursor() as cursor:
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchall() == expected_rows


def test_connection_1023(skip_unless_thick_mode, conn):
    "1023 - test multiple global transactions on the same connection"
    with conn.cursor() as cursor:
        cursor.execute("truncate table TestTempTable")

    id_ = random.randint(0, 2**128)
    xid = (0x1234, "%032x" % id_, "%032x" % 9)
    conn.begin(*xid)
    with conn.cursor() as cursor:
        cursor.execute("""
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'tesName')
            """)
        assert conn.prepare()
        conn.commit()

    for begin_trans in (True, False):
        val = 3
        if begin_trans:
            conn.begin()
            val = 2
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:int_val, 'tesName')
                """,
                int_val=val,
            )
            conn.commit()

    id2_ = random.randint(0, 2**128)
    xid2 = (0x1234, "%032x" % id2_, "%032x" % 9)
    conn.begin(*xid2)
    with conn.cursor() as cursor:
        cursor.execute("""
            insert into TestTempTable (IntCol, StringCol1)
            values (4, 'tesName')
            """)
        assert conn.prepare()
        conn.commit()

    expected_rows = [
        (1, "tesName"),
        (2, "tesName"),
        (3, "tesName"),
        (4, "tesName"),
    ]
    with conn.cursor() as cursor:
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchall() == expected_rows


def test_connection_1024(skip_unless_thick_mode, conn, test_env):
    "1024 - test creating global txn after a local txn"
    with conn.cursor() as cursor:
        cursor.execute("truncate table TestTempTable")

    with conn.cursor() as cursor:
        cursor.execute("""
            insert into TestTempTable (IntCol, StringCol1)
            values (2, 'tesName')
            """)

    id_ = random.randint(0, 2**128)
    xid = (0x1234, "%032x" % id_, "%032x" % 9)
    with test_env.assert_raises_full_code("ORA-24776"):
        conn.begin(*xid)


def test_connection_1025(conn):
    "1025 - single connection to database with multiple threads"

    def verify_fetched_data():
        expected_data = [f"String {i + 1}" for i in range(10)]
        sql = "select StringCol from TestStrings order by IntCol"
        for i in range(5):
            with conn.cursor() as cursor:
                fetched_data = [s for s, in cursor.execute(sql)]
                assert fetched_data == expected_data

    threads = [threading.Thread(target=verify_fetched_data) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def test_connection_1026(conn, test_env):
    "1026 - test connection cancel"

    def perform_cancel():
        time.sleep(0.1)
        conn.cancel()

    thread = threading.Thread(target=perform_cancel)
    thread.start()
    try:
        with conn.cursor() as cursor:
            with pytest.raises(oracledb.OperationalError):
                cursor.callproc(test_env.sleep_proc_name, [2])
    finally:
        thread.join()
    with conn.cursor() as cursor:
        cursor.execute("select user from dual")
        (user,) = cursor.fetchone()
        assert user == test_env.main_user.upper()


def test_connection_1027(skip_if_drcp, conn, test_env):
    "1027 - test changing password during connect"
    if test_env.is_on_oracle_cloud:
        pytest.skip("passwords on Oracle Cloud are strictly controlled")
    sys_random = random.SystemRandom()
    new_password = "".join(
        sys_random.choice(string.ascii_letters) for i in range(20)
    )
    with test_env.get_connection(newpassword=new_password):
        pass
    with test_env.get_connection(password=new_password) as conn:
        conn.changepassword(new_password, test_env.main_password)


def test_connection_1028(test_env):
    "1028 - test use of autocommit during reexecute"
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    data_to_insert = [(1, "Test String #1"), (2, "Test String #2")]
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        with test_env.get_connection() as other_conn:
            other_cursor = other_conn.cursor()
            cursor.execute("truncate table TestTempTable")
            cursor.execute(sql, data_to_insert[0])
            other_cursor.execute(
                "select IntCol, StringCol1 from TestTempTable"
            )
            assert other_cursor.fetchall() == []
            conn.autocommit = True
            cursor.execute(sql, data_to_insert[1])
            other_cursor.execute(
                "select IntCol, StringCol1 from TestTempTable"
            )
            assert other_cursor.fetchall() == data_to_insert


def test_connection_1029(conn, test_env):
    "1029 - test current_schema is set properly"
    assert conn.current_schema is None
    user = test_env.main_user.upper()
    if test_env.proxy_user is None:
        pytest.skip("proxy user not defined")
    proxy_user = test_env.proxy_user.upper()
    cursor = conn.cursor()
    cursor.execute(f"alter session set current_schema={proxy_user}")
    assert conn.current_schema == proxy_user
    conn.current_schema = user
    assert conn.current_schema == user
    cursor.execute("select sys_context('userenv', 'current_schema') from dual")
    (result,) = cursor.fetchone()
    assert result == user


def test_connection_1030(conn):
    "1030 - test dbms_output package"
    cursor = conn.cursor()
    test_string = "Testing DBMS_OUTPUT package"
    cursor.callproc("dbms_output.enable")
    cursor.callproc("dbms_output.put_line", [test_string])
    string_var = cursor.var(str)
    number_var = cursor.var(int)
    cursor.callproc("dbms_output.get_line", (string_var, number_var))
    assert string_var.getvalue() == test_string


def test_connection_1031(conn, test_env):
    "1031 - test connection call_timeout"
    conn.call_timeout = 500  # milliseconds
    assert conn.call_timeout == 500
    with test_env.assert_raises_full_code("DPY-4011", "DPY-4024"):
        conn.cursor().callproc(test_env.sleep_proc_name, [2])


def test_connection_1032(test_env):
    "1032 - test Connection repr()"

    class MyConnection(oracledb.Connection):
        pass

    with test_env.get_connection(conn_class=MyConnection) as conn:
        qual_name = conn.__class__.__qualname__
        expected_value = (
            f"<{__name__}.{qual_name} to {conn.username}@{conn.dsn}>"
        )
        assert repr(conn) == expected_value

    expected_value = f"<{__name__}.{qual_name} disconnected>"
    assert repr(conn) == expected_value


def test_connection_1033(conn):
    "1033 - test getting write-only attributes"
    with pytest.raises(AttributeError):
        conn.action
    with pytest.raises(AttributeError):
        conn.dbop
    with pytest.raises(AttributeError):
        conn.clientinfo
    with pytest.raises(AttributeError):
        conn.econtext_id
    with pytest.raises(AttributeError):
        conn.module
    with pytest.raises(AttributeError):
        conn.client_identifier


def test_connection_1034(test_env):
    "1034 - test error for invalid type for params and pool"
    pool = test_env.get_pool()
    pool.close()
    with test_env.assert_raises_full_code("DPY-1002"):
        test_env.get_connection(pool=pool)
    with pytest.raises(TypeError):
        test_env.get_connection(pool="This isn't an instance of a pool")
    with test_env.assert_raises_full_code("DPY-2025"):
        oracledb.connect(params={"number": 7})


def test_connection_1035(conn):
    "1035 - test connection instance name"
    cursor = conn.cursor()
    cursor.execute("""
        select upper(sys_context('userenv', 'instance_name'))
        from dual
        """)
    (instance_name,) = cursor.fetchone()
    assert conn.instance_name.upper() == instance_name


def test_connection_1036(conn):
    "1036 - test deprecated attributes"
    conn.callTimeout = 500
    assert conn.callTimeout == 500


def test_connection_1037(
    skip_if_drcp, skip_unless_long_passwords_supported, test_env
):
    "1037 - test maximum allowed length for password"
    if test_env.is_on_oracle_cloud:
        pytest.skip("passwords on Oracle Cloud are strictly controlled")

    with test_env.get_connection() as conn:
        original_password = test_env.main_password
        new_password_32 = "a" * 32
        conn.changepassword(original_password, new_password_32)
    with test_env.get_connection(password=new_password_32) as conn:
        new_password_1024 = "a" * 1024
        conn.changepassword(new_password_32, new_password_1024)
    with test_env.get_connection(password=new_password_1024) as conn:
        conn.changepassword(new_password_1024, original_password)

        new_password_1025 = "a" * 1025
        with test_env.assert_raises_full_code("ORA-28218", "ORA-00972"):
            conn.changepassword(original_password, new_password_1025)


def test_connection_1038(conn):
    "1038 - test getting db_name"
    cursor = conn.cursor()
    cursor.execute("select name from V$DATABASE")
    (db_name,) = cursor.fetchone()
    assert conn.db_name.upper() == db_name.upper()


def test_connection_1039(conn):
    "1039 - test getting max_open_cursors"
    cursor = conn.cursor()
    cursor.execute("select value from V$PARAMETER where name='open_cursors'")
    (max_open_cursors,) = cursor.fetchone()
    assert conn.max_open_cursors == int(max_open_cursors)


def test_connection_1040(conn):
    "1040 - test getting service_name"
    cursor = conn.cursor()
    cursor.execute("select sys_context('userenv', 'service_name') from dual")
    (service_name,) = cursor.fetchone()
    assert conn.service_name.upper() == service_name.upper()


def test_connection_1041(conn):
    "1041 - test transaction_in_progress"
    assert not conn.transaction_in_progress

    cursor = conn.cursor()
    cursor.execute("truncate table TestTempTable")
    assert not conn.transaction_in_progress

    cursor.execute("insert into TestTempTable (IntCol) values (1)")
    assert conn.transaction_in_progress

    conn.commit()
    assert not conn.transaction_in_progress


def test_connection_1042(conn):
    "1042 - test getting db_domain"
    cursor = conn.cursor()
    cursor.execute("select value from V$PARAMETER where name='db_domain'")
    (db_domain,) = cursor.fetchone()
    assert conn.db_domain == db_domain


def test_connection_1043(test_env):
    "1043 - test connecting with a proxy user"
    with test_env.get_connection(proxy_user=test_env.proxy_user) as conn:
        assert conn.username == test_env.main_user
        assert conn.proxy_user == test_env.proxy_user


def test_connection_1044(skip_unless_thin_mode, conn, test_env):
    "1044 - test connection.sdu"
    sdu = random.randint(512, conn.sdu)
    with test_env.get_connection(sdu=sdu) as conn:
        assert conn.sdu == sdu


def test_connection_1045(test_env):
    "1045 - test connection with invalid conn_class"
    with test_env.assert_raises_full_code("DPY-2023"):
        test_env.get_connection(conn_class=oracledb.ConnectionPool)


def test_connection_1046(skip_unless_thin_mode, test_env):
    "1046 - test passing program when creating a connection"
    sql = (
        "select program from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_connect_arg(test_env, "program", "newprogram", sql)


def test_connection_1047(skip_unless_thin_mode, test_env):
    "1047 - test passing machine when creating a connection"
    sql = (
        "select machine from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_connect_arg(test_env, "machine", "newmachine", sql)


def test_connection_1048(skip_unless_thin_mode, test_env):
    "1048 - test passing terminal when creating a connection"
    sql = (
        "select terminal from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_connect_arg(test_env, "terminal", "newterminal", sql)


def test_connection_1049(skip_unless_thin_mode, test_env):
    "1049 - test passing osuser when creating a connection"
    sql = (
        "select osuser from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_connect_arg(test_env, "osuser", "newosuser", sql)


def test_connection_1050(test_env):
    "1050 - test passing driver_name when creating a connection"
    sql = (
        "select distinct client_driver from v$session_connect_info "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_connect_arg(test_env, "driver_name", "newdriver", sql)


def test_connection_1051(skip_unless_thin_mode, conn):
    "1051 - test getting session id"
    cursor = conn.cursor()
    cursor.execute("select dbms_debug_jdwp.current_session_id from dual")
    (fetched_value,) = cursor.fetchone()
    assert conn.session_id == fetched_value


def test_connection_1052(skip_unless_thin_mode, conn):
    "1052 - test getting session serial number"
    cursor = conn.cursor()
    cursor.execute("select dbms_debug_jdwp.current_session_serial from dual")
    (fetched_value,) = cursor.fetchone()
    assert conn.serial_num == fetched_value


def test_connection_1053(skip_unless_thin_mode, test_env):
    "1053 - test passed params in hook with standalone connection"
    sdu = 4096
    params = test_env.get_connect_params()
    protocol = "proto-test"
    orig_connect_string = test_env.connect_string
    connect_string = f"{protocol}://{orig_connect_string}"

    def hook(passed_protocol, passed_protocol_arg, passed_params):
        assert passed_protocol == protocol
        assert passed_protocol_arg == orig_connect_string
        passed_params.parse_connect_string(passed_protocol_arg)
        passed_params.set(sdu=sdu)

    try:
        oracledb.register_protocol(protocol, hook)
        with oracledb.connect(dsn=connect_string, params=params):
            assert params.sdu == sdu
    finally:
        oracledb.register_protocol(protocol, None)


def test_connection_1054(conn, test_env):
    "1054 - test altering connection edition"
    assert conn.edition is None
    cursor = conn.cursor()
    sql = "select sys_context('USERENV', 'CURRENT_EDITION_NAME') from dual"
    default_edition = "ORA$BASE"
    test_edition = test_env.edition_name
    for edition in [test_edition, default_edition]:
        cursor.execute(f"alter session set edition = {edition}")
        cursor.execute(sql)
        assert conn.edition == cursor.fetchone()[0]
        assert conn.edition == edition.upper()


def test_connection_1055(test_env):
    "1055 - test connect() with edition"
    edition = test_env.edition_name
    with test_env.get_connection(edition=edition) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "select sys_context('USERENV', 'CURRENT_EDITION_NAME') from dual"
        )
        assert cursor.fetchone()[0] == edition.upper()
        assert conn.edition == edition


def test_connection_1056(conn, test_env):
    "1056 - test connect() with parameters hook"
    orig_stmtcachesize = conn.stmtcachesize
    stmtcachesize = orig_stmtcachesize + 10

    def hook(params):
        params.set(stmtcachesize=stmtcachesize)

    try:
        oracledb.register_params_hook(hook)
        with test_env.get_connection() as conn:
            assert conn.stmtcachesize == stmtcachesize
    finally:
        oracledb.unregister_params_hook(hook)

    with test_env.get_connection() as conn:
        assert conn.stmtcachesize == orig_stmtcachesize


def test_connection_1057(test_env, conn):
    "1057 - test connect() with multiple parameters hooks"

    def hook1(params):
        order.append("first")

    def hook2(params):
        order.append("second")

    def hook3(params):
        order.append("third")

    with test_env.get_connection():
        oracledb.register_params_hook(hook1)
        oracledb.register_params_hook(hook2)
        oracledb.register_params_hook(hook3)
        try:
            order = []
            with test_env.get_connection():
                assert order == ["first", "second", "third"]
        finally:
            oracledb.unregister_params_hook(hook1)
            oracledb.unregister_params_hook(hook2)
            oracledb.unregister_params_hook(hook3)


def test_connection_1058(conn, test_env):
    "1058 - test error in the middle of a database response"
    cursor = conn.cursor()
    cursor.execute("truncate table TestTempTable")
    data = [(i + 1, 2 if i < 1499 else 0) for i in range(1500)]
    cursor.executemany(
        "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)",
        data,
    )
    conn.commit()
    cursor.arraysize = 1500
    with test_env.assert_raises_full_code("ORA-01476"):
        cursor.execute("""
            select IntCol, 1 / NumberCol
            from TestTempTable
            where IntCol < 1500
            union all
            select IntCol, 1 / NumberCol
            from TestTempTable
            where IntCol = 1500
            """)
        cursor.fetchall()


def test_connection_1059(test_env):
    "1059 - test on_connect_callback is triggered for standalone connections"
    counter = 0

    def callback(conn):
        nonlocal counter
        counter += 1

    with test_env.get_connection(on_connect_callback=callback):
        assert counter == 1


def test_connection_1060(skip_unless_thin_mode, conn, test_env):
    "1060 - end user security context requires tcps protocol"
    params = test_env.get_connect_params()
    if params.protocol == "tcp":
        pytest.skip("test requires the TCP protocol")
    context = oracledb.create_end_user_security_context(
        end_user_identity="end-user-token",
        database_access_token="mid_tier_token",
    )
    with test_env.assert_raises_full_code("DPY-2073"):
        conn.set_end_user_security_context(context)


@pytest.mark.parametrize("attr_name", ["host", "port", "protocol"])
def test_connection_1061(conn, test_env, attr_name):
    "1061 - test getting connection networking attributes"
    if conn.thin:
        params = test_env.get_connect_params()
        params.parse_connect_string(test_env.connect_string)
        conn_value = getattr(conn, attr_name)
        expected_value = getattr(params, attr_name)
        assert conn_value == expected_value or (
            isinstance(expected_value, list) and conn_value in expected_value
        )
    else:
        with test_env.assert_raises_full_code("DPY-3001"):
            getattr(conn, attr_name)


def test_connection_1062(skip_unless_thin_mode, cursor, test_env):
    "1062 - test getting db_unique_name"
    test_env.skip_unless_server_version(18, 5)
    cursor.execute("select sys_context('userenv', 'db_unique_name') from dual")
    (expected_name,) = cursor.fetchone()
    assert cursor.connection.db_unique_name == expected_name


def test_connection_1063(conn, test_env):
    "1063 - test application context management with invalid inputs"
    with pytest.raises(ValueError):
        conn.set_app_context("", attr="value")
    with pytest.raises(ValueError):
        conn.clear_app_context("")
    with pytest.raises(ValueError):
        conn.set_app_context("CLIENTCONTEXT")
    with pytest.raises(ValueError):
        attrs = {"X" * 129: "value"}
        conn.set_app_context("CLIENTCONTEXT", **attrs)
    with pytest.raises(ValueError):
        conn.set_app_context("CLIENTCONTEXT", attr="X" * 4001)
    with test_env.assert_raises_full_code("ORA-28267"):
        conn.set_app_context("NOT_A_VALID_NAMESPACE", attr="value")
        conn.ping()


def test_connection_1064(conn, cursor):
    "1064 - test set_app_context() behaviour"
    namespace = "CLIENTCONTEXT"
    conn.set_app_context(namespace, ATTR1="VALUE1")
    conn.set_app_context(namespace, ATTR2="VALUE2")
    cursor.execute(
        """
        select
            sys_context(:namespace, 'ATTR1'),
            sys_context(:namespace, 'ATTR2')
        from dual
        """,
        namespace=namespace,
    )
    assert cursor.fetchone() == ("VALUE1", "VALUE2")
    conn.clear_app_context(namespace)
    cursor.execute(None, namespace=namespace)
    assert cursor.fetchone() == (None, None)


def test_connection_1065(skip_unless_transaction_priority_supported, test_env):
    "1065 - test getting and setting transaction priority"
    with test_env.get_connection() as conn:
        default_priority = conn.transaction_priority
    with test_env.get_connection(transaction_priority="medium") as conn:
        assert conn.transaction_priority == oracledb.TransactionPriority.MEDIUM
        conn.transaction_priority = "low"
        conn.ping()
        assert conn.transaction_priority == "low"
        conn.transaction_priority = ""
        conn.ping()
        assert conn.transaction_priority == default_priority
