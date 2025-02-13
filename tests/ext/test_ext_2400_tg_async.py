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

import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    service_name = "oracledb-test-tg-async"
    requires_connection = False
    setup_completed = False

    async def __perform_setup(self):
        """
        Perform setup, if needed.
        """
        if self.__class__.setup_completed:
            return
        user = test_env.get_main_user()
        async with test_env.get_admin_connection(use_async=True) as conn:
            cursor = conn.cursor()
            await cursor.execute(f"grant execute on dbms_tg_dbg to {user}")
            await cursor.execute(f"grant execute on dbms_app_cont to {user}")
            await cursor.execute(
                """
                select count(*) from dba_services
                where name = :name
                """,
                name=self.service_name,
            )
            (count,) = await cursor.fetchone()
            if count > 0:
                try:
                    await cursor.callproc(
                        "dbms_service.start_service", [self.service_name]
                    )
                except Exception as e:
                    if not str(e).startswith("ORA-44305:"):
                        raise
                return
            await cursor.execute(
                f"""
                declare
                    params          dbms_service.svc_parameter_array;
                begin
                    params('COMMIT_OUTCOME') := 'true';
                    params('RETENTION_TIMEOUT') := 604800;
                    dbms_service.create_service('{self.service_name}',
                                                '{self.service_name}', params);
                    dbms_service.start_service('{self.service_name}');
                end;
                """
            )

    async def test_ext_2400(self):
        "E2400 - test standalone connection"
        await self.__perform_setup()
        params = test_env.get_connect_params().copy()
        params.parse_connect_string(test_env.get_connect_string())
        params.set(service_name=self.service_name)
        for arg_name in ("pre_commit", "post_commit"):
            with self.subTest(arg_name=arg_name):
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
                with self.assertRaisesFullCode("DPY-4011"):
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
                self.assertEqual(committed_var.getvalue(), expected_value)
                self.assertEqual(completed_var.getvalue(), expected_value)

    async def test_ext_2401(self):
        "E2401 - test pooled connection"
        await self.__perform_setup()
        params = test_env.get_pool_params().copy()
        params.parse_connect_string(test_env.get_connect_string())
        params.set(service_name=self.service_name, max=10)
        pool = oracledb.create_pool_async(params=params)
        for arg_name in ("pre_commit", "post_commit"):
            with self.subTest(arg_name=arg_name):
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
                    with self.assertRaisesFullCode("DPY-4011"):
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
                    self.assertEqual(committed_var.getvalue(), expected_value)
                    self.assertEqual(completed_var.getvalue(), expected_value)
        await pool.close()


if __name__ == "__main__":
    test_env.run_test_cases()
