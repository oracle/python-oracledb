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
E2100 - Module for testing BFILE with asyncio. No special setup is required but
the tests here will only be run if the local_database is enabled.
"""

import os
import tempfile

import oracledb
import pytest

DIR_NAME = "EXT_TEST_2200_DIR"


@pytest.fixture(autouse=True)
def module_checks(
    anyio_backend, skip_unless_thin_mode, skip_unless_local_database
):
    pass


@pytest.fixture
def temp_dir(test_env):
    with tempfile.TemporaryDirectory() as temp_dir:
        user = test_env.main_user
        with test_env.get_admin_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    create or replace directory {DIR_NAME}
                    as '{temp_dir}'
                    """
                )
                cursor.execute(f"grant read on directory {DIR_NAME} to {user}")
        yield temp_dir


async def test_ext_2200(temp_dir, async_cursor):
    "E2200 - test fileexists() and getfilename()"
    file_name = "test_2200.txt"
    contents = b"Some arbitrary data for test 2200"
    with open(os.path.join(temp_dir, file_name), "wb") as f:
        f.write(contents)
    await async_cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = await async_cursor.fetchone()
    assert await bfile.read() == contents
    assert await bfile.fileexists()
    assert bfile.getfilename() == (DIR_NAME, file_name)


async def test_ext_2201(temp_dir, async_cursor):
    "E2201 - test setfilename()"
    file_name = "test_2201.txt"
    contents = b"Some arbitrary data for test 2201"
    new_file_name = "test_2201b.txt"
    new_contents = b"Some arbitrary different data for test 2201"
    with open(os.path.join(temp_dir, file_name), "wb") as f:
        f.write(contents)
    with open(os.path.join(temp_dir, new_file_name), "wb") as f:
        f.write(new_contents)
    await async_cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = await async_cursor.fetchone()
    assert await bfile.read() == contents
    bfile.setfilename(DIR_NAME, new_file_name)
    assert await bfile.read() == new_contents


async def test_ext_2202(temp_dir, async_cursor, test_env):
    "E2202 - test BFILE with LOB methods"
    file_name = "test_2202.txt"
    contents = b"Some arbitrary data for test 2202"
    with open(os.path.join(temp_dir, file_name), "wb") as f:
        f.write(contents)
    await async_cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = await async_cursor.fetchone()
    assert await bfile.size() == len(contents)
    assert await bfile.read(7) == contents[6:]
    assert await bfile.read(7, 2) == contents[6:8]
    assert not await bfile.isopen()
    await bfile.open()
    assert await bfile.isopen()
    await bfile.close()
    assert not await bfile.isopen()
    with test_env.assert_raises_full_code("DPY-3025"):
        await bfile.getchunksize()
    with test_env.assert_raises_full_code("DPY-3025"):
        await bfile.trim(1)
    with test_env.assert_raises_full_code("DPY-3025"):
        await bfile.write("1")


async def test_ext_2203(temp_dir, async_conn, async_cursor):
    "E2203 - test binding a BFILE"
    file_name = "test_2203.txt"
    contents = b"Some arbitrary data for test 2203"
    with open(os.path.join(temp_dir, file_name), "wb") as f:
        f.write(contents)
    await async_cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = await async_cursor.fetchone()
    await async_cursor.execute("truncate table TestBfiles")
    await async_cursor.execute(
        "insert into TestBfiles values (:1, :2)", [1, bfile]
    )
    await async_conn.commit()


async def test_ext_2204(temp_dir, async_cursor, test_env):
    "E2204 - test reading from a missing file"
    file_name = "test_2204.txt"
    await async_cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = await async_cursor.fetchone()
    assert bfile.getfilename() == (DIR_NAME, file_name)
    assert not await bfile.fileexists()
    with test_env.assert_raises_full_code("ORA-22288"):
        await bfile.read()


async def test_ext_2205(temp_dir, async_cursor):
    "E2205 - test setting and getting BFILE var"
    file_name1 = "test1.txt"
    contents1 = b"extended test 2105 - first file"
    with open(os.path.join(temp_dir, file_name1), "wb") as f:
        f.write(contents1)
    file_name2 = "test2.txt"
    contents2 = b"extended test 2105 - second file"
    with open(os.path.join(temp_dir, file_name2), "wb") as f:
        f.write(contents2)
    var1 = async_cursor.var(oracledb.DB_TYPE_BFILE)
    var2 = async_cursor.var(oracledb.DB_TYPE_BFILE)
    await async_cursor.execute(
        f"""
        begin
            :1 := BFILENAME('{DIR_NAME}', '{file_name1}');
            :2 := BFILENAME('{DIR_NAME}', '{file_name2}');
        end;
        """,
        [var1, var2],
    )
    assert await var1.getvalue().read() == contents1
    assert await var2.getvalue().read() == contents2
    await async_cursor.execute("begin :1 := :2; end;", [var1, var2])
    assert await var1.getvalue().read() == contents2
