# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
2700 - Module for testing AQ with DbObject payloads.
"""

import decimal
import threading

import oracledb
import pytest


@pytest.fixture(scope="module")
def book_data():
    return [
        ("Wings of Fire", "A.P.J. Abdul Kalam", decimal.Decimal("15.75")),
        ("The Story of My Life", "Hellen Keller", decimal.Decimal("10.50")),
        ("The Chronicles of Narnia", "C.S. Lewis", decimal.Decimal("25.25")),
    ]


@pytest.fixture
def queue(conn, test_env):
    """
    Creates the queue used by the tests in this file.
    """
    return test_env.get_and_clear_queue(conn, "TEST_BOOK_QUEUE", "UDT_BOOK")


def _deq_in_thread(test_env, queue, results):
    with test_env.get_connection() as conn:
        books_type = conn.gettype(queue.payload_type.name)
        thread_queue = conn.queue(queue.name, books_type)
        thread_queue.deqoptions.wait = 10
        props = thread_queue.deqone()
        if props is not None:
            book = props.payload
            results.append((book.TITLE, book.AUTHORS, book.PRICE))
        conn.commit()


def _verify_attr(obj, attrName, value):
    setattr(obj, attrName, value)
    assert getattr(obj, attrName) == value


def test_2700(queue):
    "2700 - test dequeuing an empty queue"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props is None


def test_2701(conn, queue, book_data):
    "2701 - test enqueuing and dequeuing multiple messages"
    props = conn.msgproperties()
    for title, authors, price in book_data:
        props.payload = book = queue.payload_type.newobject()
        book.TITLE = title
        book.AUTHORS = authors
        book.PRICE = price
        queue.enqone(props)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    results = []
    while True:
        props = queue.deqone()
        if props is None:
            break
        book = props.payload
        row = (book.TITLE, book.AUTHORS, book.PRICE)
        results.append(row)
    conn.commit()
    assert results == book_data


def test_2702(conn, queue, book_data):
    "2702 - test dequeuing with DEQ_REMOVE_NODATA option"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[1]
    props = conn.msgproperties(payload=book)
    queue.enqone(props)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
    props = queue.deqone()
    assert props is not None
    assert props.payload.TITLE is None


def test_2703(queue):
    "2703 - test getting/setting dequeue options attributes"
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


def test_2704(conn, queue, book_data, test_env):
    "2704 - test waiting for dequeue"
    results = []
    thread = threading.Thread(
        target=_deq_in_thread,
        args=(
            test_env,
            queue,
            results,
        ),
    )
    thread.start()
    book = queue.payload_type.newobject()
    title, authors, price = book_data[0]
    book.TITLE = title
    book.AUTHORS = authors
    book.PRICE = price
    props = conn.msgproperties(payload=book)
    queue.enqone(props)
    conn.commit()
    thread.join()
    assert results == [(title, authors, price)]


def test_2705(queue):
    "2705 - test getting/setting enqueue options attributes"
    options = queue.enqoptions
    _verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)


def test_2706(queue):
    "2706 - test errors for invalid values for enqueue"
    book = queue.payload_type.newobject()
    pytest.raises(TypeError, queue.enqone, book)


def test_2707(conn):
    "2707 - test getting/setting message properties attributes"
    props = conn.msgproperties()
    _verify_attr(props, "correlation", "TEST_CORRELATION")
    _verify_attr(props, "delay", 60)
    _verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
    _verify_attr(props, "expiration", 30)
    assert props.attempts == 0
    _verify_attr(props, "priority", 1)
    assert props.state == oracledb.MSG_READY
    assert props.deliverymode == 0


def test_2708(conn, queue, book_data, test_env):
    "2708 - test enqueue visibility option - ENQ_ON_COMMIT"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
    props = conn.msgproperties(payload=book)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    books_type = other_conn.gettype(queue.payload_type.name)
    queue = other_conn.queue(queue.name, books_type)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props is None
    conn.commit()
    props = queue.deqone()
    other_conn.commit()
    assert props is not None


def test_2709(conn, queue, book_data, test_env):
    "2709 - test enqueue visibility option - ENQ_IMMEDIATE"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=book)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    books_type = other_conn.gettype(queue.payload_type.name)
    queue = other_conn.queue(queue.name, books_type)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    book = props.payload
    results = (book.TITLE, book.AUTHORS, book.PRICE)
    other_conn.commit()
    assert results == book_data[0]


def test_2710(conn, queue, book_data, test_env):
    "2710 - test enqueue/dequeue delivery modes identical - buffered"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=book)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    books_type = other_conn.gettype(queue.payload_type.name)
    queue = other_conn.queue(queue.name, books_type)
    queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props.deliverymode == oracledb.MSG_BUFFERED
    book = props.payload
    results = (book.TITLE, book.AUTHORS, book.PRICE)
    other_conn.commit()
    assert results == book_data[0]


def test_2711(conn, queue, book_data, test_env):
    "2711 - test enqueue/dequeue delivery modes identical - persistent"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=book)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    books_type = other_conn.gettype(queue.payload_type.name)
    queue = other_conn.queue(queue.name, books_type)
    queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props.deliverymode == oracledb.MSG_PERSISTENT
    book = props.payload
    results = (book.TITLE, book.AUTHORS, book.PRICE)
    other_conn.commit()
    assert results == book_data[0]


def test_2712(conn, queue, book_data, test_env):
    "2712 - test enqueue/dequeue delivery modes the same"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=book)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    books_type = other_conn.gettype(queue.payload_type.name)
    queue = other_conn.queue(queue.name, books_type)
    queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props.deliverymode == oracledb.MSG_PERSISTENT
    book = props.payload
    results = (book.TITLE, book.AUTHORS, book.PRICE)
    other_conn.commit()
    assert results == book_data[0]


def test_2713(conn, queue, book_data, test_env):
    "2713 - test enqueue/dequeue delivery modes different"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=book)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    books_type = other_conn.gettype(queue.payload_type.name)
    queue = other_conn.queue(queue.name, books_type)
    queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props is None


def test_2714(skip_unless_thick_mode, conn, queue, book_data, test_env):
    "2714 - test dequeue transformation"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    expected_price = book.PRICE + 10
    props = conn.msgproperties(payload=book)
    queue.enqone(props)
    conn.commit()

    other_conn = test_env.get_connection()
    books_type = other_conn.gettype(queue.payload_type.name)
    queue = other_conn.queue(queue.name, books_type)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    transformation_str = f"{conn.username}.transform2"
    queue.deqoptions.transformation = transformation_str
    assert queue.deqoptions.transformation == transformation_str
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props.payload.PRICE == expected_price


def test_2715(skip_unless_thick_mode, conn, queue, book_data, test_env):
    "2715 - test enqueue transformation"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    expected_price = book.PRICE + 5
    queue.enqoptions.transformation = transformation_str = (
        f"{conn.username}.transform1"
    )
    queue.enqoptions.transformation = transformation_str
    if test_env.has_client_version(23):
        assert queue.enqoptions.transformation == transformation_str
    props = conn.msgproperties(payload=book)
    queue.enqone(props)
    conn.commit()

    other_conn = test_env.get_connection()
    books_type = other_conn.gettype(queue.payload_type.name)
    queue = other_conn.queue(queue.name, books_type)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props.payload.PRICE == expected_price


def test_2716(conn, queue, test_env):
    "2716 - test to verify payloadType is deprecated"
    books_type = conn.gettype(queue.payload_type.name)
    assert queue.payload_type == books_type
    assert queue.payloadType == books_type
    with test_env.assert_raises_full_code("DPY-2014"):
        conn.queue(queue.name, books_type, payloadType=books_type)


def test_2717(conn, queue, test_env):
    "2717 - test error for message with no payload"
    props = conn.msgproperties()
    with test_env.assert_raises_full_code("DPY-2000"):
        queue.enqone(props)


def test_2718(conn, cursor, queue, book_data):
    "2718 - verify that the msgid property is returned correctly"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    props = conn.msgproperties(payload=book)
    assert props.msgid is None
    queue.enqone(props)
    cursor.execute("select msgid from book_queue_tab")
    (actual_msgid,) = cursor.fetchone()
    assert props.msgid == actual_msgid
    props = queue.deqone()
    assert props.msgid == actual_msgid


def test_2719(conn, queue, book_data):
    "2719 - verify use of recipients property"
    books_type = conn.gettype(queue.payload_type.name)
    book = books_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    queue = conn.queue("BOOK_QUEUE_MULTI", books_type)
    props = conn.msgproperties(payload=book, recipients=["sub2", "sub3"])
    assert props.recipients == ["sub2", "sub3"]
    queue.enqone(props)
    conn.commit()
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.consumername = "sub3"
    props1 = queue.deqone()
    book = props1.payload
    results = (book.TITLE, book.AUTHORS, book.PRICE)
    assert results == book_data[0]
    queue.deqoptions.consumername = "sub1"
    props1 = queue.deqone()
    assert props1 is None


def test_2720(skip_unless_thick_mode, conn, queue, book_data, test_env):
    "2720 - verify attributes of AQ message which spawned notification"
    if test_env.is_on_oracle_cloud:
        pytest.skip("AQ notification not supported on the cloud")
    condition = threading.Condition()
    other_conn = test_env.get_connection(events=True)

    def notification_callback(message=None, *args, **kwargs):
        cursor = conn.cursor()
        cursor.execute("select msgid from book_queue_tab")
        (actual_msgid,) = cursor.fetchone()
        assert message.msgid == actual_msgid
        assert message.consumer_name is None
        main_user = test_env.main_user.upper()
        assert message.queue_name == f'"{main_user}"."{queue.name}"'
        assert message.type == oracledb.EVENT_AQ
        with condition:
            condition.notify()

    sub = other_conn.subscribe(
        namespace=oracledb.SUBSCR_NAMESPACE_AQ,
        name=queue.name,
        timeout=300,
        callback=notification_callback,
    )
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    props = conn.msgproperties(payload=book)
    queue.enqone(props)
    conn.commit()
    with condition:
        assert condition.wait(5)
    other_conn.unsubscribe(sub)


def test_2721(conn, cursor, queue):
    "2721 - test message props enqtime"
    book = queue.payload_type.newobject()
    cursor.execute("select current_timestamp from dual")
    (start_date,) = cursor.fetchone()
    start_date = start_date.replace(microsecond=0)
    props = conn.msgproperties(payload=book)
    queue.enqone(props)
    props = queue.deqone()
    cursor.execute("select current_timestamp from dual")
    (end_date,) = cursor.fetchone()
    end_date = end_date.replace(microsecond=0)
    assert start_date <= props.enqtime <= end_date


def test_2722(conn, queue):
    "2722 - test message props declared attributes"
    book = queue.payload_type.newobject()
    values = dict(
        payload=book,
        correlation="TEST_CORRELATION",
        delay=7,
        exceptionq="TEST_EXCEPTIONQ",
        expiration=10,
        priority=1,
    )
    props = conn.msgproperties(**values)
    for attr_name in values:
        assert getattr(props, attr_name) == values[attr_name]


def test_2723(conn):
    "2723 - test error for invalid type for payload_type"
    pytest.raises(TypeError, conn.queue, "THE QUEUE", payload_type=4)


def test_2724(conn):
    "2724 - test setting bytes to payload"
    props = conn.msgproperties()
    bytes_val = b"Hello there"
    props.payload = bytes_val
    assert props.payload == bytes_val


def test_2725(conn, queue):
    "2725 - test getting queue attributes"
    other_queue = conn.queue(queue.name, queue.payload_type)
    assert other_queue.name == queue.name
    assert queue.connection is conn


def test_2726(queue):
    "2726 - test getting write-only attributes"
    with pytest.raises(AttributeError):
        queue.enqoptions.deliverymode
    with pytest.raises(AttributeError):
        queue.deqoptions.deliverymode


def test_2727(conn, queue, book_data, test_env):
    "2727 - test correlation deqoption"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    correlations = ["Math", "Programming"]
    num_messages = 3
    messages = [
        conn.msgproperties(payload=book, correlation=c)
        for c in correlations
        for i in range(num_messages)
    ]
    queue.enqmany(messages)
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.correlation = correlations[0]
    correlated_messages = queue.deqmany(num_messages + 1)
    assert len(correlated_messages) == num_messages

    queue.deqoptions.correlation = correlations[1]
    with test_env.assert_raises_full_code("ORA-25241"):
        queue.deqone()
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    correlated_messages = queue.deqmany(num_messages + 1)
    assert len(correlated_messages) == num_messages


def test_2728(conn, queue, book_data):
    "2728 - test correlation deqoption with pattern-matching characters"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    for correlation in ("PreCalculus-math1", "Calculus-Math2"):
        props = conn.msgproperties(payload=book, correlation=correlation)
        queue.enqone(props)
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.correlation = "%Calculus-%ath_"
    messages = queue.deqmany(5)
    assert len(messages) == 2


def test_2729(conn, queue, book_data):
    "2729 - test condition deqoption with priority"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT

    priorities = [5, 10]
    indexes = [0, 1]
    for priority, ix in zip(priorities, indexes):
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = book_data[ix]
        props = conn.msgproperties(payload=book, priority=priority)
        queue.enqone(props)

    queue.deqoptions.condition = "priority = 9"
    messages = queue.deqmany(3)
    assert len(messages) == 0

    for priority, ix in zip(priorities, indexes):
        queue.deqoptions.condition = f"priority = {priority}"
        messages = queue.deqmany(3)
        assert len(messages) == 1
        book = messages[0].payload
        data = book.TITLE, book.AUTHORS, book.PRICE
        assert data == book_data[ix]


def test_2730(conn, queue, book_data):
    "2730 - test mode deqoption with DEQ_REMOVE_NODATA"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA

    book = queue.payload_type.newobject()
    for data in book_data:
        book.TITLE, book.AUTHORS, book.PRICE = data
        props = conn.msgproperties(payload=book)
        queue.enqone(props)

    messages = queue.deqmany(5)
    assert len(messages) == 3
    for message in messages:
        assert message.payload.TITLE is None
        assert message.payload.AUTHORS is None
        assert message.payload.PRICE is None


def test_2731(conn, queue):
    "2731 - test payload_type returns the correct value"
    books_type = conn.gettype(queue.payload_type.name)
    other_queue = conn.queue(queue.name, books_type)
    assert other_queue.payload_type == books_type


def test_2732(queue):
    "2732 - test deprecated attributes (enqOptions, deqOptions)"
    assert queue.enqOptions == queue.enqoptions
    assert queue.deqOptions == queue.deqoptions


def test_2733(conn, queue, book_data):
    "2733 - test deprecated AQ methods (enqOne, deqOne)"
    book = queue.payload_type.newobject()
    book.TITLE, book.AUTHORS, book.PRICE = book_data[0]
    queue.enqOne(conn.msgproperties(book))
    props = queue.deqOne()
    book = props.payload
    results = (book.TITLE, book.AUTHORS, book.PRICE)
    assert results == book_data[0]


def test_2734(conn, queue, test_env):
    "2734 - test enqueuing to an object queue with the wrong payload"
    props = conn.msgproperties(payload="A string")
    with test_env.assert_raises_full_code("DPY-2062"):
        queue.enqone(props)
