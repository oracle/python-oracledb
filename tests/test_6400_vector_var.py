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
6400 - Module for testing the VECTOR database type
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


def test_6400(cursor):
    "6400 - test binding in a vector from a Python list"
    value = [1, 2]
    cursor.setinputsizes(oracledb.DB_TYPE_VECTOR)
    cursor.execute("select :1 from dual", [value])
    (fetched_value,) = cursor.fetchone()
    assert isinstance(fetched_value, array.array)
    assert fetched_value.typecode == "d"
    assert fetched_value == array.array("d", value)


def test_6401(cursor):
    "6401 - test binding in a vector from a Python array of type float64"
    value = array.array("d", [3, 4, 5])
    cursor.execute("select :1 from dual", [value])
    (fetched_value,) = cursor.fetchone()
    assert isinstance(fetched_value, array.array)
    assert fetched_value.typecode == "d"
    assert fetched_value == value


def test_6402(cursor):
    "6402 - test binding in a vector from a Python array of type float32"
    value = array.array("f", [6, 7, 8, 9])
    cursor.execute("select :1 from dual", [value])
    (fetched_value,) = cursor.fetchone()
    assert isinstance(fetched_value, array.array)
    assert fetched_value.typecode == "f"
    assert fetched_value == value


def test_6403(cursor):
    "6402 - test binding in a vector from a Python array of type int8"
    value = array.array("b", [-10, 11, -12, 13, -14])
    cursor.execute("select :1 from dual", [value])
    (fetched_value,) = cursor.fetchone()
    assert isinstance(fetched_value, array.array)
    assert fetched_value.typecode == "b"
    assert fetched_value == value


def test_6404(cursor, test_env):
    "6404 - unspported array type for vector"
    with test_env.assert_raises_full_code("DPY-3013"):
        cursor.execute("select :1 from dual", [array.array("L", [4, 5])])


def test_6405(cursor):
    "6405 - insert a float32 vector into a float32 column"
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


def test_6406(cursor):
    "6406 - insert a float32 vector into a float64 column"
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


def test_6407(cursor):
    "6407 - insert a float32 vector into a flexible format column"
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


def test_6408(cursor):
    "6408 - insert a float64 vector into a float64 column"
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


def test_6409(cursor):
    "6409 - insert float64 vector into a float32 column"
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


def test_6410(cursor):
    "6410 - insert float64 vector into a flexible type column"
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


def test_6411(cursor, test_env):
    "6411 - insert a vector with an invalid size"
    cursor.execute("truncate table TestVectors")
    for num_elems in [4, 20]:
        statement = """
                insert into TestVectors (IntCol, Vector64Col)
                values(2, :1)"""
        vector = array.array("d", [i * 0.625 for i in range(num_elems)])
        with test_env.assert_raises_full_code("ORA-51803"):
            cursor.execute(statement, [vector])


def test_6412(cursor):
    "6412 - verify fetch info for vectors"
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


def test_6413(cursor):
    "6413 - insert an int8 vector into an int8 column"
    value = array.array(
        "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_6414(cursor):
    "6414 - insert an int8 vector into a float32 column"
    value = array.array(
        "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector32Col", "f")


def test_6415(cursor):
    "6415 - insert an int8 vector into a float64 column"
    value = array.array(
        "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector64Col", "d")


def test_6416(cursor):
    "6416 - insert an int8 vector into a flexible column"
    value = array.array(
        "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "b")


def test_6417(cursor):
    "6417 - insert a float32 vector into an int8 column"
    value = array.array(
        "f", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_6418(cursor):
    "6418 - insert a float64 vector into an int8 column"
    value = array.array(
        "d", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
    )
    _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_6419(conn, cursor):
    "6419 - test dml returning vector type"
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


def test_6420(conn, cursor):
    "6420 - test handling of NULL vector value"
    cursor.execute("delete from TestVectors")
    cursor.execute("insert into TestVectors (IntCol) values (1)")
    conn.commit()
    cursor.execute("select VectorFlexTypeCol from TestVectors")
    (fetched_value,) = cursor.fetchone()
    assert fetched_value is None


def test_6421(cursor, test_env):
    "6421 - insert a float32 vector into an int8 column (negative)"
    value = array.array(
        "f",
        [-130, -129, 0, 1, 2, 3, 127, 128, 129, 348, 12, 49, 78, 12, 9, 2],
    )
    with test_env.assert_raises_full_code("ORA-51806"):
        _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_6422(cursor):
    "6422 - insert a float64 vector with 65,533 dimensions"
    value = array.array("d", [2.5] * 65533)
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "d")


def test_6423(cursor):
    "6423 - insert a float32 vector with 65,533 dimensions"
    value = array.array("f", [2.5] * 65533)
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "f")


def test_6424(cursor):
    "6424 - insert an int8 vector with 65,533 dimensions"
    value = array.array("b", [2] * 65533)
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "b")


def test_6425(cursor):
    "6425 - insert vectors with different dimensions"
    for dim in [30, 70, 255, 256, 65534, 65535]:
        for typ in ["f", "d", "b"]:
            element_value = 3 if typ == "b" else 1.5
            value = array.array(typ, [element_value] * dim)
            _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", typ)


