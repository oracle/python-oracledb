# -----------------------------------------------------------------------------
# pipelining.py (Section 18.1)
# -----------------------------------------------------------------------------

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

import asyncio
import oracledb
import db_config


async def get_weather():
    return "Hot and sunny"


async def get_location():
    return "Melbourne"


async def main():
    con = await oracledb.connect_async(
        user=db_config.user, password=db_config.pw, dsn=db_config.dsn
    )

    pipeline = oracledb.create_pipeline()
    pipeline.add_fetchone(
        "select ename, job from emp where empno = :en", [7839]
    )
    pipeline.add_fetchall("select dname from dept order by deptno")

    # Run the pipeline and non-database operations concurrently.
    # Note although the database receives all the operations at the same time,
    # it will execute each operation sequentially. The local Python work
    # executes during the time the database is processing the queries.
    return_values = await asyncio.gather(
        get_weather(), get_location(), con.run_pipeline(pipeline)
    )

    for r in return_values:
        if isinstance(r, list):  # the pipeline return list
            for result in r:
                if result.rows:
                    for row in result.rows:
                        print(*row, sep="\t")
        else:
            print(r)  # a local operation result

    await con.close()


asyncio.run(main())
