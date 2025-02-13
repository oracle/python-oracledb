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
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def test_6800(self):
        "6800 - test parse error returns offset correctly"
        with self.assertRaises(oracledb.Error) as cm:
            await self.cursor.execute("begin t_Missing := 5; end;")
        (error_obj,) = cm.exception.args
        self.assertEqual(error_obj.full_code, "ORA-06550")
        self.assertEqual(error_obj.offset, 6)

    async def test_6801(self):
        "6801 - test picking/unpickling an error object"
        with self.assertRaises(oracledb.Error) as cm:
            await self.cursor.execute(
                """
                begin
                    raise_application_error(-20101, 'Test!');
                end;
                """
            )
        (error_obj,) = cm.exception.args
        self.assertIsInstance(error_obj, oracledb._Error)
        self.assertIn("Test!", error_obj.message)
        self.assertEqual(error_obj.code, 20101)
        self.assertEqual(error_obj.offset, 0)
        self.assertIsInstance(error_obj.isrecoverable, bool)
        self.assertFalse(error_obj.isrecoverable)
        new_error_obj = pickle.loads(pickle.dumps(error_obj))
        self.assertIsInstance(new_error_obj, oracledb._Error)
        self.assertEqual(new_error_obj.message, error_obj.message)
        self.assertEqual(new_error_obj.code, error_obj.code)
        self.assertEqual(new_error_obj.offset, error_obj.offset)
        self.assertEqual(new_error_obj.context, error_obj.context)
        self.assertEqual(new_error_obj.isrecoverable, error_obj.isrecoverable)

    async def test_6802(self):
        "6802 - test generation of full_code for ORA, DPI and DPY errors"
        cursor = self.conn.cursor()
        with self.assertRaises(oracledb.Error) as cm:
            await cursor.execute(None)
        (error_obj,) = cm.exception.args
        self.assertEqual(error_obj.full_code, "DPY-2001")

    async def test_6803(self):
        "6803 - test generation of error help portal URL"
        cursor = self.conn.cursor()
        with self.assertRaises(oracledb.Error) as cm:
            await cursor.execute("select 1 / 0 from dual")
        (error_obj,) = cm.exception.args
        to_check = "Help: https://docs.oracle.com/error-help/db/ora-01476/"
        self.assertIn(to_check, error_obj.message)

    async def test_6804(self):
        "6804 - verify warning is generated when creating a procedure"
        proc_name = "bad_proc_1704"
        self.assertIsNone(self.cursor.warning)
        await self.cursor.execute(
            f"""
            create or replace procedure {proc_name} as
            begin
                null
            end;
            """
        )
        self.assertEqual(self.cursor.warning.full_code, "DPY-7000")
        await self.cursor.execute(
            f"""
            create or replace procedure {proc_name} as
            begin
                null;
            end;
            """
        )
        self.assertIsNone(self.cursor.warning)
        await self.cursor.execute(f"drop procedure {proc_name}")

    async def test_6805(self):
        "6805 - verify warning is generated when creating a function"
        func_name = "bad_func_1705"
        await self.cursor.execute(
            f"""
            create or replace function {func_name}
            return number as
            begin
                return null
            end;
            """
        )
        self.assertEqual(self.cursor.warning.full_code, "DPY-7000")
        await self.cursor.execute(f"drop function {func_name}")
        self.assertIsNone(self.cursor.warning)

    async def test_6806(self):
        "6806 - verify warning is generated when creating a type"
        type_name = "bad_type_1706"
        await self.cursor.execute(
            f"""
            create or replace type {type_name} as object (
                x bad_type
            );
            """
        )
        self.assertEqual(self.cursor.warning.full_code, "DPY-7000")
        await self.cursor.execute(f"drop type {type_name}")
        self.assertIsNone(self.cursor.warning)

    async def test_6807(self):
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
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[0].warning.full_code, "DPY-7000")
        self.assertIsNone(results[1].warning)
        self.assertIsNone(results[2].warning)
        self.assertEqual(results[3].warning.full_code, "DPY-7000")
        self.assertIsNone(results[4].warning)
        self.assertEqual(results[5].warning.full_code, "DPY-7000")
        self.assertIsNone(results[6].warning)

    async def test_6808(self):
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
        (result,) = await self.conn.run_pipeline(pipeline)
        self.assertEqual(result.warning.full_code, "DPY-7000")
        await self.cursor.execute(f"drop procedure {proc_name}")

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    async def test_6809(self):
        "6809 - error from killed connection is deemed recoverable"
        admin_conn = await test_env.get_admin_connection_async()
        conn = await test_env.get_connection_async()
        sid, serial = await self.get_sid_serial(conn)
        with admin_conn.cursor() as admin_cursor:
            sql = f"alter system kill session '{sid},{serial}'"
            await admin_cursor.execute(sql)
        with self.assertRaisesFullCode("DPY-4011") as cm:
            with conn.cursor() as cursor:
                await cursor.execute("select user from dual")
        self.assertTrue(cm.error_obj.isrecoverable)


if __name__ == "__main__":
    test_env.run_test_cases()
