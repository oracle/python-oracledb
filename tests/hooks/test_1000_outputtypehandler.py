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
Module for testing the conversions of outputtype handler.
"""

import datetime
import decimal

import oracledb
import pytest


def _test_type_handler(
    cursor, input_type, output_type, in_value, expected_out_value
):
    def type_handler(cursor, metadata):
        return cursor.var(output_type, arraysize=cursor.arraysize)

    cursor.outputtypehandler = type_handler
    assert cursor.outputtypehandler == type_handler
    var = cursor.var(input_type)
    var.setvalue(0, in_value)
    cursor.execute("select :1 from dual", [var])
    (fetched_value,) = cursor.fetchone()
    assert type(fetched_value) is type(expected_out_value)
    assert fetched_value == expected_out_value


def _test_type_handler_lob(cursor, lob_type, output_type):
    db_type = getattr(oracledb, lob_type)

    def type_handler(cursor, metadata):
        if metadata.type_code is db_type:
            return cursor.var(output_type, arraysize=cursor.arraysize)

    cursor.outputtypehandler = type_handler
    in_value = f"Some {lob_type} data"
    if lob_type == "BLOB":
        in_value = in_value.encode()
    cursor.execute(f"delete from Test{lob_type}s")
    cursor.execute(
        f"""
        insert into Test{lob_type}s (IntCol, {lob_type}Col)
        values(1, :val)
        """,
        val=in_value,
    )
    cursor.connection.commit()
    cursor.execute(
        f"select {lob_type}Col, IntCol, {lob_type}Col from Test{lob_type}s"
    )
    assert cursor.fetchone() == (in_value, 1, in_value)


@pytest.fixture(autouse=True)
def setup(cursor):
    cursor.execute("""
        ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'
        NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF6'
        NLS_TIMESTAMP_TZ_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF6'
        time_zone='Europe/London'
        """)


def test_hooks_1000(cursor):
    "1000 - output type handler: from VARCHAR to NUMBER"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, "31.5", 31.5
    )


def test_hooks_1001(cursor):
    "1001 - output type handler: from CHAR to NUMBER"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_NUMBER, "31.5", 31.5
    )


def test_hooks_1002(cursor):
    "1002 - output type handler: from LONG to NUMBER"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_LONG, oracledb.DB_TYPE_NUMBER, "31.5", 31.5
    )


def test_hooks_1003(cursor):
    "1003 - test output type handler: from INTEGER to NUMBER"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_INTEGER,
        oracledb.DB_TYPE_NUMBER,
        31,
        31,
    )


def test_hooks_1004(cursor):
    "1004 - output type handler: from VARCHAR to INTEGER"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_VARCHAR,
        oracledb.DB_TYPE_BINARY_INTEGER,
        "31.5",
        31,
    )


def test_hooks_1005(cursor):
    "1005 - output type handler: from CHAR to INTEGER"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_CHAR,
        oracledb.DB_TYPE_BINARY_INTEGER,
        "31.5",
        31,
    )


def test_hooks_1006(cursor):
    "1006 - output type handler: from LONG to INTEGER"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_LONG,
        oracledb.DB_TYPE_BINARY_INTEGER,
        "31.5",
        31,
    )


def test_hooks_1007(cursor):
    "1007 - output type handler: from NUMBER to INTEGER"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_NUMBER,
        oracledb.DB_TYPE_BINARY_INTEGER,
        31.5,
        31,
    )


def test_hooks_1008(cursor):
    "1008 - output type handler: from DOUBLE to INTEGER"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_DOUBLE,
        oracledb.DB_TYPE_BINARY_INTEGER,
        31.5,
        31,
    )


def test_hooks_1009(cursor):
    "1009 - output type handler: from FLOAT to INTEGER"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_FLOAT,
        oracledb.DB_TYPE_BINARY_INTEGER,
        31.5,
        31,
    )


def test_hooks_1010(cursor):
    "1010 - output type handler: from DATE to VARCHAR"
    in_val = datetime.date(2021, 2, 1)
    out_val = "2021-02-01 00:00:00"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_DATE,
        oracledb.DB_TYPE_VARCHAR,
        in_val,
        out_val,
    )


def test_hooks_1011(cursor):
    "1011 - output type handler: from DATE to CHAR"
    in_val = datetime.date(2021, 2, 1)
    out_val = "2021-02-01 00:00:00"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_DATE, oracledb.DB_TYPE_CHAR, in_val, out_val
    )


def test_hooks_1012(cursor):
    "1012 - output type handler: from DATE to LONG"
    in_val = datetime.date(2021, 2, 1)
    out_val = "2021-02-01 00:00:00"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_DATE, oracledb.DB_TYPE_LONG, in_val, out_val
    )


def test_hooks_1013(cursor):
    "1013 - output type handler: from NUMBER to VARCHAR"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_VARCHAR, 31.5, "31.5"
    )
    _test_type_handler(
        cursor, oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_VARCHAR, 0, "0"
    )


def test_hooks_1014(cursor):
    "1014 - output type handler: from NUMBER to CHAR"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_CHAR, 31.5, "31.5"
    )
    _test_type_handler(
        cursor, oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_CHAR, 0, "0"
    )


def test_hooks_1015(cursor):
    "1015 - output type handler: from NUMBER to LONG"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_LONG, 31.5, "31.5"
    )


def test_hooks_1016(conn, cursor):
    "1016 - output type handler: from INTERVAL to VARCHAR"
    in_val = datetime.timedelta(days=-1, seconds=86314, microseconds=431152)
    if conn.thin:
        out_val = str(in_val)
    else:
        out_val = "-000000001 23:58:34.431152000"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_INTERVAL_DS,
        oracledb.DB_TYPE_VARCHAR,
        in_val,
        out_val,
    )


def test_hooks_1017(conn, cursor):
    "1017 - output type handler: from INTERVAL to CHAR"
    in_val = datetime.timedelta(days=-1, seconds=86314, microseconds=431152)
    if conn.thin:
        out_val = str(in_val)
    else:
        out_val = "-000000001 23:58:34.431152000"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_INTERVAL_DS,
        oracledb.DB_TYPE_CHAR,
        in_val,
        out_val,
    )


def test_hooks_1018(conn, cursor):
    "1018 - output type handler: from INTERVAL to LONG"
    in_val = datetime.timedelta(days=-1, seconds=86314, microseconds=431152)
    if conn.thin:
        out_val = str(in_val)
    else:
        out_val = "-000000001 23:58:34.431152000"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_INTERVAL_DS,
        oracledb.DB_TYPE_LONG,
        in_val,
        out_val,
    )


def test_hooks_1019(cursor):
    "1019 - output type handler: from TIMESTAMP to VARCHAR"
    in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP,
        oracledb.DB_TYPE_VARCHAR,
        in_val,
        str(in_val),
    )


def test_hooks_1020(cursor):
    "1020 - output type handler: from TIMESTAMP to CHAR"
    in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP,
        oracledb.DB_TYPE_CHAR,
        in_val,
        str(in_val),
    )


def test_hooks_1021(cursor):
    "1021 - output type handler: from TIMESTAMP to LONG"
    in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP,
        oracledb.DB_TYPE_LONG,
        in_val,
        str(in_val),
    )


def test_hooks_1022(cursor):
    "1022 - output type handler: from TIMESTAMP_TZ to VARCHAR"
    in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP_TZ,
        oracledb.DB_TYPE_VARCHAR,
        in_val,
        str(in_val),
    )


def test_hooks_1023(cursor):
    "1023 - output type handler: from TIMESTAMP_TZ to CHAR"
    in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP_TZ,
        oracledb.DB_TYPE_CHAR,
        in_val,
        str(in_val),
    )


def test_hooks_1024(cursor):
    "1024 - output type handler: from TIMESTAMP_TZ to LONG"
    in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP_TZ,
        oracledb.DB_TYPE_LONG,
        in_val,
        str(in_val),
    )


def test_hooks_1025(cursor):
    "1025 - output type handler: from TIMESTAMP_LTZ to VARCHAR"
    in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP_LTZ,
        oracledb.DB_TYPE_VARCHAR,
        in_val,
        str(in_val),
    )


def test_hooks_1026(cursor):
    "1026 - output type handler: from TIMESTAMP_LTZ to CHAR"
    in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP_LTZ,
        oracledb.DB_TYPE_CHAR,
        in_val,
        str(in_val),
    )


def test_hooks_1027(cursor):
    "1027 - output type handler: from TIMESTAMP_LTZ to LONG"
    in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP_LTZ,
        oracledb.DB_TYPE_LONG,
        in_val,
        str(in_val),
    )


def test_hooks_1028(cursor):
    "1028 - output type handler: from INTEGER to VARCHAR"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_INTEGER,
        oracledb.DB_TYPE_VARCHAR,
        31,
        "31",
    )


def test_hooks_1029(cursor):
    "1029 - output type handler: from INTEGER to CHAR"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_INTEGER,
        oracledb.DB_TYPE_CHAR,
        31,
        "31",
    )


def test_hooks_1030(cursor):
    "1030 - output type handler: from INTEGER to LONG"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_INTEGER,
        oracledb.DB_TYPE_LONG,
        31,
        "31",
    )


def test_hooks_1031(cursor):
    "1031 - output type handler: from NUMBER to DOUBLE"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_NUMBER,
        oracledb.DB_TYPE_BINARY_DOUBLE,
        31.5,
        31.5,
    )


def test_hooks_1032(cursor):
    "1032 - output type handler: from FLOAT to DOUBLE"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_FLOAT,
        oracledb.DB_TYPE_BINARY_DOUBLE,
        31.5,
        31.5,
    )


def test_hooks_1033(cursor):
    "1033 - output type handler: from VARCHAR to DOUBLE"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_VARCHAR,
        oracledb.DB_TYPE_BINARY_DOUBLE,
        "31.5",
        31.5,
    )


def test_hooks_1034(cursor):
    "1034 - output type handler: from CHAR to DOUBLE"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_CHAR,
        oracledb.DB_TYPE_BINARY_DOUBLE,
        "31.5",
        31.5,
    )


def test_hooks_1035(cursor):
    "1035 - output type handler: from LONG to DOUBLE"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_LONG,
        oracledb.DB_TYPE_BINARY_DOUBLE,
        "31.5",
        31.5,
    )


def test_hooks_1036(cursor):
    "1036 - output type handler: from NUMBER to FLOAT"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_NUMBER,
        oracledb.DB_TYPE_BINARY_FLOAT,
        31.5,
        31.5,
    )


def test_hooks_1037(cursor):
    "1037 - output type handler: from DOUBLE to FLOAT"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_DOUBLE,
        oracledb.DB_TYPE_BINARY_FLOAT,
        31.5,
        31.5,
    )


def test_hooks_1038(cursor):
    "1038 - output type handler: from VARCHAR to FLOAT"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_VARCHAR,
        oracledb.DB_TYPE_BINARY_FLOAT,
        "31.5",
        31.5,
    )


def test_hooks_1039(cursor):
    "1039 - output type handler: from CHAR to FLOAT"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_CHAR,
        oracledb.DB_TYPE_BINARY_FLOAT,
        "31.5",
        31.5,
    )


def test_hooks_1040(cursor):
    "1040 - output type handler: from LONG to FLOAT"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_LONG,
        oracledb.DB_TYPE_BINARY_FLOAT,
        "31.5",
        31.5,
    )


def test_hooks_1041(cursor):
    "1041 - output type handler: from VARCHAR to CHAR"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_CHAR, "31.5", "31.5"
    )


def test_hooks_1042(cursor):
    "1042 - output type handler: from VARCHAR to LONG"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_LONG, "31.5", "31.5"
    )


def test_hooks_1043(cursor):
    "1043 - output type handler: from LONG to VARCHAR"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_LONG, oracledb.DB_TYPE_VARCHAR, "31.5", "31.5"
    )


def test_hooks_1044(cursor):
    "1044 - output type handler: from LONG to CHAR"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_LONG, oracledb.DB_TYPE_CHAR, "31.5", "31.5"
    )


def test_hooks_1045(cursor):
    "1045 - output type handler: from CHAR to VARCHAR"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_VARCHAR, "31.5", "31.5"
    )


def test_hooks_1046(cursor):
    "1046 - output type handler: from CHAR to LONG"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_LONG, "31.5", "31.5"
    )


def test_hooks_1047(cursor):
    "1047 - output type handler: from TIMESTAMP to TIMESTAMP_TZ"
    val = datetime.datetime(2002, 12, 17, 0, 0, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP,
        oracledb.DB_TYPE_TIMESTAMP_TZ,
        val,
        val,
    )


def test_hooks_1048(cursor):
    "1048 - output type handler: from TIMESTAMP to TIMESTAMP_LTZ"
    val = datetime.datetime(2002, 12, 17, 0, 0, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP,
        oracledb.DB_TYPE_TIMESTAMP_LTZ,
        val,
        val,
    )


def test_hooks_1049(cursor):
    "1049 - output type handler: from TIMESTAMP_TZ to TIMESTAMP"
    val = datetime.datetime(2002, 12, 17, 0, 0, 16, 400000)
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_TIMESTAMP_TZ,
        oracledb.DB_TYPE_TIMESTAMP,
        val,
        val,
    )


def test_hooks_1050(cursor, test_env):
    "1050 - output type handler: from NUMBER to DATE is invalid"
    with test_env.assert_raises_full_code("DPY-4007", "ORA-00932"):
        _test_type_handler(
            cursor, oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_DATE, 3, 3
        )


def test_hooks_1051(cursor):
    "1051 - output type handler: from CLOB to CHAR"
    val = "Some Clob String"
    lob = cursor.connection.createlob(oracledb.DB_TYPE_CLOB, val)
    _test_type_handler(
        cursor, oracledb.DB_TYPE_CLOB, oracledb.DB_TYPE_CHAR, lob, val
    )


def test_hooks_1052(cursor):
    "1052 - output type handler: from CLOB to VARCHAR"
    val = "Some Clob String"
    lob = cursor.connection.createlob(oracledb.DB_TYPE_CLOB, val)
    _test_type_handler(
        cursor, oracledb.DB_TYPE_CLOB, oracledb.DB_TYPE_VARCHAR, lob, val
    )


def test_hooks_1053(cursor):
    "1053 - output type handler: from CLOB to LONG"
    val = "Some Clob String"
    lob = cursor.connection.createlob(oracledb.DB_TYPE_CLOB, val)
    _test_type_handler(
        cursor, oracledb.DB_TYPE_CLOB, oracledb.DB_TYPE_LONG, lob, val
    )


def test_hooks_1054(cursor):
    "1054 - output type handler: from BLOB to RAW"
    val = b"Some binary data"
    lob = cursor.connection.createlob(oracledb.DB_TYPE_BLOB, val)
    _test_type_handler(
        cursor, oracledb.DB_TYPE_BLOB, oracledb.DB_TYPE_RAW, lob, val
    )


def test_hooks_1055(cursor):
    "1055 - output type handler: from BLOB to LONGRAW"
    val = b"Some binary data"
    lob = cursor.connection.createlob(oracledb.DB_TYPE_BLOB, val)
    _test_type_handler(
        cursor, oracledb.DB_TYPE_BLOB, oracledb.DB_TYPE_LONG_RAW, lob, val
    )


def test_hooks_1056(cursor):
    "1056 - output type handler: from permanent BLOBs to LONG_RAW"
    _test_type_handler_lob(cursor, "BLOB", oracledb.DB_TYPE_LONG_RAW)


def test_hooks_1057(cursor):
    "1057 - output type handler: from permanent BLOBs to RAW"
    _test_type_handler_lob(cursor, "BLOB", oracledb.DB_TYPE_RAW)


def test_hooks_1058(cursor):
    "1058 - output type handler: from permanent CLOBs to VARCHAR"
    _test_type_handler_lob(cursor, "CLOB", oracledb.DB_TYPE_VARCHAR)


def test_hooks_1059(cursor):
    "1059 - output type handler: from permanent CLOBs to CHAR"
    _test_type_handler_lob(cursor, "CLOB", oracledb.DB_TYPE_CHAR)


def test_hooks_1060(cursor):
    "1060 - output type handler: from permanent CLOBs to LONG"
    _test_type_handler_lob(cursor, "CLOB", oracledb.DB_TYPE_LONG)


def test_hooks_1061(cursor):
    "1061 - output type handler: from NCLOB to CHAR"
    val = "Some nclob data"
    lob = cursor.connection.createlob(oracledb.DB_TYPE_NCLOB, val)
    _test_type_handler(
        cursor, oracledb.DB_TYPE_NCLOB, oracledb.DB_TYPE_CHAR, lob, val
    )


def test_hooks_1062(cursor):
    "1062 - output type handler: from NCLOB to VARCHAR"
    val = "Some nclob data"
    lob = cursor.connection.createlob(oracledb.DB_TYPE_NCLOB, val)
    _test_type_handler(
        cursor, oracledb.DB_TYPE_NCLOB, oracledb.DB_TYPE_VARCHAR, lob, val
    )


def test_hooks_1063(cursor):
    "1063 - output type handler: from NCLOB to LONG"
    val = "Some nclob data"
    lob = cursor.connection.createlob(oracledb.DB_TYPE_NCLOB, val)
    _test_type_handler(
        cursor, oracledb.DB_TYPE_NCLOB, oracledb.DB_TYPE_LONG, lob, val
    )


def test_hooks_1064(cursor):
    "1064 - output type handler: from permanent NCLOBs to VARCHAR"
    _test_type_handler_lob(cursor, "NCLOB", oracledb.DB_TYPE_VARCHAR)


def test_hooks_1065(cursor):
    "1065 - output type handler: from permanent NCLOBs to CHAR"
    _test_type_handler_lob(cursor, "NCLOB", oracledb.DB_TYPE_CHAR)


def test_hooks_1066(cursor):
    "1066 - output type handler: from permanent NCLOBs to LONG"
    _test_type_handler_lob(cursor, "NCLOB", oracledb.DB_TYPE_LONG)


def test_hooks_1067(cursor):
    "1067 - output type handler: from NVARCHAR to VARCHAR"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_NVARCHAR,
        oracledb.DB_TYPE_VARCHAR,
        "31.5",
        "31.5",
    )


def test_hooks_1068(cursor):
    "1068 - output type handler: from VARCHAR to NVARCHAR"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_VARCHAR,
        oracledb.DB_TYPE_NVARCHAR,
        "31.5",
        "31.5",
    )


def test_hooks_1069(cursor):
    "1069 - output type handler: from NCHAR to CHAR"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_NCHAR, oracledb.DB_TYPE_CHAR, "31.5", "31.5"
    )


def test_hooks_1070(cursor):
    "1070 - output type handler: from CHAR to NCHAR"
    _test_type_handler(
        cursor, oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_NCHAR, "31.5", "31.5"
    )


def test_hooks_1071(cursor, test_env):
    "1071 - execute raises an error if an incorrect arraysize is used"

    def type_handler(cursor, metadata):
        return cursor.var(str)

    cursor.arraysize = 100
    cursor.outputtypehandler = type_handler
    with test_env.assert_raises_full_code("DPY-2016"):
        cursor.execute("select :1 from dual", [5])


def test_hooks_1072(cursor, test_env):
    "1072 - execute raises an error if a var is not returned"

    def type_handler(cursor, metadata):
        return "incorrect_return"

    cursor.outputtypehandler = type_handler
    with test_env.assert_raises_full_code("DPY-2015"):
        cursor.execute("select :1 from dual", [5])


def test_hooks_1073(cursor):
    "1073 - output type handler: from NUMBER to decimal.Decimal"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_NUMBER,
        decimal.Decimal,
        31.5,
        decimal.Decimal("31.5"),
    )
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_NUMBER,
        decimal.Decimal,
        0,
        decimal.Decimal("0"),
    )


def test_hooks_1074(conn):
    "1074 - use of output type handler does not affect description"

    def type_handler(cursor, metadata):
        return cursor.var(str, arraysize=cursor.arraysize)

    with conn.cursor() as cursor:
        cursor.execute("select user from dual")
        desc_before = cursor.description
    with conn.cursor() as cursor:
        cursor.outputtypehandler = type_handler
        cursor.execute("select user from dual")
        assert cursor.description == desc_before


def test_hooks_1075(conn):
    "1075 - use the old signature for an output type handler"

    def type_handler(cursor, name, default_type, size, precision, scale):
        return cursor.var(str, arraysize=cursor.arraysize)

    with conn.cursor() as cursor:
        cursor.outputtypehandler = type_handler
        cursor.execute("select 1 from dual")
        assert cursor.fetchall() == [("1",)]


def test_hooks_1076(conn, cursor):
    "1076 - re-execute query with second fetch returning no rows"

    cursor.execute("truncate table TestTempTable")
    data = [(i + 1,) for i in range(5)]
    cursor.executemany("insert into TestTempTable (IntCol) values (:1)", data)
    conn.commit()

    def type_handler_1(cursor, metadata):
        return cursor.var(
            str,
            arraysize=cursor.arraysize,
            outconverter=lambda x: f"_{x}_",
        )

    def type_handler_2(cursor, metadata):
        return cursor.var(
            str,
            arraysize=cursor.arraysize,
            outconverter=lambda x: f"={x}=",
        )

    cursor.outputtypehandler = type_handler_1
    cursor.arraysize = 6
    cursor.prefetchrows = 6
    sql = "select IntCol from TestTempTable where rownum <= :1"
    cursor.execute(sql, [6])
    expected_value = [(f"_{x}_",) for x, in data]
    assert cursor.fetchall() == expected_value

    cursor.outputtypehandler = type_handler_2
    cursor.prefetchrows = 2
    cursor.arraysize = 2
    cursor.execute(sql, [0])
    assert cursor.fetchall() == []


def test_hooks_1077(conn, cursor):
    "1077 - output type handler: from BINARY_DOUBLE to VARCHAR"
    str_value = "36.75" if conn.thin else "3.675E+001"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_DOUBLE,
        oracledb.DB_TYPE_VARCHAR,
        36.75,
        str_value,
    )


def test_hooks_1078(conn, cursor):
    "1078 - output type handler: from BINARY_FLOAT to VARCHAR"
    str_value = "16.25" if conn.thin else "1.625E+001"
    _test_type_handler(
        cursor,
        oracledb.DB_TYPE_BINARY_FLOAT,
        oracledb.DB_TYPE_VARCHAR,
        16.25,
        str_value,
    )
