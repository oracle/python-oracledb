# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2024, Oracle and/or its affiliates.
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
3600 - Module for testing the conversions of outputtype handler.
"""

import datetime
import decimal

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def __test_type_handler(
        self, input_type, output_type, in_value, expected_out_value
    ):
        def type_handler(cursor, metadata):
            return cursor.var(output_type, arraysize=cursor.arraysize)

        self.cursor.outputtypehandler = type_handler
        self.assertEqual(self.cursor.outputtypehandler, type_handler)
        var = self.cursor.var(input_type)
        var.setvalue(0, in_value)
        self.cursor.execute("select :1 from dual", [var])
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(type(fetched_value), type(expected_out_value))
        self.assertEqual(fetched_value, expected_out_value)

    def __test_type_handler_lob(self, lob_type, output_type):
        db_type = getattr(oracledb, lob_type)

        def type_handler(cursor, metadata):
            if metadata.type_code is db_type:
                return cursor.var(output_type, arraysize=cursor.arraysize)

        self.cursor.outputtypehandler = type_handler
        in_value = f"Some {lob_type} data"
        if lob_type == "BLOB":
            in_value = in_value.encode()
        self.cursor.execute(f"delete from Test{lob_type}s")
        self.cursor.execute(
            f"""
            insert into Test{lob_type}s (IntCol, {lob_type}Col)
            values(1, :val)
            """,
            val=in_value,
        )
        self.conn.commit()
        self.cursor.execute(
            f"select {lob_type}Col, IntCol, {lob_type}Col from Test{lob_type}s"
        )
        self.assertEqual(self.cursor.fetchone(), (in_value, 1, in_value))

    def setUp(self):
        super().setUp()
        self.cursor.execute(
            """
            ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'
            NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF6'
            NLS_TIMESTAMP_TZ_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF6'
            time_zone='Europe/London'
            """
        )

    def test_3600(self):
        "3600 - output type handler: from VARCHAR to NUMBER"
        self.__test_type_handler(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, "31.5", 31.5
        )

    def test_3601(self):
        "3601 - output type handler: from CHAR to NUMBER"
        self.__test_type_handler(
            oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_NUMBER, "31.5", 31.5
        )

    def test_3602(self):
        "3602 - output type handler: from LONG to NUMBER"
        self.__test_type_handler(
            oracledb.DB_TYPE_LONG, oracledb.DB_TYPE_NUMBER, "31.5", 31.5
        )

    def test_3603(self):
        "3603 - test output type handler: from INTEGER to NUMBER"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_INTEGER, oracledb.DB_TYPE_NUMBER, 31, 31
        )

    def test_3604(self):
        "3604 - output type handler: from VARCHAR to INTEGER"
        self.__test_type_handler(
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_BINARY_INTEGER,
            "31.5",
            31,
        )

    def test_3605(self):
        "3605 - output type handler: from CHAR to INTEGER"
        self.__test_type_handler(
            oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_BINARY_INTEGER, "31.5", 31
        )

    def test_3606(self):
        "3606 - output type handler: from LONG to INTEGER"
        self.__test_type_handler(
            oracledb.DB_TYPE_LONG, oracledb.DB_TYPE_BINARY_INTEGER, "31.5", 31
        )

    def test_3607(self):
        "3607 - output type handler: from NUMBER to INTEGER"
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_BINARY_INTEGER, 31.5, 31
        )

    def test_3608(self):
        "3608 - output type handler: from DOUBLE to INTEGER"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_DOUBLE,
            oracledb.DB_TYPE_BINARY_INTEGER,
            31.5,
            31,
        )

    def test_3609(self):
        "3609 - output type handler: from FLOAT to INTEGER"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_FLOAT,
            oracledb.DB_TYPE_BINARY_INTEGER,
            31.5,
            31,
        )

    def test_3610(self):
        "3610 - output type handler: from DATE to VARCHAR"
        in_val = datetime.date(2021, 2, 1)
        out_val = "2021-02-01 00:00:00"
        self.__test_type_handler(
            oracledb.DB_TYPE_DATE, oracledb.DB_TYPE_VARCHAR, in_val, out_val
        )

    def test_3611(self):
        "3611 - output type handler: from DATE to CHAR"
        in_val = datetime.date(2021, 2, 1)
        out_val = "2021-02-01 00:00:00"
        self.__test_type_handler(
            oracledb.DB_TYPE_DATE, oracledb.DB_TYPE_CHAR, in_val, out_val
        )

    def test_3612(self):
        "3612 - output type handler: from DATE to LONG"
        in_val = datetime.date(2021, 2, 1)
        out_val = "2021-02-01 00:00:00"
        self.__test_type_handler(
            oracledb.DB_TYPE_DATE, oracledb.DB_TYPE_LONG, in_val, out_val
        )

    def test_3613(self):
        "3613 - output type handler: from NUMBER to VARCHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_VARCHAR, 31.5, "31.5"
        )
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_VARCHAR, 0, "0"
        )

    def test_3614(self):
        "3614 - output type handler: from NUMBER to CHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_CHAR, 31.5, "31.5"
        )
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_CHAR, 0, "0"
        )

    def test_3615(self):
        "3615 - output type handler: from NUMBER to LONG"
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_LONG, 31.5, "31.5"
        )

    def test_3616(self):
        "3616 - output type handler: from INTERVAL to VARCHAR"
        in_val = datetime.timedelta(
            days=-1, seconds=86314, microseconds=431152
        )
        if test_env.get_is_thin():
            out_val = str(in_val)
        else:
            out_val = "-000000001 23:58:34.431152000"
        self.__test_type_handler(
            oracledb.DB_TYPE_INTERVAL_DS,
            oracledb.DB_TYPE_VARCHAR,
            in_val,
            out_val,
        )

    def test_3617(self):
        "3617 - output type handler: from INTERVAL to CHAR"
        in_val = datetime.timedelta(
            days=-1, seconds=86314, microseconds=431152
        )
        if test_env.get_is_thin():
            out_val = str(in_val)
        else:
            out_val = "-000000001 23:58:34.431152000"
        self.__test_type_handler(
            oracledb.DB_TYPE_INTERVAL_DS,
            oracledb.DB_TYPE_CHAR,
            in_val,
            out_val,
        )

    def test_3618(self):
        "3618 - output type handler: from INTERVAL to LONG"
        in_val = datetime.timedelta(
            days=-1, seconds=86314, microseconds=431152
        )
        if test_env.get_is_thin():
            out_val = str(in_val)
        else:
            out_val = "-000000001 23:58:34.431152000"
        self.__test_type_handler(
            oracledb.DB_TYPE_INTERVAL_DS,
            oracledb.DB_TYPE_LONG,
            in_val,
            out_val,
        )

    def test_3619(self):
        "3619 - output type handler: from TIMESTAMP to VARCHAR"
        in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP,
            oracledb.DB_TYPE_VARCHAR,
            in_val,
            str(in_val),
        )

    def test_3620(self):
        "3620 - output type handler: from TIMESTAMP to CHAR"
        in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP,
            oracledb.DB_TYPE_CHAR,
            in_val,
            str(in_val),
        )

    def test_3621(self):
        "3621 - output type handler: from TIMESTAMP to LONG"
        in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP,
            oracledb.DB_TYPE_LONG,
            in_val,
            str(in_val),
        )

    def test_3622(self):
        "3622 - output type handler: from TIMESTAMP_TZ to VARCHAR"
        in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP_TZ,
            oracledb.DB_TYPE_VARCHAR,
            in_val,
            str(in_val),
        )

    def test_3623(self):
        "3623 - output type handler: from TIMESTAMP_TZ to CHAR"
        in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP_TZ,
            oracledb.DB_TYPE_CHAR,
            in_val,
            str(in_val),
        )

    def test_3624(self):
        "3624 - output type handler: from TIMESTAMP_TZ to LONG"
        in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP_TZ,
            oracledb.DB_TYPE_LONG,
            in_val,
            str(in_val),
        )

    def test_3625(self):
        "3625 - output type handler: from TIMESTAMP_LTZ to VARCHAR"
        in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP_LTZ,
            oracledb.DB_TYPE_VARCHAR,
            in_val,
            str(in_val),
        )

    def test_3626(self):
        "3626 - output type handler: from TIMESTAMP_LTZ to CHAR"
        in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP_LTZ,
            oracledb.DB_TYPE_CHAR,
            in_val,
            str(in_val),
        )

    def test_3627(self):
        "3627 - output type handler: from TIMESTAMP_LTZ to LONG"
        in_val = datetime.datetime(2002, 12, 17, 1, 2, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP_LTZ,
            oracledb.DB_TYPE_LONG,
            in_val,
            str(in_val),
        )

    def test_3628(self):
        "3628 - output type handler: from INTEGER to VARCHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_INTEGER, oracledb.DB_TYPE_VARCHAR, 31, "31"
        )

    def test_3629(self):
        "3629 - output type handler: from INTEGER to CHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_INTEGER, oracledb.DB_TYPE_CHAR, 31, "31"
        )

    def test_3630(self):
        "3630 - output type handler: from INTEGER to LONG"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_INTEGER, oracledb.DB_TYPE_LONG, 31, "31"
        )

    def test_3631(self):
        "3631 - output type handler: from NUMBER to DOUBLE"
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_BINARY_DOUBLE, 31.5, 31.5
        )

    def test_3632(self):
        "3632 - output type handler: from FLOAT to DOUBLE"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_FLOAT,
            oracledb.DB_TYPE_BINARY_DOUBLE,
            31.5,
            31.5,
        )

    def test_3633(self):
        "3633 - output type handler: from VARCHAR to DOUBLE"
        self.__test_type_handler(
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_BINARY_DOUBLE,
            "31.5",
            31.5,
        )

    def test_3634(self):
        "3634 - output type handler: from CHAR to DOUBLE"
        self.__test_type_handler(
            oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_BINARY_DOUBLE, "31.5", 31.5
        )

    def test_3635(self):
        "3635 - output type handler: from LONG to DOUBLE"
        self.__test_type_handler(
            oracledb.DB_TYPE_LONG, oracledb.DB_TYPE_BINARY_DOUBLE, "31.5", 31.5
        )

    def test_3636(self):
        "3636 - output type handler: from NUMBER to FLOAT"
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_BINARY_FLOAT, 31.5, 31.5
        )

    def test_3637(self):
        "3637 - output type handler: from DOUBLE to FLOAT"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_DOUBLE,
            oracledb.DB_TYPE_BINARY_FLOAT,
            31.5,
            31.5,
        )

    def test_3638(self):
        "3638 - output type handler: from VARCHAR to FLOAT"
        self.__test_type_handler(
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_BINARY_FLOAT,
            "31.5",
            31.5,
        )

    def test_3639(self):
        "3639 - output type handler: from CHAR to FLOAT"
        self.__test_type_handler(
            oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_BINARY_FLOAT, "31.5", 31.5
        )

    def test_3640(self):
        "3640 - output type handler: from LONG to FLOAT"
        self.__test_type_handler(
            oracledb.DB_TYPE_LONG, oracledb.DB_TYPE_BINARY_FLOAT, "31.5", 31.5
        )

    def test_3641(self):
        "3641 - output type handler: from VARCHAR to CHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_CHAR, "31.5", "31.5"
        )

    def test_3642(self):
        "3642 - output type handler: from VARCHAR to LONG"
        self.__test_type_handler(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_LONG, "31.5", "31.5"
        )

    def test_3643(self):
        "3643 - output type handler: from LONG to VARCHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_LONG, oracledb.DB_TYPE_VARCHAR, "31.5", "31.5"
        )

    def test_3644(self):
        "3644 - output type handler: from LONG to CHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_LONG, oracledb.DB_TYPE_CHAR, "31.5", "31.5"
        )

    def test_3645(self):
        "3645 - output type handler: from CHAR to VARCHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_VARCHAR, "31.5", "31.5"
        )

    def test_3646(self):
        "3646 - output type handler: from CHAR to LONG"
        self.__test_type_handler(
            oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_LONG, "31.5", "31.5"
        )

    def test_3647(self):
        "3647 - output type handler: from TIMESTAMP to TIMESTAMP_TZ"
        val = datetime.datetime(2002, 12, 17, 0, 0, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP, oracledb.DB_TYPE_TIMESTAMP_TZ, val, val
        )

    def test_3648(self):
        "3648 - output type handler: from TIMESTAMP to TIMESTAMP_LTZ"
        val = datetime.datetime(2002, 12, 17, 0, 0, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP,
            oracledb.DB_TYPE_TIMESTAMP_LTZ,
            val,
            val,
        )

    def test_3649(self):
        "3649 - output type handler: from TIMESTAMP_TZ to TIMESTAMP"
        val = datetime.datetime(2002, 12, 17, 0, 0, 16, 400000)
        self.__test_type_handler(
            oracledb.DB_TYPE_TIMESTAMP_TZ, oracledb.DB_TYPE_TIMESTAMP, val, val
        )

    def test_3650(self):
        "3650 - output type handler: from NUMBER to DATE is invalid"
        with self.assertRaisesFullCode("DPY-4007", "ORA-00932"):
            self.__test_type_handler(
                oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_DATE, 3, 3
            )

    def test_3651(self):
        "3651 - output type handler: from CLOB to CHAR"
        val = "Some Clob String"
        self.__test_type_handler(
            oracledb.DB_TYPE_CLOB, oracledb.DB_TYPE_CHAR, val, val
        )

    def test_3652(self):
        "3652 - output type handler: from CLOB to VARCHAR"
        val = "Some Clob String"
        self.__test_type_handler(
            oracledb.DB_TYPE_CLOB, oracledb.DB_TYPE_VARCHAR, val, val
        )

    def test_3653(self):
        "3653 - output type handler: from CLOB to LONG"
        val = "Some Clob String"
        self.__test_type_handler(
            oracledb.DB_TYPE_CLOB, oracledb.DB_TYPE_LONG, val, val
        )

    def test_3654(self):
        "3654 - output type handler: from BLOB to RAW"
        val = b"Some binary data"
        self.__test_type_handler(
            oracledb.DB_TYPE_BLOB, oracledb.DB_TYPE_RAW, val, val
        )

    def test_3655(self):
        "3655 - output type handler: from BLOB to LONGRAW"
        val = b"Some binary data"
        self.__test_type_handler(
            oracledb.DB_TYPE_BLOB, oracledb.DB_TYPE_LONG_RAW, val, val
        )

    def test_3656(self):
        "3656 - output type handler: from permanent BLOBs to LONG_RAW"
        self.__test_type_handler_lob("BLOB", oracledb.DB_TYPE_LONG_RAW)

    def test_3657(self):
        "3657 - output type handler: from permanent BLOBs to RAW"
        self.__test_type_handler_lob("BLOB", oracledb.DB_TYPE_RAW)

    def test_3658(self):
        "3658 - output type handler: from permanent CLOBs to VARCHAR"
        self.__test_type_handler_lob("CLOB", oracledb.DB_TYPE_VARCHAR)

    def test_3659(self):
        "3659 - output type handler: from permanent CLOBs to CHAR"
        self.__test_type_handler_lob("CLOB", oracledb.DB_TYPE_CHAR)

    def test_3660(self):
        "3660 - output type handler: from permanent CLOBs to LONG"
        self.__test_type_handler_lob("CLOB", oracledb.DB_TYPE_LONG)

    def test_3661(self):
        "3661 - output type handler: from NCLOB to CHAR"
        val = "Some nclob data"
        self.__test_type_handler(
            oracledb.DB_TYPE_NCLOB, oracledb.DB_TYPE_CHAR, val, val
        )

    def test_3662(self):
        "3662 - output type handler: from NCLOB to VARCHAR"
        val = "Some nclob data"
        self.__test_type_handler(
            oracledb.DB_TYPE_NCLOB, oracledb.DB_TYPE_VARCHAR, val, val
        )

    def test_3663(self):
        "3663 - output type handler: from NCLOB to LONG"
        val = "Some nclob data"
        self.__test_type_handler(
            oracledb.DB_TYPE_NCLOB, oracledb.DB_TYPE_LONG, val, val
        )

    def test_3664(self):
        "3664 - output type handler: from permanent NCLOBs to VARCHAR"
        self.__test_type_handler_lob("NCLOB", oracledb.DB_TYPE_VARCHAR)

    def test_3665(self):
        "3665 - output type handler: from permanent NCLOBs to CHAR"
        self.__test_type_handler_lob("NCLOB", oracledb.DB_TYPE_CHAR)

    def test_3666(self):
        "3666 - output type handler: from permanent NCLOBs to LONG"
        self.__test_type_handler_lob("NCLOB", oracledb.DB_TYPE_LONG)

    def test_3667(self):
        "3667 - output type handler: from NVARCHAR to VARCHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_NVARCHAR, oracledb.DB_TYPE_VARCHAR, "31.5", "31.5"
        )

    def test_3668(self):
        "3668 - output type handler: from VARCHAR to NVARCHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NVARCHAR, "31.5", "31.5"
        )

    def test_3669(self):
        "3669 - output type handler: from NCHAR to CHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_NCHAR, oracledb.DB_TYPE_CHAR, "31.5", "31.5"
        )

    def test_3670(self):
        "3670 - output type handler: from CHAR to NCHAR"
        self.__test_type_handler(
            oracledb.DB_TYPE_CHAR, oracledb.DB_TYPE_NCHAR, "31.5", "31.5"
        )

    def test_3671(self):
        "3671 - execute raises an error if an incorrect arraysize is used"

        def type_handler(cursor, metadata):
            return cursor.var(str)

        cursor = self.conn.cursor()
        cursor.arraysize = 100
        cursor.outputtypehandler = type_handler
        with self.assertRaisesFullCode("DPY-2016"):
            cursor.execute("select :1 from dual", [5])

    def test_3672(self):
        "3672 - execute raises an error if a var is not returned"

        def type_handler(cursor, metadata):
            return "incorrect_return"

        cursor = self.conn.cursor()
        cursor.outputtypehandler = type_handler
        with self.assertRaisesFullCode("DPY-2015"):
            cursor.execute("select :1 from dual", [5])

    def test_3673(self):
        "3673 - output type handler: from NUMBER to decimal.Decimal"
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER,
            decimal.Decimal,
            31.5,
            decimal.Decimal("31.5"),
        )
        self.__test_type_handler(
            oracledb.DB_TYPE_NUMBER, decimal.Decimal, 0, decimal.Decimal("0")
        )

    def test_3674(self):
        "3674 - use of output type handler does not affect description"

        def type_handler(cursor, metadata):
            return cursor.var(str, arraysize=cursor.arraysize)

        with self.conn.cursor() as cursor:
            cursor.execute("select user from dual")
            desc_before = cursor.description
        with self.conn.cursor() as cursor:
            cursor.outputtypehandler = type_handler
            cursor.execute("select user from dual")
            self.assertEqual(cursor.description, desc_before)

    def test_3675(self):
        "3675 - use the old signature for an output type handler"

        def type_handler(cursor, name, default_type, size, precision, scale):
            return cursor.var(str, arraysize=cursor.arraysize)

        with self.conn.cursor() as cursor:
            cursor.outputtypehandler = type_handler
            cursor.execute("select 1 from dual")
            self.assertEqual(cursor.fetchall(), [("1",)])

    def test_3676(self):
        "3676 - re-execute query with second fetch returning no rows"

        self.cursor.execute("truncate table TestTempTable")
        data = [(i + 1,) for i in range(5)]
        self.cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)", data
        )
        self.conn.commit()

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

        self.cursor.outputtypehandler = type_handler_1
        self.cursor.arraysize = 6
        self.cursor.prefetchrows = 6
        sql = "select IntCol from TestTempTable where rownum <= :1"
        self.cursor.execute(sql, [6])
        expected_value = [(f"_{x}_",) for x, in data]
        self.assertEqual(self.cursor.fetchall(), expected_value)

        self.cursor.outputtypehandler = type_handler_2
        self.cursor.prefetchrows = 2
        self.cursor.arraysize = 2
        self.cursor.execute(sql, [0])
        self.assertEqual(self.cursor.fetchall(), [])

    def test_3677(self):
        "3677 - output type handler: from BINARY_DOUBLE to VARCHAR"
        str_value = "36.75" if test_env.get_is_thin() else "3.675E+001"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_DOUBLE,
            oracledb.DB_TYPE_VARCHAR,
            36.75,
            str_value,
        )

    def test_3678(self):
        "3678 - output type handler: from BINARY_FLOAT to VARCHAR"
        str_value = "16.25" if test_env.get_is_thin() else "1.625E+001"
        self.__test_type_handler(
            oracledb.DB_TYPE_BINARY_FLOAT,
            oracledb.DB_TYPE_VARCHAR,
            16.25,
            str_value,
        )


if __name__ == "__main__":
    test_env.run_test_cases()
