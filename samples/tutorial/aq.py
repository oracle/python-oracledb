# -----------------------------------------------------------------------------
# aq.py (Section 14.1)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Copyright (c) 2017, 2025, Oracle and/or its affiliates.
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
import decimal
import db_config

con = oracledb.connect(
    user=db_config.user, password=db_config.pw, dsn=db_config.dsn
)
cur = con.cursor()

BOOK_TYPE_NAME = "UDT_BOOK"
QUEUE_NAME = "BOOKS"
QUEUE_TABLE_NAME = "BOOK_QUEUE_TABLE"

# Cleanup
cur.execute(
    f"""
    begin
        dbms_aqadm.stop_queue('{QUEUE_NAME}');
        dbms_aqadm.drop_queue('{QUEUE_NAME}');
        dbms_aqadm.drop_queue_table('{QUEUE_TABLE_NAME}');

        execute immediate 'drop type {BOOK_TYPE_NAME}';
        exception when others then
            if sqlcode <> -24010 then
                raise;
            end if;
    end;
    """
)

# Create a type
print("Creating books type UDT_BOOK...")
cur.execute(
    f"""
    create type {BOOK_TYPE_NAME} as object (
        title varchar2(100),
        authors varchar2(100),
        price number(5,2)
    );
    """
)


# Create queue table and queue and start the queue
print("Creating queue table...")
cur.callproc(
    "dbms_aqadm.create_queue_table", (QUEUE_TABLE_NAME, BOOK_TYPE_NAME)
)
cur.callproc("dbms_aqadm.create_queue", (QUEUE_NAME, QUEUE_TABLE_NAME))
cur.callproc("dbms_aqadm.start_queue", (QUEUE_NAME,))

books_type = con.gettype(BOOK_TYPE_NAME)
queue = con.queue(QUEUE_NAME, books_type)

# Enqueue a few messages
print("Enqueuing messages...")

BOOK_DATA = [
    (
        "The Fellowship of the Ring",
        "Tolkien, J.R.R.",
        decimal.Decimal("10.99"),
    ),
    (
        "Harry Potter and the Philosopher's Stone",
        "Rowling, J.K.",
        decimal.Decimal("7.99"),
    ),
]

for title, authors, price in BOOK_DATA:
    book = books_type.newobject()
    book.TITLE = title
    book.AUTHORS = authors
    book.PRICE = price
    print(title)
    queue.enqone(con.msgproperties(payload=book))
    con.commit()

# Dequeue the messages
print("\nDequeuing messages...")
queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
while True:
    props = queue.deqone()
    if not props:
        break
    print(props.payload.TITLE)
    con.commit()

print("\nDone.")
