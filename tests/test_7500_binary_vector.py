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
7500 - Module for testing the VECTOR database type with storage format BINARY
available in Oracle Database 23.5 and higher.
"""

import array

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(skip_unless_binary_vectors_supported):
    pass


def test_7500(conn, cursor):
    "7500 - test binding and fetching a BINARY format vector."
    value = array.array("B", [4, 8, 12, 4, 98, 127, 25, 78])
    cursor.execute("delete from TestBinaryVectors")
    cursor.execute(
        """
        insert into TestBinaryVectors (IntCol, VectorBinaryCol)
        values(1, :value)
        """,
        value=value,
    )
    conn.commit()
    cursor.execute("select VectorBinaryCol from TestBinaryVectors")
    (fetched_value,) = cursor.fetchone()
    assert isinstance(fetched_value, array.array)
    assert fetched_value.typecode == "B"
    assert fetched_value == value


def test_7501(cursor):
    "7501 - verify fetch info contents"
    attr_names = [
        "name",
        "type_code",
        "vector_dimensions",
        "vector_format",
    ]
    expected_values = [
        ["INTCOL", oracledb.DB_TYPE_NUMBER, None, None],
        [
            "VECTORBINARYCOL",
            oracledb.DB_TYPE_VECTOR,
            64,
            oracledb.VECTOR_FORMAT_BINARY,
        ],
    ]
    cursor.execute("select * from TestBinaryVectors")
    values = [[getattr(i, n) for n in attr_names] for i in cursor.description]
    assert values == expected_values
    assert cursor.description[1].vector_format is oracledb.VectorFormat.BINARY


def test_7502(conn, cursor):
    "7502 - test comparing BINARY vectors"
    value = array.array("B", [20, 9, 15, 34, 108, 125, 35, 88])
    cursor.execute("delete from TestBinaryVectors")
    cursor.execute(
        """
        insert into TestBinaryVectors (IntCol, VectorBinaryCol)
        values(1, :value)
        """,
        value=value,
    )
    conn.commit()
    cursor.execute(
        """
        select vector_distance(VectorBinaryCol, :value)
        from TestBinaryVectors
        """,
        value=value,
    )
    (result,) = cursor.fetchone()
    assert result == pytest.approx(0)
