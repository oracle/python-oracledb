# -----------------------------------------------------------------------------
# Copyright (c) 2026, Oracle and/or its affiliates.
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
Module for testing attaching external OCIStmt handle (Thick mode only)
"""

import pyarrow
import pytest


@pytest.fixture(autouse=True)
def module_checks(skip_unless_thick_mode):
    pass


@pytest.fixture
def external_cursor(conn):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            select 1 from dual
            union all
            select 2 from dual
            union all
            select 3 from dual
            union all
            select 4 from dual
            union all
            select 5 from dual
            union all
            select 6 from dual
            union all
            select 7 from dual
            union all
            select 8 from dual
            union all
            select 9 from dual
            union all
            select 10 from dual
            """
        )
        yield cursor


def test_9800(external_cursor, conn):
    "9800 - test fetchone()"
    cursor = conn.cursor(handle=external_cursor.handle)
    data = cursor.fetchone()
    assert data[0] == 1


def test_9801(external_cursor, conn):
    "9801 - test fetchall()"
    cursor = conn.cursor(handle=external_cursor.handle)
    fetched_data = cursor.fetchall()
    assert fetched_data == [(i + 1,) for i in range(10)]


def test_9802(external_cursor, conn, test_env):
    "9802 - test fetch_df_all()"
    ora_df = conn.fetch_df_all(handle=external_cursor.handle)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == [(i + 1,) for i in range(10)]


def test_9803(external_cursor, conn, test_env):
    "9803 - test fetch_df_batches()"
    data = [(i + 1,) for i in range(10)]
    offset = 0
    batch_size = 3
    for batch in conn.fetch_df_batches(
        handle=external_cursor.handle, size=batch_size
    ):
        fetched_df = pyarrow.table(batch).to_pandas()
        fetched_data = test_env.get_data_from_df(fetched_df)
        assert fetched_data == data[offset : offset + batch_size]
        offset += batch_size


def test_9804(external_cursor, conn, test_env):
    "9804 - test fetch_df_all() with requested_schema"
    requested_schema = pyarrow.schema([("1", pyarrow.int8())])
    ora_df = conn.fetch_df_all(
        handle=external_cursor.handle, requested_schema=requested_schema
    )
    fetched_table = pyarrow.table(ora_df)
    fetched_df = fetched_table.to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_table.field(0).type == pyarrow.int8()
    assert fetched_data == [(i + 1,) for i in range(10)]


def test_9805(external_cursor, conn, test_env):
    "9805 - test fetch_df_batches() with requested_schema"
    data = [(i + 1,) for i in range(10)]
    requested_schema = pyarrow.schema([("1", pyarrow.int8())])
    offset = 0
    batch_size = 3
    for batch in conn.fetch_df_batches(
        handle=external_cursor.handle,
        requested_schema=requested_schema,
        size=batch_size,
    ):
        fetched_table = pyarrow.table(batch)
        fetched_df = fetched_table.to_pandas()
        fetched_data = test_env.get_data_from_df(fetched_df)
        assert fetched_table.field(0).type == pyarrow.int8()
        assert fetched_data == data[offset : offset + batch_size]
        offset += batch_size


def test_9806(conn, test_env):
    "9806 - test exception DPY-1004 is thrown when no statement is executed"
    cursor = conn.cursor()
    with test_env.assert_raises_full_code("DPY-1004"):
        cursor.handle
