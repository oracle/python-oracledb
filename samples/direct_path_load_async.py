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

# -----------------------------------------------------------------------------
# direct_path_load_async.py
#
# An asynchronous version of direct_path_load.py
#
# Shows how Direct Path Loads can be used to insert into Oracle Database.
# -----------------------------------------------------------------------------

import asyncio

import oracledb
import sample_env

# -----------------------------------------------------------------------------


async def main():

    connection = await oracledb.connect_async(
        user=sample_env.get_main_user(),
        password=sample_env.get_main_password(),
        dsn=sample_env.get_connect_string(),
        params=sample_env.get_connect_params(),
    )

    DATA = [
        (1, "A first row"),
        (2, "A second row"),
        (3, "A third row"),
    ]

    await connection.direct_path_load(
        schema_name=sample_env.get_main_user(),
        table_name="mytab",
        column_names=["id", "data"],
        data=DATA,
    )

    with connection.cursor() as cursor:

        await cursor.execute("select * from mytab")
        async for r in cursor:
            print(r)
        # Check the data was inserted
        await cursor.execute("select * from mytab")
        async for r in cursor:
            print(r)

        # Clean up the table so the sample can be re-run
        await cursor.execute("truncate table mytab")


asyncio.run(main())
