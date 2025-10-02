# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
3200 - Module for testing features introduced in 12.1
"""

import datetime

import oracledb
import pytest


@pytest.fixture(autouse=True)
def skip_unless_has_client_12_1(test_env):
    """
    All tests in the file are skipped unless the client version is at least
    12.1.
    """
    if not test_env.has_client_version(12, 1):
        pytest.skip("unsupported client")


def test_3200(cursor, test_env):
    "3200 - test executing with arraydmlrowcounts mode disabled"
    cursor.execute("truncate table TestArrayDML")
    rows = [(1, "First"), (2, "Second")]
    sql = "insert into TestArrayDML (IntCol, StringCol) values (:1, :2)"
    cursor.executemany(sql, rows, arraydmlrowcounts=False)
    with test_env.assert_raises_full_code("DPY-4006"):
        cursor.getarraydmlrowcounts()
    rows = [(3, "Third"), (4, "Fourth")]
    cursor.executemany(sql, rows)
    with test_env.assert_raises_full_code("DPY-4006"):
        cursor.getarraydmlrowcounts()


def test_3201(conn, cursor):
    "3201 - test executing with arraydmlrowcounts mode enabled"
    cursor.execute("truncate table TestArrayDML")
    rows = [
        (1, "First", 100),
        (2, "Second", 200),
        (3, "Third", 300),
        (4, "Fourth", 300),
        (5, "Fifth", 300),
    ]
    cursor.executemany(
        """
        insert into TestArrayDML (IntCol, StringCol, IntCol2)
        values (:1, :2, :3)
        """,
        rows,
        arraydmlrowcounts=True,
    )
    conn.commit()
    assert cursor.getarraydmlrowcounts() == [1, 1, 1, 1, 1]
    cursor.execute("select count(*) from TestArrayDML")
    (count,) = cursor.fetchone()
    assert count == len(rows)


def test_3202(conn, cursor):
    "3202 - test binding a boolean collection (in)"
    type_obj = conn.gettype("PKG_TESTBOOLEANS.UDT_BOOLEANLIST")
    obj = type_obj.newobject()
    obj.setelement(1, True)
    obj.extend([True, False, True, True, False, True])
    result = cursor.callfunc("pkg_TestBooleans.TestInArrays", int, [obj])
    assert result == 5


def test_3203(conn, cursor):
    "3203 - test binding a boolean collection (out)"
    type_obj = conn.gettype("PKG_TESTBOOLEANS.UDT_BOOLEANLIST")
    obj = type_obj.newobject()
    cursor.callproc("pkg_TestBooleans.TestOutArrays", (6, obj))
    assert obj.aslist() == [True, False, True, False, True, False]


def test_3204(conn, cursor):
    "3204 - test binding a PL/SQL date collection (in)"
    type_obj = conn.gettype("PKG_TESTDATEARRAYS.UDT_DATELIST")
    obj = type_obj.newobject()
    obj.setelement(1, datetime.datetime(2016, 2, 5))
    obj.append(datetime.datetime(2016, 2, 8, 12, 15, 30))
    obj.append(datetime.datetime(2016, 2, 12, 5, 44, 30))
    result = cursor.callfunc(
        "pkg_TestDateArrays.TestInArrays",
        oracledb.NUMBER,
        (2, datetime.datetime(2016, 2, 1), obj),
    )
    assert result == 24.75


def test_3205(conn, cursor):
    "3205 - test binding a PL/SQL date collection (in/out)"
    type_obj = conn.gettype("PKG_TESTDATEARRAYS.UDT_DATELIST")
    obj = type_obj.newobject()
    obj.setelement(1, datetime.datetime(2016, 1, 1))
    obj.append(datetime.datetime(2016, 1, 7))
    obj.append(datetime.datetime(2016, 1, 13))
    obj.append(datetime.datetime(2016, 1, 19))
    cursor.callproc("pkg_TestDateArrays.TestInOutArrays", (4, obj))
    expected_values = [
        datetime.datetime(2016, 1, 8),
        datetime.datetime(2016, 1, 14),
        datetime.datetime(2016, 1, 20),
        datetime.datetime(2016, 1, 26),
    ]
    assert obj.aslist() == expected_values


def test_3206(conn, cursor):
    "3206 - test binding a PL/SQL date collection (out)"
    type_obj = conn.gettype("PKG_TESTDATEARRAYS.UDT_DATELIST")
    obj = type_obj.newobject()
    cursor.callproc("pkg_TestDateArrays.TestOutArrays", (3, obj))
    expected_values = [
        datetime.datetime(2002, 12, 13, 4, 48),
        datetime.datetime(2002, 12, 14, 9, 36),
        datetime.datetime(2002, 12, 15, 14, 24),
    ]
    assert obj.aslist() == expected_values


def test_3207(conn, cursor):
    "3207 - test binding a PL/SQL number collection (in)"
    type_name = "PKG_TESTNUMBERARRAYS.UDT_NUMBERLIST"
    type_obj = conn.gettype(type_name)
    obj = type_obj.newobject()
    obj.setelement(1, 10)
    obj.extend([20, 30, 40, 50])
    result = cursor.callfunc(
        "pkg_TestNumberArrays.TestInArrays", int, (5, obj)
    )
    assert result == 155


def test_3208(conn, cursor):
    "3208 - test binding a PL/SQL number collection (in/out)"
    type_name = "PKG_TESTNUMBERARRAYS.UDT_NUMBERLIST"
    type_obj = conn.gettype(type_name)
    obj = type_obj.newobject()
    obj.setelement(1, 5)
    obj.extend([8, 3, 2])
    cursor.callproc("pkg_TestNumberArrays.TestInOutArrays", (4, obj))
    assert obj.aslist() == [50, 80, 30, 20]


def test_3209(conn, cursor):
    "3209 - test binding a PL/SQL number collection (out)"
    type_name = "PKG_TESTNUMBERARRAYS.UDT_NUMBERLIST"
    type_obj = conn.gettype(type_name)
    obj = type_obj.newobject()
    cursor.callproc("pkg_TestNumberArrays.TestOutArrays", (3, obj))
    assert obj.aslist() == [100, 200, 300]


def test_3210(conn, cursor):
    "3210 - test binding an array of PL/SQL records (in)"
    rec_type = conn.gettype("PKG_TESTRECORDS.UDT_RECORD")
    array_type = conn.gettype("PKG_TESTRECORDS.UDT_RECORDARRAY")
    array_obj = array_type.newobject()
    for i in range(3):
        obj = rec_type.newobject()
        obj.NUMBERVALUE = i + 1
        obj.STRINGVALUE = f"String in record #{i + 1}"
        obj.DATEVALUE = datetime.datetime(2017, i + 1, 1)
        obj.TIMESTAMPVALUE = datetime.datetime(2017, 1, i + 1)
        obj.BOOLEANVALUE = (i % 2) == 1
        obj.PLSINTEGERVALUE = i * 5
        obj.BINARYINTEGERVALUE = i * 2
        array_obj.append(obj)
    result = cursor.callfunc("pkg_TestRecords.TestInArrays", str, [array_obj])
    expected_value = (
        "udt_Record(1, 'String in record #1', "
        "to_date('2017-01-01', 'YYYY-MM-DD'), "
        "to_timestamp('2017-01-01 00:00:00', "
        "'YYYY-MM-DD HH24:MI:SS'), false, 0, 0); "
        "udt_Record(2, 'String in record #2', "
        "to_date('2017-02-01', 'YYYY-MM-DD'), "
        "to_timestamp('2017-01-02 00:00:00', "
        "'YYYY-MM-DD HH24:MI:SS'), true, 5, 2); "
        "udt_Record(3, 'String in record #3', "
        "to_date('2017-03-01', 'YYYY-MM-DD'), "
        "to_timestamp('2017-01-03 00:00:00', "
        "'YYYY-MM-DD HH24:MI:SS'), false, 10, 4)"
    )
    assert result == expected_value


def test_3211(conn, cursor):
    "3211 - test binding a PL/SQL record (in)"
    type_obj = conn.gettype("PKG_TESTRECORDS.UDT_RECORD")
    obj = type_obj.newobject()
    obj.NUMBERVALUE = 18
    obj.STRINGVALUE = "A string in a record"
    obj.DATEVALUE = datetime.datetime(2016, 2, 15)
    obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 12, 14, 25, 36)
    obj.BOOLEANVALUE = False
    obj.PLSINTEGERVALUE = 21
    obj.BINARYINTEGERVALUE = 5
    result = cursor.callfunc("pkg_TestRecords.GetStringRep", str, [obj])
    expected_value = (
        "udt_Record(18, 'A string in a record', "
        "to_date('2016-02-15', 'YYYY-MM-DD'), "
        "to_timestamp('2016-02-12 14:25:36', "
        "'YYYY-MM-DD HH24:MI:SS'), false, 21, 5)"
    )
    assert result == expected_value


def test_3212(conn, cursor):
    "3212 - test binding a PL/SQL record (out)"
    type_obj = conn.gettype("PKG_TESTRECORDS.UDT_RECORD")
    obj = type_obj.newobject()
    obj.NUMBERVALUE = 5
    obj.STRINGVALUE = "Test value"
    obj.DATEVALUE = datetime.datetime.today()
    obj.TIMESTAMPVALUE = datetime.datetime.today()
    obj.BOOLEANVALUE = False
    obj.PLSINTEGERVALUE = 23
    obj.BINARYINTEGERVALUE = 9
    cursor.callproc("pkg_TestRecords.TestOut", [obj])
    assert obj.NUMBERVALUE == 25
    assert obj.STRINGVALUE == "String in record"
    assert obj.DATEVALUE == datetime.datetime(2016, 2, 16)
    assert obj.TIMESTAMPVALUE == datetime.datetime(2016, 2, 16, 18, 23, 55)
    assert obj.BOOLEANVALUE
    assert obj.PLSINTEGERVALUE == 45
    assert obj.BINARYINTEGERVALUE == 10


def test_3213(conn, cursor):
    "3213 - test binding a PL/SQL string collection (in)"
    type_name = "PKG_TESTSTRINGARRAYS.UDT_STRINGLIST"
    type_obj = conn.gettype(type_name)
    obj = type_obj.newobject()
    obj.setelement(1, "First element")
    obj.setelement(2, "Second element")
    obj.setelement(3, "Third element")
    result = cursor.callfunc(
        "pkg_TestStringArrays.TestInArrays", int, (5, obj)
    )
    assert result == 45


def test_3214(conn, cursor):
    "3214 - test binding a PL/SQL string collection (in/out)"
    type_name = "PKG_TESTSTRINGARRAYS.UDT_STRINGLIST"
    type_obj = conn.gettype(type_name)
    obj = type_obj.newobject()
    obj.setelement(1, "The first element")
    obj.append("The second element")
    obj.append("The third and final element")
    cursor.callproc("pkg_TestStringArrays.TestInOutArrays", (3, obj))
    expected_values = [
        "Converted element # 1 originally had length 17",
        "Converted element # 2 originally had length 18",
        "Converted element # 3 originally had length 27",
    ]
    assert obj.aslist() == expected_values


def test_3215(conn, cursor):
    "3215 - test binding a PL/SQL string collection (out)"
    type_name = "PKG_TESTSTRINGARRAYS.UDT_STRINGLIST"
    type_obj = conn.gettype(type_name)
    obj = type_obj.newobject()
    cursor.callproc("pkg_TestStringArrays.TestOutArrays", (4, obj))
    expected_values = [f"Test out element # {i + 1}" for i in range(4)]
    assert obj.aslist() == expected_values


def test_3216(conn, cursor):
    "3216 - test binding a PL/SQL string collection (out with holes)"
    type_name = "PKG_TESTSTRINGARRAYS.UDT_STRINGLIST"
    type_obj = conn.gettype(type_name)
    obj = type_obj.newobject()
    cursor.callproc("pkg_TestStringArrays.TestIndexBy", [obj])
    assert obj.first() == -1048576
    assert obj.last() == 8388608
    assert obj.next(-576) == 284
    assert obj.prev(284) == -576
    assert obj.size() == 4
    assert obj.exists(-576)
    assert not obj.exists(-577)
    assert obj.getelement(284) == "Third element"
    expected_list = [
        "First element",
        "Second element",
        "Third element",
        "Fourth element",
    ]
    assert obj.aslist() == expected_list
    expected_dict = {
        -1048576: "First element",
        -576: "Second element",
        284: "Third element",
        8388608: "Fourth element",
    }
    assert obj.asdict() == expected_dict
    obj.delete(-576)
    obj.delete(284)
    expected_list.pop(2)
    expected_list.pop(1)
    assert obj.aslist() == expected_list
    expected_dict.pop(-576)
    expected_dict.pop(284)
    assert obj.asdict() == expected_dict


def test_3217(cursor, test_env):
    "3217 - test executing with arraydmlrowcounts with exception"
    cursor.execute("truncate table TestArrayDML")
    rows = [(1, "First"), (2, "Second"), (2, "Third"), (4, "Fourth")]
    sql = "insert into TestArrayDML (IntCol,StringCol) values (:1,:2)"
    with test_env.assert_raises_full_code("ORA-00001"):
        cursor.executemany(sql, rows, arraydmlrowcounts=True)
    assert cursor.getarraydmlrowcounts() == [1, 1]


def test_3218(cursor):
    "3218 - test executing delete statement with arraydmlrowcount mode"
    cursor.execute("truncate table TestArrayDML")
    rows = [
        (1, "First", 100),
        (2, "Second", 200),
        (3, "Third", 300),
        (4, "Fourth", 300),
        (5, "Fifth", 300),
        (6, "Sixth", 400),
        (7, "Seventh", 400),
        (8, "Eighth", 500),
    ]
    cursor.executemany(
        """
        insert into TestArrayDML (IntCol, StringCol, IntCol2)
        values (:1, :2, :3)
        """,
        rows,
    )
    rows = [(200,), (300,), (400,)]
    cursor.executemany(
        "delete from TestArrayDML where IntCol2 = :1",
        rows,
        arraydmlrowcounts=True,
    )
    assert cursor.getarraydmlrowcounts() == [1, 3, 2]
    assert cursor.rowcount == 6


def test_3219(cursor):
    "3219 - test executing update statement with arraydmlrowcount mode"
    cursor.execute("truncate table TestArrayDML")
    rows = [
        (1, "First", 100),
        (2, "Second", 200),
        (3, "Third", 300),
        (4, "Fourth", 300),
        (5, "Fifth", 300),
        (6, "Sixth", 400),
        (7, "Seventh", 400),
        (8, "Eighth", 500),
    ]
    cursor.executemany(
        """
        insert into TestArrayDML (IntCol, StringCol, IntCol2)
        values (:1, :2, :3)
        """,
        rows,
    )
    rows = [("One", 100), ("Two", 200), ("Three", 300), ("Four", 400)]
    cursor.executemany(
        "update TestArrayDML set StringCol = :1 where IntCol2 = :2",
        rows,
        arraydmlrowcounts=True,
    )
    assert cursor.getarraydmlrowcounts() == [1, 1, 3, 2]
    assert cursor.rowcount == 7


def test_3220(cursor):
    "3220 - test getimplicitresults() returns the correct data"
    cursor.execute(
        """
        declare
            c1 sys_refcursor;
            c2 sys_refcursor;
        begin
            open c1 for
                select NullableCol
                from TestNumbers
                where IntCol between 3 and 5;

            dbms_sql.return_result(c1);

            open c2 for
                select NullableCol
                from TestNumbers
                where IntCol between 7 and 10;

            dbms_sql.return_result(c2);
        end;
        """
    )
    results = cursor.getimplicitresults()
    assert len(results) == 2
    assert [n for n, in results[0]] == [2924207, None, 59797108943]
    assert [n for n, in results[1]] == [
        1222791080775407,
        None,
        25004854810776297743,
        None,
    ]


def test_3221(cursor, test_env):
    "3221 - test getimplicitresults() without executing a statement"
    with test_env.assert_raises_full_code("DPY-1004"):
        cursor.getimplicitresults()


def test_3222(cursor):
    "3222 - test executing insert with multiple distinct batch errors"
    cursor.execute("truncate table TestArrayDML")
    rows = [
        (1, "First", 100),
        (2, "Second", 200),
        (2, "Third", 300),
        (4, "Fourth", 400),
        (5, "Fourth", 1000),
    ]
    cursor.executemany(
        """
        insert into TestArrayDML (IntCol, StringCol, IntCol2)
        values (:1, :2, :3)
        """,
        rows,
        batcherrors=True,
        arraydmlrowcounts=True,
    )
    actual_errors = [
        (error.offset, error.full_code) for error in cursor.getbatcherrors()
    ]
    assert actual_errors == [(4, "ORA-01438"), (2, "ORA-00001")]
    assert cursor.getarraydmlrowcounts() == [1, 1, 0, 1, 0]


def test_3223(cursor, test_env):
    "3223 - test batcherrors mode set to False"
    cursor.execute("truncate table TestArrayDML")
    rows = [(1, "First", 100), (2, "Second", 200), (2, "Third", 300)]
    sql = """insert into TestArrayDML (IntCol, StringCol, IntCol2)
             values (:1, :2, :3)"""
    with test_env.assert_raises_full_code("ORA-00001"):
        cursor.executemany(sql, rows, batcherrors=False)


def test_3224(cursor):
    "3224 - test executing in succession with batch error"
    cursor.execute("truncate table TestArrayDML")
    rows = [
        (1, "First", 100),
        (2, "Second", 200),
        (3, "Third", 300),
        (4, "Second", 300),
        (5, "Fifth", 300),
        (6, "Sixth", 400),
        (6, "Seventh", 400),
        (8, "Eighth", 100),
    ]
    cursor.executemany(
        """
        insert into TestArrayDML (IntCol, StringCol, IntCol2)
        values (:1, :2, :3)
        """,
        rows,
        batcherrors=True,
    )
    actual_errors = [
        (error.offset, error.full_code) for error in cursor.getbatcherrors()
    ]
    assert actual_errors == [(6, "ORA-00001")]
    rows = [
        (101, "First"),
        (201, "Second"),
        (3000, "Third"),
        (900, "Ninth"),
        (301, "Third"),
    ]
    cursor.executemany(
        "update TestArrayDML set IntCol2 = :1 where StringCol = :2",
        rows,
        arraydmlrowcounts=True,
        batcherrors=True,
    )
    actual_errors = [
        (error.offset, error.full_code) for error in cursor.getbatcherrors()
    ]
    assert actual_errors == [(2, "ORA-01438")]
    assert cursor.getarraydmlrowcounts() == [1, 2, 0, 0, 1]
    assert cursor.rowcount == 4


def test_3225(cursor):
    "3225 - test using implicit cursors to execute new statements"
    cursor.execute(
        """
        declare
            c1 sys_refcursor;
        begin
            open c1 for
                select NumberCol
                from TestNumbers
                where IntCol between 3 and 5;

            dbms_sql.return_result(c1);
        end;
        """
    )
    results = cursor.getimplicitresults()
    assert len(results) == 1
    assert [n for n, in results[0]] == [3.75, 5, 6.25]
    results[0].execute("select :1 from dual", [7])
    (row,) = results[0].fetchone()
    assert row == 7


def test_3226(cursor):
    "3226 - test batcherrors mode without any errors produced"
    cursor.execute("truncate table TestArrayDML")
    rows = [(1, "First", 100), (2, "Second", 200), (3, "Third", 300)]
    cursor.executemany(
        """
        insert into TestArrayDML (IntCol, StringCol, IntCol2)
        values (:1, :2, :3)
        """,
        rows,
        batcherrors=True,
    )
    assert cursor.getbatcherrors() == []


def test_3227(cursor):
    "3227 - test batcherrors mode with multiple executes"
    cursor.execute("truncate table TestArrayDML")
    rows_1 = [
        (1, "Value 1", 100),
        (2, "Value 2", 200),
        (2, "Value 2", 200),
    ]
    rows_2 = [
        (3, "Value 3", 300),
        (3, "Value 3", 300),
        (4, "Value 4", 400),
    ]
    sql = """
            insert into TestArrayDML (IntCol, StringCol, IntCol2)
            values (:1, :2, :3)"""
    cursor.executemany(sql, rows_1, batcherrors=True)
    actual_errors = [
        (error.offset, error.full_code) for error in cursor.getbatcherrors()
    ]
    assert actual_errors == [(2, "ORA-00001")]
    cursor.executemany(sql, rows_2, batcherrors=True)
    actual_errors = [
        (error.offset, error.full_code) for error in cursor.getbatcherrors()
    ]
    assert actual_errors == [(1, "ORA-00001")]


def test_3228(conn):
    "3228 - test %ROWTYPE record type"
    type_obj = conn.gettype("TESTTEMPTABLE%ROWTYPE")
    assert type_obj.attributes[3].name == "NUMBERCOL"


def test_3229(conn):
    "3229 - test collection of %ROWTYPE record type"
    type_name = "PKG_TESTBINDOBJECT.UDT_COLLECTIONROWTYPE"
    type_obj = conn.gettype(type_name)
    assert type_obj.element_type.attributes[3].name == "NUMBERCOL"


def test_3230(cursor, test_env):
    "3230 - enabling batcherrors parameter with PL/SQL"
    with test_env.assert_raises_full_code("DPY-2040"):
        cursor.executemany("begin null; end;", 30, batcherrors=True)


def test_3231(cursor, test_env):
    "3231 - enabling arraydmlrowcountsbatcherrors parameter with PL/SQL"
    with test_env.assert_raises_full_code("DPY-2040"):
        cursor.executemany("begin null; end;", 31, arraydmlrowcounts=True)


def test_3232(test_env):
    "3232 - fetch implicit cursors after closing connection"
    conn = test_env.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        declare
            c1 sys_refcursor;
            c2 sys_refcursor;
        begin
            open c1 for
                select NullableCol
                from TestNumbers;

            dbms_sql.return_result(c1);

            open c2 for
                select NullableCol
                from TestNumbers;

            dbms_sql.return_result(c2);
        end;
        """
    )
    cursor1, cursor2 = cursor.getimplicitresults()
    conn.close()
    with test_env.assert_raises_full_code("DPY-1001"):
        cursor1.fetchall()
    with test_env.assert_raises_full_code("DPY-1001"):
        cursor2.fetchall()


