# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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
6300 - Module for testing other cursor methods and attributes with asyncio.
"""

import decimal

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def test_6300(async_cursor):
    "6300 - test preparing a statement and executing it multiple times"
    assert async_cursor.statement is None
    statement = "begin :value := :value + 5; end;"
    async_cursor.prepare(statement)
    var = async_cursor.var(oracledb.NUMBER)
    assert async_cursor.statement == statement
    var.setvalue(0, 2)
    await async_cursor.execute(None, value=var)
    assert var.getvalue() == 7
    await async_cursor.execute(None, value=var)
    assert var.getvalue() == 12
    await async_cursor.execute("begin :value2 := 3; end;", value2=var)
    assert var.getvalue() == 3


async def test_6301(async_conn, test_env):
    "6301 - confirm an exception is raised after closing a cursor"
    with async_conn.cursor() as cursor:
        pass
    with test_env.assert_raises_full_code("DPY-1006"):
        await cursor.execute("select 1 from dual")


async def test_6302(async_cursor):
    "6302 - test iterators"
    await async_cursor.execute(
        """
        select IntCol
        from TestNumbers
        where IntCol between 1 and 3
        order by IntCol
        """
    )
    rows = [v async for v, in async_cursor]
    assert rows == [1, 2, 3]


async def test_6303(async_cursor, test_env):
    "6303 - test iterators (with intermediate execute)"
    await async_cursor.execute("truncate table TestTempTable")
    await async_cursor.execute(
        """
        select IntCol
        from TestNumbers
        where IntCol between 1 and 3
        order by IntCol
        """
    )
    test_iter = async_cursor.__aiter__()
    (value,) = await test_iter.__anext__()
    await async_cursor.execute("insert into TestTempTable (IntCol) values (1)")
    with test_env.assert_raises_full_code("DPY-1003"):
        await test_iter.__anext__()


async def test_6304(async_cursor):
    "6304 - test setting input sizes without any parameters"
    async_cursor.setinputsizes()
    await async_cursor.execute("select :val from dual", val="Test Value")
    assert await async_cursor.fetchall() == [("Test Value",)]


async def test_6305(async_cursor):
    "6305 - test setting input sizes with an empty dictionary"
    empty_dict = {}
    async_cursor.prepare("select 236 from dual")
    async_cursor.setinputsizes(**empty_dict)
    await async_cursor.execute(None, empty_dict)
    assert await async_cursor.fetchall() == [(236,)]


async def test_6306(async_cursor):
    "6306 - test setting input sizes with an empty list"
    empty_list = []
    async_cursor.prepare("select 239 from dual")
    async_cursor.setinputsizes(*empty_list)
    await async_cursor.execute(None, empty_list)
    assert await async_cursor.fetchall() == [(239,)]


async def test_6307(async_cursor):
    "6307 - test setting input sizes with positional args"
    var = async_cursor.var(oracledb.STRING, 100)
    async_cursor.setinputsizes(None, 5, None, 10, None, oracledb.NUMBER)
    await async_cursor.execute(
        """
        begin
          :1 := :2 || to_char(:3) || :4 || to_char(:5) || to_char(:6);
        end;
        """,
        [var, "test_", 5, "_second_", 3, 7],
    )
    assert var.getvalue() == "test_5_second_37"


async def test_6308(async_cursor):
    "6308 - test parsing query statements"
    sql = "select LongIntCol from TestNumbers where IntCol = :val"
    await async_cursor.parse(sql)
    assert async_cursor.statement == sql
    assert async_cursor.description == [
        ("LONGINTCOL", oracledb.DB_TYPE_NUMBER, 17, None, 16, 0, 0)
    ]


async def test_6309(async_cursor):
    "6309 - test binding boolean data without the use of PL/SQL"
    await async_cursor.execute("truncate table TestTempTable")
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    await async_cursor.execute(sql, (False, "Value should be 0"))
    await async_cursor.execute(sql, (True, "Value should be 1"))
    await async_cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    expected_value = [(0, "Value should be 0"), (1, "Value should be 1")]
    assert await async_cursor.fetchall() == expected_value


async def test_6310(async_conn, test_env):
    "6310 - test using a cursor as a context manager"
    with async_conn.cursor() as cursor:
        await cursor.execute("truncate table TestTempTable")
        await cursor.execute("select count(*) from TestTempTable")
        (count,) = await cursor.fetchone()
        assert count == 0
    with test_env.assert_raises_full_code("DPY-1006"):
        cursor.close()


async def test_6311(async_cursor):
    "6311 - test that rowcount attribute is reset to zero on query execute"
    for num in [0, 1, 1, 0]:
        await async_cursor.execute("select * from dual where 1 = :s", [num])
        await async_cursor.fetchone()
        assert async_cursor.rowcount == num


async def test_6312(async_conn, async_cursor):
    "6312 - test that an object type can be used as type in cursor.var()"
    obj_type = await async_conn.gettype("UDT_OBJECT")
    var = async_cursor.var(obj_type)
    await async_cursor.callproc(
        "pkg_TestBindObject.BindObjectOut", (28, "Bind obj out", var)
    )
    obj = var.getvalue()
    result = await async_cursor.callfunc(
        "pkg_TestBindObject.GetStringRep", str, (obj,)
    )
    exp = "udt_Object(28, 'Bind obj out', null, null, null, null, null)"
    assert result == exp


async def test_6313(async_cursor):
    "6313 - test that fetching an XMLType returns a string"
    int_val = 5
    label = "IntCol"
    expected_result = f"<{label}>{int_val}</{label}>"
    await async_cursor.execute(
        f"""
        select XMLElement("{label}", IntCol)
        from TestStrings
        where IntCol = :int_val
        """,
        int_val=int_val,
    )
    (result,) = await async_cursor.fetchone()
    assert result == expected_result


async def test_6314(async_cursor):
    "6314 - test last rowid"

    # no statement executed: no rowid
    assert async_cursor.lastrowid is None

    # DDL statement executed: no rowid
    await async_cursor.execute("truncate table TestTempTable")
    assert async_cursor.lastrowid is None

    # statement prepared: no rowid
    async_cursor.prepare("insert into TestTempTable (IntCol) values (:1)")
    assert async_cursor.lastrowid is None

    # multiple rows inserted: rowid of last row inserted
    rows = [(n,) for n in range(225)]
    await async_cursor.executemany(None, rows)
    rowid = async_cursor.lastrowid
    await async_cursor.execute(
        """
        select rowid
        from TestTempTable
        where IntCol = :1
        """,
        rows[-1],
    )
    row = await async_cursor.fetchone()
    assert row[0] == rowid

    # statement executed but no rows updated: no rowid
    await async_cursor.execute("delete from TestTempTable where 1 = 0")
    assert async_cursor.lastrowid is None

    # stetement executed with one row updated: rowid of updated row
    await async_cursor.execute(
        """
        update TestTempTable set StringCol1 = 'Modified'
        where IntCol = :1
        """,
        rows[-2],
    )
    rowid = async_cursor.lastrowid
    await async_cursor.execute(
        "select rowid from TestTempTable where IntCol = :1",
        rows[-2],
    )
    row = await async_cursor.fetchone()
    assert row[0] == rowid

    # statement executed with many rows updated: rowid of last updated row
    await async_cursor.execute(
        """
        update TestTempTable set
            StringCol1 = 'Row ' || to_char(IntCol)
        where IntCol = :1
        """,
        rows[-3],
    )
    rowid = async_cursor.lastrowid
    await async_cursor.execute(
        "select StringCol1 from TestTempTable where rowid = :1",
        [rowid],
    )
    row = await async_cursor.fetchone()
    assert row[0] == "Row %s" % rows[-3]


async def test_6315(async_conn, round_trip_checker_async):
    "6315 - test prefetch rows"

    # perform simple query and verify only one round trip is needed
    with async_conn.cursor() as cursor:
        await cursor.execute("select sysdate from dual")
        await cursor.fetchall()
        assert await round_trip_checker_async.get_value_async() == 1

    # set prefetchrows to 1 and verify that two round trips are now needed
    with async_conn.cursor() as cursor:
        cursor.prefetchrows = 1
        assert cursor.prefetchrows == 1
        await cursor.execute("select sysdate from dual")
        await cursor.fetchall()
        assert await round_trip_checker_async.get_value_async() == 2

    # simple DDL only requires a single round trip
    with async_conn.cursor() as cursor:
        await cursor.execute("truncate table TestTempTable")
        assert await round_trip_checker_async.get_value_async() == 1

    # array execution only requires a single round trip
    num_rows = 590
    with async_conn.cursor() as cursor:
        data = [(n + 1,) for n in range(num_rows)]
        await cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)",
            data,
        )
        assert await round_trip_checker_async.get_value_async() == 1

    # setting prefetch and array size to 1 requires a round-trip for each
    # row
    with async_conn.cursor() as cursor:
        cursor.arraysize = 1
        cursor.prefetchrows = 1
        assert cursor.prefetchrows == 1
        await cursor.execute("select IntCol from TestTempTable")
        await cursor.fetchall()
        assert await round_trip_checker_async.get_value_async() == num_rows + 1

    # setting prefetch and array size to 300 requires 2 round-trips
    with async_conn.cursor() as cursor:
        cursor.arraysize = 300
        cursor.prefetchrows = 300
        assert cursor.prefetchrows == 300
        await cursor.execute("select IntCol from TestTempTable")
        await cursor.fetchall()
        assert await round_trip_checker_async.get_value_async() == 2


async def test_6316(async_conn, round_trip_checker_async):
    "6316 - test prefetch rows using existing cursor"

    # Set prefetch rows on an existing cursor
    num_rows = 590
    with async_conn.cursor() as cursor:
        await cursor.execute("truncate table TestTempTable")
        assert await round_trip_checker_async.get_value_async() == 1
        data = [(n + 1,) for n in range(num_rows)]
        await cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)",
            data,
        )
        assert await round_trip_checker_async.get_value_async() == 1
        cursor.prefetchrows = 30
        cursor.arraysize = 100
        await cursor.execute("select IntCol from TestTempTable")
        await cursor.fetchall()
        assert await round_trip_checker_async.get_value_async() == 7


async def test_6317(async_cursor):
    "6317 - test parsing plsql statements"
    sql = "begin :value := 5; end;"
    await async_cursor.parse(sql)
    assert async_cursor.statement == sql
    assert async_cursor.description is None


async def test_6318(async_cursor):
    "6318 - test parsing ddl statements"
    sql = "truncate table TestTempTable"
    await async_cursor.parse(sql)
    assert async_cursor.statement == sql
    assert async_cursor.description is None


async def test_6319(async_cursor):
    "6319 - test parsing dml statements"
    sql = "insert into TestTempTable (IntCol) values (1)"
    await async_cursor.parse(sql)
    assert async_cursor.statement == sql
    assert async_cursor.description is None


async def test_6320(async_cursor):
    "6320 - test binding by name with leading colon"
    params = {":arg1": 5}
    await async_cursor.execute("select :arg1 from dual", params)
    (result,) = await async_cursor.fetchone()
    assert result == params[":arg1"]


async def test_6321(async_cursor):
    "6321 - test binding mixed null and not null values in a PL/SQL block"
    out_vars = [async_cursor.var(str) for i in range(4)]
    await async_cursor.execute(
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


async def test_6322(async_conn, parse_count_checker_async):
    "6322 - test excluding statement from statement cache"
    num_iters = 10
    sql = "select user from dual"

    # with statement cache enabled, only one parse should take place
    for i in range(num_iters):
        with async_conn.cursor() as cursor:
            await cursor.execute(sql)
    assert await parse_count_checker_async.get_value_async() == 1

    # with statement cache disabled for the statement, parse count should
    # be the same as the number of iterations
    for i in range(num_iters):
        with async_conn.cursor() as cursor:
            cursor.prepare(sql, cache_statement=False)
            await cursor.execute(None)
    assert await parse_count_checker_async.get_value_async() == num_iters - 1


async def test_6323(async_cursor):
    "6323 - test repeated DDL"
    await async_cursor.execute("truncate table TestTempTable")
    await async_cursor.execute("insert into TestTempTable (IntCol) values (1)")
    await async_cursor.execute("truncate table TestTempTable")
    await async_cursor.execute("insert into TestTempTable (IntCol) values (1)")


async def test_6324(async_cursor):
    "6324 - test executing SQL with non-ASCII characters"
    await async_cursor.execute("select 'FÖÖ' from dual")
    (result,) = await async_cursor.fetchone()
    assert result in ("FÖÖ", "F¿¿")


async def test_6325(async_cursor):
    "6325 - test case sensitivity of unquoted bind names"
    await async_cursor.execute("select :test from dual", {"TEST": "a"})
    (result,) = await async_cursor.fetchone()
    assert result == "a"


async def test_6326(async_cursor, test_env):
    "6326 - test case sensitivity of quoted bind names"
    with test_env.assert_raises_full_code("ORA-01036", "DPY-4008"):
        await async_cursor.execute('select :"test" from dual', {'"TEST"': "a"})


async def test_6327(async_cursor, test_env):
    "6327 - test using a reserved keywords as a bind name"
    sql = "select :ROWID from dual"
    with test_env.assert_raises_full_code("ORA-01745"):
        await async_cursor.parse(sql)


async def test_6328(async_conn):
    "6328 - test array size less than prefetch rows"
    for i in range(2):
        with async_conn.cursor() as cursor:
            cursor.arraysize = 1
            await cursor.execute("select 1 from dual union select 2 from dual")
            assert await cursor.fetchall() == [(1,), (2,)]


async def test_6329(async_conn, async_cursor):
    "6329 - test re-executing a query with blob as bytes"

    def type_handler(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_BLOB:
            return cursor.var(bytes, arraysize=cursor.arraysize)

    async_conn.outputtypehandler = type_handler
    blob_data = b"An arbitrary set of blob data for test case 4348"
    await async_cursor.execute("truncate table TestBLOBs")
    await async_cursor.execute(
        "insert into TestBLOBs (IntCol, BlobCol) values (1, :data)",
        [blob_data],
    )
    await async_cursor.execute("select IntCol, BlobCol from TestBLOBs")
    assert await async_cursor.fetchall() == [(1, blob_data)]

    await async_cursor.execute("truncate table TestBLOBs")
    await async_cursor.execute(
        "insert into TestBLOBs (IntCol, BlobCol) values (1, :data)",
        [blob_data],
    )
    await async_cursor.execute("select IntCol, BlobCol from TestBLOBs")
    assert await async_cursor.fetchall() == [(1, blob_data)]


async def test_6330(async_cursor, test_env):
    "6330 - test re-executing a statement after raising an error"
    sql = "select * from TestFakeTable"
    with test_env.assert_raises_full_code("ORA-00942"):
        await async_cursor.execute(sql)
    with test_env.assert_raises_full_code("ORA-00942"):
        await async_cursor.execute(sql)

    sql = "insert into TestStrings (StringCol) values (NULL)"
    with test_env.assert_raises_full_code("ORA-01400"):
        await async_cursor.execute(sql)
    with test_env.assert_raises_full_code("ORA-01400"):
        await async_cursor.execute(sql)


async def test_6331(async_conn):
    "6331 - test executing a statement that raises ORA-01007"
    with async_conn.cursor() as cursor:
        await cursor.execute(
            """
            create or replace view ora_1007 as
                select 1 as SampleNumber, 'String' as SampleString,
                    'Another String' as AnotherString
                from dual
            """
        )
    with async_conn.cursor() as cursor:
        await cursor.execute("select * from ora_1007")
        assert await cursor.fetchone() == (1, "String", "Another String")
    with async_conn.cursor() as cursor:
        await cursor.execute(
            """
            create or replace view ora_1007 as
                select 1 as SampleNumber,
                    'Another String' as AnotherString
                from dual
            """
        )
    with async_conn.cursor() as cursor:
        await cursor.execute("select * from ora_1007")
        assert await cursor.fetchone() == (1, "Another String")


async def test_6332(async_cursor):
    "6332 - test updating an empty row"
    int_var = async_cursor.var(int)
    await async_cursor.execute("truncate table TestTempTable")
    await async_cursor.execute(
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


async def test_6333(async_conn):
    "6333 - fetch duplicate data from query in statement cache"
    sql = """
            select 'A', 'B', 'C' from dual
            union all
            select 'A', 'B', 'C' from dual
            union all
            select 'A', 'B', 'C' from dual"""
    expected_data = [("A", "B", "C")] * 3
    with async_conn.cursor() as cursor:
        cursor.prefetchrows = 0
        await cursor.execute(sql)
        assert await cursor.fetchall() == expected_data
    with async_conn.cursor() as cursor:
        cursor.prefetchrows = 0
        await cursor.execute(sql)
        assert await cursor.fetchall() == expected_data


async def test_6334(async_cursor):
    "6334 - fetch duplicate data with outconverter"

    def out_converter(value):
        assert isinstance(value, str)
        return int(value)

    def type_handler(cursor, metadata):
        if metadata.name == "COL_3":
            return cursor.var(
                str, arraysize=cursor.arraysize, outconverter=out_converter
            )

    async_cursor.outputtypehandler = type_handler
    await async_cursor.execute(
        """
        select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
            union all
        select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
            union all
        select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
        """
    )
    expected_data = [("A", 2, 3)] * 3
    assert await async_cursor.fetchall() == expected_data


async def test_6335(skip_if_drcp, test_env):
    "6335 - kill connection with open cursor"
    admin_conn = await test_env.get_admin_connection_async()
    conn = await test_env.get_connection_async()
    assert conn.is_healthy()
    sid, serial = (conn.session_id, conn.serial_num)
    with admin_conn.cursor() as admin_cursor:
        sql = f"alter system kill session '{sid},{serial}'"
        await admin_cursor.execute(sql)
    with test_env.assert_raises_full_code("DPY-4011"):
        with conn.cursor() as cursor:
            await cursor.execute("select user from dual")
    assert not conn.is_healthy()


async def test_6336(skip_if_drcp, test_env):
    "6336 - kill connection in cursor context manager"
    admin_conn = await test_env.get_admin_connection_async()
    conn = await test_env.get_connection_async()
    assert conn.is_healthy()
    sid, serial = (conn.session_id, conn.serial_num)
    with admin_conn.cursor() as admin_cursor:
        await admin_cursor.execute(
            f"alter system kill session '{sid},{serial}'"
        )
    with test_env.assert_raises_full_code("DPY-4011"):
        with conn.cursor() as cursor:
            await cursor.execute("select user from dual")
    assert not conn.is_healthy()


async def test_6337(async_conn):
    "6337 - fetchmany() with and without parameters"
    sql_part = "select user from dual"
    sql = " union all ".join([sql_part] * 10)
    with async_conn.cursor() as cursor:
        cursor.arraysize = 6
        await cursor.execute(sql)
        rows = await cursor.fetchmany()
        assert len(rows) == cursor.arraysize
        await cursor.execute(sql)
        rows = await cursor.fetchmany(size=2)
        assert len(rows) == 2
        await cursor.execute(sql)


async def test_6338(async_conn):
    "6338 - access cursor.rowcount after closing cursor"
    with async_conn.cursor() as cursor:
        await cursor.execute("select user from dual")
        await cursor.fetchall()
        assert cursor.rowcount == 1
    assert cursor.rowcount == -1


async def test_6339(disable_fetch_lobs, async_cursor):
    "6339 - changing bind type with define needed"
    await async_cursor.execute("truncate table TestClobs")
    row_for_1 = (1, "Short value 1")
    row_for_56 = (56, "Short value 56")
    for data in (row_for_1, row_for_56):
        await async_cursor.execute(
            "insert into TestClobs (IntCol, ClobCol) values (:1, :2)",
            data,
        )
    sql = "select IntCol, ClobCol from TestClobs where IntCol = :int_col"
    await async_cursor.execute(sql, int_col="1")
    assert await async_cursor.fetchone() == row_for_1
    await async_cursor.execute(sql, int_col="56")
    assert await async_cursor.fetchone() == row_for_56
    await async_cursor.execute(sql, int_col=1)
    assert await async_cursor.fetchone() == row_for_1


async def test_6340(async_cursor):
    "6340 - test calling cursor.parse() twice with the same statement"
    await async_cursor.execute("truncate table TestTempTable")
    data = (4363, "Value for test 4363")
    await async_cursor.execute(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        data,
    )
    sql = "update TestTempTable set StringCol1 = :v where IntCol = :i"
    for i in range(2):
        await async_cursor.parse(sql)
        await async_cursor.execute(sql, ("Updated value", data[0]))


async def test_6341(async_conn, async_cursor):
    "6341 - test addition of column to cached query"
    table_name = "test_4365"
    try:
        await async_cursor.execute(f"drop table {table_name}")
    except oracledb.DatabaseError:
        pass
    data = ("val 1", "val 2")
    await async_cursor.execute(
        f"create table {table_name} (col1 varchar2(10))"
    )
    await async_cursor.execute(
        f"insert into {table_name} values (:1)", [data[0]]
    )
    await async_conn.commit()
    await async_cursor.execute(f"select * from {table_name}")
    assert await async_cursor.fetchall() == [(data[0],)]
    await async_cursor.execute(
        f"alter table {table_name} add col2 varchar2(10)"
    )
    await async_cursor.execute(f"update {table_name} set col2 = :1", [data[1]])
    await async_conn.commit()
    await async_cursor.execute(f"select * from {table_name}")
    assert await async_cursor.fetchall() == [data]


async def test_6342(async_cursor):
    "6342 - test executemany() with PL/SQL and increasing data lengths"
    sql = "begin :1 := length(:2); end;"
    var = async_cursor.var(int, arraysize=3)
    await async_cursor.executemany(
        sql, [(var, "one"), (var, "two"), (var, "end")]
    )
    assert var.values == [3, 3, 3]
    await async_cursor.executemany(
        sql, [(var, "three"), (var, "four"), (var, "end")]
    )
    assert var.values == [5, 4, 3]
    await async_cursor.executemany(
        sql, [(var, "five"), (var, "six"), (var, "end")]
    )
    assert var.values == [4, 3, 3]


async def test_6343(async_cursor):
    "6343 - test cursor.rowcount values for queries"
    max_rows = 93
    async_cursor.arraysize = 10
    await async_cursor.execute(
        "select rownum as id from dual connect by rownum <= :1",
        [max_rows],
    )
    assert async_cursor.rowcount == 0
    batch_num = 1
    while True:
        rows = await async_cursor.fetchmany()
        if not rows:
            break
        expected_value = min(max_rows, batch_num * async_cursor.arraysize)
        assert async_cursor.rowcount == expected_value
        batch_num += 1
    await async_cursor.fetchall()
    assert async_cursor.rowcount == max_rows


async def test_6344(disable_fetch_lobs, async_conn, async_cursor):
    "6344 - test bind order for PL/SQL"
    await async_cursor.execute("truncate table TestClobs")
    sql = """
        insert into TestClobs (IntCol, CLOBCol, ExtraNumCol1)
        values (:1, :2, :3)"""
    data = "x" * 9000
    rows = [(1, data, 5), (2, data, 6)]
    await async_cursor.execute(sql, rows[0])
    plsql = f"begin {sql}; end;"
    await async_cursor.execute(plsql, rows[1])
    await async_conn.commit()
    await async_cursor.execute(
        """
        select IntCol, CLOBCol, ExtraNumCol1
        from TestCLOBs
        order by IntCol
        """
    )
    assert await async_cursor.fetchall() == rows


async def test_6345(disable_fetch_lobs, async_cursor):
    "6345 - test rebuild of table with LOB in cached query (as string)"
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
        await async_cursor.execute(drop_sql)
    except oracledb.DatabaseError:
        pass
    await async_cursor.execute(create_sql)
    await async_cursor.executemany(insert_sql, data)
    await async_cursor.execute(query_sql)
    assert await async_cursor.fetchall() == data
    await async_cursor.execute(query_sql)
    assert await async_cursor.fetchall() == data
    await async_cursor.execute(drop_sql)
    await async_cursor.execute(create_sql)
    await async_cursor.executemany(insert_sql, data)
    await async_cursor.execute(query_sql)
    assert await async_cursor.fetchall() == data


async def test_6346(async_cursor):
    "6346 - test rebuild of table with LOB in cached query (as LOB)"
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
        await async_cursor.execute(drop_sql)
    except oracledb.DatabaseError:
        pass
    await async_cursor.execute(create_sql)
    await async_cursor.executemany(insert_sql, data)
    await async_cursor.execute(query_sql)
    fetched_data = [(n, await c.read()) async for n, c in async_cursor]
    assert fetched_data == data
    await async_cursor.execute(query_sql)
    fetched_data = [(n, await c.read()) async for n, c in async_cursor]
    assert fetched_data == data
    await async_cursor.execute(drop_sql)
    await async_cursor.execute(create_sql)
    await async_cursor.executemany(insert_sql, data)
    await async_cursor.execute(query_sql)
    fetched_data = [(n, await c.read()) async for n, c in async_cursor]
    assert fetched_data == data


async def test_6347(skip_unless_domains_supported, async_cursor, test_env):
    "6347 - fetch table with domain and annotations"
    await async_cursor.execute("select * from TableWithDomainAndAnnotations")
    assert await async_cursor.fetchall() == [(1, 25)]
    column_1 = async_cursor.description[0]
    assert column_1.domain_schema is None
    assert column_1.domain_name is None
    assert column_1.annotations is None
    column_2 = async_cursor.description[1]
    assert column_2.domain_schema == test_env.main_user.upper()
    assert column_2.domain_name == "SIMPLEDOMAIN"
    expected_annotations = {
        "ANNO_1": "first annotation",
        "ANNO_2": "second annotation",
        "ANNO_3": "",
    }
    assert column_2.annotations == expected_annotations


async def test_6348(async_cursor, test_env):
    "6348 - test fetching LOBs after an error"
    sql = """
        select
            to_clob(:val),
            1 / (dbms_lob.getlength(to_clob(:val)) - 1)
        from dual"""
    with test_env.assert_raises_full_code("ORA-01476"):
        await async_cursor.execute(sql, val="a")
    await async_cursor.execute(sql, val="bb")
    lob, num_val = await async_cursor.fetchone()
    assert await lob.read() == "bb"
    assert num_val == 1


async def test_6349(test_env):
    "6349 - test parse() with autocommit enabled"
    async with test_env.get_connection_async() as conn:
        conn.autocommit = True
        cursor = conn.cursor()
        await cursor.execute("truncate table TestTempTable")
        await cursor.parse("insert into TestTempTable (IntCol) values (:1)")
        await cursor.execute(None, [1])


async def test_6350(async_cursor, test_env):
    "6350 - test cursor.setinputsizes() with early failed execute"
    async_cursor.setinputsizes(a=int, b=str)
    with test_env.assert_raises_full_code("DPY-2006"):
        await async_cursor.execute("select :c from dual", [5])
    value = 4368
    await async_cursor.execute("select :d from dual", [value])
    (fetched_value,) = await async_cursor.fetchone()
    assert fetched_value == value


async def test_6351(async_cursor, test_env):
    "6351 - fetch JSON columns as Python objects"
    test_env.skip_unless_server_version(21)
    expected_data = [
        (1, [1, 2, 3], [4, 5, 6], [7, 8, 9]),
        (2, None, None, None),
    ]
    await async_cursor.execute("select * from TestJsonCols order by IntCol")
    assert await async_cursor.fetchall() == expected_data


async def test_6352(async_conn):
    "6352 - test fetching nested cursors repeatedly"
    sql = """
        select
            s.Description,
            cursor(select 'Nested String for ' || s.Description from dual)
        from
            (
                select 'Top Level String 1' as Description
                from dual
                union all
                select 'Top Level String 2'
                from dual
                union all
                select 'Top Level String 3'
                from dual
                union all
                select 'Top Level String 4'
                from dual
                union all
                select 'Top Level String 5'
                from dual
            ) s"""

    for i in range(3):
        with async_conn.cursor() as cursor:
            cursor.arraysize = 10
            await cursor.execute(sql)
            desc, nested1 = await cursor.fetchone()
            assert desc == "Top Level String 1"
            nested_rows = await nested1.fetchall()
            assert nested_rows == [("Nested String for Top Level String 1",)]
            desc, nested2 = await cursor.fetchone()
            assert desc == "Top Level String 2"
            nested_rows = await nested2.fetchall()
            assert nested_rows == [("Nested String for Top Level String 2",)]


async def test_6353(test_env):
    "6353 - access cursor.rowcount after closing connection"
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
    assert cursor.rowcount == -1


async def test_6354(async_conn, async_cursor):
    "6354 - execute PL/SQL with out vars after query with duplicate data"
    await async_cursor.execute("truncate table TestTempTable")
    await async_cursor.executemany(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        [(i + 1, "test_4370") for i in range(20)],
    )
    await async_conn.commit()
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    var = async_cursor.var(int)
    await async_cursor.execute("begin :1 := 4370; end;", [var])
    assert var.getvalue() == 4370


async def test_6355(async_cursor):
    "6355 - test cursor with fetch_decimals=True specified"
    value = 4371
    await async_cursor.execute(
        "select :1 from dual", [value], fetch_decimals=True
    )
    rows = await async_cursor.fetchall()
    assert isinstance(rows[0][0], decimal.Decimal)


async def test_6356(async_cursor):
    "6356 - test cursor.parse() uses oracledb.defaults.fetch_lobs"
    await async_cursor.parse("select to_clob('some_value') from dual")
    fetch_info = async_cursor.description[0]
    assert fetch_info.type is oracledb.DB_TYPE_CLOB
