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
8500 - Module for testing AQ with JSON queues with asyncio
"""

import asyncio
import datetime
import decimal

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


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


@pytest.fixture
async def queue(async_conn, test_env):
    """
    Creates the queue used by the tests in this file.
    """
    return await test_env.get_and_clear_queue_async(
        async_conn, JSON_QUEUE_NAME, "JSON"
    )


async def _deq_in_task(test_env, results):
    async with test_env.get_connection_async() as conn:
        queue = conn.queue(JSON_QUEUE_NAME, "JSON")
        queue.deqoptions.wait = 10
        props = await queue.deqone()
        if props is not None:
            results.append(props.payload)
        await conn.commit()


def _verify_attr(obj, attrName, value):
    setattr(obj, attrName, value)
    assert getattr(obj, attrName) == value


async def test_8500(queue):
    "8500 - test dequeuing an empty JSON queue"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = await queue.deqone()
    assert props is None


async def test_8501(queue, async_conn):
    "8501 - test enqueuing and dequeuing multiple JSON messages"
    props = async_conn.msgproperties()
    for data in JSON_DATA:
        props.payload = data
        await queue.enqone(props)
    await async_conn.commit()
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    results = []
    while True:
        props = await queue.deqone()
        if props is None:
            break
        results.append(props.payload)
    await async_conn.commit()
    assert results == JSON_DATA


@pytest.mark.skip("awaiting fix for bug 37746852")
async def test_8502(queue, async_conn):
    "8502 - test dequeuing with DEQ_REMOVE_NODATA option"
    data = JSON_DATA[1]
    props = async_conn.msgproperties(payload=data)
    await queue.enqone(props)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
    props = await queue.deqone()
    assert props is not None
    assert props.payload is None


async def test_8503(queue):
    "8503 - test getting/setting dequeue options attributes"
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


async def test_8504(queue, async_conn, test_env):
    "8504 - test waiting for dequeue"
    results = []
    task = asyncio.create_task(_deq_in_task(test_env, results))
    data = JSON_DATA[0]
    props = async_conn.msgproperties(payload=data)
    await queue.enqone(props)
    await async_conn.commit()
    await task
    assert results == [data]


async def test_8505(queue):
    "8505 - test getting/setting enqueue options attributes"
    options = queue.enqoptions
    _verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)


async def test_8506(async_conn):
    "8506 - test getting/setting message properties attributes"
    props = async_conn.msgproperties()
    _verify_attr(props, "correlation", "TEST_CORRELATION")
    _verify_attr(props, "delay", 60)
    _verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
    _verify_attr(props, "expiration", 30)
    assert props.attempts == 0
    _verify_attr(props, "priority", 1)
    assert props.state == oracledb.MSG_READY
    assert props.deliverymode == 0


async def test_8507(queue, async_conn, test_env):
    "8507 - test enqueue visibility options - ENQ_ON_COMMIT"
    data = JSON_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
    props = async_conn.msgproperties(payload=data)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        queue = other_conn.queue(JSON_QUEUE_NAME, "JSON")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        assert props is None
        await async_conn.commit()
        props = await queue.deqone()
        assert props is not None


async def test_8508(queue, async_conn, test_env):
    "8508 - test enqueue visibility option - ENQ_IMMEDIATE"
    data = JSON_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=data)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        queue = other_conn.queue(JSON_QUEUE_NAME, "JSON")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        data = props.payload
        results = data
        await other_conn.commit()
        assert results == JSON_DATA[0]


async def test_8509(queue, async_conn, test_env):
    "8509 - test enqueue/dequeue delivery modes identical - persistent"
    data = JSON_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=data)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        queue = other_conn.queue(JSON_QUEUE_NAME, "JSON")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        data = props.payload
        results = data
        await other_conn.commit()
        assert results == JSON_DATA[0]


async def test_8510(queue, async_conn, test_env):
    "8510 - test error for message with no payload"
    props = async_conn.msgproperties()
    with test_env.assert_raises_full_code("DPY-2000"):
        await queue.enqone(props)


async def test_8511(queue, async_conn, async_cursor):
    "8511 - verify that the msgid property is returned correctly"
    data = JSON_DATA[0]
    props = async_conn.msgproperties(payload=data)
    assert props.msgid is None
    await queue.enqone(props)
    await async_cursor.execute("select msgid from JSON_QUEUE_TAB")
    (actual_msgid,) = await async_cursor.fetchone()
    assert props.msgid == actual_msgid
    props = await queue.deqone()
    assert props.msgid == actual_msgid


async def test_8512(queue, async_conn, async_cursor):
    "8512 - test message props enqtime"
    data = JSON_DATA[0]
    await async_cursor.execute("select current_timestamp from dual")
    (start_date,) = await async_cursor.fetchone()
    start_date = start_date.replace(microsecond=0)
    props = async_conn.msgproperties(payload=data)
    await queue.enqone(props)
    props = await queue.deqone()
    await async_cursor.execute("select current_timestamp from dual")
    (end_date,) = await async_cursor.fetchone()
    end_date = end_date.replace(microsecond=0)
    assert start_date <= props.enqtime <= end_date


async def test_8513(queue, async_conn):
    "8513 - test message props declared attributes"
    data = JSON_DATA[0]
    values = dict(
        payload=data,
        correlation="TEST_CORRELATION",
        delay=0,
        exceptionq="PYTHONTEST.TEST_EXCEPTIONQ",
        expiration=15,
        priority=1,
    )
    props = async_conn.msgproperties(**values)
    for attr_name in values:
        assert getattr(props, attr_name) == values[attr_name]
    await queue.enqone(props)
    await async_conn.commit()
    prop = await queue.deqone()
    for attr_name in values:
        assert getattr(prop, attr_name) == values[attr_name]


async def test_8514(queue, async_conn):
    "8514 - test getting queue attributes"
    assert queue.name == "TEST_JSON_QUEUE"
    assert queue.connection is async_conn


async def test_8515(queue):
    "8515 - test getting write-only attributes"
    for options in (queue.enqoptions, queue.deqoptions):
        with pytest.raises(AttributeError):
            options.deliverymode


async def test_8516(queue, async_conn):
    "8516 - test deqoption condition with priority"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    priorities = [5, 5, 5, 5, 10, 9, 9, 10, 9]
    for priority in priorities:
        data = JSON_DATA[0]
        props = async_conn.msgproperties(payload=data, priority=priority)
        await queue.enqone(props)

    queue.deqoptions.condition = "priority = 9"
    results = []
    while True:
        props = await queue.deqone()
        if props is None:
            break
        results.append(props.payload)
    await async_conn.commit()
    assert len(results) == 3


async def test_8517(queue, async_conn):
    "8517 - test deqoption correlation"
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
        props = async_conn.msgproperties(payload=data, correlation=correlation)
        await queue.enqone(props)
    await async_conn.commit()
    queue.deqoptions.correlation = "sample correlation"
    results = []
    while True:
        props = await queue.deqone()
        if props is None:
            break
        results.append(props.payload)
    await async_conn.commit()
    assert len(results) == 2


async def test_8518(queue, async_conn):
    "8518 - test deqoption msgid"
    data = JSON_DATA[0]
    props = async_conn.msgproperties(payload=data)
    await queue.enqone(props)
    await queue.enqone(props)
    await async_conn.commit()
    msgid = props.msgid
    await queue.enqone(props)
    await async_conn.commit()
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.msgid = msgid
    prop = await queue.deqone()
    await async_conn.commit()
    assert prop.msgid == msgid


async def test_8519(queue):
    "8519 - test payload_type returns the correct value"
    assert queue.payload_type == "JSON"


async def test_8520(queue):
    "8520 - test deprecated attributes (enqOptions, deqOptions)"
    assert queue.enqOptions is queue.enqoptions
    assert queue.deqOptions is queue.deqoptions


async def test_8521(queue, async_conn, test_env):
    "8521 - test wrong payload type"
    props = async_conn.msgproperties(payload="A string")
    with test_env.assert_raises_full_code("DPY-2062"):
        await queue.enqone(props)
