# -----------------------------------------------------------------------------
# connect_pool.py (Section 2.1)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Copyright (c) 2017, 2023, Oracle and/or its affiliates.
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

import oracledb
import threading
import db_config

pool = oracledb.create_pool(
    user=db_config.user,
    password=db_config.pw,
    dsn=db_config.dsn,
    min=2,
    max=5,
    increment=1,
    getmode=oracledb.POOL_GETMODE_WAIT,
)


def Query():
    con = pool.acquire()
    cur = con.cursor()
    for i in range(4):
        cur.execute("select myseq.nextval from dual")
        (seqval,) = cur.fetchone()
        print(
            "Thread",
            threading.current_thread().name,
            "fetched sequence =",
            seqval,
        )


thread1 = threading.Thread(name="#1", target=Query)
thread1.start()

thread2 = threading.Thread(name="#2", target=Query)
thread2.start()

thread1.join()
thread2.join()

print("All done!")
