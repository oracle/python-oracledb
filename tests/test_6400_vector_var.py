# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
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
import unittest
import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_client_version() >= (23, 4), "unsupported client"
)
@unittest.skipUnless(
    test_env.get_server_version() >= (23, 4), "unsupported server"
)
class TestCase(test_env.BaseTestCase):
    def __test_insert_and_fetch(self, value, column_name, expected_typecode):
        """
        Test inserting and fetching a vector.
        """
        self.cursor.execute("delete from TestVectors")
        if isinstance(value, list):
            self.cursor.setinputsizes(value=oracledb.DB_TYPE_VECTOR)
        self.cursor.execute(
            f"""
            insert into TestVectors (IntCol, {column_name})
            values(1, :value)
            """,
            value=value,
        )
        self.conn.commit()
        self.cursor.execute(f"select {column_name} from TestVectors")
        (fetched_value,) = self.cursor.fetchone()
        if expected_typecode == "b":
            expected_value = array.array("b", [int(i) for i in value])
        else:
            expected_value = array.array(expected_typecode, value)
        self.assertEqual(fetched_value, expected_value)
        self.assertEqual(fetched_value.typecode, expected_typecode)

    def __test_plsql_insert_and_fetch(self, vec1, vec2, expected_distance):
        in_out_vec = self.cursor.var(oracledb.DB_TYPE_VECTOR)
        in_out_vec.setvalue(0, vec2)

        distance = self.cursor.var(oracledb.DB_TYPE_BINARY_DOUBLE)
        output_vec = self.cursor.var(oracledb.DB_TYPE_VECTOR)

        plsql_block = """
            BEGIN
                select
                    vector_distance(:in_vec, :in_out_vec, euclidean)
                    into :distance;
                :output_vec := :in_out_vec;
                :in_out_vec := :in_vec;
            END;
            """

        self.cursor.execute(
            plsql_block,
            in_vec=vec1,
            in_out_vec=in_out_vec,
            distance=distance,
            output_vec=output_vec,
        )
        self.assertEqual(output_vec.getvalue(), vec2)
        self.assertEqual(in_out_vec.getvalue(), vec1)
        self.assertAlmostEqual(
            distance.getvalue(), expected_distance, places=2
        )

    def test_6400(self):
        "6400 - test binding in a vector from a Python list"
        value = [1, 2]
        self.cursor.setinputsizes(oracledb.DB_TYPE_VECTOR)
        self.cursor.execute("select :1 from dual", [value])
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsInstance(fetched_value, array.array)
        self.assertEqual(fetched_value.typecode, "d")
        self.assertEqual(fetched_value, array.array("d", value))

    def test_6401(self):
        "6401 - test binding in a vector from a Python array of type float64"
        value = array.array("d", [3, 4, 5])
        self.cursor.execute("select :1 from dual", [value])
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsInstance(fetched_value, array.array)
        self.assertEqual(fetched_value.typecode, "d")
        self.assertEqual(fetched_value, value)

    def test_6402(self):
        "6402 - test binding in a vector from a Python array of type float32"
        value = array.array("f", [6, 7, 8, 9])
        self.cursor.execute("select :1 from dual", [value])
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsInstance(fetched_value, array.array)
        self.assertEqual(fetched_value.typecode, "f")
        self.assertEqual(fetched_value, value)

    def test_6403(self):
        "6402 - test binding in a vector from a Python array of type int8"
        value = array.array("b", [-10, 11, -12, 13, -14])
        self.cursor.execute("select :1 from dual", [value])
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsInstance(fetched_value, array.array)
        self.assertEqual(fetched_value.typecode, "b")
        self.assertEqual(fetched_value, value)

    def test_6404(self):
        "6404 - unspported array type for vector"
        with self.assertRaisesFullCode("DPY-3013"):
            self.cursor.execute(
                "select :1 from dual", [array.array("L", [4, 5])]
            )

    def test_6405(self):
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
        self.__test_insert_and_fetch(value, "Vector32Col", "f")

    def test_6406(self):
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
        self.__test_insert_and_fetch(value, "Vector64Col", "d")

    def test_6407(self):
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
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "f")

    def test_6408(self):
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
        self.__test_insert_and_fetch(value, "Vector64Col", "d")

    def test_6409(self):
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
        self.__test_insert_and_fetch(value, "Vector32Col", "f")

    def test_6410(self):
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
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "d")

    def test_6411(self):
        "6411 - insert a vector with an invalid size"
        self.cursor.execute("truncate table TestVectors")
        for num_elems in [4, 20]:
            statement = """
                    insert into TestVectors (IntCol, Vector64Col)
                    values(2, :1)"""
            vector = array.array("d", [i * 0.625 for i in range(num_elems)])
            with self.assertRaisesFullCode("ORA-51803"):
                self.cursor.execute(statement, [vector])

    def test_6412(self):
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
        self.cursor.execute("select * from TestVectors")
        values = [
            [getattr(i, n) for n in attr_names]
            for i in self.cursor.description
        ]
        self.assertEqual(values, expected_values)
        self.assertIs(
            self.cursor.description[3].vector_format,
            oracledb.VectorFormat.INT8,
        )

    def test_6413(self):
        "6413 - insert an int8 vector into an int8 column"
        value = array.array(
            "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
        )
        self.__test_insert_and_fetch(value, "Vector8Col", "b")

    def test_6414(self):
        "6414 - insert an int8 vector into a float32 column"
        value = array.array(
            "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
        )
        self.__test_insert_and_fetch(value, "Vector32Col", "f")

    def test_6415(self):
        "6415 - insert an int8 vector into a float64 column"
        value = array.array(
            "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
        )
        self.__test_insert_and_fetch(value, "Vector64Col", "d")

    def test_6416(self):
        "6416 - insert an int8 vector into a flexible column"
        value = array.array(
            "b", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
        )
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "b")

    def test_6417(self):
        "6417 - insert a float32 vector into an int8 column"
        value = array.array(
            "f", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
        )
        self.__test_insert_and_fetch(value, "Vector8Col", "b")

    def test_6418(self):
        "6418 - insert a float64 vector into an int8 column"
        value = array.array(
            "d", [-5, 4, -7, 6, -9, 8, -127, 127, 0, -128, 1, 4, -3, 2, -8, 0]
        )
        self.__test_insert_and_fetch(value, "Vector8Col", "b")

    def test_6419(self):
        "6419 - test dml returning vector type"
        value = array.array("d", [6423.5, 6423.625])
        out_var = self.cursor.var(oracledb.DB_TYPE_VECTOR)
        self.cursor.execute("delete from TestVectors")
        self.cursor.execute(
            """
            insert into TestVectors (IntCol, VectorFlexTypeCol)
            values (1, :value)
            returning VectorFlexTypeCol into :out_value
            """,
            [value, out_var],
        )
        self.conn.commit()
        self.assertEqual(value, out_var.getvalue()[0])

    def test_6420(self):
        "6420 - test handling of NULL vector value"
        self.cursor.execute("delete from TestVectors")
        self.cursor.execute("insert into TestVectors (IntCol) values (1)")
        self.conn.commit()
        self.cursor.execute("select VectorFlexTypeCol from TestVectors")
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsNone(fetched_value)

    def test_6421(self):
        "6421 - insert a float32 vector into an int8 column (negative)"
        value = array.array(
            "f",
            [-130, -129, 0, 1, 2, 3, 127, 128, 129, 348, 12, 49, 78, 12, 9, 2],
        )
        with self.assertRaisesFullCode("ORA-51806"):
            self.__test_insert_and_fetch(value, "Vector8Col", "b")

    def test_6422(self):
        "6422 - insert a float64 vector with 65,533 dimensions"
        value = array.array("d", [2.5] * 65533)
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "d")

    def test_6423(self):
        "6423 - insert a float32 vector with 65,533 dimensions"
        value = array.array("f", [2.5] * 65533)
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "f")

    def test_6424(self):
        "6424 - insert an int8 vector with 65,533 dimensions"
        value = array.array("b", [2] * 65533)
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "b")

    def test_6425(self):
        "6425 - insert vectors with different dimensions"
        for dim in [30, 70, 255, 256, 65534, 65535]:
            for typ in ["f", "d", "b"]:
                with self.subTest(dim=dim, typ=typ):
                    element_value = 3 if typ == "b" else 1.5
                    value = array.array(typ, [element_value] * dim)
                    self.__test_insert_and_fetch(
                        value, "VectorFlexAllCol", typ
                    )

    @unittest.skip("awaiting database support")
    def test_6426(self):
        "6426 - insert and fetch VECTOR data using CLOB"
        value = [6426, -15.75, 283.125, -8.625]
        clob = self.conn.createlob(oracledb.DB_TYPE_CLOB)
        clob.write(json.dumps(value))
        self.cursor.execute("delete from TestVectors")
        self.cursor.execute(
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

        self.cursor.outputtypehandler = type_handler

        self.cursor.execute("select VectorFlexAllCol from TestVectors")
        (clob_data,) = self.cursor.fetchone()
        fetched_value = json.loads(clob_data.read())
        self.assertEqual(fetched_value, value)

    def test_6427(self):
        "6427 - insert and fetch VECTOR data using strings"
        value = [6427, -25.75, 383.125, -18.625]
        self.cursor.execute("delete from TestVectors")
        self.cursor.execute(
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

        self.cursor.outputtypehandler = type_handler

        self.cursor.execute("select VectorFlexAllCol from TestVectors")
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(json.loads(fetched_value), value)

    def test_6428(self):
        "6428 - insert vectors with flexible dimensions and conversion"
        for dim in [30, 255, 256, 257, 32768, 65535]:
            for source_type in ["f", "d", "b"]:
                for target_type in ["f", "d", "b"]:
                    with self.subTest(
                        dim=dim,
                        source_type=source_type,
                        target_type=target_type,
                    ):
                        if target_type == "f":
                            target_col = "VectorFlex32Col"
                        elif target_type == "d":
                            target_col = "VectorFlex64Col"
                        else:
                            target_col = "VectorFlex8Col"
                        element_value = 4 if source_type == "b" else 2.5
                        value = array.array(source_type, [element_value] * dim)
                        self.__test_insert_and_fetch(
                            value, target_col, target_type
                        )

    @unittest.skip("awaiting database support")
    def test_6429(self):
        "6427 - insert and fetch large VECTOR data using strings"
        value = [0.12345678925] * 35625
        self.cursor.execute("delete from TestVectors")
        self.cursor.execute(
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

        self.cursor.outputtypehandler = type_handler

        self.cursor.execute("select VectorFlex64Col from TestVectors")
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(json.loads(fetched_value), value)

    def test_6430(self):
        "6430 - test binding a vector with inf values (negative)"
        value = array.array(
            "d", [float("inf") if i % 2 else float("-inf") for i in range(16)]
        )
        with self.assertRaisesFullCode("ORA-51805"):
            self.cursor.execute("select :1 from dual", [value])

    def test_6431(self):
        "6431 - test setting an invalid type to a vector"
        var = self.cursor.var(oracledb.DB_TYPE_VECTOR)
        self.assertRaises(TypeError, var.setvalue, 0, [[i] for i in range(16)])

    def test_6432(self):
        "6432 - fetch JSON value with an embedded vector"
        self.cursor.execute(
            """
            select json_object(
                'id' : 6432,
                'vector' : to_vector('[1, 2, 3]')
                returning json
            ) from dual
            """
        )
        (result,) = self.cursor.fetchone()
        expected_val = dict(id=6432, vector=array.array("f", [1, 2, 3]))
        self.assertEqual(result, expected_val)

    def test_6433(self):
        "6433 - bind JSON value with an embedded vector"
        value = dict(id=6433, vector=array.array("d", [6433, 6433.25, 6433.5]))
        self.cursor.execute("delete from TestJson")
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        self.cursor.execute(
            "insert into TestJson values (:1, :2)", [6433, value]
        )
        self.conn.commit()
        self.cursor.execute("select JsonCol from TestJson")
        (fetched_val,) = self.cursor.fetchone()
        self.assertEqual(fetched_val, value)

    def test_6434(self):
        "6434 - executemany() without setinputsizes()"
        self.cursor.execute("delete from TestVectors")
        values = [array.array("f", [3.1416, 4]), [3.14159, 5]]
        self.cursor.executemany(
            """
            insert into TestVectors (IntCol, VectorFlexTypeCol)
            values (:1, :2)
            """,
            list(enumerate(values)),
        )
        self.cursor.execute(
            "select VectorFlexTypeCol from TestVectors order by IntCol"
        )
        expected_value = [
            (array.array("f", [3.1416, 4.0]),),
            (array.array("d", [3.14159, 5.0]),),
        ]
        self.assertEqual(self.cursor.fetchall(), expected_value)

    def test_6435(self):
        "6435 - executemany() with setinputsizes()"
        self.cursor.execute("delete from TestVectors")
        values = [[144, 1000], array.array("d", [66.0, 7.14])]
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR)
        self.cursor.executemany(
            """
            insert into TestVectors (IntCol, VectorFlex64Col)
            values (:1, :2)
            """,
            list(enumerate(values)),
        )
        self.cursor.execute(
            "select VectorFlex64Col from TestVectors order by IntCol"
        )
        expected_value = [
            (array.array("d", [144.0, 1000.0]),),
            (array.array("d", [66.0, 7.14]),),
        ]
        self.assertEqual(self.cursor.fetchall(), expected_value)

    def test_6436(self):
        "6436 - vector with zero dimensions"
        with self.assertRaisesFullCode("DPY-4031"):
            self.cursor.setinputsizes(oracledb.DB_TYPE_VECTOR)
            self.cursor.execute("select :1", [[]])
        with self.assertRaisesFullCode("DPY-4031"):
            self.cursor.execute("select :1", [array.array("d", [])])

    def test_6437(self):
        "6437 - insert a list vector into a flexible format column"
        value = [1.5, 9.9]
        self.__test_insert_and_fetch(value, "VectorFlexTypeCol", "d")

    def test_6438(self):
        "6438 - insert a list vector into a flexible size column"
        value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "d")

    def test_6439(self):
        "6439 - insert a list vector into a flexible float32 column"
        value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
        self.__test_insert_and_fetch(value, "VectorFlex32Col", "f")

    def test_6440(self):
        "6440 - insert a list vector into a flexible float64 column"
        value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
        self.__test_insert_and_fetch(value, "VectorFlex64Col", "d")

    def test_6441(self):
        "6441 - insert a list vector into a float32 column"
        value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
        self.__test_insert_and_fetch(value, "Vector32Col", "f")

    def test_6442(self):
        "6442 - insert a list vector into a float64 column"
        value = [1.5, 9.9, 3, 8, 4.25, 7, 5, 6.125, 0, 2, 6, 4, 5, 6, 7, 8]
        self.__test_insert_and_fetch(value, "Vector64Col", "d")

    def test_6443(self):
        "6443 - insert a list vector into a flexible int8 column"
        value = [1, 9, 3, 8, 4, 7, 5, 6, 0, 2, 6, 4, 5, 6, 7, 8]
        self.__test_insert_and_fetch(value, "VectorFlex8Col", "b")

    def test_6444(self):
        "6444 - insert a list vector into an int8 column"
        value = [1, 9, 3, 8, 4, 7, 5, 6, 0, 2, 6, 4, 5, 6, 7, 8]
        self.__test_insert_and_fetch(value, "Vector8Col", "b")

    def test_6445(self):
        "6445 - test setting a PL-SQL type to a float32 vector"
        vec1 = array.array("f", [1, 1.5, 2, 2.5])
        vec2 = array.array("f", [4, 4.5, 5, 5.5])
        self.__test_plsql_insert_and_fetch(vec1, vec2, 6)

        vec3 = array.array("f", [3.5] * 65535)
        vec4 = array.array("f", [2.5] * 65535)
        self.__test_plsql_insert_and_fetch(vec3, vec4, 256)

    def test_6446(self):
        "6446 - test setting a PL-SQL type to a float64 vector"
        vec1 = array.array("d", [1, 1.5, 2, 2.5])
        vec2 = array.array("d", [4, 4.5, 5, 5.5])
        self.__test_plsql_insert_and_fetch(vec1, vec2, 6)

        vec3 = array.array("d", [3.5] * 65535)
        vec4 = array.array("d", [2.5] * 65535)
        self.__test_plsql_insert_and_fetch(vec3, vec4, 256)

    def test_6447(self):
        "6447 - test setting a PL-SQL type to a int8 vector"
        vec1 = array.array("b", [1, 2, 3, 4])
        vec2 = array.array("b", [5, 6, 7, 8])
        self.__test_plsql_insert_and_fetch(vec1, vec2, 8)

        vec3 = array.array("b", [3] * 65535)
        vec4 = array.array("b", [2] * 65535)
        self.__test_plsql_insert_and_fetch(vec3, vec4, 256)


if __name__ == "__main__":
    test_env.run_test_cases()
