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
E2400 - Module for testing Transaction Guard (TG) using asyncio. No special
setup is required but the test suite makes use of debugging packages that are
not intended for normal use. It also creates and drops a service.
"""

import oracledb
import pytest

SERVICE_NAME = "oracledb-test-tg-async"


@pytest.fixture(scope="module", autouse=True)
def setup_service(test_env):
    user = test_env.main_user
    with test_env.get_admin_connection() as admin_conn:
        with admin_conn.cursor() as cursor:
            cursor.execute(
                f"""
                declare
                    params          dbms_service.svc_parameter_array;
                begin
                    params('COMMIT_OUTCOME') := 'true';
                    params('RETENTION_TIMEOUT') := 604800;
                    dbms_service.create_service('{SERVICE_NAME}',
                                                '{SERVICE_NAME}', params);
                    dbms_service.start_service('{SERVICE_NAME}');
                end;
                """
            )
            cursor.execute(f"grant execute on dbms_tg_dbg to {user}")
            cursor.execute(f"grant execute on dbms_app_cont to {user}")
        yield
        with admin_conn.cursor() as cursor:
            cursor.execute(f"revoke execute on dbms_tg_dbg from {user}")
            cursor.execute(f"revoke execute on dbms_app_cont from {user}")
            cursor.callproc("dbms_service.stop_service", [SERVICE_NAME])
            cursor.callproc("dbms_service.delete_service", [SERVICE_NAME])


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def test_ext_2400(test_env):
    "E2400 - test standalone connection"
    params = test_env.get_connect_params().copy()
    params.parse_connect_string(test_env.connect_string)
    params.set(service_name=SERVICE_NAME)
    for arg_name in ("pre_commit", "post_commit"):
        conn = await oracledb.connect_async(params=params)
        cursor = conn.cursor()
        await cursor.execute("truncate table TestTempTable")
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            [2400, "String for test 2400"],
        )
        full_arg_name = f"dbms_tg_dbg.tg_failpoint_{arg_name}"
        await cursor.execute(
            f"""
            begin
                dbms_tg_dbg.set_failpoint({full_arg_name});
            end;
            """
        )
        ltxid = conn.ltxid
        with test_env.assert_raises_full_code("DPY-4011"):
            await conn.commit()
        conn = await oracledb.connect_async(params=params)
        cursor = conn.cursor()
        committed_var = cursor.var(bool)
        completed_var = cursor.var(bool)
        await cursor.callproc(
            "dbms_app_cont.get_ltxid_outcome",
            [ltxid, committed_var, completed_var],
        )
        expected_value = arg_name == "post_commit"
        assert committed_var.getvalue() == expected_value
        assert completed_var.getvalue() == expected_value


async def test_ext_2401(test_env):
    "E2401 - test pooled connection"
    params = test_env.get_pool_params().copy()
    params.parse_connect_string(test_env.connect_string)
    params.set(service_name=SERVICE_NAME, max=10)
    pool = oracledb.create_pool_async(params=params)
    for arg_name in ("pre_commit", "post_commit"):
        async with pool.acquire() as conn:
            cursor = conn.cursor()
            await cursor.execute("truncate table TestTempTable")
            await cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)
                """,
                [2400, "String for test 2400"],
            )
            full_arg_name = f"dbms_tg_dbg.tg_failpoint_{arg_name}"
            await cursor.execute(
                f"""
                begin
                    dbms_tg_dbg.set_failpoint({full_arg_name});
                end;
                """
            )
            ltxid = conn.ltxid
            with test_env.assert_raises_full_code("DPY-4011"):
                await conn.commit()
        async with pool.acquire() as conn:
            cursor = conn.cursor()
            committed_var = cursor.var(bool)
            completed_var = cursor.var(bool)
            await cursor.callproc(
                "dbms_app_cont.get_ltxid_outcome",
                [ltxid, committed_var, completed_var],
            )
            expected_value = arg_name == "post_commit"
            assert committed_var.getvalue() == expected_value
            assert completed_var.getvalue() == expected_value
    await pool.close()
