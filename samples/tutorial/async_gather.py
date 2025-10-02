# -----------------------------------------------------------------------------
# async_gather.py (Section 18.1)
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

# Number of coroutines to run
CONCURRENCY = 5

# Maximum connection pool size
POOLSIZE = 5

# Query the unique session identifier/serial number combination of a connection
SQL = """select unique current_timestamp as ct, sid||'-'||serial# as sidser
         from v$session_connect_info
         where sid = sys_context('userenv', 'sid')"""


# Show the unique session identifier/serial number of each connection that the
# pool opens
async def init_session(connection, requested_tag):
    res = await connection.fetchone(SQL)
    print(res[0].strftime("%H:%M:%S.%f"), "- init_session SID-SERIAL#", res[1])


# The coroutine simply shows the session identifier/serial number of the
# connection returned by the pool.acquire() call
async def query(pool):
    async with pool.acquire() as connection:
        await connection.callproc("dbms_session.sleep", [1])
        res = await connection.fetchone(SQL)
        print(res[0].strftime("%H:%M:%S.%f"), "- query SID-SERIAL#", res[1])


async def main():

    pool = oracledb.create_pool_async(
        user=db_config.user,
        password=db_config.pw,
        dsn=db_config.dsn,
        min=1,
        max=POOLSIZE,
        session_callback=init_session,
    )

    coroutines = [query(pool) for i in range(CONCURRENCY)]

    await asyncio.gather(*coroutines)

    await pool.close()


asyncio.run(main())