@pytest.mark.skip("awaiting database support")
def test_6426(conn, cursor):
    "6426 - insert and fetch VECTOR data using CLOB"
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


def test_6427(cursor):
    "6427 - insert and fetch VECTOR data using strings"
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


def test_6428(cursor):
    "6428 - insert vectors with flexible dimensions and conversion"
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
def test_6429(cursor):
    "6427 - insert and fetch large VECTOR data using strings"
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


def test_6430(cursor, test_env):
    "6430 - test binding a vector with inf values (negative)"
    value = array.array(
        "d", [float("inf") if i % 2 else float("-inf") for i in range(16)]
    )
    with test_env.assert_raises_full_code("ORA-51805"):
        cursor.execute("select :1 from dual", [value])


def test_6431(cursor):
    "6431 - test setting an invalid type to a vector"
    var = cursor.var(oracledb.DB_TYPE_VECTOR)
    pytest.raises(TypeError, var.setvalue, 0, [[i] for i in range(16)])


def test_6432(cursor):
    "6432 - fetch JSON value with an embedded vector"
    cursor.execute(
        """
        select json_object(
            'id' : 6432,
            'vector' : to_vector('[1, 2, 3]')
            returning json
        ) from dual
        """
    )
    (result,) = cursor.fetchone()
    expected_val = dict(id=6432, vector=array.array("f", [1, 2, 3]))
    assert result == expected_val


def test_6433(conn, cursor):
    "6433 - bind JSON value with an embedded vector"
    value = dict(id=6433, vector=array.array("d", [6433, 6433.25, 6433.5]))
    cursor.execute("delete from TestJson")
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.execute("insert into TestJson values (:1, :2)", [6433, value])
    conn.commit()
    cursor.execute("select JsonCol from TestJson")
    (fetched_val,) = cursor.fetchone()
    assert fetched_val == value


def test_6434(cursor):
    "6434 - executemany() without setinputsizes()"
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


def test_6435(cursor):
    "6435 - executemany() with setinputsizes()"
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


def test_6436(cursor, test_env):
    "6436 - vector with zero dimensions"
    with test_env.assert_raises_full_code("DPY-4031"):
        cursor.setinputsizes(oracledb.DB_TYPE_VECTOR)
        cursor.execute("select :1", [[]])
    with test_env.assert_raises_full_code("DPY-4031"):
        cursor.execute("select :1", [array.array("d", [])])


def test_6437(cursor):
    "6437 - insert a list vector into a flexible format column"
    value = [1.5, 9.9]
    _test_insert_and_fetch(cursor, value, "VectorFlexTypeCol", "d")


def test_6438(cursor):
    "6438 - insert a list vector into a flexible size column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "VectorFlexAllCol", "d")


def test_6439(cursor):
    "6439 - insert a list vector into a flexible float32 column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "VectorFlex32Col", "f")


def test_6440(cursor):
    "6440 - insert a list vector into a flexible float64 column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "VectorFlex64Col", "d")


def test_6441(cursor):
    "6441 - insert a list vector into a float32 column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "Vector32Col", "f")


def test_6442(cursor):
    "6442 - insert a list vector into a float64 column"
    value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "Vector64Col", "d")


def test_6443(cursor):
    "6443 - insert a list vector into a flexible int8 column"
    value = [1, 9, 3, 8, 4, 7, 5, 6, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "VectorFlex8Col", "b")


def test_6444(cursor):
    "6444 - insert a list vector into an int8 column"
    value = [1, 9, 3, 8, 4, 7, 5, 6, 0, 2, 6, 4, 5, 6, 7, 8]
    _test_insert_and_fetch(cursor, value, "Vector8Col", "b")


def test_6445(cursor):
    "6445 - test setting a PL-SQL type to a float32 vector"
    vec1 = array.array("f", [1, 1.5, 2, 2.5])
    vec2 = array.array("f", [4, 4.5, 5, 5.5])
    _test_plsql_insert_and_fetch(cursor, vec1, vec2, 6)

    vec3 = array.array("f", [3.5] * 65535)
    vec4 = array.array("f", [2.5] * 65535)
    _test_plsql_insert_and_fetch(cursor, vec3, vec4, 256)


def test_6446(cursor):
    "6446 - test setting a PL-SQL type to a float64 vector"
    vec1 = array.array("d", [1, 1.5, 2, 2.5])
    vec2 = array.array("d", [4, 4.5, 5, 5.5])
    _test_plsql_insert_and_fetch(cursor, vec1, vec2, 6)

    vec3 = array.array("d", [3.5] * 65535)
    vec4 = array.array("d", [2.5] * 65535)
    _test_plsql_insert_and_fetch(cursor, vec3, vec4, 256)


def test_6447(cursor):
    "6447 - test setting a PL-SQL type to a int8 vector"
    vec1 = array.array("b", [1, 2, 3, 4])
    vec2 = array.array("b", [5, 6, 7, 8])
    _test_plsql_insert_and_fetch(cursor, vec1, vec2, 8)

    vec3 = array.array("b", [3] * 65535)
    vec4 = array.array("b", [2] * 65535)
    _test_plsql_insert_and_fetch(cursor, vec3, vec4, 256)
