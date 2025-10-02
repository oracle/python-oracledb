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
E2600 - Module for testing timing of sessionless transactions. No special setup
is required but the tests here will only be run if the run_long_tests value is
enabled.
"""

import time

import pytest


@pytest.fixture(autouse=True)
def module_checks(
    skip_unless_sessionless_transactions_supported, skip_unless_run_long_tests
):
    pass


def test_ext_2600(cursor, test_env):
    "E2600 - test error conditions with client API"
    cursor.execute("truncate table TestTempTable")

    transaction_id = "test_2600_transaction_id"
    other_transaction_id = "test_2600_different_transaction_id"
    with test_env.get_connection() as conn:
        cursor = conn.cursor()

        # suspending a non-existent transaction will fail only in thin
        # mode
        if conn.thin:
            with test_env.assert_raises_full_code("DPY-3036"):
                conn.suspend_sessionless_transaction()

        # start first sessionless transaction
        conn.begin_sessionless_transaction(
            transaction_id=transaction_id, timeout=5
        )

        # starting another sessionless transaction will fail only in thin
        # mode
        if conn.thin:
            with test_env.assert_raises_full_code("DPY-3035"):
                conn.begin_sessionless_transaction(
                    transaction_id=other_transaction_id, timeout=5
                )

        cursor.execute(
            """
            INSERT INTO TestTempTable(IntCol, StringCol1)
            VALUES(:1, :2)
            """,
            (1, "test_row"),
        )

        # suspend using server API should fail
        with test_env.assert_raises_full_code("DPY-3034"):
            cursor.callproc("dbms_transaction.suspend_transaction")

        # suspend using client API should succeed
        conn.suspend_sessionless_transaction()

        # wait till it times out
        time.sleep(10)

        # attmpting to resume the transaction should fail
        with test_env.assert_raises_full_code("ORA-26218"):
            conn.resume_sessionless_transaction(transaction_id=transaction_id)
