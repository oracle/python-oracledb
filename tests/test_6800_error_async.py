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
6800 - Module for testing error objects with asyncio
"""

import pickle

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def test_6800(async_cursor):
    "6800 - test parse error returns offset correctly"
    with pytest.raises(oracledb.Error) as excinfo:
        await async_cursor.execute("begin t_Missing := 5; end;")
    (error_obj,) = excinfo.value.args
    assert error_obj.full_code == "ORA-06550"
    assert error_obj.offset == 6


async def test_6801(async_cursor):
    "6801 - test picking/unpickling an error object"
    with pytest.raises(oracledb.Error) as excinfo:
        await async_cursor.execute(
            """
            begin
                raise_application_error(-20101, 'Test!');
            end;
            """
        )
    (error_obj,) = excinfo.value.args
    assert isinstance(error_obj, oracledb._Error)
    assert "Test!" in error_obj.message
    assert error_obj.code == 20101
    assert error_obj.offset == 0
    assert isinstance(error_obj.isrecoverable, bool)
    assert not error_obj.isrecoverable
    new_error_obj = pickle.loads(pickle.dumps(error_obj))
    assert isinstance(new_error_obj, oracledb._Error)
    assert new_error_obj.message == error_obj.message
    assert new_error_obj.code == error_obj.code
    assert new_error_obj.offset == error_obj.offset
    assert new_error_obj.context == error_obj.context
    assert new_error_obj.isrecoverable == error_obj.isrecoverable


async def test_6802(async_cursor):
    "6802 - test generation of full_code for ORA, DPI and DPY errors"
    with pytest.raises(oracledb.Error) as excinfo:
        await async_cursor.execute(None)
    (error_obj,) = excinfo.value.args
    assert error_obj.full_code == "DPY-2001"


async def test_6803(async_cursor):
    "6803 - test generation of error help portal URL"
    with pytest.raises(oracledb.Error) as excinfo:
        await async_cursor.execute("select 1 / 0 from dual")
    (error_obj,) = excinfo.value.args
    to_check = "Help: https://docs.oracle.com/error-help/db/ora-01476/"
    assert to_check in error_obj.message


async def test_6804(async_cursor):
    "6804 - verify warning is generated when creating a procedure"
    proc_name = "bad_proc_1704"
    assert async_cursor.warning is None
    await async_cursor.execute(
        f"""
        create or replace procedure {proc_name} as
        begin
            null
        end;
        """
    )
    assert async_cursor.warning.full_code == "DPY-7000"
    await async_cursor.execute(
        f"""
        create or replace procedure {proc_name} as
        begin
            null;
        end;
        """
    )
    assert async_cursor.warning is None
    await async_cursor.execute(f"drop procedure {proc_name}")


async def test_6805(async_cursor):
    "6805 - verify warning is generated when creating a function"
    func_name = "bad_func_1705"
    await async_cursor.execute(
        f"""
        create or replace function {func_name}
        return number as
        begin
            return null
        end;
        """
    )
    assert async_cursor.warning.full_code == "DPY-7000"
    await async_cursor.execute(f"drop function {func_name}")
    assert async_cursor.warning is None


async def test_6806(async_cursor):
    "6806 - verify warning is generated when creating a type"
    type_name = "bad_type_1706"
    await async_cursor.execute(
        f"""
        create or replace type {type_name} as object (
            x bad_type
        );
        """
    )
    assert async_cursor.warning.full_code == "DPY-7000"
    await async_cursor.execute(f"drop type {type_name}")
    assert async_cursor.warning is None


async def test_6807(async_conn):
    "6807 - verify warning is saved in a pipeline"
    proc_name = "bad_proc_1704"
    func_name = "bad_func_1705"
    type_name = "bad_type_1706"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute(
        f"""
        create or replace procedure {proc_name} as
        begin
            null
        end;
        """
    )
    pipeline.add_execute(
        f"""
        create or replace procedure {proc_name} as
        begin
            null;
        end;
        """
    )
    pipeline.add_execute(f"drop procedure {proc_name}")
    pipeline.add_execute(
        f"""
        create or replace function {func_name}
        return number as
        begin
            return null
        end;
        """
    )
    pipeline.add_execute(f"drop function {func_name}")
    pipeline.add_execute(
        f"""
        create or replace type {type_name} as object (
            x bad_type
        );
        """
    )
    pipeline.add_execute(f"drop type {type_name}")
    results = await async_conn.run_pipeline(pipeline)
    assert results[0].warning.full_code == "DPY-7000"
    assert results[1].warning is None
    assert results[2].warning is None
    assert results[3].warning.full_code == "DPY-7000"
    assert results[4].warning is None
    assert results[5].warning.full_code == "DPY-7000"
    assert results[6].warning is None


async def test_6808(async_conn, async_cursor):
    "6808 - verify warning is saved in a pipeline with a single operation"
    proc_name = "bad_proc_6808"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute(
        f"""
        create or replace procedure {proc_name} as
        begin
            null
        end;
        """
    )
    (result,) = await async_conn.run_pipeline(pipeline)
    assert result.warning.full_code == "DPY-7000"
    await async_cursor.execute(f"drop procedure {proc_name}")


async def test_6809(skip_if_drcp, test_env):
    "6809 - error from killed connection is deemed recoverable"
    admin_conn = await test_env.get_admin_connection_async()
    conn = await test_env.get_connection_async()
    sid, serial = (conn.session_id, conn.serial_num)
    with admin_conn.cursor() as admin_cursor:
        sql = f"alter system kill session '{sid},{serial}'"
        await admin_cursor.execute(sql)
    with test_env.assert_raises_full_code("DPY-4011") as cm:
        with conn.cursor() as cursor:
            await cursor.execute("select user from dual")
    assert cm.error_obj.isrecoverable
