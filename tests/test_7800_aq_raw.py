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
7800 - Module for testing AQ with raw queues
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


def test_7800(queue):
    "7800 - test dequeuing an empty RAW queue"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props is None


def test_7801(queue, conn):
    "7801 - test enqueuing and dequeuing multiple RAW messages"
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


def test_7802(queue, conn):
    "7802 - test dequeuing with DEQ_REMOVE_NODATA in RAW queue"
    value = RAW_DATA[1]
    props = conn.msgproperties(payload=value)
    queue.enqone(props)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
    props = queue.deqone()
    assert props is not None
    assert props.payload == b""


def test_7803(queue):
    "7803 - test getting/setting dequeue options attributes"
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


def test_7804(queue):
    "7804 - test enqueue options attributes RAW queue"
    options = queue.enqoptions
    _verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)


def test_7805(queue, conn, test_env):
    "7805 - test waiting for dequeue"
    results = []
    thread = threading.Thread(target=_deq_in_thread, args=(test_env, results))
    thread.start()
    value = RAW_DATA[0]
    props = conn.msgproperties(payload=value)
    queue.enqone(props)
    conn.commit()
    thread.join()
    assert results == [value]


def test_7806(conn):
    "7806 - test getting/setting message properties attributes"
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


def test_7807(queue, conn, test_env):
    "7807 - test enqueue visibility option - ENQ_ON_COMMIT"
    value = RAW_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    queue = other_conn.queue("TEST_RAW_QUEUE")
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props is None
    conn.commit()
    props = queue.deqone()
    assert props is not None


def test_7808(queue, conn, test_env):
    "7808 - test enqueue visibility option - ENQ_IMMEDIATE"
    value = RAW_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    queue = other_conn.queue("TEST_RAW_QUEUE")
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    value = props.payload
    results = value
    other_conn.commit()
    assert results == RAW_DATA[0]


def test_7809(queue, conn, test_env):
    "7809 - test enqueue/dequeue delivery modes identical - buffered"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    other_conn = test_env.get_connection()
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


def test_7810(queue, conn, test_env):
    "7810 - test enqueue/dequeue delivery modes identical - persistent"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    other_conn = test_env.get_connection()
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


def test_7811(queue, conn, test_env):
    "7811 - test enqueue/dequeue delivery modes the same"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    other_conn = test_env.get_connection()
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


def test_7812(queue, conn, test_env):
    "7812 - test enqueue/dequeue delivery modes different"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=value)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    queue = other_conn.queue("TEST_RAW_QUEUE")
    queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props is None


def test_7813(queue, conn, test_env):
    "7813 - test error for message with no payload"
    props = conn.msgproperties()
    with test_env.assert_raises_full_code("DPY-2000"):
        queue.enqone(props)


def test_7814(queue, conn, cursor):
    "7814 - verify that the msgid property is returned correctly"
    value = RAW_DATA[0]
    props = conn.msgproperties(payload=value)
    assert props.msgid is None
    queue.enqone(props)
    cursor.execute("select msgid from RAW_QUEUE_TAB")
    (actual_msgid,) = cursor.fetchone()
    assert props.msgid == actual_msgid
    props = queue.deqone()
    assert props.msgid == actual_msgid


def test_7815(queue, conn, cursor):
    "7815 - test message props enqtime"
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


def test_7816(queue, conn):
    "7816 - test message props declared attributes"
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


def test_7817(queue, conn):
    "7817 - test getting queue attributes"
    assert queue.name == "TEST_RAW_QUEUE"
    assert queue.connection is conn


def test_7818(queue):
    "7818 - test getting write-only attributes"
    for options in (queue.enqoptions, queue.deqoptions):
        with pytest.raises(AttributeError):
            options.deliverymode


def test_7819(queue, conn):
    "7819 - test deqoption condition with priority"
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


def test_7820(queue, conn):
    "7820 - test deqoption correlation"
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


def test_7821(queue, conn):
    "7821 - test deqoption msgid"
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


def test_7822(queue):
    "7822 - test payload_type returns the correct value"
    assert queue.payload_type is None


def test_7823(queue):
    "7823 - test deprecated attributes (enqOptions, deqOptions)"
    assert queue.enqOptions is queue.enqoptions
    assert queue.deqOptions is queue.deqoptions


def test_7824(queue, conn):
    "7824 - test deprecated AQ methods (enqOne, deqOne)"
    value = b"Test 7823"
    queue.enqOne(conn.msgproperties(value))
    props = queue.deqOne()
    assert props.payload == value


def test_7825(queue, conn, test_env):
    "7825 - test wrong payload type"
    typ = conn.gettype("UDT_BOOK")
    obj = typ.newobject()
    props = conn.msgproperties(payload=obj)
    with test_env.assert_raises_full_code("DPY-2062"):
        queue.enqone(props)


def test_7826(queue):
    "7826 - test providing null values on queue dequeue options"
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


def test_7827(queue):
    "7827 - test providing null values on queue enqueue options"
    value = "test - 7827"
    for name in ["transformation"]:
        setattr(queue.enqoptions, name, value)
        assert getattr(queue.enqoptions, name) == value
        setattr(queue.enqoptions, name, None)
        assert getattr(queue.enqoptions, name) is None


def test_7828(conn):
    "7828 - test providing null correlation on message properties"
    props = conn.msgproperties()
    value = "test - 7828"
    for name in ["correlation", "exceptionq"]:
        setattr(props, name, value)
        assert getattr(props, name) == value
        setattr(props, name, None)
        assert getattr(props, name) is None


def test_7829(queue, conn):
    "7829 - test deq options correlation with buffered messages"
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


def test_7830(queue, test_env):
    "7830 - test deq options with msgid > 16 bytes"
    queue.deqoptions.msgid = b"invalid_msgid_123456789"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    with test_env.assert_raises_full_code("ORA-25263"):
        queue.deqone()


def test_7831(queue, test_env):
    "7831 - test deq options with msgid < 16 bytes"
    queue.deqoptions.msgid = b"short_msgid"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    with test_env.assert_raises_full_code("ORA-25263"):
        queue.deqone()
