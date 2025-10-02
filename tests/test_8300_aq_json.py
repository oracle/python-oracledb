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
8300 - Module for testing AQ with JSON queues
"""

import datetime
import decimal
import threading

import oracledb
import pytest


JSON_QUEUE_NAME = "TEST_JSON_QUEUE"
JSON_DATA = [
    [
        2.75,
        True,
        "Ocean Beach",
        b"Some bytes",
        {"keyA": 1.0, "KeyB": "Melbourne"},
        datetime.datetime(2022, 8, 1, 0, 0),
    ],
    [
        True,
        False,
        "String",
        b"Some Bytes",
        {},
        {"name": None},
        {"name": "John"},
        {"age": 30},
        {"Permanent": True},
        {
            "employee": {
                "name": "John",
                "age": 30,
                "city": "Delhi",
                "Parmanent": True,
            }
        },
        {"employees": ["John", "Matthew", "James"]},
        {
            "employees": [
                {"employee1": {"name": "John", "city": "Delhi"}},
                {"employee2": {"name": "Matthew", "city": "Mumbai"}},
                {"employee3": {"name": "James", "city": "Bangalore"}},
            ]
        },
    ],
    [
        datetime.datetime.today(),
        datetime.datetime(2004, 2, 1, 3, 4, 5),
        datetime.datetime(2020, 12, 2, 13, 29, 14),
        datetime.timedelta(8.5),
        datetime.datetime(2002, 12, 13, 9, 36, 0),
        oracledb.Timestamp(2002, 12, 13, 9, 36, 0),
        datetime.datetime(2002, 12, 13),
    ],
    dict(name="John", age=30, city="New York"),
    [
        0,
        1,
        25.25,
        6088343244,
        -9999999999999999999,
        decimal.Decimal("0.25"),
        decimal.Decimal("10.25"),
        decimal.Decimal("319438950232418390.273596"),
    ],
]


@pytest.fixture
def queue(conn, test_env):
    """
    Creates the queue used by the tests in this file.
    """
    return test_env.get_and_clear_queue(conn, JSON_QUEUE_NAME, "JSON")


def _deq_in_thread(test_env, results):
    with test_env.get_connection() as conn:
        queue = conn.queue(JSON_QUEUE_NAME, "JSON")
        queue.deqoptions.wait = 10
        props = queue.deqone()
        if props is not None:
            results.append(props.payload)
        conn.commit()


def _verify_attr(obj, attrName, value):
    setattr(obj, attrName, value)
    assert getattr(obj, attrName) == value


def test_8300(queue):
    "8300 - test dequeuing an empty JSON queue"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props is None


def test_8301(queue, conn):
    "8301 - test enqueuing and dequeuing multiple JSON messages"
    props = conn.msgproperties()
    for data in JSON_DATA:
        props.payload = data
        queue.enqone(props)
    conn.commit()
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    results = []
    while True:
        props = queue.deqone()
        if props is None:
            break
        results.append(props.payload)
    conn.commit()
    assert results == JSON_DATA


@pytest.mark.skip("awaiting fix for bug 37746852")
def test_8302(queue, conn):
    "8302 - test dequeuing with DEQ_REMOVE_NODATA option"
    data = JSON_DATA[1]
    props = conn.msgproperties(payload=data)
    queue.enqone(props)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
    props = queue.deqone()
    assert props is not None
    assert props.payload is None


def test_8303(queue):
    "8303 - test getting/setting dequeue options attributes"
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


def test_8304(queue, conn, test_env):
    "8304 - test waiting for dequeue"
    results = []
    thread = threading.Thread(target=_deq_in_thread, args=(test_env, results))
    thread.start()
    data = JSON_DATA[0]
    props = conn.msgproperties(payload=data)
    queue.enqone(props)
    conn.commit()
    thread.join()
    assert results == [data]


def test_8305(queue):
    "8305 - test getting/setting enqueue options attributes"
    options = queue.enqoptions
    _verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)


def test_8306(conn):
    "8306 - test getting/setting message properties attributes"
    props = conn.msgproperties()
    _verify_attr(props, "correlation", "TEST_CORRELATION")
    _verify_attr(props, "delay", 60)
    _verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
    _verify_attr(props, "expiration", 30)
    assert props.attempts == 0
    _verify_attr(props, "priority", 1)
    assert props.state == oracledb.MSG_READY
    assert props.deliverymode == 0


def test_8307(queue, conn, test_env):
    "8307 - test enqueue visibility options - ENQ_ON_COMMIT"
    data = JSON_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
    props = conn.msgproperties(payload=data)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    queue = other_conn.queue(JSON_QUEUE_NAME, "JSON")
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    assert props is None
    conn.commit()
    props = queue.deqone()
    assert props is not None


def test_8308(queue, conn, test_env):
    "8308 - test enqueue visibility option - ENQ_IMMEDIATE"
    data = JSON_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=data)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    queue = other_conn.queue(JSON_QUEUE_NAME, "JSON")
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    data = props.payload
    results = data
    other_conn.commit()
    assert results == JSON_DATA[0]


def test_8309(queue, conn, test_env):
    "8309 - test enqueue/dequeue delivery modes identical - persistent"
    data = JSON_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = conn.msgproperties(payload=data)
    queue.enqone(props)

    other_conn = test_env.get_connection()
    queue = other_conn.queue(JSON_QUEUE_NAME, "JSON")
    queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = queue.deqone()
    data = props.payload
    results = data
    other_conn.commit()
    assert results == JSON_DATA[0]


def test_8310(queue, conn, test_env):
    "8310 - test error for message with no payload"
    props = conn.msgproperties()
    with test_env.assert_raises_full_code("DPY-2000"):
        queue.enqone(props)


def test_8311(queue, conn, cursor):
    "8311 - verify that the msgid property is returned correctly"
    data = JSON_DATA[0]
    props = conn.msgproperties(payload=data)
    assert props.msgid is None
    queue.enqone(props)
    cursor.execute("select msgid from JSON_QUEUE_TAB")
    (actual_msgid,) = cursor.fetchone()
    assert props.msgid == actual_msgid
    props = queue.deqone()
    assert props.msgid == actual_msgid


def test_8312(queue, conn, cursor):
    "8312 - test message props enqtime"
    data = JSON_DATA[0]
    cursor.execute("select current_timestamp from dual")
    (start_date,) = cursor.fetchone()
    start_date = start_date.replace(microsecond=0)
    props = conn.msgproperties(payload=data)
    queue.enqone(props)
    props = queue.deqone()
    cursor.execute("select current_timestamp from dual")
    (end_date,) = cursor.fetchone()
    end_date = end_date.replace(microsecond=0)
    assert start_date <= props.enqtime <= end_date


def test_8313(queue, conn):
    "8313 - test message props declared attributes"
    data = JSON_DATA[0]
    values = dict(
        payload=data,
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


def test_8314(queue, conn):
    "8314 - test getting queue attributes"
    assert queue.name == "TEST_JSON_QUEUE"
    assert queue.connection is conn


def test_8315(queue):
    "8315 - test getting write-only attributes"
    for options in (queue.enqoptions, queue.deqoptions):
        with pytest.raises(AttributeError):
            options.deliverymode


def test_8316(queue, conn):
    "8316 - test deqoption condition with priority"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    priorities = [5, 5, 5, 5, 10, 9, 9, 10, 9]
    for priority in priorities:
        data = JSON_DATA[0]
        props = conn.msgproperties(payload=data, priority=priority)
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


def test_8317(queue, conn):
    "8317 - test deqoption correlation"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    correlations = [
        "sample",
        "sample correlation",
        "sample",
        "sample",
        "sample correlation",
    ]
    for correlation in correlations:
        data = JSON_DATA[0]
        props = conn.msgproperties(payload=data, correlation=correlation)
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


def test_8318(queue, conn):
    "8318 - test deqoption msgid"
    data = JSON_DATA[0]
    props = conn.msgproperties(payload=data)
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


def test_8319(queue):
    "8319 - test payload_type returns the correct value"
    assert queue.payload_type == "JSON"


def test_8320(queue):
    "8320 - test deprecated attributes (enqOptions, deqOptions)"
    assert queue.enqOptions is queue.enqoptions
    assert queue.deqOptions is queue.deqoptions


def test_8321(queue, conn):
    "8321 - test deprecated AQ methods (enqOne, deqOne)"
    data = JSON_DATA[0]
    queue.enqOne(conn.msgproperties(payload=data))
    props = queue.deqOne()
    assert props.payload == data


def test_8322(queue, conn, test_env):
    "8322 - test wrong payload type"
    props = conn.msgproperties(payload="A string")
    with test_env.assert_raises_full_code("DPY-2062"):
        queue.enqone(props)
