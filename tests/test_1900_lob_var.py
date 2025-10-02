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
1900 - Module for testing LOB (CLOB and BLOB) variables
"""

import pickle

import oracledb
import pytest


def _get_temp_lobs(conn, sid):
    cursor = conn.cursor()
    cursor.execute(
        """
        select cache_lobs + nocache_lobs + abstract_lobs
        from v$temporary_lobs
        where sid = :sid
        """,
        sid=sid,
    )
    row = cursor.fetchone()
    if row is None:
        return 0
    return int(row[0])


def _perform_test(cursor, lob_type, input_type):
    long_string = ""
    db_type = getattr(oracledb, f"DB_TYPE_{lob_type}")
    cursor.execute(f"delete from Test{lob_type}s")
    cursor.connection.commit()
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
        cursor.execute(
            f"""
            insert into Test{lob_type}s (IntCol, {lob_type}Col)
            values (:integer_value, :long_string)
            """,
            integer_value=i,
            long_string=bind_value,
        )
    cursor.connection.commit()
    cursor.execute(
        f"""
        select IntCol, {lob_type}Col
        from Test{lob_type}s
        order by IntCol
        """
    )
    _validate_query(cursor, lob_type)


def _test_bind_ordering(conn, cursor, lob_type):
    main_col = "A" * 32768
    extra_col_1 = "B" * 65536
    extra_col_2 = "C" * 131072
    if lob_type == "BLOB":
        main_col = main_col.encode()
        extra_col_1 = extra_col_1.encode()
        extra_col_2 = extra_col_2.encode()
    conn.stmtcachesize = 0
    cursor.execute(f"delete from Test{lob_type}s")
    conn.commit()
    data = (1, main_col, 8, extra_col_1, 15, extra_col_2)
    cursor.execute(
        f"""
        insert into Test{lob_type}s (IntCol, {lob_type}Col,
            ExtraNumCol1, Extra{lob_type}Col1, ExtraNumCol2,
            Extra{lob_type}Col2)
        values (:1, :2, :3, :4, :5, :6)
        """,
        data,
    )
    cursor.execute(f"select * from Test{lob_type}s", fetch_lobs=False)
    assert cursor.fetchone() == data


def _test_fetch_lobs_direct(cursor, lob_type):
    cursor.execute(f"delete from Test{lob_type}s")
    cursor.connection.commit()
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
    cursor.executemany(
        f"""
        insert into Test{lob_type}s (IntCol, {lob_type}Col)
        values (:1, :2)
        """,
        data,
    )
    cursor.execute(
        f"""
        select IntCol, {lob_type}Col
        from Test{lob_type}s
        order by IntCol
        """
    )
    assert cursor.fetchall() == data


def _test_lob_operations(cursor, test_env, lob_type):
    cursor.execute(f"delete from Test{lob_type}s")
    cursor.connection.commit()
    cursor.setinputsizes(long_string=getattr(oracledb, lob_type))
    long_string = "X" * 75000
    write_value = "TEST"
    if lob_type == "BLOB":
        long_string = long_string.encode("ascii")
        write_value = write_value.encode("ascii")
    cursor.execute(
        f"""
        insert into Test{lob_type}s (IntCol, {lob_type}Col)
        values (:integer_value, :long_string)
        """,
        integer_value=1,
        long_string=long_string,
    )
    cursor.execute(
        f"""
        select {lob_type}Col
        from Test{lob_type}s
        where IntCol = 1
        """
    )
    (lob,) = cursor.fetchone()
    assert not lob.isopen()
    lob.open()
    with test_env.assert_raises_full_code("ORA-22293"):
        lob.open()
    assert lob.isopen()
    lob.close()
    with test_env.assert_raises_full_code("ORA-22289"):
        lob.close()
    assert not lob.isopen()
    assert lob.size() == 75000
    lob.write(write_value, 75001)
    pytest.raises(TypeError, lob.write, 1000, 1)
    pytest.raises(TypeError, lob.write, "data", "1")
    assert lob.size() == 75000 + len(write_value)
    with test_env.assert_raises_full_code("DPY-2030"):
        lob.read(0)
    with test_env.assert_raises_full_code("DPY-2030"):
        lob.read(-25)
    with test_env.assert_raises_full_code("DPY-2047"):
        lob.read(amount=0)
    with test_env.assert_raises_full_code("DPY-2047"):
        lob.read(amount=-5)
    assert lob.read() == long_string + write_value
    lob.write(write_value, 1)
    assert lob.read() == write_value + long_string[4:] + write_value
    lob.trim(25000)
    assert lob.size() == 25000
    lob.trim(newSize=10000)
    assert lob.size() == 10000
    with test_env.assert_raises_full_code("DPY-2014"):
        lob.trim(new_size=50, newSize=60)
    pytest.raises(TypeError, lob.trim, new_size="10000")
    pytest.raises(TypeError, lob.trim, newSize="10000")
    lob.trim(new_size=40)
    assert lob.size() == 40
    lob.trim()
    assert lob.size() == 0
    assert isinstance(lob.getchunksize(), int)


def _test_pickle(conn, lob_type):
    value = "A test string value for pickling"
    if lob_type == "BLOB":
        value = value.encode("ascii")
    db_type = getattr(oracledb, "DB_TYPE_" + lob_type)
    lob = conn.createlob(db_type, value)
    pickled_data = pickle.dumps(lob)
    unpickled_value = pickle.loads(pickled_data)
    assert unpickled_value == value


def _test_temporary_lob(conn, cursor, lob_type):
    cursor.execute(f"delete from Test{lob_type}s")
    conn.commit()
    value = "A test string value"
    if lob_type == "BLOB":
        value = value.encode("ascii")
    db_type = getattr(oracledb, f"DB_TYPE_{lob_type}")
    lob = conn.createlob(db_type, value)
    cursor.execute(
        f"""
        insert into Test{lob_type}s (IntCol, {lob_type}Col)
        values (:int_val, :lob_val)
        """,
        int_val=1,
        lob_val=lob,
    )
    cursor.execute(f"select {lob_type}Col from Test{lob_type}s")
    (lob,) = cursor.fetchone()
    assert lob.read() == value


def _validate_query(rows, lob_type):
    long_string = ""
    db_type = getattr(oracledb, f"DB_TYPE_{lob_type}")
    for row in rows:
        integer_value, lob = row
        assert lob.type == db_type
        if integer_value == 0:
            assert lob.size() == 0
            expected_value = ""
            if lob_type == "BLOB":
                expected_value = expected_value.encode()
            assert lob.read() == expected_value
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
            assert lob.size() == len(expected_value)
            assert lob.read() == expected_value
            if lob_type == "CLOB":
                assert str(lob) == expected_value
            assert lob.read(len(expected_value)) == char
        if integer_value > 1:
            offset = (integer_value - 1) * 25000 - 4
            string = prev_char * 5 + char * 5
            assert lob.read(offset, 10) == string


def test_1900(conn, cursor):
    "1900 - test binding a LOB value directly"
    cursor.execute("delete from TestCLOBs")
    cursor.execute(
        """
        insert into TestCLOBs
        (IntCol, ClobCol)
        values (1, 'Short value')
        """
    )
    conn.commit()
    cursor.execute("select ClobCol from TestCLOBs")
    (lob,) = cursor.fetchone()
    cursor.execute(
        """
        insert into TestCLOBs
        (IntCol, ClobCol)
        values (2, :value)
        """,
        value=lob,
    )


def test_1901(cursor):
    "1901 - test cursor description is accurate for BLOBs"
    cursor.execute("select IntCol, BlobCol from TestBLOBs")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
        ("BLOBCOL", oracledb.DB_TYPE_BLOB, None, None, None, None, 0),
    ]
    assert cursor.description == expected_value


def test_1902(cursor):
    "1902 - test binding and fetching BLOB data (directly)"
    _perform_test(cursor, "BLOB", oracledb.DB_TYPE_BLOB)


def test_1903(cursor):
    "1903 - test binding and fetching BLOB data (indirectly)"
    _perform_test(cursor, "BLOB", oracledb.DB_TYPE_LONG_RAW)


def test_1904(cursor, test_env):
    "1904 - test operations on BLOBs"
    _test_lob_operations(cursor, test_env, "BLOB")


def test_1905(cursor):
    "1905 - test cursor description is accurate for CLOBs"
    cursor.execute("select IntCol, ClobCol from TestCLOBs")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        ("CLOBCOL", oracledb.DB_TYPE_CLOB, None, None, None, None, False),
    ]
    assert cursor.description == expected_value


def test_1906(cursor):
    "1906 - test binding and fetching CLOB data (directly)"
    _perform_test(cursor, "CLOB", oracledb.DB_TYPE_CLOB)


def test_1907(cursor):
    "1907 - test binding and fetching CLOB data (indirectly)"
    _perform_test(cursor, "CLOB", oracledb.DB_TYPE_LONG)


def test_1908(cursor, test_env):
    "1908 - test operations on CLOBs"
    _test_lob_operations(cursor, test_env, "CLOB")


def test_1909(conn, cursor):
    "1909 - test creating a temporary BLOB"
    _test_temporary_lob(conn, cursor, "BLOB")


def test_1910(conn, cursor):
    "1910 - test creating a temporary CLOB"
    _test_temporary_lob(conn, cursor, "CLOB")


def test_1911(conn, cursor):
    "1911 - test creating a temporary NCLOB"
    _test_temporary_lob(conn, cursor, "NCLOB")


def test_1912(cursor):
    "1912 - test retrieving data from a CLOB after multiple fetches"
    cursor.arraysize = 1
    _perform_test(cursor, "CLOB", oracledb.DB_TYPE_CLOB)


def test_1913(cursor):
    "1913 - test cursor description is accurate for NCLOBs"
    cursor.execute("select IntCol, NClobCol from TestNCLOBs")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
        ("NCLOBCOL", oracledb.DB_TYPE_NCLOB, None, None, None, None, 0),
    ]
    assert cursor.description == expected_value


def test_1914(cursor):
    "1914 - test binding and fetching NCLOB data (directly)"
    _perform_test(cursor, "NCLOB", oracledb.DB_TYPE_NCLOB)


def test_1915(conn, cursor):
    "1915 - test binding and fetching NCLOB data (with non-ASCII chars)"
    value = "\u03b4\u4e2a"
    cursor.execute("delete from TestNCLOBs")
    cursor.setinputsizes(val=oracledb.DB_TYPE_NVARCHAR)
    cursor.execute(
        """
        insert into TestNCLOBs (IntCol, NClobCol)
        values (1, :val)
        """,
        val=value,
    )
    conn.commit()
    cursor.execute("select NCLOBCol from TestNCLOBs")
    (nclob,) = cursor.fetchone()
    cursor.setinputsizes(val=oracledb.DB_TYPE_NVARCHAR)
    cursor.execute(
        "update TestNCLOBs set NCLOBCol = :val", val=nclob.read() + value
    )
    cursor.execute("select NCLOBCol from TestNCLOBs")
    (nclob,) = cursor.fetchone()
    assert nclob.read() == value + value


def test_1916(cursor):
    "1916 - test binding and fetching NCLOB data (indirectly)"
    _perform_test(cursor, "NCLOB", oracledb.DB_TYPE_LONG)


def test_1917(cursor, test_env):
    "1917 - test operations on NCLOBs"
    _test_lob_operations(cursor, test_env, "NCLOB")


def test_1918(skip_if_implicit_pooling, conn, cursor):
    "1918 - test temporary LOBs"
    cursor.execute("select sys_context('USERENV', 'SID') from dual")
    (sid,) = cursor.fetchone()
    temp_lobs = _get_temp_lobs(conn, sid)
    with conn.cursor() as cursor:
        cursor.arraysize = 27
        assert temp_lobs == 0
        cursor.execute("select extract(xmlcol, '/').getclobval() from TestXML")
        for (lob,) in cursor:
            lob.read()
            del lob
    temp_lobs = _get_temp_lobs(conn, sid)
    assert temp_lobs == 0


def test_1919(cursor):
    "1919 - test assign string to NCLOB beyond array size"
    nclobVar = cursor.var(oracledb.DB_TYPE_NCLOB)
    pytest.raises(IndexError, nclobVar.setvalue, 1, "test char")


def test_1920(conn, cursor, test_env):
    "1920 - test read/write temporary LOBs using supplemental characters"
    if test_env.charset != "AL32UTF8":
        pytest.skip("Database character set must be AL32UTF8")
    supplemental_chars = (
        "𠜎 𠜱 𠝹 𠱓 𠱸 𠲖 𠳏 𠳕 𠴕 𠵼 𠵿 𠸎 𠸏 𠹷 𠺝 𠺢 𠻗 𠻹 𠻺 𠼭 𠼮 "
        "𠽌 𠾴 𠾼 𠿪 𡁜 𡁯 𡁵 𡁶 𡁻 𡃁 𡃉 𡇙 𢃇 𢞵 𢫕 𢭃 𢯊 𢱑 𢱕 𢳂 𢴈 "
        "𢵌 𢵧 𢺳 𣲷 𤓓 𤶸 𤷪 𥄫 𦉘 𦟌 𦧲 𦧺 𧨾 𨅝 𨈇 𨋢 𨳊 𨳍 𨳒 𩶘"
    )
    cursor.execute("delete from TestCLOBs")
    lob = conn.createlob(oracledb.DB_TYPE_CLOB, supplemental_chars)
    cursor.execute(
        """
        insert into TestCLOBs
        (IntCol, ClobCol)
        values (1, :val)
        """,
        [lob],
    )
    conn.commit()
    cursor.execute("select ClobCol from TestCLOBs")
    (lob,) = cursor.fetchone()
    assert lob.read() == supplemental_chars


def test_1921(cursor, test_env):
    "1921 - test automatic conversion to CLOB for PL/SQL"
    test_env.skip_unless_server_version(12, 2)
    var = cursor.var(str, outconverter=lambda v: v[-15:])
    var.setvalue(0, "A" * 50000)
    cursor.execute(
        """
        declare
            t_Clob          clob;
        begin
            t_Clob := :data;
            dbms_lob.copy(:data, t_Clob, 50000);
            dbms_lob.writeappend(:data, 5, 'BBBBB');
        end;
        """,
        data=var,
    )
    assert var.getvalue() == "A" * 10 + "B" * 5


def test_1922(cursor, test_env):
    "1922 - test automatic conversion to NCLOB for PL/SQL"
    test_env.skip_unless_server_version(12, 2)
    var = cursor.var(oracledb.DB_TYPE_NCHAR, outconverter=lambda v: v[-12:])
    var.setvalue(0, "N" * 51234)
    cursor.execute(
        """
        declare
            t_Clob          nclob;
        begin
            t_Clob := :data;
            dbms_lob.copy(:data, t_Clob, 51234);
            dbms_lob.writeappend(:data, 7, 'PPPPPPP');
        end;
        """,
        data=var,
    )
    assert var.getvalue() == "N" * 5 + "P" * 7


def test_1923(cursor, test_env):
    "1923 - test automatic conversion to BLOB for PL/SQL"
    test_env.skip_unless_server_version(12, 2)
    var = cursor.var(bytes, outconverter=lambda v: v[-14:])
    var.setvalue(0, b"L" * 52345)
    cursor.execute(
        """
        declare
            t_Blob          blob;
        begin
            t_Blob := :data;
            dbms_lob.copy(:data, t_Blob, 52345);
            dbms_lob.writeappend(:data, 6, '515151515151');
        end;
        """,
        data=var,
    )
    assert var.getvalue() == b"L" * 8 + b"Q" * 6


def test_1924(conn):
    "1924 - test pickling of BLOB"
    _test_pickle(conn, "BLOB")


def test_1925(conn):
    "1925 - test pickling of CLOB"
    _test_pickle(conn, "CLOB")


def test_1926(conn):
    "1925 - test pickling of NCLOB"
    _test_pickle(conn, "NCLOB")


def test_1927(cursor, disable_fetch_lobs):
    "1927 - test fetching BLOB as bytes"
    _test_fetch_lobs_direct(cursor, "BLOB")


def test_1928(cursor, disable_fetch_lobs):
    "1928 - test fetching CLOB as str"
    _test_fetch_lobs_direct(cursor, "CLOB")


def test_1929(cursor, disable_fetch_lobs):
    "1929 - test fetching NCLOB as str"
    _test_fetch_lobs_direct(cursor, "NCLOB")


def test_1930(conn, cursor):
    "1930 - test bind ordering with BLOB"
    _test_bind_ordering(conn, cursor, "BLOB")


def test_1931(conn, cursor):
    "1931 - test bind ordering with CLOB"
    _test_bind_ordering(conn, cursor, "CLOB")


def test_1932(conn, cursor):
    "1932 - test bind ordering with NCLOB"
    _test_bind_ordering(conn, cursor, "NCLOB")


def test_1933(conn):
    "1933 - test creating a lob with an invalid type"
    with pytest.raises(TypeError):
        conn.createlob(oracledb.DB_TYPE_NUMBER)
    with pytest.raises(TypeError):
        conn.createlob(oracledb.DB_TYPE_BFILE)


def test_1934(conn):
    "1934 - test creation of temporary LOBs with varying data"
    cases = [
        (oracledb.DB_TYPE_BLOB, b"test_1934A", b"!", b"test_1934A!"),
        (oracledb.DB_TYPE_BLOB, "test_1934B", "!", b"test_1934B!"),
        (oracledb.DB_TYPE_CLOB, b"test_1934C", b"!", "test_1934C!"),
        (oracledb.DB_TYPE_CLOB, "test_1934D", "!", "test_1934D!"),
        (oracledb.DB_TYPE_NCLOB, b"test_1934E", b"!", "test_1934E!"),
        (oracledb.DB_TYPE_NCLOB, "test_1934F", "!", "test_1934F!"),
    ]
    for typ, initial_data, additional_data, expected_result in cases:
        lob = conn.createlob(typ, initial_data)
        lob.write(additional_data, len(initial_data) + 1)
        assert lob.read() == expected_result


def test_1935(test_env):
    "1935 - test reading and writing a LOB with a closed connection"
    types = [
        oracledb.DB_TYPE_BLOB,
        oracledb.DB_TYPE_CLOB,
        oracledb.DB_TYPE_NCLOB,
    ]
    for typ in types:
        conn = test_env.get_connection()
        lob = conn.createlob(typ, "Temp LOB")
        conn.close()
        with test_env.assert_raises_full_code("DPY-1001"):
            lob.read()
        with test_env.assert_raises_full_code("DPY-1001"):
            lob.write("x")


def test_1936(cursor, test_env):
    "1936 - test reading a non-existent directory"
    directory_name = "TEST_1936_MISSING_DIR"
    file_name = "test_1936_missing_file.txt"
    cursor.execute(
        "select BFILENAME(:1, :2) from dual", [directory_name, file_name]
    )
    (bfile,) = cursor.fetchone()
    assert bfile.getfilename() == (directory_name, file_name)
    with test_env.assert_raises_full_code("ORA-22285"):
        bfile.fileexists()
    with test_env.assert_raises_full_code("ORA-22285"):
        bfile.read()


def test_1937(conn, test_env):
    "1937 - test using BFILE methods on non-BFILE LOBs"
    types = [
        oracledb.DB_TYPE_BLOB,
        oracledb.DB_TYPE_CLOB,
        oracledb.DB_TYPE_NCLOB,
    ]
    for typ in types:
        lob = conn.createlob(typ)
        with test_env.assert_raises_full_code("DPY-3026"):
            lob.getfilename()
        with test_env.assert_raises_full_code("DPY-3026"):
            lob.setfilename("not_relevant", "not_relevant")
        with test_env.assert_raises_full_code("DPY-3026"):
            lob.fileexists()


def test_1938(conn, cursor):
    "1938 - confirm that LOB objects are retained across getvalue() calls"
    for typ in (
        oracledb.DB_TYPE_BLOB,
        oracledb.DB_TYPE_CLOB,
        oracledb.DB_TYPE_NCLOB,
    ):
        var = cursor.var(typ)
        lob = conn.createlob(typ, "Some data for test 1938")
        var.setvalue(0, lob)
        assert var.getvalue() is lob


def test_1939(cursor):
    "1939 - temporary LOB in/out without modification"
    value = "test - 1939"
    var = cursor.var(oracledb.DB_TYPE_CLOB)
    var.setvalue(0, value)
    assert var.getvalue().read() == value
    cursor.callproc("pkg_TestLOBs.TestInOut", [var, None, None])
    assert var.getvalue().read() == value


def test_1940(cursor):
    "1940 - temporary LOB in/out with modification"
    search_value = "test"
    replace_value = "replaced"
    initial_value = f"{search_value} - 1939"
    final_value = f"{replace_value} - 1939"
    var = cursor.var(oracledb.DB_TYPE_CLOB)
    var.setvalue(0, initial_value)
    assert var.getvalue().read() == initial_value
    cursor.callproc(
        "pkg_TestLOBs.TestInOut", [var, search_value, replace_value]
    )
    assert var.getvalue().read() == final_value
