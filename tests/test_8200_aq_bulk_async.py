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
8200 - Module for testing AQ Bulk enqueue/dequeue with asyncio
"""

import datetime

import oracledb
import pytest

RAW_QUEUE_NAME = "TEST_RAW_QUEUE"
JSON_QUEUE_NAME = "TEST_JSON_QUEUE"
RAW_PAYLOAD_DATA = [
    "The first message",
    "The second message",
    "The third message",
    "The fourth message",
    "The fifth message",
    "The sixth message",
    "The seventh message",
    "The eighth message",
    "The ninth message",
    "The tenth message",
    "The eleventh message",
    "The twelfth and final message",
]

JSON_DATA_PAYLOAD = [
    [
        2.75,
        True,
        "Ocean Beach",
        b"Some bytes",
        {"keyA": 1.0, "KeyB": "Melbourne"},
        datetime.datetime(2022, 8, 1, 0, 0),
    ],
    dict(name="John", age=30, city="New York"),
]


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


@pytest.fixture
async def queue(async_conn, test_env):
    """
    Creates the queue used by the tests in this file.
    """
    return await test_env.get_and_clear_queue_async(async_conn, RAW_QUEUE_NAME)


@pytest.fixture
async def json_queue(async_conn, test_env):
    """
    Creates the queue used by the tests in this file.
    """
    return await test_env.get_and_clear_queue_async(
        async_conn, JSON_QUEUE_NAME, "JSON"
    )


async def _deq_in_thread(test_env, results):
    async with test_env.get_connection_async() as conn:
        queue = conn.queue(RAW_QUEUE_NAME)
        queue.deqoptions.wait = 10
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        while len(results) < len(RAW_PAYLOAD_DATA):
            messages = await queue.deqmany(5)
            if not messages:
                break
            for message in messages:
                results.append(message.payload.decode())
        await conn.commit()


async def test_8200(queue, async_conn):
    "8200 - test bulk enqueue and dequeue"
    messages = [
        async_conn.msgproperties(payload=data) for data in RAW_PAYLOAD_DATA
    ]
    await queue.enqmany(messages)
    messages = await queue.deqmany(len(RAW_PAYLOAD_DATA))
    data = [message.payload.decode() for message in messages]
    await async_conn.commit()
    assert data == RAW_PAYLOAD_DATA


async def test_8201(queue, async_conn):
    "8201 - test empty bulk dequeue"
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    messages = await queue.deqmany(5)
    await async_conn.commit()
    assert messages == []


async def test_8202(queue, async_conn):
    "8202 - test enqueue and dequeue multiple times"
    data_to_enqueue = RAW_PAYLOAD_DATA
    for num in (2, 6, 4):
        messages = [
            async_conn.msgproperties(payload=data)
            for data in data_to_enqueue[:num]
        ]
        data_to_enqueue = data_to_enqueue[num:]
        await queue.enqmany(messages)
    await async_conn.commit()
    all_data = []
    for num in (3, 5, 10):
        messages = await queue.deqmany(num)
        all_data.extend(message.payload.decode() for message in messages)
    await async_conn.commit()
    assert all_data == RAW_PAYLOAD_DATA


async def test_8203(queue, async_conn, test_env):
    "8203 - test error for messages with no payload"
    messages = [async_conn.msgproperties() for _ in RAW_PAYLOAD_DATA]
    with test_env.assert_raises_full_code("DPY-2000"):
        await queue.enqmany(messages)


async def test_8204(queue, async_conn, async_cursor):
    "8204 - verify that the msgid property is returned correctly"
    messages = [
        async_conn.msgproperties(payload=data) for data in RAW_PAYLOAD_DATA
    ]
    await queue.enqmany(messages)
    await async_cursor.execute("select msgid from raw_queue_tab")
    actual_msgids = set(m for m, in await async_cursor.fetchall())
    msgids = set(message.msgid for message in messages)
    assert msgids == actual_msgids
    messages = await queue.deqmany(len(RAW_PAYLOAD_DATA))
    msgids = set(message.msgid for message in messages)
    assert msgids == actual_msgids


async def test_8205(json_queue, async_conn):
    "8205 - test enqueuing and dequeuing JSON message"
    props = [
        async_conn.msgproperties(payload=data) for data in JSON_DATA_PAYLOAD
    ]
    await json_queue.enqmany(props)
    await async_conn.commit()
    json_queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
    messages = await json_queue.deqmany(5)
    actual_data = [message.payload for message in messages]
    assert actual_data == JSON_DATA_PAYLOAD


async def test_8206(json_queue, async_conn, test_env):
    "8206 - test enqueuing to a JSON queue without a JSON payload"
    props = async_conn.msgproperties(payload="string message")
    with test_env.assert_raises_full_code("DPY-2062"):
        await json_queue.enqmany([props, props])


async def test_8207(json_queue, async_conn):
    "8207 - test errors for invalid values for enqmany and deqmany"
    props = async_conn.msgproperties(payload="string message")
    with pytest.raises(TypeError):
        await json_queue.enqmany(props)
    with pytest.raises(TypeError):
        await json_queue.enqmany(["Not", "msgproperties"])
    with pytest.raises(TypeError):
        await json_queue.deqmany("5")
