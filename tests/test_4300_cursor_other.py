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
4300 - Module for testing other cursor methods and attributes.
"""

import decimal

import oracledb


def test_4300(cursor):
    "4300 - test preparing a statement and executing it multiple times"
    assert cursor.statement is None
    statement = "begin :value := :value + 5; end;"
    cursor.prepare(statement)
    var = cursor.var(oracledb.NUMBER)
    assert cursor.statement == statement
    var.setvalue(0, 2)
    cursor.execute(None, value=var)
    assert var.getvalue() == 7
    cursor.execute(None, value=var)
    assert var.getvalue() == 12
    cursor.execute("begin :value2 := 3; end;", value2=var)
    assert var.getvalue() == 3


def test_4301(conn, test_env):
    "4301 - confirm an exception is raised after closing a cursor"
    cursor = conn.cursor()
    cursor.close()
    with test_env.assert_raises_full_code("DPY-1006"):
        cursor.execute("select 1 from dual")


def test_4302(cursor):
    "4302 - test iterators"
    cursor.execute(
        """
        select IntCol
        from TestNumbers
        where IntCol between 1 and 3
        order by IntCol
        """
    )
    rows = [v for v, in cursor]
    assert rows == [1, 2, 3]


def test_4303(cursor, test_env):
    "4303 - test iterators (with intermediate execute)"
    cursor.execute("truncate table TestTempTable")
    cursor.execute(
        """
        select IntCol
        from TestNumbers
        where IntCol between 1 and 3
        order by IntCol
        """
    )
    test_iter = iter(cursor)
    (value,) = next(test_iter)
    cursor.execute("insert into TestTempTable (IntCol) values (1)")
    with test_env.assert_raises_full_code("DPY-1003"):
        next(test_iter)


def test_4304(cursor, test_env):
    "4304 - test that bindnames() works correctly."
    with test_env.assert_raises_full_code("DPY-2002"):
        cursor.bindnames()
    cursor.prepare("begin null; end;")
    assert cursor.bindnames() == []
    cursor.prepare("begin :retval := :inval + 5; end;")
    assert cursor.bindnames() == ["RETVAL", "INVAL"]
    cursor.prepare("begin :retval := :a * :a + :b * :b; end;")
    assert cursor.bindnames() == ["RETVAL", "A", "B"]
    cursor.prepare(
        """
        begin
            :a := :b + :c + :d + :e + :f + :g + :h + :i + :j + :k + :l;
        end;
        """
    )
    names = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
    assert cursor.bindnames() == names
    cursor.prepare("select :a * :a + :b * :b from dual")
    assert cursor.bindnames() == ["A", "B"]
    cursor.prepare("select :value1 + :VaLue_2 from dual")
    assert cursor.bindnames() == ["VALUE1", "VALUE_2"]
    cursor.prepare("select :élevé, :fenêtre from dual")
    assert cursor.bindnames() == ["ÉLEVÉ", "FENÊTRE"]


def test_4305(cursor, test_env):
    "4305 - test cursor.setinputsizes() with invalid parameters"
    val = decimal.Decimal(5)
    with test_env.assert_raises_full_code("DPY-2005"):
        cursor.setinputsizes(val, x=val)
    with test_env.assert_raises_full_code("DPY-2007"):
        cursor.setinputsizes(val)


def test_4306(cursor):
    "4306 - test setting input sizes without any parameters"
    cursor.setinputsizes()
    cursor.execute("select :val from dual", val="Test Value")
    assert cursor.fetchall() == [("Test Value",)]


def test_4307(cursor):
    "4307 - test setting input sizes with an empty dictionary"
    empty_dict = {}
    cursor.prepare("select 236 from dual")
    cursor.setinputsizes(**empty_dict)
    cursor.execute(None, empty_dict)
    assert cursor.fetchall() == [(236,)]


def test_4308(cursor):
    "4308 - test setting input sizes with an empty list"
    empty_list = []
    cursor.prepare("select 239 from dual")
    cursor.setinputsizes(*empty_list)
    cursor.execute(None, empty_list)
    assert cursor.fetchall() == [(239,)]


def test_4309(cursor):
    "4309 - test setting input sizes with positional args"
    var = cursor.var(oracledb.STRING, 100)
    cursor.setinputsizes(None, 5, None, 10, None, oracledb.NUMBER)
    cursor.execute(
        """
        begin
          :1 := :2 || to_char(:3) || :4 || to_char(:5) || to_char(:6);
        end;
        """,
        [var, "test_", 5, "_second_", 3, 7],
    )
    assert var.getvalue() == "test_5_second_37"


def test_4310(conn, cursor):
    "4310 - test Cursor repr()"
    expected_value = f"<oracledb.Cursor on {conn}>"
    assert str(cursor) == expected_value
    assert repr(cursor) == expected_value


def test_4311(cursor):
    "4311 - test parsing query statements"
    sql = "select LongIntCol from TestNumbers where IntCol = :val"
    cursor.parse(sql)
    assert cursor.statement == sql
    assert cursor.description == [
        ("LONGINTCOL", oracledb.DB_TYPE_NUMBER, 17, None, 16, 0, 0)
    ]


def test_4312(cursor):
    "4312 - test cursor.setoutputsize() does not fail (but does nothing)"
    cursor.setoutputsize(100, 2)


def test_4313(cursor, test_env):
    "4313 - test cursor.var() with invalid parameters"
    with test_env.assert_raises_full_code("DPY-2007"):
        cursor.var(5)


def test_4314(cursor, test_env):
    "4314 - test cursor.arrayvar() with invalid parameters"
    with test_env.assert_raises_full_code("DPY-2007"):
        cursor.arrayvar(5, 1)


def test_4315(cursor):
    "4315 - test binding boolean data without the use of PL/SQL"
    cursor.execute("truncate table TestTempTable")
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    cursor.execute(sql, (False, "Value should be 0"))
    cursor.execute(sql, (True, "Value should be 1"))
    cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    expected_value = [(0, "Value should be 0"), (1, "Value should be 1")]
    assert cursor.fetchall() == expected_value


def test_4316(conn, test_env):
    "4316 - test using a cursor as a context manager"
    with conn.cursor() as cursor:
        cursor.execute("truncate table TestTempTable")
        cursor.execute("select count(*) from TestTempTable")
        (count,) = cursor.fetchone()
        assert count == 0
    with test_env.assert_raises_full_code("DPY-1006"):
        cursor.close()


def test_4317(cursor):
    "4317 - test that rowcount attribute is reset to zero on query execute"
    for num in [0, 1, 1, 0]:
        cursor.execute("select * from dual where 1 = :s", [num])
        cursor.fetchone()
        assert cursor.rowcount == num


def test_4318(cursor):
    "4318 - test that the typename attribute can be passed a value of None"
    value_to_set = 5
    var = cursor.var(int, typename=None)
    var.setvalue(0, value_to_set)
    assert var.getvalue() == value_to_set


def test_4319(conn, cursor):
    "4319 - test that an object type can be used as type in cursor.var()"
    obj_type = conn.gettype("UDT_OBJECT")
    var = cursor.var(obj_type)
    cursor.callproc(
        "pkg_TestBindObject.BindObjectOut", (28, "Bind obj out", var)
    )
    obj = var.getvalue()
    result = cursor.callfunc("pkg_TestBindObject.GetStringRep", str, (obj,))
    exp = "udt_Object(28, 'Bind obj out', null, null, null, null, null)"
    assert result == exp


def test_4320(cursor):
    "4320 - test that fetching an XMLType returns a string"
    int_val = 5
    label = "IntCol"
    expected_result = f"<{label}>{int_val}</{label}>"
    cursor.execute(
        f"""
        select XMLElement("{label}", IntCol)
        from TestStrings
        where IntCol = :int_val
        """,
        int_val=int_val,
    )
    (result,) = cursor.fetchone()
    assert result == expected_result


def test_4321(cursor):
    "4321 - test last rowid"

    # no statement executed: no rowid
    assert cursor.lastrowid is None

    # DDL statement executed: no rowid
    cursor.execute("truncate table TestTempTable")
    assert cursor.lastrowid is None

    # statement prepared: no rowid
    cursor.prepare("insert into TestTempTable (IntCol) values (:1)")
    assert cursor.lastrowid is None

    # multiple rows inserted: rowid of last row inserted
    rows = [(n,) for n in range(225)]
    cursor.executemany(None, rows)
    rowid = cursor.lastrowid
    cursor.execute(
        """
        select rowid
        from TestTempTable
        where IntCol = :1
        """,
        rows[-1],
    )
    assert cursor.fetchone()[0] == rowid

    # statement executed but no rows updated: no rowid
    cursor.execute("delete from TestTempTable where 1 = 0")
    assert cursor.lastrowid is None

    # stetement executed with one row updated: rowid of updated row
    cursor.execute(
        """
        update TestTempTable set StringCol1 = 'Modified'
        where IntCol = :1
        """,
        rows[-2],
    )
    rowid = cursor.lastrowid
    cursor.execute(
        "select rowid from TestTempTable where IntCol = :1",
        rows[-2],
    )
    assert cursor.fetchone()[0] == rowid

    # statement executed with many rows updated: rowid of last updated row
    cursor.execute(
        """
        update TestTempTable set
            StringCol1 = 'Row ' || to_char(IntCol)
        where IntCol = :1
        """,
        rows[-3],
    )
    rowid = cursor.lastrowid
    cursor.execute(
        "select StringCol1 from TestTempTable where rowid = :1",
        [rowid],
    )
    assert cursor.fetchone()[0] == "Row %s" % rows[-3]


def test_4322(conn, round_trip_checker):
    "4322 - test prefetch rows"

    # perform simple query and verify only one round trip is needed
    with conn.cursor() as cursor:
        cursor.execute("select sysdate from dual").fetchall()
        assert round_trip_checker.get_value() == 1

    # set prefetchrows to 1 and verify that two round trips are now needed
    with conn.cursor() as cursor:
        cursor.prefetchrows = 1
        assert cursor.prefetchrows == 1
        cursor.execute("select sysdate from dual").fetchall()
        assert round_trip_checker.get_value() == 2

    # simple DDL only requires a single round trip
    with conn.cursor() as cursor:
        cursor.execute("truncate table TestTempTable")
        assert round_trip_checker.get_value() == 1

    # array execution only requires a single round trip
    num_rows = 590
    with conn.cursor() as cursor:
        data = [(n + 1,) for n in range(num_rows)]
        cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)",
            data,
        )
        assert round_trip_checker.get_value() == 1

    # setting prefetch and array size to 1 requires a round-trip for each
    # row
    with conn.cursor() as cursor:
        cursor.arraysize = 1
        cursor.prefetchrows = 1
        assert cursor.prefetchrows == 1
        cursor.execute("select IntCol from TestTempTable").fetchall()
        assert round_trip_checker.get_value() == num_rows + 1

    # setting prefetch and array size to 300 requires 2 round-trips
    with conn.cursor() as cursor:
        cursor.arraysize = 300
        cursor.prefetchrows = 300
        assert cursor.prefetchrows == 300
        cursor.execute("select IntCol from TestTempTable").fetchall()
        assert round_trip_checker.get_value() == 2


def test_4323(conn, round_trip_checker):
    "4323 - test prefetch rows using existing cursor"

    # Set prefetch rows on an existing cursor
    num_rows = 590
    with conn.cursor() as cursor:
        cursor.execute("truncate table TestTempTable")
        assert round_trip_checker.get_value() == 1
        data = [(n + 1,) for n in range(num_rows)]
        cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)",
            data,
        )
        assert round_trip_checker.get_value() == 1
        cursor.prefetchrows = 30
        cursor.arraysize = 100
        cursor.execute("select IntCol from TestTempTable").fetchall()
        assert round_trip_checker.get_value() == 7


def test_4324(cursor):
    "4324 - test parsing plsql statements"
    sql = "begin :value := 5; end;"
    cursor.parse(sql)
    assert cursor.statement == sql
    assert cursor.description is None


def test_4325(cursor):
    "4325 - test parsing ddl statements"
    sql = "truncate table TestTempTable"
    cursor.parse(sql)
    assert cursor.statement == sql
    assert cursor.description is None


def test_4326(cursor):
    "4326 - test parsing dml statements"
    sql = "insert into TestTempTable (IntCol) values (1)"
    cursor.parse(sql)
    assert cursor.statement == sql
    assert cursor.description is None


def test_4327(cursor, test_env):
    "4327 - test to verify encodingErrors is deprecated"
    errors = "strict"
    with test_env.assert_raises_full_code("DPY-2014"):
        cursor.var(
            oracledb.NUMBER, encoding_errors=errors, encodingErrors=errors
        )


def test_4328(cursor, test_env):
    "4328 - test arrays of arrays not supported"
    simple_var = cursor.arrayvar(oracledb.NUMBER, 3)
    with test_env.assert_raises_full_code("DPY-3005"):
        simple_var.setvalue(1, [1, 2, 3])


def test_4329(cursor, test_env):
    "4329 - test cursor.setinputsizes() with invalid list parameters"
    with test_env.assert_raises_full_code("DPY-2011"):
        cursor.setinputsizes([int, 2, 10])


def test_4330(cursor, test_env):
    "4330 - test unsupported python type on cursor"
    with test_env.assert_raises_full_code("DPY-3003"):
        cursor.var(list)


def test_4331(cursor):
    "4331 - test binding by name with leading colon"
    params = {":arg1": 5}
    cursor.execute("select :arg1 from dual", params)
    (result,) = cursor.fetchone()
    assert result == params[":arg1"]


def test_4332(cursor):
    "4332 - test binding mixed null and not null values in a PL/SQL block"
    out_vars = [cursor.var(str) for i in range(4)]
    cursor.execute(
        """
        begin
            :1 := null;
            :2 := 'Value 1';
            :3 := null;
            :4 := 'Value 2';
        end;
        """,
        out_vars,
    )
    values = [var.getvalue() for var in out_vars]
    assert values == [None, "Value 1", None, "Value 2"]


def test_4333(conn, parse_count_checker):
    "4333 - test excluding statement from statement cache"
    num_iters = 10
    sql = "select user from dual"

    # with statement cache enabled, only one parse should take place
    for i in range(num_iters):
        with conn.cursor() as cursor:
            cursor.execute(sql)
    assert parse_count_checker.get_value() == 1

    # with statement cache disabled for the statement, parse count should
    # be the same as the number of iterations
    for i in range(num_iters):
        with conn.cursor() as cursor:
            cursor.prepare(sql, cache_statement=False)
            cursor.execute(None)
    assert parse_count_checker.get_value() == num_iters - 1


def test_4334(cursor):
    "4334 - test repeated DDL"
    cursor.execute("truncate table TestTempTable")
    cursor.execute("insert into TestTempTable (IntCol) values (1)")
    cursor.execute("truncate table TestTempTable")
    cursor.execute("insert into TestTempTable (IntCol) values (1)")


def test_4335(cursor):
    "4335 - test executing SQL with non-ASCII characters"
    cursor.execute("select 'FÖÖ' from dual")
    (result,) = cursor.fetchone()
    assert result in ("FÖÖ", "F¿¿")


def test_4336(cursor):
    "4336 - test case sensitivity of unquoted bind names"
    cursor.execute("select :test from dual", {"TEST": "a"})
    (result,) = cursor.fetchone()
    assert result == "a"


def test_4337(cursor, test_env):
    "4337 - test case sensitivity of quoted bind names"
    with test_env.assert_raises_full_code("ORA-01036", "DPY-4008"):
        cursor.execute('select :"test" from dual', {'"TEST"': "a"})


def test_4338(cursor, test_env):
    "4338 - test using a reserved keywords as a bind name"
    sql = "select :ROWID from dual"
    with test_env.assert_raises_full_code("ORA-01745"):
        cursor.parse(sql)


def test_4339(conn):
    "4339 - test array size less than prefetch rows"
    for i in range(2):
        with conn.cursor() as cursor:
            cursor.arraysize = 1
            cursor.execute("select 1 from dual union select 2 from dual")
            assert cursor.fetchall() == [(1,), (2,)]


def test_4340(conn, cursor):
    "4340 - test re-executing a query with blob as bytes"

    def type_handler(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_BLOB:
            return cursor.var(bytes, arraysize=cursor.arraysize)

    conn.outputtypehandler = type_handler
    blob_data = b"An arbitrary set of blob data for test case 4348"
    cursor.execute("delete from TestBLOBs")
    cursor.execute(
        "insert into TestBLOBs (IntCol, BlobCol) values (1, :data)",
        [blob_data],
    )
    cursor.execute("select IntCol, BlobCol from TestBLOBs")
    assert cursor.fetchall() == [(1, blob_data)]

    cursor.execute("delete from TestBLOBs")
    cursor.execute(
        "insert into TestBLOBs (IntCol, BlobCol) values (1, :data)",
        [blob_data],
    )
    cursor.execute("select IntCol, BlobCol from TestBLOBs")
    assert cursor.fetchall() == [(1, blob_data)]


def test_4341(cursor, test_env):
    "4341 - test re-executing a statement after raising an error"
    sql = "select * from TestFakeTable"
    with test_env.assert_raises_full_code("ORA-00942"):
        cursor.execute(sql)
    with test_env.assert_raises_full_code("ORA-00942"):
        cursor.execute(sql)

    sql = "insert into TestStrings (StringCol) values (NULL)"
    with test_env.assert_raises_full_code("ORA-01400"):
        cursor.execute(sql)
    with test_env.assert_raises_full_code("ORA-01400"):
        cursor.execute(sql)


def test_4342(conn):
    "4342 - test executing a statement that raises ORA-01007"
    with conn.cursor() as cursor:
        cursor.execute(
            """
            create or replace view ora_1007 as
                select 1 as SampleNumber, 'String' as SampleString,
                    'Another String' as AnotherString
                from dual
            """
        )
    with conn.cursor() as cursor:
        cursor.execute("select * from ora_1007")
        assert cursor.fetchone() == (1, "String", "Another String")
    with conn.cursor() as cursor:
        cursor.execute(
            """
            create or replace view ora_1007 as
                select 1 as SampleNumber,
                    'Another String' as AnotherString
                from dual
            """
        )
    with conn.cursor() as cursor:
        cursor.execute("select * from ora_1007")
        assert cursor.fetchone() == (1, "Another String")


def test_4343(cursor):
    "4343 - test updating an empty row"
    int_var = cursor.var(int)
    cursor.execute("truncate table TestTempTable")
    cursor.execute(
        """
        begin
            update TestTempTable set IntCol = :1
            where StringCol1 = :2
            returning IntCol into :3;
        end;
        """,
        [1, "test string 4352", int_var],
    )
    assert int_var.values == [None]


def test_4344(conn):
    "4344 - fetch duplicate data from query in statement cache"
    sql = """
            select 'A', 'B', 'C' from dual
            union all
            select 'A', 'B', 'C' from dual
            union all
            select 'A', 'B', 'C' from dual"""
    expected_data = [("A", "B", "C")] * 3
    with conn.cursor() as cursor:
        cursor.prefetchrows = 0
        cursor.execute(sql)
        assert cursor.fetchall() == expected_data
    with conn.cursor() as cursor:
        cursor.prefetchrows = 0
        cursor.execute(sql)
        assert cursor.fetchall() == expected_data


def test_4345(cursor):
    "4345 - fetch duplicate data with outconverter"

    def out_converter(value):
        assert isinstance(value, str)
        return int(value)

    def type_handler(cursor, metadata):
        if metadata.name == "COL_3":
            return cursor.var(
                str, arraysize=cursor.arraysize, outconverter=out_converter
            )

    cursor.outputtypehandler = type_handler
    cursor.execute(
        """
        select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
            union all
        select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
            union all
        select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
        """
    )
    expected_data = [("A", 2, 3)] * 3
    assert cursor.fetchall() == expected_data


def test_4346(cursor):
    "4346 - test setinputsizes() with defaults specified"
    cursor.setinputsizes(None, str)
    assert cursor.bindvars[0] is None
    assert isinstance(cursor.bindvars[1], oracledb.Var)
    cursor.setinputsizes(a=None, b=str)
    assert cursor.bindvars.get("a") is None
    assert isinstance(cursor.bindvars["b"], oracledb.Var)


def test_4347(skip_if_drcp, test_env):
    "4547 - kill connection with open cursor"
    admin_conn = test_env.get_admin_connection()
    conn = test_env.get_connection()
    assert conn.is_healthy()
    sid, serial = test_env.get_sid_serial(conn)
    with admin_conn.cursor() as admin_cursor:
        sql = f"alter system kill session '{sid},{serial}'"
        admin_cursor.execute(sql)
    with test_env.assert_raises_full_code("DPY-4011"):
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
    assert not conn.is_healthy()


def test_4348(skip_if_drcp, test_env):
    "4348 - kill connection in cursor context manager"
    admin_conn = test_env.get_admin_connection()
    conn = test_env.get_connection()
    assert conn.is_healthy()
    sid, serial = test_env.get_sid_serial(conn)
    with admin_conn.cursor() as admin_cursor:
        admin_cursor.execute(f"alter system kill session '{sid},{serial}'")
    with test_env.assert_raises_full_code("DPY-4011"):
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
    assert not conn.is_healthy()


def test_4349(conn, test_env):
    "4349 - fetchmany() with and without parameters"
    sql_part = "select user from dual"
    sql = " union all ".join([sql_part] * 10)
    with conn.cursor() as cursor:
        cursor.arraysize = 6
        cursor.execute(sql)
        rows = cursor.fetchmany()
        assert len(rows) == cursor.arraysize
        cursor.execute(sql)
        rows = cursor.fetchmany(size=2)
        assert len(rows) == 2
        cursor.execute(sql)
        rows = cursor.fetchmany(numRows=4)
        assert len(rows) == 4
        cursor.execute(sql)
        with test_env.assert_raises_full_code("DPY-2014"):
            cursor.fetchmany(size=2, numRows=4)


def test_4350(conn):
    "4350 - access cursor.rowcount after closing cursor"
    with conn.cursor() as cursor:
        cursor.execute("select user from dual")
        cursor.fetchall()
        assert cursor.rowcount == 1
    assert cursor.rowcount == -1


def test_4351(disable_fetch_lobs, cursor, test_env):
    "4351 - changing bind type with define needed"
    cursor.execute("delete from TestClobs")
    row_for_1 = (1, "Short value 1")
    row_for_56 = (56, "Short value 56")
    for data in (row_for_1, row_for_56):
        cursor.execute(
            "insert into TestClobs (IntCol, ClobCol) values (:1, :2)",
            data,
        )
    sql = "select IntCol, ClobCol from TestClobs where IntCol = :int_col"
    cursor.execute(sql, int_col="1")
    assert cursor.fetchone() == row_for_1
    cursor.execute(sql, int_col="56")
    assert cursor.fetchone() == row_for_56
    cursor.execute(sql, int_col=1)
    assert cursor.fetchone() == row_for_1


def test_4352(cursor):
    "4352 - test calling cursor.parse() twice with the same statement"
    cursor.execute("truncate table TestTempTable")
    data = (4363, "Value for test 4363")
    cursor.execute(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        data,
    )
    sql = "update TestTempTable set StringCol1 = :v where IntCol = :i"
    for i in range(2):
        cursor.parse(sql)
        cursor.execute(sql, ("Updated value", data[0]))


def test_4353(conn, cursor):
    "4353 - test addition of column to cached query"
    table_name = "test_4365"
    try:
        cursor.execute(f"drop table {table_name}")
    except oracledb.DatabaseError:
        pass
    data = ("val 1", "val 2")
    cursor.execute(f"create table {table_name} (col1 varchar2(10))")
    cursor.execute(f"insert into {table_name} values (:1)", [data[0]])
    conn.commit()
    cursor.execute(f"select * from {table_name}")
    assert cursor.fetchall() == [(data[0],)]
    cursor.execute(f"alter table {table_name} add col2 varchar2(10)")
    cursor.execute(f"update {table_name} set col2 = :1", [data[1]])
    conn.commit()
    cursor.execute(f"select * from {table_name}")
    assert cursor.fetchall() == [data]


def test_4354(cursor, test_env):
    "4354 - test population of array var with too many elements"
    var = cursor.arrayvar(int, 3)
    with test_env.assert_raises_full_code("DPY-2016"):
        var.setvalue(0, [1, 2, 3, 4])


def test_4355(cursor):
    "4355 - test executemany() with PL/SQL and increasing data lengths"
    sql = "begin :1 := length(:2); end;"
    var = cursor.var(int, arraysize=3)
    cursor.executemany(sql, [(var, "one"), (var, "two"), (var, "end")])
    assert var.values == [3, 3, 3]
    cursor.executemany(sql, [(var, "three"), (var, "four"), (var, "end")])
    assert var.values == [5, 4, 3]
    cursor.executemany(sql, [(var, "five"), (var, "six"), (var, "end")])
    assert var.values == [4, 3, 3]


def test_4356(cursor):
    "4356 - test cursor.rowcount values for queries"
    max_rows = 93
    cursor.arraysize = 10
    cursor.execute(
        "select rownum as id from dual connect by rownum <= :1",
        [max_rows],
    )
    assert cursor.rowcount == 0
    batch_num = 1
    while True:
        rows = cursor.fetchmany()
        if not rows:
            break
        expected_value = min(max_rows, batch_num * cursor.arraysize)
        assert cursor.rowcount == expected_value
        batch_num += 1
    cursor.fetchall()
    assert cursor.rowcount == max_rows


def test_4357(disable_fetch_lobs, conn, cursor, test_env):
    "4357 - test bind order for PL/SQL"
    cursor.execute("delete from TestClobs")
    sql = """
        insert into TestClobs (IntCol, CLOBCol, ExtraNumCol1)
        values (:1, :2, :3)"""
    data = "x" * 9000
    rows = [(1, data, 5), (2, data, 6)]
    cursor.execute(sql, rows[0])
    plsql = f"begin {sql}; end;"
    cursor.execute(plsql, rows[1])
    conn.commit()
    cursor.execute(
        """
        select IntCol, CLOBCol, ExtraNumCol1
        from TestCLOBs
        order by IntCol
        """
    )
    assert cursor.fetchall() == rows


def test_4358(disable_fetch_lobs, cursor, test_env):
    "4358 - test rebuild of table with LOB in cached query (as string)"
    table_name = "test_4370"
    drop_sql = f"drop table {table_name} purge"
    create_sql = f"""
        create table {table_name} (
            Col1 number(9) not null,
            Col2 clob not null
        )"""
    insert_sql = f"insert into {table_name} values (:1, :2)"
    query_sql = f"select * from {table_name} order by Col1"
    data = [(1, "CLOB value 1"), (2, "CLOB value 2")]
    try:
        cursor.execute(drop_sql)
    except oracledb.DatabaseError:
        pass
    cursor.execute(create_sql)
    cursor.executemany(insert_sql, data)
    cursor.execute(query_sql)
    assert cursor.fetchall() == data
    cursor.execute(query_sql)
    assert cursor.fetchall() == data
    cursor.execute(drop_sql)
    cursor.execute(create_sql)
    cursor.executemany(insert_sql, data)
    cursor.execute(query_sql)
    assert cursor.fetchall() == data


def test_4359(cursor):
    "4359 - test rebuild of table with LOB in cached query (as LOB)"
    table_name = "test_4371"
    drop_sql = f"drop table {table_name} purge"
    create_sql = f"""
        create table {table_name} (
            Col1 number(9) not null,
            Col2 clob not null)"""
    insert_sql = f"insert into {table_name} values (:1, :2)"
    query_sql = f"select * from {table_name} order by Col1"
    data = [(1, "CLOB value 1"), (2, "CLOB value 2")]
    try:
        cursor.execute(drop_sql)
    except oracledb.DatabaseError:
        pass
    cursor.execute(create_sql)
    cursor.executemany(insert_sql, data)
    cursor.execute(query_sql)
    fetched_data = [(n, c.read()) for n, c in cursor]
    assert fetched_data == data
    cursor.execute(query_sql)
    fetched_data = [(n, c.read()) for n, c in cursor]
    assert fetched_data == data
    cursor.execute(drop_sql)
    cursor.execute(create_sql)
    cursor.executemany(insert_sql, data)
    cursor.execute(query_sql)
    fetched_data = [(n, c.read()) for n, c in cursor]
    assert fetched_data == data


def test_4360(skip_unless_json_supported, cursor, test_env):
    "4360 - fetch JSON columns as Python objects"
    test_env.skip_unless_server_version(21)
    expected_data = [
        (1, [1, 2, 3], [4, 5, 6], [7, 8, 9]),
        (2, None, None, None),
    ]
    cursor.execute("select * from TestJsonCols order by IntCol")
    assert cursor.fetchall() == expected_data


def test_4361(skip_unless_domains_supported, cursor, test_env):
    "4361 - fetch table with domain and annotations"
    cursor.execute("select * from TableWithDomainAndAnnotations")
    assert cursor.fetchall() == [(1, 25)]
    column_1 = cursor.description[0]
    assert column_1.domain_schema is None
    assert column_1.domain_name is None
    assert column_1.annotations is None
    column_2 = cursor.description[1]
    assert column_2.domain_schema == test_env.main_user.upper()
    assert column_2.domain_name == "SIMPLEDOMAIN"
    expected_annotations = {
        "ANNO_1": "first annotation",
        "ANNO_2": "second annotation",
        "ANNO_3": "",
    }
    assert column_2.annotations == expected_annotations


def test_4362(cursor):
    "4362 - test getting statement after it was executed"
    sql = "select 1 from dual"
    cursor.execute(sql)
    assert cursor.statement == sql


def test_4363(cursor):
    "4363 - test getting cursor fetchvars"
    assert cursor.fetchvars is None

    cursor.execute("truncate table TestTempTable")
    cursor.execute(
        "insert into TestTempTable (IntCol, StringCol1) values (1, '12')",
    )
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    cursor.fetchall()
    assert len(cursor.fetchvars) == 2
    assert cursor.fetchvars[0].getvalue() == 1
    assert cursor.fetchvars[1].getvalue() == "12"


def test_4364(cursor):
    "4364 - test fetchmany() with non-default cursor.arraysize"
    cursor.arraysize = 20
    values = [(i,) for i in range(30)]
    cursor.execute("truncate table TestTempTable")
    cursor.executemany(
        "insert into TestTempTable (IntCol) values (:1)", values
    )
    cursor.execute("select IntCol from TestTempTable order by IntCol")
    # fetch first 20 elements
    fetched_values = cursor.fetchmany()
    assert fetched_values == values[: cursor.arraysize]

    # fetch missing elements
    fetched_values = cursor.fetchmany()
    assert fetched_values == values[cursor.arraysize :]


def test_4365(cursor, test_env):
    "4365 - negative tests for cursor.arraysize"
    with test_env.assert_raises_full_code("DPY-2045"):
        cursor.arraysize = 0
    with test_env.assert_raises_full_code("DPY-2045"):
        cursor.arraysize = -1
    with test_env.assert_raises_full_code("DPY-2045"):
        cursor.arraysize = "not valid"


def test_4366(cursor, test_env):
    "4366 - test fetching LOBs after an error"
    sql = """
        select
            to_clob(:val),
            1 / (dbms_lob.getlength(to_clob(:val)) - 1)
        from dual"""
    with test_env.assert_raises_full_code("ORA-01476"):
        cursor.execute(sql, val="a")
        cursor.fetchall()
    cursor.execute(sql, val="bb")
    lob, num_val = cursor.fetchone()
    assert lob.read() == "bb"
    assert num_val == 1


def test_4367(conn):
    "4367 - test parse() with autocommit enabled"
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("truncate table TestTempTable")
    cursor.parse("insert into TestTempTable (IntCol) values (:1)")
    cursor.execute(None, [1])


def test_4368(cursor, test_env):
    "4368 - test cursor.setinputsizes() with early failed execute"
    cursor.setinputsizes(a=int, b=str)
    with test_env.assert_raises_full_code("DPY-2006"):
        cursor.execute("select :c from dual", [5])
    value = 4368
    cursor.execute("select :d from dual", [value])
    (fetched_value,) = cursor.fetchone()
    assert fetched_value == value


def test_4369(test_env):
    "4369 - access cursor.rowcount after closing connection"
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
    assert cursor.rowcount == -1


def test_4370(conn, cursor):
    "4370 - execute PL/SQL with out vars after query with duplicate data"
    cursor.execute("truncate table TestTempTable")
    cursor.executemany(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        [(i + 1, "test_4370") for i in range(20)],
    )
    conn.commit()
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    var = cursor.var(int)
    cursor.execute("begin :1 := 4370; end;", [var])
    assert var.getvalue() == 4370


def test_4371(cursor):
    "4371 - test cursor with fetch_decimals=True specified"
    value = 4371
    cursor.execute("select :1 from dual", [value], fetch_decimals=True)
    rows = cursor.fetchall()
    assert isinstance(rows[0][0], decimal.Decimal)


def test_4372(cursor):
    "4372 - test cursor.parse() uses oracledb.defaults.fetch_lobs"
    cursor.parse("select to_clob('some_value') from dual")
    fetch_info = cursor.description[0]
    assert fetch_info.type is oracledb.DB_TYPE_CLOB
