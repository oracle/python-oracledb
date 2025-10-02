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
2500 - Module for testing string variables
"""

import random
import string

import oracledb
import pytest


@pytest.fixture(scope="module")
def module_data():
    data = []
    for i in range(1, 11):
        string_col = f"String {i}"
        fixed_char_col = f"Fixed Char {i}".ljust(40)
        raw_col = f"Raw {i}".encode("ascii")
        if i % 2:
            nullable_col = f"Nullable {i}"
        else:
            nullable_col = None
        data_tuple = (i, string_col, raw_col, fixed_char_col, nullable_col)
        data.append(data_tuple)
    return data


@pytest.fixture(scope="module")
def module_data_by_key(module_data):
    data_by_key = {}
    for row in module_data:
        data_by_key[row[0]] = row
    return data_by_key


def return_strings_as_bytes(cursor, metadata):
    if metadata.type_code is oracledb.DB_TYPE_VARCHAR:
        return cursor.var(str, arraysize=cursor.arraysize, bypass_decode=True)


def test_2500(cursor):
    "2500 - test creating array var and then increasing the internal size"
    val = ["12345678901234567890"] * 3
    var = cursor.arrayvar(str, len(val), 4)
    var.setvalue(0, val)
    assert var.getvalue() == val


def test_2501(cursor, module_data_by_key):
    "2501 - test binding in a string"
    cursor.execute(
        "select * from TestStrings where StringCol = :value",
        value="String 5",
    )
    assert cursor.fetchall() == [module_data_by_key[5]]


def test_2502(cursor):
    "2502 - test binding a different variable on second execution"
    retval_1 = cursor.var(oracledb.STRING, 30)
    retval_2 = cursor.var(oracledb.STRING, 30)
    cursor.execute("begin :retval := 'Called'; end;", retval=retval_1)
    assert retval_1.getvalue() == "Called"
    cursor.execute("begin :retval := 'Called'; end;", retval=retval_2)
    assert retval_2.getvalue() == "Called"


def test_2503(cursor):
    "2503 - test exceeding the number of elements returns IndexError"
    var = cursor.var(str)
    pytest.raises(IndexError, var.getvalue, 1)


def test_2504(cursor, module_data_by_key):
    "2504 - test binding in a string after setting input sizes to a number"
    cursor.setinputsizes(value=oracledb.NUMBER)
    cursor.execute(
        "select * from TestStrings where StringCol = :value",
        value="String 6",
    )
    assert cursor.fetchall() == [module_data_by_key[6]]


def test_2505(cursor, module_data):
    "2505 - test binding in a string array"
    return_value = cursor.var(oracledb.NUMBER)
    array = [r[1] for r in module_data]
    statement = """
            begin
                :return_value := pkg_TestStringArrays.TestInArrays(
                    :integer_value, :array);
            end;"""
    cursor.execute(
        statement, return_value=return_value, integer_value=5, array=array
    )
    assert return_value.getvalue() == 86
    array = [f"String - {i}" for i in range(15)]
    cursor.execute(statement, integer_value=8, array=array)
    assert return_value.getvalue() == 163


def test_2506(cursor, module_data):
    "2506 - test binding in a string array (with setinputsizes)"
    return_value = cursor.var(oracledb.NUMBER)
    cursor.setinputsizes(array=[oracledb.STRING, 10])
    array = [r[1] for r in module_data]
    cursor.execute(
        """
        begin
            :return_value := pkg_TestStringArrays.TestInArrays(
                :integer_value, :array);
        end;
        """,
        return_value=return_value,
        integer_value=6,
        array=array,
    )
    assert return_value.getvalue() == 87


def test_2507(cursor, module_data):
    "2507 - test binding in a string array (with arrayvar)"
    return_value = cursor.var(oracledb.NUMBER)
    array = cursor.arrayvar(oracledb.STRING, 10, 20)
    array.setvalue(0, [r[1] for r in module_data])
    cursor.execute(
        """
        begin
            :return_value := pkg_TestStringArrays.TestInArrays(
                :integer_value, :array);
        end;
        """,
        return_value=return_value,
        integer_value=7,
        array=array,
    )
    assert return_value.getvalue() == 88


def test_2508(cursor, module_data):
    "2508 - test binding in/out a string array (with arrayvar)"
    array = cursor.arrayvar(oracledb.STRING, 10, 100)
    original_data = [r[1] for r in module_data]
    expected_data = [
        "Converted element # %d originally had length %d"
        % (i, len(original_data[i - 1]))
        for i in range(1, 6)
    ] + original_data[5:]
    array.setvalue(0, original_data)
    cursor.execute(
        """
        begin
            pkg_TestStringArrays.TestInOutArrays(:num_elems, :array);
        end;
        """,
        num_elems=5,
        array=array,
    )
    assert array.getvalue() == expected_data


def test_2509(cursor):
    "2509 - test binding out a string array (with arrayvar)"
    array = cursor.arrayvar(oracledb.STRING, 6, 100)
    expected_data = [f"Test out element # {i}" for i in range(1, 7)]
    cursor.execute(
        """
        begin
            pkg_TestStringArrays.TestOutArrays(:num_elems, :array);
        end;
        """,
        num_elems=6,
        array=array,
    )
    assert array.getvalue() == expected_data


def test_2510(cursor, module_data_by_key):
    "2510 - test binding in a raw"
    cursor.setinputsizes(value=oracledb.BINARY)
    cursor.execute(
        "select * from TestStrings where RawCol = :value",
        value="Raw 4".encode(),
    )
    assert cursor.fetchall() == [module_data_by_key[4]]


def test_2511(cursor, module_data_by_key):
    "2511 - test binding (and fetching) a rowid"
    cursor.execute("select rowid from TestStrings where IntCol = 3")
    (rowid,) = cursor.fetchone()
    cursor.execute(
        "select * from TestStrings where rowid = :value",
        value=rowid,
    )
    assert cursor.fetchall() == [module_data_by_key[3]]


def test_2513(cursor):
    "2513 - test binding in a null"
    cursor.execute(
        "select * from TestStrings where StringCol = :value",
        value=None,
    )
    assert cursor.fetchall() == []


def test_2514(cursor):
    "2514 - test binding out with set input sizes defined (by type)"
    bind_vars = cursor.setinputsizes(value=oracledb.STRING)
    cursor.execute(
        """
        begin
            :value := 'TSI';
        end;
        """
    )
    assert bind_vars["value"].getvalue() == "TSI"


def test_2515(cursor):
    "2515 - test binding out with set input sizes defined (by integer)"
    bind_vars = cursor.setinputsizes(value=30)
    cursor.execute(
        """
        begin
            :value := 'TSI (I)';
        end;
        """
    )
    assert bind_vars["value"].getvalue() == "TSI (I)"


def test_2516(cursor):
    "2516 - test binding in/out with set input sizes defined (by type)"
    bind_vars = cursor.setinputsizes(value=oracledb.STRING)
    cursor.execute(
        """
        begin
            :value := :value || ' TSI';
        end;
        """,
        value="InVal",
    )
    assert bind_vars["value"].getvalue() == "InVal TSI"


def test_2517(cursor):
    "2517 - test binding in/out with set input sizes defined (by integer)"
    bind_vars = cursor.setinputsizes(value=30)
    cursor.execute(
        """
        begin
            :value := :value || ' TSI (I)';
        end;
        """,
        value="InVal",
    )
    assert bind_vars["value"].getvalue() == "InVal TSI (I)"


def test_2518(cursor):
    "2518 - test binding out with cursor.var() method"
    var = cursor.var(oracledb.STRING)
    cursor.execute(
        """
        begin
            :value := 'TSI (VAR)';
        end;
        """,
        value=var,
    )
    assert var.getvalue() == "TSI (VAR)"


def test_2519(cursor):
    "2519 - test binding in/out with cursor.var() method"
    var = cursor.var(oracledb.STRING)
    var.setvalue(0, "InVal")
    cursor.execute(
        """
        begin
            :value := :value || ' TSI (VAR)';
        end;
        """,
        value=var,
    )
    assert var.getvalue() == "InVal TSI (VAR)"


def test_2520(cursor):
    "2520 - test that binding a long string succeeds"
    cursor.setinputsizes(big_string=oracledb.DB_TYPE_LONG)
    cursor.execute(
        """
        declare
            t_Temp varchar2(20000);
        begin
            t_Temp := :big_string;
        end;
        """,
        big_string="X" * 10000,
    )


def test_2521(cursor):
    "2521 - test that setinputsizes() returns a long variable"
    var = cursor.setinputsizes(test=90000)["test"]
    in_string = "1234567890" * 9000
    var.setvalue(0, in_string)
    out_string = var.getvalue()
    msg = (
        f"output does not match: in was {len(in_string)}, "
        f"out was {len(out_string)}"
    )
    assert in_string == out_string, msg


def test_2522(cursor, test_env):
    "2522 - test cursor description is accurate"
    cursor.execute("select * from TestStrings")
    varchar_ratio, nvarchar_ratio = test_env.charset_ratios
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        (
            "STRINGCOL",
            oracledb.DB_TYPE_VARCHAR,
            20,
            20 * varchar_ratio,
            None,
            None,
            False,
        ),
        ("RAWCOL", oracledb.DB_TYPE_RAW, 30, 30, None, None, False),
        (
            "FIXEDCHARCOL",
            oracledb.DB_TYPE_CHAR,
            40,
            40 * varchar_ratio,
            None,
            None,
            False,
        ),
        (
            "NULLABLECOL",
            oracledb.DB_TYPE_VARCHAR,
            50,
            50 * varchar_ratio,
            None,
            None,
            True,
        ),
    ]
    assert cursor.description == expected_value


def test_2523(cursor, module_data):
    "2523 - test that fetching all of the data returns the correct results"
    cursor.execute("select * From TestStrings order by IntCol")
    assert cursor.fetchall() == module_data
    assert cursor.fetchall() == []


def test_2524(cursor, module_data):
    "2524 - test that fetching data in chunks returns the correct results"
    cursor.execute("select * From TestStrings order by IntCol")
    assert cursor.fetchmany(3) == module_data[0:3]
    assert cursor.fetchmany(2) == module_data[3:5]
    assert cursor.fetchmany(4) == module_data[5:9]
    assert cursor.fetchmany(3) == module_data[9:]
    assert cursor.fetchmany(3) == []


def test_2525(cursor, module_data_by_key):
    "2525 - test that fetching a single row returns the correct results"
    cursor.execute(
        """
        select *
        from TestStrings
        where IntCol in (3, 4)
        order by IntCol
        """
    )
    assert cursor.fetchone() == module_data_by_key[3]
    assert cursor.fetchone() == module_data_by_key[4]
    assert cursor.fetchone() is None


def test_2526(conn, cursor, test_env):
    "2526 - test binding and fetching supplemental charcters"
    if test_env.charset != "AL32UTF8":
        pytest.skip("Database character set must be AL32UTF8")
    supplemental_chars = (
        "𠜎 𠜱 𠝹 𠱓 𠱸 𠲖 𠳏 𠳕 𠴕 𠵼 𠵿 𠸎 𠸏 "
        "𠹷 𠺝 𠺢 𠻗 𠻹 𠻺 𠼭 𠼮 𠽌 𠾴 𠾼 𠿪 𡁜 "
        "𡁯 𡁵 𡁶 𡁻 𡃁 𡃉 𡇙 𢃇 𢞵 𢫕 𢭃 𢯊 𢱑 "
        "𢱕 𢳂 𢴈 𢵌 𢵧 𢺳 𣲷 𤓓 𤶸 𤷪 𥄫 𦉘 𦟌 "
        "𦧲 𦧺 𧨾 𨅝 𨈇 𨋢 𨳊 𨳍 𨳒 𩶘"
    )
    cursor.execute("truncate table TestTempTable")
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        (1, supplemental_chars),
    )
    conn.commit()
    cursor.execute("select StringCol1 from TestTempTable")
    (value,) = cursor.fetchone()
    assert value == supplemental_chars


def test_2527(conn, cursor):
    "2527 - test binding twice with a larger string the second time"
    cursor.execute("truncate table TestTempTable")
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    short_string = "short string"
    long_string = "long string " * 30
    cursor.execute(sql, (1, short_string))
    cursor.execute(sql, (2, long_string))
    conn.commit()
    cursor.execute(
        """
        select IntCol, StringCol1
        from TestTempTable
        order by IntCol
        """
    )
    assert cursor.fetchall() == [(1, short_string), (2, long_string)]


def test_2528(conn, test_env):
    "2528 - test issue 50 - avoid error ORA-24816"
    if not test_env.has_server_version(12, 2):
        pytest.skip("not supported on this server")

    cursor = conn.cursor()
    try:
        cursor.execute("drop table issue_50 purge")
    except oracledb.DatabaseError:
        pass
    cursor.execute(
        """
        create table issue_50 (
            Id          number(11) primary key,
            Str1        nvarchar2(256),
            Str2        nvarchar2(256),
            Str3        nvarchar2(256),
            NClob1      nclob,
            NClob2      nclob
        )
        """
    )
    id_var = cursor.var(oracledb.NUMBER)
    cursor.execute(
        """
        insert into issue_50 (Id, Str2, Str3, NClob1, NClob2, Str1)
        values (:arg0, :arg1, :arg2, :arg3, :arg4, :arg5)
        returning id into :arg6
        """,
        [1, "555a4c78", "f319ef0e", "23009914", "", "", id_var],
    )
    cursor = conn.cursor()
    cursor.execute(
        """
        insert into issue_50 (Id, Str2, Str3, NClob1, NClob2, Str1)
        values (:arg0, :arg1, :arg2, :arg3, :arg4, :arg5)
        returning id into :arg6
        """,
        [2, "d5ff845a", "94275767", "bf161ff6", "", "", id_var],
    )
    cursor.execute("drop table issue_50 purge")


def test_2529(cursor, test_env):
    "2529 - test assigning a string to rowid"
    var = cursor.var(oracledb.ROWID)
    with test_env.assert_raises_full_code("DPY-3004"):
        var.setvalue(0, "ABDHRYTHFJGKDKKDH")


def test_2530(cursor):
    "2530 - test fetching XMLType (< 1K) as a string"
    cursor.execute(
        """
        select XMLElement("string", stringCol) as xml
        from TestStrings
        where intCol = 1
        """
    )
    (actual_value,) = cursor.fetchone()
    assert actual_value == "<string>String 1</string>"
    assert cursor.description == [
        ("XML", oracledb.DB_TYPE_XMLTYPE, None, None, None, None, True)
    ]


def test_2531(cursor):
    "2531 - test inserting and fetching XMLType (1K) as a string"
    cursor.execute("truncate table TestTempXML")
    chars = string.ascii_uppercase + string.ascii_lowercase
    random_string = "".join(random.choice(chars) for _ in range(1024))
    int_val = 2531
    xml_string = f"<data>{random_string}</data>"
    cursor.execute(
        "insert into TestTempXML (IntCol, XMLCol) values (:1, :2)",
        (int_val, xml_string),
    )
    cursor.execute(
        "select XMLCol from TestTempXML where intCol = :1",
        [int_val],
    )
    (actual_value,) = cursor.fetchone()
    assert actual_value.strip() == xml_string


def test_2532(cursor, module_data):
    "2532 - fetching null and not null values can use optimised path"
    sql = """
            select * from TestStrings
            where IntCol between :start_value and :end_value"""
    cursor.execute(sql, start_value=2, end_value=5)
    assert cursor.fetchall() == module_data[1:5]
    cursor.execute(sql, start_value=5, end_value=8)
    assert cursor.fetchall() == module_data[4:8]
    cursor.execute(sql, start_value=8, end_value=10)
    assert cursor.fetchall() == module_data[7:10]


def test_2533(conn, cursor):
    "2533 - test bypass string decode"
    cursor.execute("truncate table TestTempTable")
    string_val = "I bought a cafetière on the Champs-Élysées"
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    with conn.cursor() as cursor:
        cursor.execute(sql, (1, string_val))
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchone() == (1, string_val)
    with conn.cursor() as cursor:
        cursor.outputtypehandler = return_strings_as_bytes
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchone() == (1, string_val.encode())
    with conn.cursor() as cursor:
        cursor.outputtypehandler = None
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchone() == (1, string_val)


def test_2534(skip_unless_thin_mode, conn, cursor):
    "2534 - test inserting and fetching XMLType (32K) as a string"
    cursor.execute("truncate table TestTempXML")
    chars = string.ascii_uppercase + string.ascii_lowercase
    random_string = "".join(random.choice(chars) for _ in range(32768))
    int_val = 2534
    xml_string = f"<data>{random_string}</data>"
    lob = conn.createlob(oracledb.DB_TYPE_CLOB)
    lob.write(xml_string)
    cursor.execute(
        """
        insert into TestTempXML (IntCol, XMLCol)
        values (:1, sys.xmltype(:2))
        """,
        (int_val, lob),
    )
    cursor.execute(
        "select XMLCol from TestTempXML where intCol = :1",
        [int_val],
    )
    (actual_value,) = cursor.fetchone()
    assert actual_value.strip() == xml_string
