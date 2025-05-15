# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
7700 - Module for testing the VECTOR database type with storage type SPARSE
available in Oracle Database 23.7 and higher.
"""

import array
import json
import unittest
import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_client_version() >= (23, 7), "unsupported client"
)
@unittest.skipUnless(
    test_env.get_server_version() >= (23, 7), "unsupported server"
)
class TestCase(test_env.BaseTestCase):
    def __test_insert_and_fetch(self, vector, column_name, expected_typecode):
        """
        Test inserting sparse and fetching from a dense vector column.
        """
        self.cursor.execute("delete from TestVectors")
        self.cursor.execute(
            f"""
            insert into TestVectors (IntCol, {column_name})
            values(1, :vector)
            """,
            vector=vector,
        )
        self.conn.commit()
        self.cursor.execute(f"select {column_name} from TestVectors")
        (fetched_value,) = self.cursor.fetchone()
        dense_values = [0 for _ in range(vector.num_dimensions)]
        for i, index in enumerate(vector.indices):
            if expected_typecode == "b":
                dense_values[index] = int(vector.values[i])
            else:
                dense_values[index] = vector.values[i]
        expected_value = array.array(expected_typecode, dense_values)
        self.assertEqual(fetched_value, expected_value)
        self.assertEqual(fetched_value.typecode, expected_typecode)

    def __test_insert_and_fetch_sparse(
        self, vector, column_name, expected_typecode
    ):
        """
        Test inserting and fetching from a sparse vector column.
        """
        self.cursor.execute("delete from TestSparseVectors")
        self.cursor.execute(
            f"""
            insert into TestSparseVectors (IntCol, {column_name})
            values(1, :vector)
            """,
            vector=vector,
        )
        self.conn.commit()
        self.cursor.execute(f"select {column_name} from TestSparseVectors")
        (fetched_value,) = self.cursor.fetchone()
        expected_value = vector.values
        if fetched_value.values.typecode == "b":
            expected_value = array.array("b", [int(i) for i in vector.values])
        expected_indices = vector.indices
        expected_num_dimensions = vector.num_dimensions
        self.assertEqual(fetched_value.values, expected_value)
        self.assertEqual(fetched_value.indices, expected_indices)
        self.assertEqual(fetched_value.num_dimensions, expected_num_dimensions)

    def __fetch_with_vector(
        self,
        vector,
        column_name,
        dimensions,
        vector_format,
        expected_typecode,
    ):
        """
        Test fetching a vector with vector() function.
        """
        self.cursor.execute("delete from TestSparseVectors")
        self.cursor.execute(
            f"""
            insert into TestSparseVectors (IntCol, {column_name})
            values(1, :vector)
            """,
            vector=vector,
        )
        self.cursor.execute(
            f"""
            select
            vector({column_name}, {dimensions}, {vector_format}, DENSE)
            from TestSparseVectors
            """
        )
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsInstance(fetched_value, array.array)
        self.assertEqual(fetched_value.typecode, expected_typecode)

        self.cursor.execute(
            f"""
            select
            vector({column_name}, {dimensions}, {vector_format}, SPARSE)
            from TestSparseVectors
            """
        )
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsInstance(fetched_value, oracledb.SparseVector)
        self.assertEqual(fetched_value.values.typecode, expected_typecode)

    def test_7700(self):
        "7700 - test binding in a sparse vector with oracledb.SparseVector"
        vector = oracledb.SparseVector(3, [1], [9])
        self.cursor.execute("select :1 from dual", [vector])
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsInstance(fetched_value, oracledb.SparseVector)
        self.assertEqual(fetched_value.num_dimensions, vector.num_dimensions)
        self.assertEqual(fetched_value.indices, vector.indices)
        self.assertEqual(fetched_value.values, vector.values)

    def test_7701(self):
        "7701 - test binding in a sparse vector of type float32"
        vector = oracledb.SparseVector(3, [1], array.array("f", [0.5]))
        self.cursor.execute("select :1 from dual", [vector])
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(fetched_value.values, vector.values)
        self.assertEqual(fetched_value.indices, vector.indices)
        self.assertEqual(fetched_value.num_dimensions, vector.num_dimensions)
        self.assertEqual(fetched_value.values.typecode, "f")

    def test_7702(self):
        "7702 - test binding in a sparse vector of type float64"
        vector = oracledb.SparseVector(3, [1], array.array("d", [0.25]))
        self.cursor.execute("select :1 from dual", [vector])
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(fetched_value.values, vector.values)
        self.assertEqual(fetched_value.indices, vector.indices)
        self.assertEqual(fetched_value.num_dimensions, vector.num_dimensions)
        self.assertEqual(fetched_value.values.typecode, "d")
        self.assertIsInstance(fetched_value, oracledb.SparseVector)

    def test_7703(self):
        "7703 - test binding in a sparse vector of type int8"
        vector = oracledb.SparseVector(3, [1], array.array("b", [3]))
        self.cursor.execute("select :1 from dual", [vector])
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(fetched_value.values, vector.values)
        self.assertEqual(fetched_value.indices, vector.indices)
        self.assertEqual(fetched_value.num_dimensions, vector.num_dimensions)
        self.assertEqual(fetched_value.values.typecode, "b")
        self.assertIsInstance(fetched_value, oracledb.SparseVector)

    def test_7704(self):
        "7704 - insert a float32 sparse vector into a float32 column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [1.5, 0.25, 0.5])
        )
        self.__test_insert_and_fetch(value, "Vector32Col", "f")
        self.__test_insert_and_fetch_sparse(value, "SparseVector32Col", "f")

    def test_7705(self):
        "7705 - insert a float32 vector into a float64 column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("d", [1.5, 0.25, 0.5])
        )
        self.__test_insert_and_fetch(value, "Vector64Col", "d")
        self.__test_insert_and_fetch_sparse(value, "SparseVector64Col", "d")

    def test_7706(self):
        "7706 - insert a float32 vector into a flexible format column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [1.5, 0.25, 0.5])
        )
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "f")
        self.__test_insert_and_fetch_sparse(
            value, "SparseVectorFlexAllCol", "f"
        )

    def test_7707(self):
        "7707 - insert a float64 vector into a float64 column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("d", [1.5, 0.25, 0.5])
        )
        self.__test_insert_and_fetch(value, "Vector64Col", "d")
        self.__test_insert_and_fetch_sparse(value, "SparseVector64Col", "d")

    def test_7708(self):
        "7708 - insert float64 vector into a float32 column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [1.5, 0.25, 0.5])
        )
        self.__test_insert_and_fetch(value, "Vector32Col", "f")
        self.__test_insert_and_fetch_sparse(value, "SparseVector32Col", "f")

    def test_7709(self):
        "7709 - insert float64 vector into a flexible type column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("d", [1.5, 0.25, 0.5])
        )
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "d")
        self.__test_insert_and_fetch_sparse(
            value, "SparseVectorFlexAllCol", "d"
        )

    def test_7710(self):
        "7710 - insert a vector with an invalid size"
        self.cursor.execute("delete from TestVectors")
        self.cursor.execute("delete from TestSparseVectors")
        statements = [
            """
            insert into TestVectors (IntCol, Vector64Col)
            values(1, :1)
            """,
            """
            insert into TestSparseVectors (IntCol, SparseVector64Col)
            values(2, :1)
            """,
        ]
        for statement in statements:
            for num_elems in [4, 20]:
                vector = oracledb.SparseVector(
                    num_elems, [2, 3], array.array("f", [6.54, 9.6])
                )
                with self.assertRaisesFullCode("ORA-51803"):
                    self.cursor.execute(statement, [vector])

    def test_7711(self):
        "7711 - verify fetch info for vectors"
        attr_names = [
            "name",
            "type_code",
            "vector_dimensions",
            "vector_format",
            "vector_is_sparse",
        ]
        expected_values = [
            ["INTCOL", oracledb.DB_TYPE_NUMBER, None, None, None],
            [
                "SPARSEVECTORFLEXALLCOL",
                oracledb.DB_TYPE_VECTOR,
                None,
                None,
                True,
            ],
            [
                "SPARSEVECTORFLEXTYPECOL",
                oracledb.DB_TYPE_VECTOR,
                2,
                None,
                True,
            ],
            [
                "SPARSEVECTORFLEX8COL",
                oracledb.DB_TYPE_VECTOR,
                None,
                oracledb.VECTOR_FORMAT_INT8,
                True,
            ],
            [
                "SPARSEVECTORFLEX32COL",
                oracledb.DB_TYPE_VECTOR,
                None,
                oracledb.VECTOR_FORMAT_FLOAT32,
                True,
            ],
            [
                "SPARSEVECTORFLEX64COL",
                oracledb.DB_TYPE_VECTOR,
                None,
                oracledb.VECTOR_FORMAT_FLOAT64,
                True,
            ],
            [
                "SPARSEVECTOR8COL",
                oracledb.DB_TYPE_VECTOR,
                16,
                oracledb.VECTOR_FORMAT_INT8,
                True,
            ],
            [
                "SPARSEVECTOR32COL",
                oracledb.DB_TYPE_VECTOR,
                16,
                oracledb.VECTOR_FORMAT_FLOAT32,
                True,
            ],
            [
                "SPARSEVECTOR64COL",
                oracledb.DB_TYPE_VECTOR,
                16,
                oracledb.VECTOR_FORMAT_FLOAT64,
                True,
            ],
        ]
        self.cursor.execute("select * from TestSparseVectors")
        values = [
            [getattr(i, n) for n in attr_names]
            for i in self.cursor.description
        ]
        self.assertEqual(values, expected_values)
        self.assertIs(
            self.cursor.description[6].vector_format,
            oracledb.VectorFormat.INT8,
        )

    def test_7712(self):
        "7712 - insert an int8 vector into an int8 column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [1, 0, 5])
        )
        self.__test_insert_and_fetch(value, "Vector8Col", "b")
        self.__test_insert_and_fetch_sparse(value, "SparseVector8Col", "b")

    def test_7713(self):
        "7713 - insert an int8 vector into a float32 column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [1, 0, 5])
        )
        self.__test_insert_and_fetch(value, "Vector32Col", "f")
        self.__test_insert_and_fetch_sparse(value, "SparseVector32Col", "f")

    def test_7714(self):
        "7714 - insert an int8 vector into a float64 column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("b", [1, 0, 5])
        )
        self.__test_insert_and_fetch(value, "Vector64Col", "d")
        self.__test_insert_and_fetch_sparse(value, "SparseVector64Col", "d")

    def test_7715(self):
        "7715 - insert an int8 vector into a flexible column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("b", [1, 0, 5])
        )
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "b")
        self.__test_insert_and_fetch_sparse(
            value, "SparseVectorFlexAllCol", "b"
        )

    def test_7716(self):
        "7716 - insert a float32 vector into an int8 column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [1, 0, 5])
        )
        self.__test_insert_and_fetch(value, "Vector8Col", "b")
        self.__test_insert_and_fetch_sparse(value, "SparseVector8Col", "b")

    def test_7717(self):
        "7717 - insert a float64 vector into an int8 column"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("d", [1, 0, 5])
        )
        self.__test_insert_and_fetch(value, "Vector8Col", "b")
        self.__test_insert_and_fetch_sparse(value, "SparseVector8Col", "b")

    def test_7718(self):
        "7718 - test dml returning vector type"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [1, 0, 5])
        )
        out_var = self.cursor.var(oracledb.DB_TYPE_VECTOR)
        self.cursor.execute("delete from TestSparseVectors")
        self.cursor.execute(
            """
            insert into TestSparseVectors (IntCol, SparseVectorFlex32Col)
            values (1, :value)
            returning SparseVectorFlex32Col into :out_value
            """,
            [value, out_var],
        )
        self.conn.commit()
        vector = out_var.getvalue()[0]
        self.assertEqual(vector.values, value.values)
        self.assertEqual(vector.indices, value.indices)
        self.assertEqual(vector.num_dimensions, value.num_dimensions)

    def test_7719(self):
        "7719 - test handling of NULL vector value"
        self.cursor.execute("delete from TestSparseVectors")
        self.cursor.execute(
            "insert into TestSparseVectors (IntCol) values (1)"
        )
        self.conn.commit()
        self.cursor.execute(
            "select SparseVectorFlexTypeCol from TestSparseVectors"
        )
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsNone(fetched_value)

    def test_7720(self):
        "7720 - insert a float32 vector into an int8 column (negative)"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [-130, 400, 5])
        )
        with self.assertRaisesFullCode("ORA-51806"):
            self.__test_insert_and_fetch(value, "Vector8Col", "b")
        with self.assertRaisesFullCode("ORA-51806"):
            self.__test_insert_and_fetch_sparse(value, "SparseVector8Col", "b")

    def test_7721(self):
        "7721 - insert a float32 vector with 65,533 dimensions"
        value = oracledb.SparseVector(
            65533, [1, 3, 5], array.array("f", [1, 0, 5])
        )
        self.__test_insert_and_fetch(value, "VectorFlexAllCol", "f")
        self.__test_insert_and_fetch_sparse(
            value, "SparseVectorFlexAllCol", "f"
        )

    def test_7722(self):
        "7722 - insert vectors with different dimensions"
        for dim in [30, 70, 255, 256, 65534, 65535]:
            for typ in ["f", "d", "b"]:
                with self.subTest(dim=dim, typ=typ):
                    element_value = 3 if typ == "b" else 1.5
                    value = oracledb.SparseVector(
                        dim, [1, 3, 5], array.array(typ, [element_value] * 3)
                    )
                    self.__test_insert_and_fetch(
                        value, "VectorFlexAllCol", typ
                    )
                    self.__test_insert_and_fetch_sparse(
                        value, "SparseVectorFlexAllCol", typ
                    )

    def test_7723(self):
        "7723 - insert and fetch VECTOR data using strings"
        values = [16, [1, 3, 5], [1, 0, 5]]
        vector = oracledb.SparseVector(*values)
        self.cursor.execute("delete from TestSparseVectors")
        self.cursor.execute(
            """
            insert into TestSparseVectors (IntCol, SparseVectorFlexAllCol)
            values(1, :value)
            """,
            value=str(vector),
        )

        def type_handler(cursor, metadata):
            if metadata.name == "SPARSEVECTORFLEXALLCOL":
                return cursor.var(
                    oracledb.DB_TYPE_LONG, arraysize=cursor.arraysize
                )

        self.cursor.outputtypehandler = type_handler

        self.cursor.execute(
            "select SparseVectorFlexAllCol from TestSparseVectors"
        )
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(json.loads(fetched_value), values)

    def test_7724(self):
        "7724 - insert vectors with flexible dimensions and conversion"
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
                        element_value = 4 if source_type == "b" else 2.25
                        value = oracledb.SparseVector(
                            dim,
                            [1, 3, 7, 9],
                            array.array(source_type, [element_value] * 4),
                        )
                        self.__test_insert_and_fetch(
                            value, target_col, target_type
                        )
                        self.__test_insert_and_fetch_sparse(
                            value, f"Sparse{target_col}", target_type
                        )

    def test_7725(self):
        "7725 - test binding a vector with inf values (negative)"
        value = oracledb.SparseVector(
            16,
            [1, 3, 5],
            array.array("d", [float("inf"), float("-inf"), float("-inf")]),
        )
        with self.assertRaisesFullCode("ORA-51805", "ORA-51831"):
            self.cursor.execute("select :1 from dual", [value])

    def test_7726(self):
        "7726 - test setting a sparse vector to a vector variable"
        value = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [1, 0, 5])
        )
        var = self.cursor.var(oracledb.DB_TYPE_VECTOR)
        var.setvalue(0, value)
        vector = var.getvalue()
        self.assertEqual(vector.values, value.values)
        self.assertEqual(vector.indices, value.indices)
        self.assertEqual(vector.num_dimensions, value.num_dimensions)

    def test_7727(self):
        "7727 - fetch JSON value with an embedded vector"
        self.cursor.execute("delete from TestSparseVectors")
        vector = oracledb.SparseVector(
            16, [1, 3, 5], array.array("d", [1.5, 0.25, 0.5])
        )
        self.cursor.execute(
            """
            insert into TestSparseVectors (IntCol, SparseVector64Col)
            values (1, :1)
            """,
            [vector],
        )
        self.cursor.execute(
            """
            select json_object(
                'id': 7732,
                'vector' : vector(SparseVector64Col, 16, float64, sparse)
                returning json
            ) from TestSparseVectors
            """
        )
        (result,) = self.cursor.fetchone()
        fetched_vector = result["vector"]
        self.assertIsInstance(fetched_vector, oracledb.SparseVector)
        self.assertEqual(fetched_vector.indices, vector.indices)
        self.assertEqual(fetched_vector.values, vector.values)
        self.assertEqual(fetched_vector.num_dimensions, vector.num_dimensions)

    def test_7728(self):
        "7728 - executemany() without setinputsizes()"
        self.cursor.execute("delete from TestSparseVectors")
        vector = oracledb.SparseVector(
            16, [1, 3, 5], array.array("f", [1, 0, 5])
        )
        values = [vector, [0, 0, 0, 2, 0, 0, 0, 0, 0, 1, 0, 4, 0, 0, 0, 0]]
        self.cursor.executemany(
            """
            insert into TestSparseVectors (IntCol, SparseVector32Col)
            values (:1, :2)
            """,
            list(enumerate(values)),
        )
        self.cursor.execute(
            "select SparseVector32Col from TestSparseVectors order by IntCol"
        )
        (fetched_vector1,), (fetched_vector2,) = self.cursor.fetchall()
        self.assertEqual(fetched_vector1.values, vector.values)
        self.assertEqual(fetched_vector1.indices, vector.indices)
        self.assertEqual(fetched_vector1.num_dimensions, vector.num_dimensions)
        self.assertEqual(
            fetched_vector2.values, array.array("f", [2.0, 1.0, 4.0])
        )
        self.assertEqual(fetched_vector2.indices, array.array("I", [3, 9, 11]))
        self.assertEqual(fetched_vector2.num_dimensions, 16)

    def test_7729(self):
        "7729 - executemany() with setinputsizes()"
        self.cursor.execute("delete from TestSparseVectors")
        vector = oracledb.SparseVector(
            16, [1, 3, 5], array.array("d", [1, 0, 5])
        )
        values = [[144, 0, 1000], vector]
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR)
        self.cursor.executemany(
            """
            insert into TestSparseVectors (IntCol, SparseVectorFlex64Col)
            values (:1, :2)
            """,
            list(enumerate(values)),
        )
        self.cursor.execute(
            """
            select SparseVectorFlex64Col
            from TestSparseVectors order by IntCol
            """
        )
        (fetched_vector1,), (fetched_vector2,) = self.cursor.fetchall()
        self.assertEqual(
            fetched_vector1.values, array.array("d", [144.0, 1000.0])
        )
        self.assertEqual(fetched_vector1.indices, array.array("I", [0, 2]))
        self.assertEqual(fetched_vector1.num_dimensions, 3)
        self.assertEqual(fetched_vector2.values, vector.values)
        self.assertEqual(fetched_vector2.indices, vector.indices)
        self.assertEqual(fetched_vector2.num_dimensions, vector.num_dimensions)

    def test_7730(self):
        "7730 - vector with zero dimensions"
        self.cursor.setinputsizes(oracledb.DB_TYPE_VECTOR)
        vector = oracledb.SparseVector(4, [], [])
        with self.assertRaisesFullCode("ORA-51803", "ORA-21560"):
            self.cursor.execute("select :1", [vector])

    def test_7731(self):
        "7731 - test inserting a vector as a string and fetching it"
        self.cursor.execute("delete from TestSparseVectors")
        self.cursor.execute(
            """
            insert into TestSparseVectors (IntCol, SparseVectorFlexAllCol)
            values (1, '[4, [1, 3], [1.0, 2.0]]')
            """
        )
        self.cursor.execute(
            "select SparseVectorFlexAllCol from TestSparseVectors"
        )
        vector = self.cursor.fetchone()[0]
        self.assertEqual(vector.values, array.array("f", [1, 2]))
        self.assertEqual(vector.num_dimensions, 4)
        self.assertEqual(vector.indices, array.array("I", [1, 3]))

    def test_7732(self):
        "7732 - SparseVector() with invalid values"
        # pass strings instead of number or list/array.array
        with self.assertRaises(TypeError):
            oracledb.SparseVector("10", [1, 2], [1.5, 3.5])
        with self.assertRaises(TypeError):
            oracledb.SparseVector(10, "[1, 2]", [1.5, 3.5])
        with self.assertRaises(TypeError):
            oracledb.SparseVector(10, [1, 2], "[1.5, 3.5]")

        # insert matrix
        with self.assertRaises(TypeError):
            oracledb.SparseVector(10, [[1, 2]], [1.5, 3.5])
        with self.assertRaises(TypeError):
            oracledb.SparseVector(10, [1, 2], [[1.5, 3.5]])
        # use num_dimensions as a list
        with self.assertRaises(TypeError):
            oracledb.SparseVector([10], [1, 2], [1.5, 3.5])
        # use num_dimensions as a float
        value = oracledb.SparseVector(10.4, [1, 2], [1.5, 3.5])
        self.assertEqual(value.num_dimensions, 10)

        # negative index
        with self.assertRaises(OverflowError):
            oracledb.SparseVector(10, [-1], [1.5])
        # negative num_dimensions
        with self.assertRaises(OverflowError):
            oracledb.SparseVector(-10, [1], [3.5])
        # use float index
        with self.assertRaises(TypeError):
            oracledb.SparseVector(10, [2.4], [3.5])

    def test_7733(self):
        "7733 - SparseVector() with indices and values of different length"
        with self.assertRaises(TypeError):
            oracledb.SparseVector(10, [1], [1.5, 3.5])
        with self.assertRaises(TypeError):
            oracledb.SparseVector(10, [1, 2, 3, 4], [6.75])

    def test_7734(self):
        "7734 - declare and insert an empty SparseVector"
        value = oracledb.SparseVector(0, [], [])
        self.assertEqual(value.values, array.array("d"))
        self.assertEqual(value.indices, array.array("I"))
        self.assertEqual(value.num_dimensions, 0)
        with self.assertRaisesFullCode("ORA-51803", "ORA-21560", "ORA-51862"):
            self.__test_insert_and_fetch(value, "VectorFlexAllCol", "d")
        with self.assertRaisesFullCode("ORA-51803", "ORA-21560", "ORA-51862"):
            self.__test_insert_and_fetch_sparse(
                value, "SparseVectorFlexAllCol", "d"
            )

    def test_7735(self):
        "7735 - select with vector()"
        dense_vector = array.array(
            "f", [1, 2, 3, 4, 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0, 0]
        )
        sparse_vector = oracledb.SparseVector(16, [1], array.array("f", [9]))
        column_names = [
            "SparseVector8Col",
            "SparseVector32Col",
            "SparseVector64Col",
            "SparseVectorFlex8Col",
            "SparseVectorFlex32Col",
            "SparseVectorFlex64Col",
            "SparseVectorFlexAllCol",
        ]
        for vector in [dense_vector, sparse_vector]:
            for column_name in column_names:
                with self.subTest(vector=vector, column_name=column_name):
                    self.__fetch_with_vector(
                        vector, column_name, 16, "INT8", "b"
                    )
                    self.__fetch_with_vector(
                        vector, column_name, 16, "FLOAT32", "f"
                    )
                    self.__fetch_with_vector(
                        vector, column_name, 16, "FLOAT64", "d"
                    )

        # fixed dimension columns
        dense_vector = array.array("f", [1, 2])
        sparse_vector = oracledb.SparseVector(2, [1], array.array("f", [1]))
        for vector in [dense_vector, sparse_vector]:
            for column_name in column_names[3:]:
                with self.subTest(vector=vector, column_name=column_name):
                    self.__fetch_with_vector(
                        vector, column_name, 2, "INT8", "b"
                    )
                    self.__fetch_with_vector(
                        vector, column_name, 2, "FLOAT32", "f"
                    )
                    self.__fetch_with_vector(
                        vector, column_name, 2, "FLOAT64", "d"
                    )

    def test_7736(self):
        "7736 - test from_vector() with returning and vector storage format"
        self.cursor.execute("delete from TestSparseVectors")
        values = [16, [1, 2, 15], [2, 45.5, 73.25]]
        vector = oracledb.SparseVector(*values)
        dense_vector = [0, 2, 45.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 73.25]
        column_name = "SparseVector64Col"
        self.cursor.execute(
            f"""
            insert into TestSparseVectors (IntCol, {column_name})
            values(1, :vector)
            """,
            vector=vector,
        )
        self.cursor.execute(
            f"""
            select from_vector({column_name} returning clob format sparse)
            from TestSparseVectors
            """
        )
        (lob,) = self.cursor.fetchone()
        self.assertEqual(json.loads(lob.read()), values)
        self.cursor.execute(
            f"""
            select from_vector({column_name} returning clob format dense)
            from TestSparseVectors
            """
        )
        (lob,) = self.cursor.fetchone()
        self.assertEqual(json.loads(lob.read()), dense_vector)
        self.cursor.execute(
            f"""
            select from_vector({column_name} returning clob)
            from TestSparseVectors
            """
        )
        (lob,) = self.cursor.fetchone()
        self.assertEqual(json.loads(lob.read()), values)
        self.cursor.execute(
            f"""
            select from_vector({column_name} returning varchar2 format sparse)
            from TestSparseVectors
            """
        )
        self.assertEqual(json.loads(self.cursor.fetchone()[0]), values)
        self.cursor.execute(
            f"""
            select from_vector({column_name} returning varchar2 format dense)
            from TestSparseVectors
            """
        )
        self.assertEqual(json.loads(self.cursor.fetchone()[0]), dense_vector)
        self.cursor.execute(
            f"""
            select from_vector({column_name} returning varchar2)
            from TestSparseVectors
            """
        )
        self.assertEqual(json.loads(self.cursor.fetchone()[0]), values)


if __name__ == "__main__":
    test_env.run_test_cases()