def test_3233(conn, test_env):
    "3233 - fetch implicit cursors after closing parent cursor"
    cursor = conn.cursor()
    cursor.execute(
        """
        declare
            c1 sys_refcursor;
            c2 sys_refcursor;
        begin
            open c1 for
                select NullableCol
                from TestNumbers
                where IntCol between 3 and 5;

            dbms_sql.return_result(c1);

            open c2 for
                select NullableCol
                from TestNumbers
                where IntCol between 7 and 10;

            dbms_sql.return_result(c2);
        end;
        """
    )
    cursor1, cursor2 = cursor.getimplicitresults()
    cursor.close()
    if conn.thin:
        assert [n for n, in cursor1] == [2924207, None, 59797108943]
        assert [n for n, in cursor2] == [
            1222791080775407,
            None,
            25004854810776297743,
            None,
        ]
    else:
        with test_env.assert_raises_full_code("DPI-1039"):
            cursor1.fetchall()
        with test_env.assert_raises_full_code("DPI-1039"):
            cursor1.fetchall()


def test_3234(conn):
    "3234 - test PL/SQL record metadata"
    rec_type = conn.gettype("PKG_TESTRECORDS.UDT_RECORD")
    expected_metadata = [
        ("NUMBERVALUE", oracledb.DB_TYPE_NUMBER, 0, -127, None),
        ("STRINGVALUE", oracledb.DB_TYPE_VARCHAR, None, None, 30),
        ("DATEVALUE", oracledb.DB_TYPE_DATE, None, None, None),
        ("TIMESTAMPVALUE", oracledb.DB_TYPE_TIMESTAMP, None, None, None),
        ("BOOLEANVALUE", oracledb.DB_TYPE_BOOLEAN, None, None, None),
        (
            "PLSINTEGERVALUE",
            oracledb.DB_TYPE_BINARY_INTEGER,
            None,
            None,
            None,
        ),
        (
            "BINARYINTEGERVALUE",
            oracledb.DB_TYPE_BINARY_INTEGER,
            None,
            None,
            None,
        ),
    ]
    actual_metadata = [
        (attr.name, attr.type, attr.precision, attr.scale, attr.max_size)
        for attr in rec_type.attributes
    ]
    assert actual_metadata == expected_metadata
