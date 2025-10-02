# -----------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
Module for testing dataframe with vector support with asyncio
"""

import array

import pyarrow
import pytest


@pytest.fixture(autouse=True)
def module_checks(
    anyio_backend, skip_unless_thin_mode, skip_unless_vectors_supported
):
    pass


async def test_9200(async_conn, test_env):
    "9200 - fetch float32 vector"

    # float32 is a special case while comparing dataframe values
    # Converting Dataframe cell value of type numpy.ndarray[float32]
    # using .tolist() converts each value to Python float. Python
    # float uses 64-bit precision causing mismatches in assertEqual.
    # As a workaround we use array.array('f', src).tolist() on the
    # source data
    data = [
        (array.array("f", [34.6, 77.8]).tolist(),),
        (None,),
        (array.array("f", [34.6, 77.8, 55.9]).tolist(),),
    ]
    ora_df = await async_conn.fetch_df_all(
        """
        select to_vector('[34.6, 77.8]', 2, float32)
        union all
        select null
        union all
        select to_vector('[34.6, 77.8, 55.9]', 3, float32)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9201(async_conn, test_env):
    "9201 - fetch float64 vector"
    data = [
        ([34.6, 77.8],),
        (None,),
        ([34.6, 77.8, 55.9],),
    ]
    ora_df = await async_conn.fetch_df_all(
        """
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select null
        union all
        select to_vector('[34.6, 77.8, 55.9]', 3, float64)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9202(async_conn, test_env):
    "9202 - fetch int8 vector"
    data = [
        ([34, -77],),
        (None,),
        ([34, 77, 55],),
    ]
    ora_df = await async_conn.fetch_df_all(
        """
        select to_vector('[34, -77]', 2, int8)
        union all
        select null
        union all
        select to_vector('[34, 77, 55]', 3, int8)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9203(
    skip_unless_binary_vectors_supported, async_conn, test_env
):
    "9203 - fetch binary vector"
    data = [
        ([3, 2, 3],),
        (None,),
        ([3, 2],),
    ]
    ora_df = await async_conn.fetch_df_all(
        """
        select to_vector('[3, 2, 3]', 24, binary)
        union all
        select null
        union all
        select to_vector('[3, 2]', 16, binary)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9204(async_conn, test_env):
    "9204 - fetch duplicate float64 vectors"
    data = [
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
    ]
    ora_df = await async_conn.fetch_df_all(
        """
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        union all
        select to_vector('[34.6, 77.8]', 2, float64)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9205(
    skip_unless_sparse_vectors_supported, async_conn, test_env
):
    "9205 - fetch float32 sparse vectors"
    data = [
        (
            {
                "num_dimensions": 8,
                "indices": [0, 7],
                "values": array.array("f", [34.6, 77.8]).tolist(),
            },
        ),
        (
            {
                "num_dimensions": 8,
                "indices": [0, 7],
                "values": array.array("f", [34.6, 9.1]).tolist(),
            },
        ),
    ]
    ora_df = await async_conn.fetch_df_all(
        """
        select to_vector('[8, [0, 7], [34.6, 77.8]]', 8, float32, sparse)
        union all
        select to_vector('[8, [0, 7], [34.6, 9.1]]', 8, float32, sparse)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9206(
    skip_unless_sparse_vectors_supported, async_conn, test_env
):
    "9206 - fetch float64 sparse vectors"
    data = [
        (
            {
                "num_dimensions": 8,
                "indices": [0, 7],
                "values": [34.6, 77.8],
            },
        ),
        (None,),
        (
            {
                "num_dimensions": 8,
                "indices": [0, 7],
                "values": [34.6, 9.1],
            },
        ),
    ]
    ora_df = await async_conn.fetch_df_all(
        """
        select to_vector('[8, [0, 7], [34.6, 77.8]]', 8, float64, sparse)
        union all
        select null
        union all
        select to_vector('[8, [0, 7], [34.6, 9.1]]', 8, float64, sparse)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9207(async_conn, test_env):
    "9207 - DPY-3031 - Unsupported flexible vector formats"
    with test_env.assert_raises_full_code("DPY-3031"):
        await async_conn.fetch_df_all(
            """
            select to_vector('[44, 55, 89]', 3, int8) as flex_col
            union all
            select to_vector('[34.6, 77.8, 55.9]', 3, float32)
            """
        )


async def test_9208(async_conn, test_env):
    "9208 - test vector operations with different dimensions"
    data = [([1, 0, 3],), ([0, 5, -12.25, 0],), ([5.5, -6.25, 7, 8, 9],)]
    ora_df = await async_conn.fetch_df_all(
        """
        select to_vector('[1, 0, 3]', 3, float64) from dual
        union all
        select to_vector('[0, 5, -12.25, 0]', 4, float64) from dual
        union all
        select to_vector('[5.5, -6.25, 7, 8, 9]', 5, float64) from dual
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9209(async_conn, test_env):
    "9209 - test vector operations with large arrays"
    large_array = list(range(1, 1001))
    data = [(large_array,), (large_array,)]
    str_value = ",".join(str(i) for i in large_array)
    ora_df = await async_conn.fetch_df_all(
        f"""
        select to_vector('[{str_value}]', {len(large_array)}, float64)
        union all
        select to_vector('[{str_value}]', {len(large_array)}, float64)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9210(
    skip_unless_sparse_vectors_supported, async_conn, test_env
):
    "9210 - test sparse vector operations with different dimensions"
    with test_env.assert_raises_full_code("DPY-2065"):
        await async_conn.fetch_df_all(
            """
            select to_vector('[10, [1, 3], [2, 4]]', 10, float64, sparse)
            union all
            select to_vector('[5, [1, 3], [2, 4]]', 5, float64, sparse)
            """
        )


async def test_9211(async_conn, test_env):
    "9211 - test mixed vector types in a single dataframe"
    data = [
        ([1.5, 2.5, 3.5], [1, 2, 3]),
        ([4.25, 5.25, 6.25], [4, 5, 6]),
    ]
    ora_df = await async_conn.fetch_df_all(
        """
        select
            to_vector('[1.5, 2.5, 3.5]', 3, float64) as float_vec,
            to_vector('[1, 2, 3]', 3, int8) as int_vec
        union all
        select
            to_vector('[4.25, 5.25, 6.25]', 3, float64),
            to_vector('[4, 5, 6]', 3, int8)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9212(async_conn, test_env):
    "9212 - test vectors with very large dimensions"
    large_dim = 800
    large_vector = [2.25] * large_dim
    large_vector[12] = 1.5
    large_vector[-25] = 8.5
    data = [(large_vector,)]
    vector_str = ",".join(str(i) for i in large_vector)
    ora_df = await async_conn.fetch_df_all(
        f"""
        select to_vector('[{vector_str}]', {large_dim}, float64)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_9213(
    skip_unless_binary_vectors_supported, async_conn, test_env
):
    "9213 - test binary vector edge case - max value"
    data = [
        ([255, 255, 255],),
        ([255, 0, 255],),
    ]
    ora_df = await async_conn.fetch_df_all(
        """
        select to_vector('[255, 255, 255]', 24, binary)
        union all
        select to_vector('[255, 0, 255]', 24, binary)
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)
