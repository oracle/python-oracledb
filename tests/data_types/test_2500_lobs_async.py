# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
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
Module for testing LOB (CLOB and BLOB) variables with asyncio
"""

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def _get_temp_lobs(conn, sid):
    cursor = conn.cursor()
    await cursor.execute(
        """
        select cache_lobs + nocache_lobs + abstract_lobs
        from v$temporary_lobs
        where sid = :sid
        """,
        sid=sid,
    )
    row = await cursor.fetchone()
    if row is None:
        return 0
    return int(row[0])


async def _perform_test(conn, lob_type, input_type, arraysize=None):
    long_string = ""
    cursor = conn.cursor()
    if arraysize is not None:
        cursor.arraysize = arraysize
    db_type = getattr(oracledb, f"DB_TYPE_{lob_type}")
    await cursor.execute(f"delete from Test{lob_type}s")
    for i in range(11):
        if i > 0:
            char = chr(ord("A") + i - 1)
            long_string += char * 25000
        elif input_type is not db_type:
            continue
        cursor.setinputsizes(long_string=input_type)
        if lob_type == "BLOB":
            bind_value = long_string.encode()
        else:
            bind_value = long_string
        await cursor.execute(
            f"""
            insert into Test{lob_type}s (IntCol, {lob_type}Col)
            values (:integer_value, :long_string)
            """,
            integer_value=i,
            long_string=bind_value,
        )
    await conn.commit()
    await cursor.execute(f"""
        select IntCol, {lob_type}Col
        from Test{lob_type}s
        order by IntCol
        """)
    await _validate_query(await cursor.fetchall(), lob_type)


async def _test_bind_ordering(conn, lob_type):
    cursor = conn.cursor()
    main_col = "A" * 32768
    extra_col_1 = "B" * 65536
    extra_col_2 = "C" * 131072
    if lob_type == "BLOB":
        main_col = main_col.encode()
        extra_col_1 = extra_col_1.encode()
        extra_col_2 = extra_col_2.encode()
    conn.stmtcachesize = 0
    await cursor.execute(f"delete from Test{lob_type}s")
    await conn.commit()
    data = (1, main_col, 8, extra_col_1, 15, extra_col_2)
    await cursor.execute(
        f"""
        insert into Test{lob_type}s (IntCol, {lob_type}Col,
            ExtraNumCol1, Extra{lob_type}Col1, ExtraNumCol2,
            Extra{lob_type}Col2)
        values (:1, :2, :3, :4, :5, :6)
        """,
        data,
    )
    await cursor.execute(f"select * from Test{lob_type}s")
    assert await cursor.fetchone() == data


async def _test_fetch_lobs_direct(conn, lob_type):
    cursor = conn.cursor()
    await cursor.execute(f"delete from Test{lob_type}s")
    await conn.commit()
    data = []
    long_string = ""
    for i in range(1, 11):
        if i > 0:
            char = chr(ord("A") + i - 1)
            long_string += char * 25000
        if lob_type == "BLOB":
            data.append((i, long_string.encode()))
        else:
            data.append((i, long_string))
    await cursor.executemany(
        f"""
        insert into Test{lob_type}s (IntCol, {lob_type}Col)
        values (:1, :2)
        """,
        data,
    )
    await cursor.execute(f"""
        select IntCol, {lob_type}Col
        from Test{lob_type}s
        order by IntCol
        """)
    assert await cursor.fetchall() == data


async def _test_lob_operations(conn, test_env, lob_type):
    cursor = conn.cursor()
    await cursor.execute(f"delete from Test{lob_type}s")
    await conn.commit()
    cursor.setinputsizes(long_string=getattr(oracledb, lob_type))
    long_string = "X" * 75000
    write_value = "TEST"
    if lob_type == "BLOB":
        long_string = long_string.encode("ascii")
        write_value = write_value.encode("ascii")
    await cursor.execute(
        f"""
        insert into Test{lob_type}s (IntCol, {lob_type}Col)
        values (:integer_value, :long_string)
        """,
        integer_value=1,
        long_string=long_string,
    )
    await cursor.execute(f"""
        select {lob_type}Col
        from Test{lob_type}s
        where IntCol = 1
        """)
    (lob,) = await cursor.fetchone()
    assert not await lob.isopen()
    await lob.open()
    with test_env.assert_raises_full_code("ORA-22293"):
        await lob.open()
    assert await lob.isopen()
    await lob.close()
    with test_env.assert_raises_full_code("ORA-22289"):
        await lob.close()
    assert not await lob.isopen()
    assert await lob.size() == 75000
    await lob.write(write_value, 75001)
    assert await lob.size() == 75000 + len(write_value)
    with test_env.assert_raises_full_code("DPY-2030"):
        await lob.read(0)
    with test_env.assert_raises_full_code("DPY-2030"):
        await lob.read(-25)
    assert await lob.read() == long_string + write_value
    await lob.write(write_value, 1)
    assert await lob.read() == write_value + long_string[4:] + write_value
    await lob.trim(25000)
    assert await lob.size() == 25000
    await lob.trim(newSize=10000)
    assert await lob.size() == 10000
    with test_env.assert_raises_full_code("DPY-2014"):
        await lob.trim(new_size=50, newSize=60)
    with pytest.raises(TypeError):
        await lob.trim(new_size="10000")
    await lob.trim(new_size=40)
    assert await lob.size() == 40
    await lob.trim()
    assert await lob.size() == 0
    assert isinstance(await lob.getchunksize(), int)


async def _test_temporary_lob(conn, lob_type):
    cursor = conn.cursor()
    await cursor.execute(f"delete from Test{lob_type}s")
    value = "A test string value"
    if lob_type == "BLOB":
        value = value.encode("ascii")
    db_type = getattr(oracledb, f"DB_TYPE_{lob_type}")
    lob = await conn.createlob(db_type, value)
    await cursor.execute(
        f"""
        insert into Test{lob_type}s (IntCol, {lob_type}Col)
        values (:int_val, :lob_val)
        """,
        int_val=1,
        lob_val=lob,
    )
    await conn.commit()
    await cursor.execute(f"select {lob_type}Col from Test{lob_type}s")
    (lob,) = await cursor.fetchone()
    assert await lob.read() == value


async def _validate_query(rows, lob_type):
    long_string = ""
    db_type = getattr(oracledb, f"DB_TYPE_{lob_type}")
    for row in rows:
        integer_value, lob = row
        assert lob.type == db_type
        if integer_value == 0:
            assert await lob.size() == 0
            expected_value = ""
            if lob_type == "BLOB":
                expected_value = expected_value.encode()
            assert await lob.read() == expected_value
        else:
            char = chr(ord("A") + integer_value - 1)
            prev_char = chr(ord("A") + integer_value - 2)
            long_string += char * 25000
            if lob_type == "BLOB":
                expected_value = long_string.encode("ascii")
                char = char.encode("ascii")
                prev_char = prev_char.encode("ascii")
            else:
                expected_value = long_string
            assert await lob.size() == len(expected_value)
            assert await lob.read() == expected_value
            assert await lob.read(len(expected_value)) == char
        if integer_value > 1:
            offset = (integer_value - 1) * 25000 - 4
            string = prev_char * 5 + char * 5
            assert await lob.read(offset, 10) == string


async def test_2500(async_conn, async_cursor):
    "2500 - test binding a LOB value directly"
    await async_cursor.execute("delete from TestCLOBs")
    await async_cursor.execute("""
        insert into TestCLOBs
        (IntCol, ClobCol)
        values (1, 'Short value')
        """)
    await async_cursor.execute("select ClobCol from TestCLOBs")
    (lob,) = await async_cursor.fetchone()
    await async_cursor.execute(
        """
        insert into TestCLOBs
        (IntCol, ClobCol)
        values (2, :value)
        """,
        value=lob,
    )
    await async_conn.commit()


async def test_2501(async_cursor):
    "2501 - test cursor description is accurate for BLOBs"
    await async_cursor.execute("select IntCol, BlobCol from TestBLOBs")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
        ("BLOBCOL", oracledb.DB_TYPE_BLOB, None, None, None, None, 0),
    ]
    assert async_cursor.description == expected_value


async def test_2502(async_conn):
    "2503 - test binding and fetching BLOB data (indirectly)"
    await _perform_test(async_conn, "BLOB", oracledb.DB_TYPE_LONG_RAW)


async def test_2503(async_conn, test_env):
    "2503 - test operations on BLOBs"
    await _test_lob_operations(async_conn, test_env, "BLOB")


async def test_2504(async_cursor):
    "2504 - test cursor description is accurate for CLOBs"
    await async_cursor.execute("select IntCol, ClobCol from TestCLOBs")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        ("CLOBCOL", oracledb.DB_TYPE_CLOB, None, None, None, None, False),
    ]
    assert async_cursor.description == expected_value


async def test_2505(async_conn):
    "2505 - test binding and fetching CLOB data (indirectly)"
    await _perform_test(async_conn, "CLOB", oracledb.DB_TYPE_LONG)


async def test_2506(async_conn, test_env):
    "2506 - test operations on CLOBs"
    await _test_lob_operations(async_conn, test_env, "CLOB")


async def test_2507(async_conn):
    "2507 - test creating a temporary BLOB"
    await _test_temporary_lob(async_conn, "BLOB")


async def test_2508(async_conn):
    "2508 - test creating a temporary CLOB"
    await _test_temporary_lob(async_conn, "CLOB")


async def test_2509(async_conn):
    "2509 - test creating a temporary NCLOB"
    await _test_temporary_lob(async_conn, "NCLOB")


async def test_2510(async_conn):
    "2510 - test retrieving data from a CLOB after multiple fetches"
    await _perform_test(async_conn, "CLOB", oracledb.DB_TYPE_LONG, arraysize=1)


async def test_2511(async_cursor):
    "2511 - test cursor description is accurate for NCLOBs"
    await async_cursor.execute("select IntCol, NClobCol from TestNCLOBs")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
        ("NCLOBCOL", oracledb.DB_TYPE_NCLOB, None, None, None, None, 0),
    ]
    assert async_cursor.description == expected_value


async def test_2512(async_conn, async_cursor):
    "2512 - test binding and fetching NCLOB data (with non-ASCII chars)"
    value = "\u03b4\u4e2a"
    await async_cursor.execute("delete from TestNCLOBs")
    async_cursor.setinputsizes(val=oracledb.DB_TYPE_NVARCHAR)
    await async_cursor.execute(
        """
        insert into TestNCLOBs (IntCol, NClobCol)
        values (1, :val)
        """,
        val=value,
    )
    await async_conn.commit()
    await async_cursor.execute("select NCLOBCol from TestNCLOBs")
    (nclob,) = await async_cursor.fetchone()
    async_cursor.setinputsizes(val=oracledb.DB_TYPE_NVARCHAR)
    await async_cursor.execute(
        "update TestNCLOBs set NCLOBCol = :val",
        val=await nclob.read() + value,
    )
    await async_cursor.execute("select NCLOBCol from TestNCLOBs")
    (nclob,) = await async_cursor.fetchone()
    assert await nclob.read() == value + value


async def test_2513(async_conn):
    "2513 - test binding and fetching NCLOB data (indirectly)"
    await _perform_test(async_conn, "NCLOB", oracledb.DB_TYPE_LONG)


async def test_2514(async_conn, test_env):
    "2514 - test operations on NCLOBs"
    await _test_lob_operations(async_conn, test_env, "NCLOB")


async def test_2515(
    skip_if_implicit_pooling, skip_unless_refcounting, async_conn, async_cursor
):
    "2515 - test temporary LOBs"
    await async_cursor.execute(
        "select sys_context('USERENV', 'SID') from dual"
    )
    (sid,) = await async_cursor.fetchone()
    temp_lobs = await _get_temp_lobs(async_conn, sid)
    with async_conn.cursor() as cursor:
        cursor.arraysize = 27
        assert temp_lobs == 0
        await cursor.execute(
            "select extract(xmlcol, '/').getclobval() from TestXML"
        )
        async for (lob,) in cursor:
            await lob.read()
            del lob
    temp_lobs = await _get_temp_lobs(async_conn, sid)
    assert temp_lobs == 0


async def test_2516(async_conn, async_cursor, test_env):
    "2516 - test read/write temporary LOBs using supplemental characters"
    if test_env.charset != "AL32UTF8":
        pytest.skip("Database character set must be AL32UTF8")
    supplemental_chars = (
        "𠜎 𠜱 𠝹 𠱓 𠱸 𠲖 𠳏 𠳕 𠴕 𠵼 𠵿 𠸎 𠸏 𠹷 𠺝 𠺢 𠻗 𠻹 𠻺 𠼭 𠼮 "
        "𠽌 𠾴 𠾼 𠿪 𡁜 𡁯 𡁵 𡁶 𡁻 𡃁 𡃉 𡇙 𢃇 𢞵 𢫕 𢭃 𢯊 𢱑 𢱕 𢳂 𢴈 "
        "𢵌 𢵧 𢺳 𣲷 𤓓 𤶸 𤷪 𥄫 𦉘 𦟌 𦧲 𦧺 𧨾 𨅝 𨈇 𨋢 𨳊 𨳍 𨳒 𩶘"
    )
    await async_cursor.execute("delete from TestCLOBs")
    lob = await async_conn.createlob(oracledb.DB_TYPE_CLOB, supplemental_chars)
    await async_cursor.execute(
        """
        insert into TestCLOBs
        (IntCol, ClobCol)
        values (1, :val)
        """,
        [lob],
    )
    await async_conn.commit()
    await async_cursor.execute("select ClobCol from TestCLOBs")
    (lob,) = await async_cursor.fetchone()
    assert await lob.read() == supplemental_chars


async def test_2517(disable_fetch_lobs, async_conn):
    "2517 - test fetching BLOB as bytes"
    await _test_fetch_lobs_direct(async_conn, "BLOB")


async def test_2518(disable_fetch_lobs, async_conn):
    "2518 - test fetching CLOB as str"
    await _test_fetch_lobs_direct(async_conn, "CLOB")


async def test_2519(disable_fetch_lobs, async_conn):
    "2519 - test fetching NCLOB as str"
    await _test_fetch_lobs_direct(async_conn, "NCLOB")


async def test_2520(disable_fetch_lobs, async_conn):
    "2520 - test bind ordering with BLOB"
    await _test_bind_ordering(async_conn, "BLOB")


async def test_2521(disable_fetch_lobs, async_conn):
    "2521 - test bind ordering with CLOB"
    await _test_bind_ordering(async_conn, "CLOB")


async def test_2522(disable_fetch_lobs, async_conn):
    "2522 - test bind ordering with NCLOB"
    await _test_bind_ordering(async_conn, "NCLOB")


async def test_2523(async_conn):
    "2523 - test creating a lob with an invalid type"
    with pytest.raises(TypeError):
        await async_conn.createlob(oracledb.DB_TYPE_NUMBER)
    with pytest.raises(TypeError):
        await async_conn.createlob(oracledb.DB_TYPE_BFILE)


async def test_2524(async_conn):
    "2524 - test creation of temporary LOBs with varying data"
    cases = [
        (oracledb.DB_TYPE_BLOB, b"test_2524A", b"!", b"test_2524A!"),
        (oracledb.DB_TYPE_BLOB, "test_2524B", "!", b"test_2524B!"),
        (oracledb.DB_TYPE_CLOB, b"test_2524C", b"!", "test_2524C!"),
        (oracledb.DB_TYPE_CLOB, "test_2524D", "!", "test_2524D!"),
        (oracledb.DB_TYPE_NCLOB, b"test_2524E", b"!", "test_2524E!"),
        (oracledb.DB_TYPE_NCLOB, "test_2524F", "!", "test_2524F!"),
    ]
    for typ, initial_data, additional_data, expected_result in cases:
        lob = await async_conn.createlob(typ, initial_data)
        await lob.write(additional_data, len(initial_data) + 1)
        assert await lob.read() == expected_result


async def test_2525(test_env):
    "2525 - test reading and writing a LOB with a closed connection"
    types = [
        oracledb.DB_TYPE_BLOB,
        oracledb.DB_TYPE_CLOB,
        oracledb.DB_TYPE_NCLOB,
    ]
    for typ in types:
        conn = await test_env.get_connection(use_async=True)
        lob = await conn.createlob(typ, "Temp LOB")
        await conn.close()
        with test_env.assert_raises_full_code("DPY-1001"):
            await lob.read()
        with test_env.assert_raises_full_code("DPY-1001"):
            await lob.write("x")


async def test_2526(async_cursor, test_env):
    "2526 - test reading a non-existent directory"
    directory_name = "test_2526_MISSING_DIR"
    file_name = "test_2526_missing_file.txt"
    await async_cursor.execute(
        "select BFILENAME(:1, :2) from dual", [directory_name, file_name]
    )
    (bfile,) = await async_cursor.fetchone()
    assert bfile.getfilename() == (directory_name, file_name)
    with test_env.assert_raises_full_code("ORA-22285"):
        await bfile.fileexists()
    with test_env.assert_raises_full_code("ORA-22285"):
        await bfile.read()


async def test_2527(async_conn, test_env):
    "2527 - test using BFILE methods on non-BFILE LOBs"
    types = [
        oracledb.DB_TYPE_BLOB,
        oracledb.DB_TYPE_CLOB,
        oracledb.DB_TYPE_NCLOB,
    ]
    for typ in types:
        lob = await async_conn.createlob(typ)
        with test_env.assert_raises_full_code("DPY-3026"):
            lob.getfilename()
        with test_env.assert_raises_full_code("DPY-3026"):
            lob.setfilename("not_relevant", "not_relevant")
        with test_env.assert_raises_full_code("DPY-3026"):
            await lob.fileexists()
