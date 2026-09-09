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
Module for testing the VECTOR database type
"""

import array
import json

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(skip_unless_vectors_supported):
    pass


def _test_insert_and_fetch(cursor, value, column_name, expected_typecode):
    """
    Test inserting and fetching a vector.
    """
    cursor.execute("delete from TestVectors")
    if isinstance(value, list):
        cursor.setinputsizes(value=oracledb.DB_TYPE_VECTOR)
    cursor.execute(
        f"""
        insert into TestVectors (IntCol, {column_name})
        values(1, :value)
        """,
        value=value,
    )
    cursor.connection.commit()
    cursor.execute(f"select {column_name} from TestVectors")
    (fetched_value,) = cursor.fetchone()
    if expected_typecode == "b":
        expected_value = array.array("b", [int(i) for i in value])
    else:
        expected_value = array.array(expected_typecode, value)
    assert fetched_value == expected_value
    assert fetched_value.typecode == expected_typecode


def _test_plsql_insert_and_fetch(cursor, vec1, vec2, expected_distance):
    in_out_vec = cursor.var(oracledb.DB_TYPE_VECTOR)
    in_out_vec.setvalue(0, vec2)

    distance = cursor.var(oracledb.DB_TYPE_BINARY_DOUBLE)
    output_vec = cursor.var(oracledb.DB_TYPE_VECTOR)

    plsql_block = """
        BEGIN
            select
                vector_distance(:in_vec, :in_out_vec, euclidean)
                into :distance;
            :output_vec := :in_out_vec;
            :in_out_vec := :in_vec;
        END;
        """

    cursor.execute(
        plsql_block,
        in_vec=vec1,
        in_out_vec=in_out_vec,
        distance=distance,
        output_vec=output_vec,
    )
    assert output_vec.getvalue() == vec2
    assert in_out_vec.getvalue() == vec1
    assert distance.getvalue() == pytest.approx(expected_distance, abs=0.01)


def test_data_types_2700(cursor):
    "2700 - test binding in a vector from a Python list"
    value = [1, 2]
    cursor.setinputsizes(oracledb.DB_TYPE_VECTOR)
    cursor.execute("select :1 from dual", [value])
    (fetched_value,) = cursor.fetchone()
    assert isinstance(fetched_value, array.array)
    assert fetched_value.typecode == "d"
    assert fetched_value == array.array("d", value)


def test_data_types_2701(cursor):
    "2701 - test binding in a vector from a Python array of type float64"
    value = array.array("d", [3, 4, 5])
    cursor.execute("select :1 from dual", [value])
    (fetched_value,) = cursor.fetchone()
    assert isinstance(fetched_value, array.array)
    assert fetched_value.typecode == "d"
    assert fetched_value == value


def test_data_types_2702(cursor):
    "2702 - test binding in a vector from a Python array of type float32"
    value = array.array("f", [6, 7, 8, 9])
    cursor.execute("select :1 from dual", [value])
    (fetched_value,) = cursor.fetchone()
    assert isinstance(fetched_value, array.array)
    assert fetched_value.typecode == "f"
    assert fetched_value == value


def test_data_types_2703(cursor):
    "2702 - test binding in a vector from a Python array of type int8"
    value = array.array("b", [-10, 11, -12, 13, -14])
    cursor.execute("select :1 from dual", [value])
    (fetched_value,) = cursor.fetchone()
    assert isinstance(fetched_value, array.array)
    assert fetched_value.typecode == "b"
    assert fetched_value == value


def test_data_types_2704(cursor, test_env):
    "2704 - unspported array type for vector"
    with test_env.assert_raises_full_code("DPY-3013"):
        cursor.execute("select :1 from dual", [array.array("L", [4, 5])])


def test_data_types_2705(cursor):
    "2705 - insert a float32 vector into a float32 column"
    value = array.array(
        "f",
        [
            1.23,
            4.56,
            -7.89,
            10.11,
            -12.13,
            14.15,
            -16.17,
            18.19,
            -20.21,
            9.23,
            -2.54,
            6.5,
            4.21,
            -1.96,
            3.54,
            2.6,
        ],
    )
    _test_insert_and_fetch(cursor, value, "Vector32Col", "f")


def test_data_types_2706(cursor):
    "2706 - insert a float32 vector into a float64 column"
    value = array.array(
        "f",
        [
            1.23,
            4.56,
            -7.89,
            10.11,
            -12.13,
            14.15,
            -16.17,
            18.19,
            -20.21,
            9.23,
            -2.54,
            6.5,
            4.21,
            -1.96,
            3.54,
            2.6,
        ],
    )
    _test_insert_and_fetch(cursor, value, "Vector64Col", "d")


def test_data_types_2707(cursor):
    "2707 - insert a float32 vector into a flexible format column"
    value = array.array(
        "f",
        [
            1.23,
            4.56,
            -7.89,
            10.11,
            -12.13,
            14.15,
            -16.17,
            18.19,
            -20.21,
            9.23,
            -2.54,
            6.5,
            4.21,
            -1.96,
            3.54,
            2.6,
        ],
    )
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "f")


def test_data_types_2708(cursor):
    "2708 - insert a float64 vector into a float64 column"
    value = array.array(
        "d",
        [
            -0.0375,
            0.625,
            -0.025,
            0.125,
            -0.75,
            0.0,
            -0.3625,
            0.125,
            -0.5,
            0.03125,
            -2.50,
            -0.75,
            1.625,
            1.025,
            0.125,
            0.725,
        ],
    )
    _test_insert_and_fetch(cursor, value, "Vector64Col", "d")


def test_data_types_2709(cursor):
    "2709 - insert float64 vector into a float32 column"
    value = array.array(
        "d",
        [
            -0.0375,
            0.625,
            -0.025,
            0.125,
            -0.75,
            0.0,
            -0.3625,
            0.125,
            -0.5,
            0.03125,
            -2.50,
            -0.75,
            1.625,
            1.025,
            0.125,
            0.725,
        ],
    )
    _test_insert_and_fetch(cursor, value, "Vector32Col", "f")


def test_data_types_2710(cursor):
    "2710 - insert float64 vector into a flexible type column"
    value = array.array(
        "d",
        [
            -0.0375,
            0.625,
            -0.025,
            0.125,
            -0.75,
            0.0,
            -0.3625,
            0.125,
            -0.5,
            0.03125,
            -2.50,
            -0.75,
            1.625,
            1.025,
            0.125,
            0.725,
        ],
    )
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "d")


def test_data_types_2711(cursor, test_env):
    "2711 - insert a vector with an invalid size"
    cursor.execute("truncate table TestVectors")
    for num_elems in [4, 20]:
        statement = """
                insert into TestVectors (IntCol, Vector64Col)
                values(2, :1)"""
        vector = array.array("d", [i * 0.625 for i in range(num_elems)])
        with test_env.assert_raises_full_code("ORA-51803"):
            cursor.execute(statement, [vector])


def test_data_types_2712(cursor):
    "2712 - verify fetch info for vectors"
    attr_names = [
        "name",
        "type_code",
        "vector_dimensions",
        "vector_format",
        "vector_is_sparse",
    ]
    expected_values = [
        ["INTCOL", oracledb.DB_TYPE_NUMBER, None, None, None],
        ["VECTORFLEXALLCOL", oracledb.DB_TYPE_VECTOR, None, None, False],
        ["VECTORFLEXTYPECOL", oracledb.DB_TYPE_VECTOR, 2, None, False],
        [
            "VECTORFLEX8COL",
            oracledb.DB_TYPE_VECTOR,
            None,
            oracledb.VECTOR_FORMAT_INT8,
            False,
        ],
        [
            "VECTORFLEX32COL",
            oracledb.DB_TYPE_VECTOR,
            None,
            oracledb.VECTOR_FORMAT_FLOAT32,
            False,
        ],
        [
            "VECTORFLEX64COL",
            oracledb.DB_TYPE_VECTOR,
            None,
            oracledb.VECTOR_FORMAT_FLOAT64,
            False,
        ],
        [
            "VECTOR8COL",
            oracledb.DB_TYPE_VECTOR,
            16,
            oracledb.VECTOR_FORMAT_INT8,
            False,
        ],
        [
            "VECTOR32COL",
            oracledb.DB_TYPE_VECTOR,
            16,
            oracledb.VECTOR_FORMAT_FLOAT32,
            False,
        ],
        [
            "VECTOR64COL",
            oracledb.DB_TYPE_VECTOR,
            16,
            oracledb.VECTOR_FORMAT_FLOAT64,
            False,
        ],
    ]
    cursor.execute("select * from TestVectors")
    values = [[getattr(i, n) for n in attr_names] for i in cursor.description]
    assert values == expected_values
    assert cursor.description[3].vector_format is oracledb.VectorFormat.INT8


def test_data_types_2713(cursor):
    "2713 - insert an int8 vector into an int8 column"
    value = array.array(
        "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_data_types_2714(cursor):
    "2714 - insert an int8 vector into a float32 column"
    value = array.array(
        "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector32Col", "f")


def test_data_types_2715(cursor):
    "2715 - insert an int8 vector into a float64 column"
    value = array.array(
        "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector64Col", "d")


def test_data_types_2716(cursor):
    "2716 - insert an int8 vector into a flexible column"
    value = array.array(
        "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "b")


def test_data_types_2717(cursor):
    "2717 - insert a float32 vector into an int8 column"
    value = array.array(
        "f", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_data_types_2718(cursor):
    "2718 - insert a float64 vector into an int8 column"
    value = array.array(
        "d", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_data_types_2719(conn, cursor):
    "2719 - test dml returning vector type"
    value = array.array("d", [6423.5, 6423.625])
    out_var = cursor.var(oracledb.DB_TYPE_VECTOR)
    cursor.execute("delete from TestVectors")
    cursor.execute(
        """
        insert into TestVectors (IntCol, VectorFlexTypeCol)
        values (1, :value)
        returning VectorFlexTypeCol into :out_value
        """,
        [value, out_var],
    )
    conn.commit()
    assert value == out_var.getvalue()[0]


def test_data_types_2720(conn, cursor):
    "2720 - test handling of NULL vector value"
    cursor.execute("delete from TestVectors")
    cursor.execute("insert into TestVectors (IntCol) values (1)")
    conn.commit()
    cursor.execute("select VectorFlexTypeCol from TestVectors")
    (fetched_value,) = cursor.fetchone()
    assert fetched_value is None


def test_data_types_2721(cursor, test_env):
    "2721 - insert a float32 vector into an int8 column (negative)"
    value = array.array(
        "f",
        [-130, -129, 0, 1, 2, 3, 127, 128, 129, 348, 12, 49, 78, 12, 9, 2],
    )
    with test_env.assert_raises_full_code("ORA-51806"):
        _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_data_types_2722(cursor):
    "2722 - insert a float64 vector with 65,533 dimensions"
    value = array.array("d", [2.5] * 65533)
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "d")


def test_data_types_2723(cursor):
    "2723 - insert a float32 vector with 65,533 dimensions"
    value = array.array("f", [2.5] * 65533)
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "f")


def test_data_types_2724(cursor):
    "2724 - insert an int8 vector with 65,533 dimensions"
    value = array.array("b", [2] * 65533)
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "b")


def test_data_types_2725(cursor):
    "2725 - insert vectors with different dimensions"
    for dim in [30, 70, 255, 256, 65534, 65535]:
        for typ in ["f", "d", "b"]:
            element_value = 3 if typ == "b" else 1.5
            value = array.array(typ, [element_value] * dim)
            _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", typ)


@pytest.mark.skip("awaiting database support")
def test_data_types_2726(conn, cursor):
    "2726 - insert and fetch VECTOR data using CLOB"
    value = [6426, -15.75, 283.125, -8.625]
    clob = conn.createlob(oracledb.DB_TYPE_CLOB)
    clob.write(json.dumps(value))
    cursor.execute("delete from TestVectors")
    cursor.execute(
        """
        insert into TestVectors (IntCol, VectorFlexAllCol)
        values(1, :value)
        """,
        value=clob,
    )

    def type_handler(cursor, metadata):
        if metadata.name == "VECTORFLEXALLCOL":
            return cursor.var(
                oracledb.DB_TYPE_CLOB, arraysize=cursor.arraysize
            )

    cursor.outputtypehandler = type_handler

    cursor.execute("select VectorFlexAllCol from TestVectors")
    (clob_data,) = cursor.fetchone()
    fetched_value = json.loads(clob_data.read())
    assert fetched_value == value


def test_data_types_2727(cursor):
    "2727 - insert and fetch VECTOR data using strings"
    value = [6427, -25.75, 383.125, -18.625]
    cursor.execute("delete from TestVectors")
    cursor.execute(
        """
        insert into TestVectors (IntCol, VectorFlexAllCol)
        values(1, :value)
        """,
        value=json.dumps(value),
    )

    def type_handler(cursor, metadata):
        if metadata.name == "VECTORFLEXALLCOL":
            return cursor.var(
                oracledb.DB_TYPE_LONG, arraysize=cursor.arraysize
            )

    cursor.outputtypehandler = type_handler

    cursor.execute("select VectorFlexAllCol from TestVectors")
    (fetched_value,) = cursor.fetchone()
    assert json.loads(fetched_value) == value


def test_data_types_2728(cursor):
    "2728 - insert vectors with flexible dimensions and conversion"
    for dim in [30, 255, 256, 257, 32768, 65535]:
        for source_type in ["f", "d", "b"]:
            for target_type in ["f", "d", "b"]:
                if target_type == "f":
                    target_col = "VectorFlex32Col"
                elif target_type == "d":
                    target_col = "VectorFlex64Col"
                else:
                    target_col = "VectorFlex8Col"
                element_value = 4 if source_type == "b" else 2.5
                value = array.array(source_type, [element_value] * dim)
                _test_insert_and_fetch(cursor, value, target_col, target_type)


@pytest.mark.skip("awaiting database support")
def test_data_types_2729(cursor):
    "2727 - insert and fetch large VECTOR data using strings"
    value = [0.12345678925] * 35625
    cursor.execute("delete from TestVectors")
    cursor.execute(
        """
        insert into TestVectors (IntCol, VectorFlex64Col)
        values(1, :value)
        """,
        value=json.dumps(value),
    )

    def type_handler(cursor, metadata):
        if metadata.name == "VECTORFLEX64COL":
            return cursor.var(
                oracledb.DB_TYPE_LONG, arraysize=cursor.arraysize
            )

    cursor.outputtypehandler = type_handler

    cursor.execute("select VectorFlex64Col from TestVectors")
    (fetched_value,) = cursor.fetchone()
    assert json.loads(fetched_value) == value


def test_data_types_2730(cursor, test_env):
    "2730 - test binding a vector with inf values (negative)"
    value = array.array(
        "d", [float("inf") if i % 2 else float("-inf") for i in range(16)]
    )
    with test_env.assert_raises_full_code("ORA-51805", "ORA-51807"):
        cursor.execute("select :1 from dual", [value])


def test_data_types_2731(cursor):
    "2731 - test setting an invalid type to a vector"
    var = cursor.var(oracledb.DB_TYPE_VECTOR)
    pytest.raises(TypeError, var.setvalue, 0, [[i] for i in range(16)])


def test_data_types_2732(cursor):
    "2732 - fetch JSON value with an embedded vector"
    cursor.execute("""
        select json_object(
            'id' : 6432,
            'vector' : to_vector('[1, 2, 3]')
            returning json
        ) from dual
        """)
    (result,) = cursor.fetchone()
    expected_val = dict(id=6432, vector=array.array("f", [1, 2, 3]))
    assert result == expected_val


def test_data_types_2733(conn, cursor):
    "2733 - bind JSON value with an embedded vector"
    value = dict(id=6433, vector=array.array("d", [6433, 6433.25, 6433.5]))
    cursor.execute("delete from TestJson")
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.execute("insert into TestJson values (:1, :2)", [6433, value])
    conn.commit()
    cursor.execute("select JsonCol from TestJson")
    (fetched_val,) = cursor.fetchone()
    assert fetched_val == value


def test_data_types_2734(cursor):
    "2734 - executemany() without setinputsizes()"
    cursor.execute("delete from TestVectors")
    values = [array.array("f", [3.1416, 4]), [3.14159, 5]]
    cursor.executemany(
        """
        insert into TestVectors (IntCol, VectorFlexTypeCol)
        values (:1, :2)
        """,
        list(enumerate(values)),
    )
    cursor.execute("select VectorFlexTypeCol from TestVectors order by IntCol")
    expected_value = [
        (array.array("f", [3.1416, 4.0]),),
        (array.array("d", [3.14159, 5.0]),),
    ]
    assert cursor.fetchall() == expected_value


def test_data_types_2735(cursor):
    "2735 - executemany() with setinputsizes()"
    cursor.execute("delete from TestVectors")
    values = [[144, 1000], array.array("d", [66.0, 7.14])]
    cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR)
    cursor.executemany(
        """
        insert into TestVectors (IntCol, VectorFlex64Col)
        values (:1, :2)
        """,
        list(enumerate(values)),
    )
    cursor.execute("select VectorFlex64Col from TestVectors order by IntCol")
    expected_value = [
        (array.array("d", [144.0, 1000.0]),),
        (array.array("d", [66.0, 7.14]),),
    ]
    assert cursor.fetchall() == expected_value


def test_data_types_2736(cursor, test_env):
    "2736 - vector with zero dimensions"
    with test_env.assert_raises_full_code("DPY-4031"):
        cursor.setinputsizes(oracledb.DB_TYPE_VECTOR)
        cursor.execute("select :1", [[]])
    with test_env.assert_raises_full_code("DPY-4031"):
        cursor.execute("select :1", [array.array("d", [])])


def test_data_types_2737(cursor):
    "2737 - insert a list vector into a flexible format column"
    value = [1.5, 9.9]
    _test_insert_and_fetch(cursor, value, "VectorFlexTypeCol", "d")


def test_data_types_2738(cursor):
    "2738 - insert a list vector into a flexible size column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "d")


def test_data_types_2739(cursor):
    "2739 - insert a list vector into a flexible float32 column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "VectorFlex32Col", "f")


def test_data_types_2740(cursor):
    "2740 - insert a list vector into a flexible float64 column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "VectorFlex64Col", "d")


def test_data_types_2741(cursor):
    "2741 - insert a list vector into a float32 column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "Vector32Col", "f")


def test_data_types_2742(cursor):
    "2742 - insert a list vector into a float64 column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "Vector64Col", "d")


def test_data_types_2743(cursor):
    "2743 - insert a list vector into a flexible int8 column"
    value = [1, 9, 3, 8, 4, 7, 5, 6, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "VectorFlex8Col", "b")


def test_data_types_2744(cursor):
    "2744 - insert a list vector into an int8 column"
    value = [1, 9, 3, 8, 4, 7, 5, 6, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_data_types_2745(cursor):
    "2745 - test setting a PL-SQL type to a float32 vector"
    vec1 = array.array("f", [1, 1.5, 2, 2.5])
    vec2 = array.array("f", [4, 4.5, 5, 5.5])
    _test_plsql_insert_and_fetch(cursor, vec1, vec2, 6)

    vec3 = array.array("f", [3.5] * 65535)
    vec4 = array.array("f", [2.5] * 65535)
    _test_plsql_insert_and_fetch(cursor, vec3, vec4, 256)


def test_data_types_2746(cursor):
    "2746 - test setting a PL-SQL type to a float64 vector"
    vec1 = array.array("d", [1, 1.5, 2, 2.5])
    vec2 = array.array("d", [4, 4.5, 5, 5.5])
    _test_plsql_insert_and_fetch(cursor, vec1, vec2, 6)

    vec3 = array.array("d", [3.5] * 65535)
    vec4 = array.array("d", [2.5] * 65535)
    _test_plsql_insert_and_fetch(cursor, vec3, vec4, 256)


def test_data_types_2747(cursor):
    "2747 - test setting a PL-SQL type to a int8 vector"
    vec1 = array.array("b", [1, 2, 3, 4])
    vec2 = array.array("b", [5, 6, 7, 8])
    _test_plsql_insert_and_fetch(cursor, vec1, vec2, 8)

    vec3 = array.array("b", [3] * 65535)
    vec4 = array.array("b", [2] * 65535)
    _test_plsql_insert_and_fetch(cursor, vec3, vec4, 256)
