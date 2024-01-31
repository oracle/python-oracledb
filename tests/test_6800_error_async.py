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


if __name__ == "__main__":
    test_env.run_test_cases()
