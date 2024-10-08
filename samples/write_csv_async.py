# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
# write_csv_async.py
#
# An asynchronous version of write_csv.py
#
# A sample showing one way of writing CSV data.
# -----------------------------------------------------------------------------

import asyncio
import csv

import oracledb
import sample_env

# CSV file to create
FILE_NAME = "sample.csv"


async def main():
    connection = await oracledb.connect_async(
        user=sample_env.get_main_user(),
        password=sample_env.get_main_password(),
        dsn=sample_env.get_connect_string(),
        params=sample_env.get_connect_params(),
    )

    with connection.cursor() as cursor:
        cursor.arraysize = 1000  # tune this for large queries
        print(f"Writing to {FILE_NAME}")
        with open(FILE_NAME, "w") as f:
            writer = csv.writer(
                f, lineterminator="\n", quoting=csv.QUOTE_NONNUMERIC
            )
            await cursor.execute(
                """select rownum, sysdate, mycol from BigTab"""
            )
            writer.writerow(info.name for info in cursor.description)
            writer.writerows(await cursor.fetchall())


asyncio.run(main())
