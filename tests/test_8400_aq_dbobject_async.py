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
8400 - Module for testing AQ with DbObject payloads with asyncio.
"""

import decimal

import oracledb
import pytest

BOOK_TYPE_NAME = "UDT_BOOK"
BOOK_QUEUE_NAME = "TEST_BOOK_QUEUE"
BOOK_DATA = [
    ("Wings of Fire", "A.P.J. Abdul Kalam", decimal.Decimal("15.75")),
    ("The Story of My Life", "Hellen Keller", decimal.Decimal("10.50")),
    ("The Chronicles of Narnia", "C.S. Lewis", decimal.Decimal("25.25")),
]


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


@pytest.fixture
async def queue(async_conn, test_env):
    return await test_env.get_and_clear_queue_async(
        async_conn, BOOK_QUEUE_NAME, BOOK_TYPE_NAME
    )


def _verify_attr(obj, attrName, value):
    setattr(obj, attrName, value)
    assert getattr(obj, attrName) == value


async def test_8400(queue):
    "8400 - test dequeuing an empty queue"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = await queue.deqone()
    assert props is None


async def test_8401(queue, async_conn):
    "8401 - test enqueuing and dequeuing multiple messages"
    props = async_conn.msgproperties()
    for title, authors, price in BOOK_DATA:
        props.payload = book = queue.payload_type.newobject()
        book.TITLE = title
        book.AUTHORS = authors
        book.PRICE = price
        await queue.enqone(props)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    results = []
    while True:
        props = await queue.deqone()
        if props is None:
            break
        book = props.payload
        row = (book.TITLE, book.AUTHORS, book.PRICE)
        results.append(row)
    await async_conn.commit()
    assert results == BOOK_DATA


async def test_8402(queue, async_conn):
    "8402 - test dequeuing with DEQ_REMOVE_NODATA option"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[1]
    props = async_conn.msgproperties(payload=book)
    await queue.enqone(props)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
    props = await queue.deqone()
    assert props is not None
    assert props.payload.TITLE is None


async def test_8403(queue):
    "8403 - test getting/setting dequeue options attributes"
    options = queue.deqoptions
    _verify_attr(options, "condition", "TEST_CONDITION")
    _verify_attr(options, "consumername", "TEST_CONSUMERNAME")
    _verify_attr(options, "correlation", "TEST_CORRELATION")
    _verify_attr(options, "mode", oracledb.DEQ_LOCKED)
    _verify_attr(options, "navigation", oracledb.DEQ_NEXT_TRANSACTION)
    _verify_attr(options, "transformation", "TEST_TRANSFORMATION")
    _verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)
    _verify_attr(options, "wait", 1287)
    _verify_attr(options, "msgid", b"mID")


async def test_8404(queue):
    "8404 - test getting/setting enqueue options attributes"
    options = queue.enqoptions
    _verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)


async def test_8405(queue):
    "8405 - test errors for invalid values for enqueue"
    book = queue.payload_type.newobject()
    with pytest.raises(TypeError):
        await queue.enqone(book)


async def test_8406(async_conn):
    "8406 - test getting/setting message properties attributes"
    props = async_conn.msgproperties()
    _verify_attr(props, "correlation", "TEST_CORRELATION")
    _verify_attr(props, "delay", 60)
    _verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
    _verify_attr(props, "expiration", 30)
    assert props.attempts == 0
    _verify_attr(props, "priority", 1)
    assert props.state == oracledb.MSG_READY
    assert props.deliverymode == 0


async def test_8407(queue, async_conn, test_env):
    "8407 - test enqueue visibility option - ENQ_ON_COMMIT"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
    props = async_conn.msgproperties(payload=book)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        books_type = await other_conn.gettype(BOOK_TYPE_NAME)
        queue = other_conn.queue(BOOK_QUEUE_NAME, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        assert props is None
        await async_conn.commit()
        props = await queue.deqone()
        await other_conn.commit()
        assert props is not None


async def test_8408(queue, async_conn, test_env):
    "8408 - test enqueue visibility option - ENQ_IMMEDIATE"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=book)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        books_type = await other_conn.gettype(BOOK_TYPE_NAME)
        queue = other_conn.queue(BOOK_QUEUE_NAME, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        await other_conn.commit()
        assert results == BOOK_DATA[0]


async def test_8409(queue, async_conn, test_env):
    "8409 - test enqueue/dequeue delivery modes identical - buffered"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=book)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        books_type = await other_conn.gettype(BOOK_TYPE_NAME)
        queue = other_conn.queue(BOOK_QUEUE_NAME, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        assert props.deliverymode == oracledb.MSG_BUFFERED
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        await other_conn.commit()
        assert results == BOOK_DATA[0]


async def test_8410(queue, async_conn, test_env):
    "8410 - test enqueue/dequeue delivery modes identical - persistent"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=book)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        books_type = await other_conn.gettype(BOOK_TYPE_NAME)
        queue = other_conn.queue(BOOK_QUEUE_NAME, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        assert props.deliverymode == oracledb.MSG_PERSISTENT
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        await other_conn.commit()
        assert results == BOOK_DATA[0]


async def test_8411(queue, async_conn, test_env):
    "8411 - test enqueue/dequeue delivery modes the same"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=book)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        books_type = await other_conn.gettype(BOOK_TYPE_NAME)
        queue = other_conn.queue(BOOK_QUEUE_NAME, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        assert props.deliverymode == oracledb.MSG_PERSISTENT
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        await other_conn.commit()
        assert results == BOOK_DATA[0]


async def test_8412(queue, async_conn, test_env):
    "8412 - test enqueue/dequeue delivery modes different"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=book)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        books_type = await other_conn.gettype(BOOK_TYPE_NAME)
        queue = other_conn.queue(BOOK_QUEUE_NAME, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        assert props is None


async def test_8413(async_conn, test_env):
    "8413 - test error for message with no payload"
    books_type = await async_conn.gettype(BOOK_TYPE_NAME)
    queue = async_conn.queue(BOOK_QUEUE_NAME, books_type)
    props = async_conn.msgproperties()
    with test_env.assert_raises_full_code("DPY-2000"):
        await queue.enqone(props)


async def test_8414(queue, async_conn, async_cursor):
    "8414 - verify that the msgid property is returned correctly"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[0]
    props = async_conn.msgproperties(payload=book)
    assert props.msgid is None
    await queue.enqone(props)
    await async_cursor.execute("select msgid from book_queue_tab")
    (actual_msgid,) = await async_cursor.fetchone()
    assert props.msgid == actual_msgid
    props = await queue.deqone()
    assert props.msgid == actual_msgid


async def test_8415(queue, async_conn, async_cursor):
    "8415 - test message props enqtime"
    book = queue.payload_type.newobject()
    await async_cursor.execute("select current_timestamp from dual")
    (start_date,) = await async_cursor.fetchone()
    start_date = start_date.replace(microsecond=0)
    props = async_conn.msgproperties(payload=book)
    await queue.enqone(props)
    props = await queue.deqone()
    await async_cursor.execute("select current_timestamp from dual")
    (end_date,) = await async_cursor.fetchone()
    end_date = end_date.replace(microsecond=0)
    assert start_date <= props.enqtime <= end_date


async def test_8416(queue, async_conn):
    "8416 - test message props declared attributes"
    book = queue.payload_type.newobject()
    values = dict(
        payload=book,
        correlation="TEST_CORRELATION",
        delay=7,
        exceptionq="TEST_EXCEPTIONQ",
        expiration=10,
        priority=1,
    )
    props = async_conn.msgproperties(**values)
    for attr_name in values:
        assert getattr(props, attr_name) == values[attr_name]


async def test_8417(async_conn):
    "8417 - test error for invalid type for payload_type"
    with pytest.raises(TypeError):
        await async_conn.queue("THE QUEUE", payload_type=4)


async def test_8418(queue, async_conn):
    "8418 - test getting queue attributes"
    assert queue.name == BOOK_QUEUE_NAME
    assert queue.connection is async_conn


async def test_8419(queue):
    "8419 - test getting write-only attributes"
    with pytest.raises(AttributeError):
        queue.enqoptions.deliverymode
    with pytest.raises(AttributeError):
        queue.deqoptions.deliverymode


async def test_8420(queue, async_conn, test_env):
    "8420 - test correlation deqoption"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[0]
    correlations = ["Math", "Programming"]
    num_messages = 3
    messages = [
        async_conn.msgproperties(payload=book, correlation=c)
        for c in correlations
        for i in range(num_messages)
    ]
    await queue.enqmany(messages)
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.correlation = correlations[0]
    correlated_messages = await queue.deqmany(num_messages + 1)
    assert len(correlated_messages) == num_messages

    queue.deqoptions.correlation = correlations[1]
    with test_env.assert_raises_full_code("ORA-25241"):
        await queue.deqone()
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    correlated_messages = await queue.deqmany(num_messages + 1)
    assert len(correlated_messages) == num_messages


async def test_8421(queue, async_conn):
    "8421 - test correlation deqoption with pattern-matching characters"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[0]
    for correlation in ("PreCalculus-math1", "Calculus-Math2"):
        props = async_conn.msgproperties(payload=book, correlation=correlation)
        await queue.enqone(props)
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.correlation = "%Calculus-%ath_"
    messages = await queue.deqmany(5)
    assert len(messages) == 2


async def test_8422(queue, async_conn):
    "8422 - test condition deqoption with priority"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT

    priorities = [5, 10]
    indexes = [0, 1]
    for priority, ix in zip(priorities, indexes):
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = BOOK_DATA[ix]
        props = async_conn.msgproperties(payload=book, priority=priority)
        await queue.enqone(props)

    queue.deqoptions.condition = "priority = 9"
    messages = await queue.deqmany(3)
    assert len(messages) == 0

    for priority, ix in zip(priorities, indexes):
        queue.deqoptions.condition = f"priority = {priority}"
        messages = await queue.deqmany(3)
        assert len(messages) == 1
        book = messages[0].payload
        data = book.TITLE, book.AUTHORS, book.PRICE
        assert data == BOOK_DATA[ix]


async def test_8423(queue, async_conn):
    "8423 - test mode deqoption with DEQ_REMOVE_NODATA"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA

    book = queue.payload_type.newobject()
    for data in BOOK_DATA:
        book.TITLE, book.AUTHORS, book.PRICE = data
        props = async_conn.msgproperties(payload=book)
        await queue.enqone(props)

    messages = await queue.deqmany(5)
    assert len(messages) == 3
    for message in messages:
        assert message.payload.TITLE is None
        assert message.payload.AUTHORS is None
        assert message.payload.PRICE is None


async def test_8424(async_conn):
    "8424 - test payload_type returns the correct value"
    books_type = await async_conn.gettype(BOOK_TYPE_NAME)
    queue = async_conn.queue(BOOK_QUEUE_NAME, books_type)
    assert queue.payload_type == books_type


async def test_8425(queue, async_conn, test_env):
    "8425 - test enqueuing to an object queue with the wrong payload"
    props = async_conn.msgproperties(payload="A string")
    with test_env.assert_raises_full_code("DPY-2062"):
        await queue.enqone(props)
