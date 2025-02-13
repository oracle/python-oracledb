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
E2300 - Module for testing Transaction Guard (TG). No special setup is required
but the test suite makes use of debugging packages that are not intended for
normal use. It also creates and drops a service.
"""

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    service_name = "oracledb-test-tg"
    requires_connection = False

    @classmethod
    def setUpClass(cls):
        cls.admin_conn = test_env.get_admin_connection()
        user = test_env.get_main_user()
        with cls.admin_conn.cursor() as cursor:
            cursor.execute(
                f"""
                declare
                    params          dbms_service.svc_parameter_array;
                begin
                    params('COMMIT_OUTCOME') := 'true';
                    params('RETENTION_TIMEOUT') := 604800;
                    dbms_service.create_service('{cls.service_name}',
                                                '{cls.service_name}', params);
                    dbms_service.start_service('{cls.service_name}');
                end;
                """
            )
            cursor.execute(f"grant execute on dbms_tg_dbg to {user}")
            cursor.execute(f"grant execute on dbms_app_cont to {user}")

    @classmethod
    def tearDownClass(cls):
        user = test_env.get_main_user()
        with cls.admin_conn.cursor() as cursor:
            cursor.execute(f"revoke execute on dbms_tg_dbg from {user}")
            cursor.execute(f"revoke execute on dbms_app_cont from {user}")
            cursor.callproc("dbms_service.stop_service", [cls.service_name])
            cursor.callproc("dbms_service.delete_service", [cls.service_name])

    def test_ext_2300(self):
        "E2300 - test standalone connection"
        params = test_env.get_connect_params().copy()
        params.parse_connect_string(test_env.get_connect_string())
        params.set(service_name=self.service_name)
        for arg_name in ("pre_commit", "post_commit"):
            with self.subTest(arg_name=arg_name):
                conn = oracledb.connect(params=params)
                cursor = conn.cursor()
                cursor.execute("truncate table TestTempTable")
                cursor.execute(
                    """
                    insert into TestTempTable (IntCol, StringCol1)
                    values (:1, :2)
                    """,
                    [2300, "String for test 2300"],
                )
                full_arg_name = f"dbms_tg_dbg.tg_failpoint_{arg_name}"
                cursor.execute(
                    f"""
                    begin
                        dbms_tg_dbg.set_failpoint({full_arg_name});
                    end;
                    """
                )
                ltxid = conn.ltxid
                with self.assertRaisesFullCode("DPY-4011"):
                    conn.commit()
                conn = oracledb.connect(params=params)
                cursor = conn.cursor()
                committed_var = cursor.var(bool)
                completed_var = cursor.var(bool)
                cursor.callproc(
                    "dbms_app_cont.get_ltxid_outcome",
                    [ltxid, committed_var, completed_var],
                )
                expected_value = arg_name == "post_commit"
                self.assertEqual(committed_var.getvalue(), expected_value)
                self.assertEqual(completed_var.getvalue(), expected_value)

    def test_ext_2301(self):
        "E2301 - test pooled connection"
        params = test_env.get_pool_params().copy()
        params.parse_connect_string(test_env.get_connect_string())
        params.set(service_name=self.service_name, max=10)
        pool = oracledb.create_pool(params=params)
        for arg_name in ("pre_commit", "post_commit"):
            with self.subTest(arg_name=arg_name):
                conn = pool.acquire()
                cursor = conn.cursor()
                cursor.execute("truncate table TestTempTable")
                cursor.execute(
                    """
                    insert into TestTempTable (IntCol, StringCol1)
                    values (:1, :2)
                    """,
                    [2300, "String for test 2300"],
                )
                full_arg_name = f"dbms_tg_dbg.tg_failpoint_{arg_name}"
                cursor.execute(
                    f"""
                    begin
                        dbms_tg_dbg.set_failpoint({full_arg_name});
                    end;
                    """
                )
                ltxid = conn.ltxid
                with self.assertRaisesFullCode("DPY-4011"):
                    conn.commit()
                conn = pool.acquire()
                cursor = conn.cursor()
                committed_var = cursor.var(bool)
                completed_var = cursor.var(bool)
                cursor.callproc(
                    "dbms_app_cont.get_ltxid_outcome",
                    [ltxid, committed_var, completed_var],
                )
                expected_value = arg_name == "post_commit"
                self.assertEqual(committed_var.getvalue(), expected_value)
                self.assertEqual(completed_var.getvalue(), expected_value)


if __name__ == "__main__":
    test_env.run_test_cases()
