# -----------------------------------------------------------------------------
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
Module for testing AQ with raw queues
"""

import threading

import oracledb
import pytest

RAW_DATA = [
    b"sample raw data 1",
    b"sample raw data 2",
    b"sample raw data 3",
    b"sample raw data 4",
    b"sample raw data 5",
    b"sample raw data 6",
]


@pytest.fixture
def queue(conn, test_env):
    """
    Creates the queue used by the tests in this file.
    """
    return test_env.get_and_clear_queue(conn, "TEST_RAW_QUEUE")


def _deq_in_thread(test_env, results):
    with test_env.get_connection() as conn:
        queue = conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.wait = 10
        props = queue.deqone()
        if props is not None:
            results.append(props.payload)
        conn.commit()


def _verify_attr(obj, attrName, value):
    setattr(obj, attrName, value)
    assert getattr(obj, attrName) == value


def test_1400(queue):
    "1400 - test dequeuing an empty RAW queue"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props is None


def test_1401(queue, conn):
    "1401 - test enqueuing and dequeuing multiple RAW messages"
    props = conn.msgproperties()
    for value in RAW_DATA:
        props.payload = value
        queue.enqone(props)
    conn.commit()
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    results = []
    while True:
        props = queue.deqone()
        if props is None:
            break
        value = props.payload
        results.append(value)
    conn.commit()
    assert results == RAW_DATA


def test_1402(queue, conn):
    "1402 - test dequeuing with DEQ_REMOVE_NODATA in RAW queue"
    value = RAW_DATA[1]
    props = conn.msgproperties(payload=value)
    queue.enqone(props)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
    props = queue.deqone()
    assert props is not None
    assert props.payload == b""


def test_1403(queue):
    "1403 - test getting/setting dequeue options attributes"
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


def test_1404(queue):
    "1404 - test enqueue options attributes RAW queue"
    options = queue.enqoptions
    _verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)


def test_1405(queue, conn, test_env):
    "1405 - test waiting for dequeue"
    results = []
    thread = threading.Thread(target=_deq_in_thread, args=(test_env, results))
    thread.start()
    value = RAW_DATA[0]
    props = conn.msgproperties(payload=value)
    queue.enqone(props)
    conn.commit()
    thread.join()
    assert results == [value]


def test_1406(conn):
    "1406 - test getting/setting message properties attributes"
    props = conn.msgproperties()
    _verify_attr(props, "correlation", "TEST_CORRELATION")
    _verify_attr(props, "delay", 60)
    _verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
    _verify_attr(props, "expiration", 30)
    assert props.attempts == 0
    _verify_attr(props, "priority", 1)
    assert props.state == oracledb.MSG_READY
    assert props.deliverymode == 0
    assert props.enqtime is None


def test_1407(queue, conn, test_env):
    "1407 - test enqueue visibility option - ENQ_ON_COMMIT"
    value = RAW_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    with test_env.get_connection() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        assert props is None
        conn.commit()
        props = queue.deqone()
        assert props is not None


def test_1408(queue, conn, test_env):
    "1408 - test enqueue visibility option - ENQ_IMMEDIATE"
    value = RAW_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    with test_env.get_connection() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        value = props.payload
        results = value
        other_conn.commit()
        assert results == RAW_DATA[0]


def test_1409(queue, conn, test_env):
    "1409 - test enqueue/dequeue delivery modes identical - buffered"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    with test_env.get_connection() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        value = props.payload
        results = value
        other_conn.commit()
        assert results == RAW_DATA[0]
        assert props.deliverymode == oracledb.MSG_BUFFERED


def test_1410(queue, conn, test_env):
    "1410 - test enqueue/dequeue delivery modes identical - persistent"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    with test_env.get_connection() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        value = props.payload
        results = value
        other_conn.commit()
        assert results == RAW_DATA[0]
        assert props.deliverymode == oracledb.MSG_PERSISTENT


def test_1411(queue, conn, test_env):
    "1411 - test enqueue/dequeue delivery modes the same"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    with test_env.get_connection() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        value = props.payload
        results = value
        other_conn.commit()
        assert results == RAW_DATA[0]


def test_1412(queue, conn, test_env):
    "1412 - test enqueue/dequeue delivery modes different"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    with test_env.get_connection() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        assert props is None


def test_1413(queue, conn, test_env):
    "1413 - test error for message with no payload"
    props = conn.msgproperties()
    with test_env.assert_raises_full_code("DPY-2000"):
        queue.enqone(props)


def test_1414(queue, conn, cursor):
    "1414 - verify that the msgid property is returned correctly"
    value = RAW_DATA[0]
    props = conn.msgproperties(payload=value)
    assert props.msgid is None
    queue.enqone(props)
    cursor.execute("select msgid from RAW_QUEUE_TAB")
    (actual_msgid,) = cursor.fetchone()
    assert props.msgid == actual_msgid
    props = queue.deqone()
    assert props.msgid == actual_msgid


def test_1415(queue, conn, cursor):
    "1415 - test message props enqtime"
    value = RAW_DATA[0]
    cursor.execute("select current_timestamp from dual")
    (start_date,) = cursor.fetchone()
    start_date = start_date.replace(microsecond=0)
    props = conn.msgproperties(payload=value)
    queue.enqone(props)
    props = queue.deqone()
    cursor.execute("select current_timestamp from dual")
    (end_date,) = cursor.fetchone()
    end_date = end_date.replace(microsecond=0)
    assert start_date <= props.enqtime <= end_date


def test_1416(queue, conn):
    "1416 - test message props declared attributes"
    value = RAW_DATA[0]
    values = dict(
        payload=value,
        correlation="TEST_CORRELATION",
        delay=0,
        exceptionq="PYTHONTEST.TEST_EXCEPTIONQ",
        expiration=15,
        priority=1,
    )
    props = conn.msgproperties(**values)
    for attr_name in values:
        assert getattr(props, attr_name) == values[attr_name]
    queue.enqone(props)
    conn.commit()
    prop = queue.deqone()
    for attr_name in values:
        assert getattr(prop, attr_name) == values[attr_name]


def test_1417(queue, conn):
    "1417 - test getting queue attributes"
    assert queue.name == "TEST_RAW_QUEUE"
    assert queue.connection is conn


def test_1418(queue):
    "1418 - test getting write-only attributes"
    for options in (queue.enqoptions, queue.deqoptions):
        with pytest.raises(AttributeError):
            options.deliverymode


def test_1419(queue, conn):
    "1419 - test deqoption condition with priority"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    priorities = [5, 5, 5, 5, 10, 9, 9, 10, 9]
    for priority in priorities:
        value = RAW_DATA[0]
        props = conn.msgproperties(payload=value, priority=priority)
        queue.enqone(props)

    queue.deqoptions.condition = "priority = 9"
    results = []
    while True:
        props = queue.deqone()
        if props is None:
            break
        results.append(props.payload)
    conn.commit()
    assert len(results) == 3


def test_1420(queue, conn):
    "1420 - test deqoption correlation"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    correlations = [
        "sample",
        "sample correlation",
        "sample",
        "sample",
        "sample correlation",
    ]
    for correlation in correlations:
        value = RAW_DATA[0]
        props = conn.msgproperties(payload=value, correlation=correlation)
        queue.enqone(props)
    conn.commit()
    queue.deqoptions.correlation = "sample correlation"
    results = []
    while True:
        props = queue.deqone()
        if props is None:
            break
        results.append(props.payload)
    conn.commit()
    assert len(results) == 2


def test_1421(queue, conn):
    "1421 - test deqoption msgid"
    value = RAW_DATA[0]
    props = conn.msgproperties(payload=value)
    queue.enqone(props)
    queue.enqone(props)
    conn.commit()
    msgid = props.msgid
    queue.enqone(props)
    conn.commit()
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.msgid = msgid
    prop = queue.deqone()
    conn.commit()
    assert prop.msgid == msgid


def test_1422(queue):
    "1422 - test payload_type returns the correct value"
    assert queue.payload_type is None


def test_1423(queue):
    "1423 - test deprecated attributes (enqOptions, deqOptions)"
    assert queue.enqOptions is queue.enqoptions
    assert queue.deqOptions is queue.deqoptions


def test_1424(queue, conn):
    "1424 - test deprecated AQ methods (enqOne, deqOne)"
    value = b"Test 7823"
    queue.enqOne(conn.msgproperties(value))
    props = queue.deqOne()
    assert props.payload == value


def test_1425(queue, conn, test_env):
    "1425 - test wrong payload type"
    typ = conn.gettype("UDT_BOOK")
    obj = typ.newobject()
    props = conn.msgproperties(payload=obj)
    with test_env.assert_raises_full_code("DPY-2062"):
        queue.enqone(props)


def test_1426(queue):
    "1426 - test providing null values on queue dequeue options"
    str_value = "test - 7826"
    bytes_value = str_value.encode()
    for name in [
        "condition",
        "consumername",
        "correlation",
        "msgid",
        "transformation",
    ]:
        value = bytes_value if name == "msgid" else str_value
        setattr(queue.deqoptions, name, value)
        assert getattr(queue.deqoptions, name) == value
        setattr(queue.deqoptions, name, None)
        assert getattr(queue.deqoptions, name) is None


def test_1427(queue):
    "1427 - test providing null values on queue enqueue options"
    value = "test - 7827"
    for name in ["transformation"]:
        setattr(queue.enqoptions, name, value)
        assert getattr(queue.enqoptions, name) == value
        setattr(queue.enqoptions, name, None)
        assert getattr(queue.enqoptions, name) is None


def test_1428(conn):
    "1428 - test providing null correlation on message properties"
    props = conn.msgproperties()
    value = "test - 7828"
    for name in ["correlation", "exceptionq"]:
        setattr(props, name, value)
        assert getattr(props, name) == value
        setattr(props, name, None)
        assert getattr(props, name) is None


def test_1429(queue, conn):
    "1429 - test deq options correlation with buffered messages"
    value = RAW_DATA[0]
    props = conn.msgproperties(payload=value, correlation="sample")
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqone(props)
    conn.commit()
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.correlation = "sample"
    msg = queue.deqone()
    conn.commit()
    assert msg.payload == value


def test_1430(queue, test_env):
    "1430 - test deq options with msgid > 16 bytes"
    queue.deqoptions.msgid = b"invalid_msgid_123456789"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    with test_env.assert_raises_full_code("ORA-25263"):
        queue.deqone()


def test_1431(queue, test_env):
    "1431 - test deq options with msgid < 16 bytes"
    queue.deqoptions.msgid = b"short_msgid"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    with test_env.assert_raises_full_code("ORA-25263"):
        queue.deqone()


def test_1432(queue, test_env):
    "1432 - test enqueue/dequeue options attributes maximum lengths"
    consumer_name = "€" * 10
    correlation = "€" * 42 + "XX"
    transformation = "€" * 20 + "X"
    queue.deqoptions.consumername = consumer_name
    queue.deqoptions.correlation = correlation
    queue.deqoptions.transformation = transformation
    queue.enqoptions.transformation = transformation
    with test_env.assert_raises_full_code("DPY-2075"):
        queue.deqoptions.consumername = consumer_name + "X"
    with test_env.assert_raises_full_code("DPY-2075"):
        queue.deqoptions.correlation = correlation + "X"
    with test_env.assert_raises_full_code("DPY-2075"):
        queue.deqoptions.transformation = transformation + "X"
    with test_env.assert_raises_full_code("DPY-2075"):
        queue.enqoptions.transformation = transformation + "X"


def test_1433(conn, test_env):
    "1433 - test message properties attributes maximum lengths"
    props = conn.msgproperties()
    correlation = "€" * 42 + "XX"
    exceptionq = "€" * 17
    recipient = "€" * 10
    props.correlation = correlation
    props.exceptionq = exceptionq
    props.recipients = [recipient]
    with test_env.assert_raises_full_code("DPY-2075"):
        props.correlation = correlation + "X"
    with test_env.assert_raises_full_code("DPY-2075"):
        props.exceptionq = exceptionq + "X"
    with test_env.assert_raises_full_code("DPY-2075"):
        props.recipients = [recipient + "X"]
