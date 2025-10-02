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
7900 - Module for testing AQ with raw queues with asyncio
"""

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


@pytest.fixture
async def queue(async_conn, test_env):
    """
    Creates the queue used by the tests in this file.
    """
    return await test_env.get_and_clear_queue_async(
        async_conn, "TEST_RAW_QUEUE"
    )


RAW_DATA = [
    b"sample raw data 1",
    b"sample raw data 2",
    b"sample raw data 3",
    b"sample raw data 4",
    b"sample raw data 5",
    b"sample raw data 6",
]


def _verify_attr(obj, attrName, value):
    setattr(obj, attrName, value)
    assert getattr(obj, attrName) == value


async def test_7900(queue):
    "7900 - test dequeuing an empty RAW queue"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    props = await queue.deqone()
    assert props is None


async def test_7901(async_conn, queue):
    "7901 - test enqueuing and dequeuing multiple RAW messages"
    props = async_conn.msgproperties()
    for value in RAW_DATA:
        props.payload = value
        await queue.enqone(props)
    await async_conn.commit()
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    results = []
    while True:
        props = await queue.deqone()
        if props is None:
            break
        value = props.payload
        results.append(value)
    await async_conn.commit()
    assert results == RAW_DATA


async def test_7902(async_conn, queue):
    "7902 - test dequeuing with DEQ_REMOVE_NODATA in RAW queue"
    value = RAW_DATA[1]
    props = async_conn.msgproperties(payload=value)
    await queue.enqone(props)
    queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
    props = await queue.deqone()
    assert props is not None
    assert props.payload == b""


async def test_7903(queue):
    "7903 - test getting/setting dequeue options attributes"
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


async def test_7904(queue):
    "7904 - test enqueue options attributes RAW queue"
    options = queue.enqoptions
    _verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)


async def test_7905(queue):
    "7905 - test errors for invalid values for enqueue"
    value = RAW_DATA[0]
    with pytest.raises(TypeError):
        await queue.enqone(value)


async def test_7906(async_conn):
    "7906 - test getting/setting message properties attributes"
    props = async_conn.msgproperties()
    _verify_attr(props, "correlation", "TEST_CORRELATION")
    _verify_attr(props, "delay", 60)
    _verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
    _verify_attr(props, "expiration", 30)
    assert props.attempts == 0
    _verify_attr(props, "priority", 1)
    assert props.state == oracledb.MSG_READY
    assert props.deliverymode == 0


async def test_7907(async_conn, queue, test_env):
    "7907 - test enqueue visibility option - ENQ_ON_COMMIT"
    value = RAW_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
    props = async_conn.msgproperties(payload=value)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        assert props is None
        await async_conn.commit()
        props = await queue.deqone()
        assert props is not None


async def test_7908(queue, async_conn, test_env):
    "7908 - test enqueue visibility option - ENQ_IMMEDIATE"
    value = RAW_DATA[0]
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=value)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        value = props.payload
        results = value
        await other_conn.commit()
        assert results == RAW_DATA[0]


async def test_7909(queue, async_conn, test_env):
    "7909 - test enqueue/dequeue delivery modes identical - buffered"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=value)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        value = props.payload
        results = value
        await other_conn.commit()
        assert results == RAW_DATA[0]
        assert props.deliverymode == oracledb.MSG_BUFFERED


async def test_7910(queue, async_conn, test_env):
    "7910 - test enqueue/dequeue delivery modes identical - persistent"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=value)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        value = props.payload
        results = value
        await other_conn.commit()
        assert results == RAW_DATA[0]
        assert props.deliverymode == oracledb.MSG_PERSISTENT


async def test_7911(queue, async_conn, test_env):
    "7911 - test enqueue/dequeue delivery modes the same"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=value)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        value = props.payload
        results = value
        await other_conn.commit()
        assert results == RAW_DATA[0]


async def test_7912(queue, async_conn, test_env):
    "7912 - test enqueue/dequeue delivery modes different"
    value = RAW_DATA[0]
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    props = async_conn.msgproperties(payload=value)
    await queue.enqone(props)

    async with test_env.get_connection_async() as other_conn:
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        assert props is None


async def test_7913(async_conn, test_env):
    "7913 - test error for message with no payload"
    queue = async_conn.queue("TEST_RAW_QUEUE")
    props = async_conn.msgproperties()
    with test_env.assert_raises_full_code("DPY-2000"):
        await queue.enqone(props)


async def test_7914(async_conn, async_cursor, queue):
    "7914 - verify that the msgid property is returned correctly"
    value = RAW_DATA[0]
    props = async_conn.msgproperties(payload=value)
    assert props.msgid is None
    await queue.enqone(props)
    await async_cursor.execute("select msgid from RAW_QUEUE_TAB")
    (actual_msgid,) = await async_cursor.fetchone()
    assert props.msgid == actual_msgid
    props = await queue.deqone()
    assert props.msgid == actual_msgid


async def test_7915(async_conn, async_cursor, queue):
    "7915 - test message props enqtime"
    value = RAW_DATA[0]
    await async_cursor.execute("select current_timestamp from dual")
    (start_date,) = await async_cursor.fetchone()
    start_date = start_date.replace(microsecond=0)
    props = async_conn.msgproperties(payload=value)
    await queue.enqone(props)
    props = await queue.deqone()
    await async_cursor.execute("select current_timestamp from dual")
    (end_date,) = await async_cursor.fetchone()
    end_date = end_date.replace(microsecond=0)
    assert start_date <= props.enqtime <= end_date


async def test_7916(async_conn, queue):
    "7916 - test message props declared attributes"
    value = RAW_DATA[0]
    values = dict(
        payload=value,
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


async def test_7917(async_conn, queue):
    "7917 - test getting queue attributes"
    assert queue.name == "TEST_RAW_QUEUE"
    assert queue.connection is async_conn


async def test_7918(queue):
    "7918 - test getting write-only attributes"
    for options in (queue.enqoptions, queue.deqoptions):
        with pytest.raises(AttributeError):
            options.deliverymode


async def test_7919(async_conn, queue):
    "7919 - test deqoption condition with priority"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    priorities = [5, 5, 5, 5, 10, 9, 9, 10, 9]
    for priority in priorities:
        value = RAW_DATA[0]
        props = async_conn.msgproperties(payload=value, priority=priority)
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


async def test_7920(async_conn, queue):
    "7920 - test deqoption correlation"
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
        props = async_conn.msgproperties(
            payload=value, correlation=correlation
        )
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


async def test_7921(async_conn, queue):
    "7921 - test deqoption msgid"
    value = RAW_DATA[0]
    props = async_conn.msgproperties(payload=value)
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


async def test_7922(queue):
    "7922 - test payload_type returns the correct value"
    assert queue.payload_type is None


async def test_7923(queue):
    "7923 - test deprecated attributes (enqOptions, deqOptions)"
    assert queue.enqOptions is queue.enqoptions
    assert queue.deqOptions is queue.deqoptions


async def test_7924(async_conn, queue, test_env):
    "7924 - test wrong payload type"
    typ = await async_conn.gettype("UDT_BOOK")
    obj = typ.newobject()
    props = async_conn.msgproperties(payload=obj)
    with test_env.assert_raises_full_code("DPY-2062"):
        await queue.enqone(props)


async def test_7925(async_conn, queue):
    "7925 - test deq options correlation with buffered messages"
    value = RAW_DATA[0]
    props = async_conn.msgproperties(payload=value, correlation="sample")
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
    queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
    await queue.enqone(props)
    await async_conn.commit()
    queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
    queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    queue.deqoptions.correlation = "sample"
    msg = await queue.deqone()
    await async_conn.commit()
    assert msg.payload == value


async def test_7926(queue, test_env):
    "7926 - test deq options with msgid > 16 bytes"
    queue.deqoptions.msgid = b"invalid_msgid_123456789"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    with test_env.assert_raises_full_code("ORA-25263"):
        await queue.deqone()


async def test_7927(queue, test_env):
    "7927 - test deq options with msgid < 16 bytes"
    queue.deqoptions.msgid = b"short_msgid"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    with test_env.assert_raises_full_code("ORA-25263"):
        await queue.deqone()
