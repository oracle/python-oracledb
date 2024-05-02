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
6500 - Module for testing the VECTOR database type with older clients
"""

import json
import unittest

import oracledb
import test_env


@unittest.skipIf(
    test_env.get_client_version() >= (23, 4),
    "client supports vectors directly",
)
@unittest.skipUnless(
    test_env.get_server_version() >= (23, 4), "unsupported server"
)
class TestCase(test_env.BaseTestCase):
    def test_6500(self):
        "6500 - verify fetch information for older clients"
        attr_names = ["name", "type_code", "is_json"]
        expected_values = [
            ["INTCOL", oracledb.DB_TYPE_NUMBER, False],
            ["VECTORFLEXALLCOL", oracledb.DB_TYPE_CLOB, True],
            ["VECTORFLEXTYPECOL", oracledb.DB_TYPE_CLOB, True],
            ["VECTORFLEX8COL", oracledb.DB_TYPE_CLOB, True],
            ["VECTORFLEX32COL", oracledb.DB_TYPE_CLOB, True],
            ["VECTORFLEX64COL", oracledb.DB_TYPE_CLOB, True],
            ["VECTOR32COL", oracledb.DB_TYPE_CLOB, True],
            ["VECTOR64COL", oracledb.DB_TYPE_CLOB, True],
            ["VECTOR8COL", oracledb.DB_TYPE_CLOB, True],
        ]
        self.cursor.execute("select * from TestVectors")
        values = [
            [getattr(i, n) for n in attr_names]
            for i in self.cursor.description
        ]
        self.assertEqual(values, expected_values)

    def test_6501(self):
        "6501 - verify default fetched value is a Python list"
        expected_data = (
            1,
            [6501, 25.25, 18.125, -3.5],
            [11, -12.5],
            [-5.25, -1.75, 0, 18.375],
            [-1, 1, -2, 2, -3, 3, -4, 4, -5, 5],
            [-10, 10, -20, 20, -30, 30, -40, 40, -50, 50],
            [-5, 5, -10, 10, -15, 15, -20, 20, -25, 25],
        )
        self.cursor.execute("delete from TestVectors")
        frag = ", ".join(f"'{d}'" for d in expected_data)
        sql = f"""
            insert into TestVectors
            (IntCol, VectorFlexAllCol, VectorFlexTypeCol,
             VectorFlex64Col, Vector32Col, Vector64Col, Vector8Col)
             values ({frag})"""
        self.cursor.execute(sql)
        self.conn.commit()
        self.cursor.execute(
            """
            select
                IntCol,
                VectorFlexAllCol,
                VectorFlexTypeCol,
                VectorFlex64Col,
                Vector32Col,
                Vector64Col,
                Vector8Col
            from TestVectors
            """
        )
        fetched_data = self.cursor.fetchone()
        self.assertEqual(fetched_data, expected_data)

    def test_6502(self):
        "6502 - verify fetched value as intermediate long value"
        expected_data = (
            1,
            [6501, 25.25, 18.125, -3.5],
            [11, -12.5],
            [-5.25, -1.75, 0, 18.375],
            [-1, 1, -2, 2, -3, 3, -4, 4, -5, 5],
            [-10, 10, -20, 20, -30, 30, -40, 40, -50, 50],
            [-5, 5, -10, 10, -15, 15, -20, 20, -25, 25],
        )
        self.cursor.execute("delete from TestVectors")
        frag = ", ".join(f"'{d}'" for d in expected_data)
        sql = f"""
            insert into TestVectors
            (IntCol, VectorFlexAllCol, VectorFlexTypeCol,
             VectorFlex64Col, Vector32Col, Vector64Col, Vector8Col)
             values ({frag})"""
        self.cursor.execute(sql)
        self.conn.commit()
        executions = [0]

        def type_handler(cursor, fetch_info):
            executions[0] += 1
            if fetch_info.type_code is oracledb.DB_TYPE_CLOB:
                return cursor.var(
                    oracledb.DB_TYPE_LONG,
                    arraysize=cursor.arraysize,
                    outconverter=lambda x: json.loads(x),
                )

        self.cursor.outputtypehandler = type_handler
        self.cursor.execute(
            """
            select
                IntCol,
                VectorFlexAllCol,
                VectorFlexTypeCol,
                VectorFlex64Col,
                Vector32Col,
                Vector64Col,
                Vector8Col
            from TestVectors
            """
        )
        fetched_data = self.cursor.fetchone()
        self.assertEqual(fetched_data, expected_data)
        self.assertEqual(executions[0], 7)

    def test_6503(self):
        "6503 - verify fetched value as intermediate string value"
        expected_data = (
            1,
            [6501, 25.25, 18.125, -3.5],
            [11, -12.5],
            [-5.25, -1.75, 0, 18.375],
            [-1, 1, -2, 2, -3, 3, -4, 4, -5, 5],
            [-10, 10, -20, 20, -30, 30, -40, 40, -50, 50],
            [-5, 5, -10, 10, -15, 15, -20, 20, -25, 25],
        )
        self.cursor.execute("delete from TestVectors")
        frag = ", ".join(f"'{d}'" for d in expected_data)
        sql = f"""
            insert into TestVectors
            (IntCol, VectorFlexAllCol, VectorFlexTypeCol,
             VectorFlex64Col, Vector32Col, Vector64Col, Vector8Col)
             values ({frag})"""
        self.cursor.execute(sql)
        self.conn.commit()
        executions = [0]

        def type_handler(cursor, fetch_info):
            executions[0] += 1
            if fetch_info.type_code is oracledb.DB_TYPE_CLOB:
                return cursor.var(
                    oracledb.DB_TYPE_VARCHAR,
                    arraysize=cursor.arraysize,
                    outconverter=lambda x: json.loads(x),
                )

        self.cursor.outputtypehandler = type_handler
        self.cursor.execute(
            """
            select
                IntCol,
                VectorFlexAllCol,
                VectorFlexTypeCol,
                VectorFlex64Col,
                Vector32Col,
                Vector64Col,
                Vector8Col
            from TestVectors
            """
        )
        fetched_data = self.cursor.fetchone()
        self.assertEqual(fetched_data, expected_data)
        self.assertEqual(executions[0], 7)

    @unittest.skip("awaiting database support")
    def test_6504(self):
        "6502 - verify fetching large vector as intermediate long value"
        num_dimensions = 35655
        expected_data = (
            1,
            [4] * num_dimensions,
            [12.5] * num_dimensions,
            [128.625] * num_dimensions,
        )
        self.cursor.execute("delete from TestVectors")
        sql = """
            insert into TestVectors
            (IntCol, VectorFlex8Col, VectorFlex32Col, VectorFlex64Col)
            values (:1, :2, :3, :4)"""
        bind_data = [
            expected_data[0],
            json.dumps(expected_data[1]),
            json.dumps(expected_data[2]),
            json.dumps(expected_data[3]),
        ]
        self.cursor.execute(sql, bind_data)
        self.conn.commit()
        executions = [0]

        def type_handler(cursor, fetch_info):
            executions[0] += 1
            if fetch_info.type_code is oracledb.DB_TYPE_CLOB:
                return cursor.var(
                    oracledb.DB_TYPE_LONG,
                    arraysize=cursor.arraysize,
                    outconverter=lambda x: json.loads(x),
                )

        self.cursor.outputtypehandler = type_handler
        self.cursor.execute(
            """"
            select
                IntCol,
                VectorFlex8Col,
                VectorFlex32Col,
                VectorFlex64Col
            from TestVectors"""
        )
        fetched_data = self.cursor.fetchone()
        self.assertEqual(fetched_data, expected_data)
        self.assertEqual(executions[0], 7)


if __name__ == "__main__":
    test_env.run_test_cases()
