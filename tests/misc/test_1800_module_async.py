# -----------------------------------------------------------------------------
# Copyright (c) 2026, Oracle and/or its affiliates.
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
Module for testing top-level module methods with asyncio
"""

import asyncio
import contextvars
import datetime

import oracledb
import pytest


@pytest.fixture(autouse=True)
async def module_checks(anyio_backend):
    oracledb.clear_all_secrets()
    oracledb.clear_all_secrets(context_local=True)
    yield
    oracledb.clear_all_secrets()
    oracledb.clear_all_secrets(context_local=True)


async def test_misc_1800():
    "1800 - independent tasks have separate context-local secrets"
    key = (1800, "key")
    ready = [asyncio.Event(), asyncio.Event()]

    async def worker(index):
        initial_value = oracledb.get_secret(key, context_local=True)
        value = f"secret_1800_{index}"
        oracledb.save_secret(key, value, context_local=True)
        ready[index].set()
        await ready[1 - index].wait()
        assert initial_value is None
        assert oracledb.get_secret(key, context_local=True) == value

    await asyncio.gather(worker(0), worker(1))
    assert oracledb.get_secret(key, context_local=True) is None


async def test_misc_1801():
    "1801 - child and grandchild tasks inherit and replace secrets"
    key = (1801, "key")
    child_key = (1801, "child_key")
    parent_value = "parent_1801"
    child_value = "child_1801"
    grandchild_value = "grandchild_1801"
    oracledb.save_secret(key, parent_value, context_local=True)

    async def grandchild():
        assert oracledb.get_secret(key, context_local=True) == child_value
        oracledb.save_secret(key, grandchild_value, context_local=True)
        assert oracledb.get_secret(key, context_local=True) == grandchild_value

    async def child():
        assert oracledb.get_secret(key, context_local=True) == parent_value
        oracledb.save_secret(key, child_value, context_local=True)
        await asyncio.create_task(grandchild())
        assert oracledb.get_secret(key, context_local=True) == child_value

    await asyncio.create_task(child())
    assert oracledb.get_secret(key, context_local=True) == parent_value
    assert oracledb.get_secret(child_key, context_local=True) is None


async def test_misc_1802():
    "1802 - child tasks inherit context at creation, not at first execution"
    key = (1802, "key")
    new_key = (1802, "new_key")
    updated = asyncio.Event()
    original_value = "original_1802"
    updated_value = "updated_1802"
    new_value = "new_1802"
    oracledb.save_secret(key, original_value, context_local=True)

    async def child():
        await updated.wait()
        assert oracledb.get_secret(key, context_local=True) == original_value
        assert oracledb.get_secret(new_key, context_local=True) is None

    task = asyncio.create_task(child())
    oracledb.save_secret(key, updated_value, context_local=True)
    oracledb.save_secret(new_key, new_value, context_local=True)
    updated.set()
    await task
    assert oracledb.get_secret(key, context_local=True) == updated_value
    assert oracledb.get_secret(new_key, context_local=True) == new_value


@pytest.mark.parametrize("clear_all", [False, True], ids=["delete", "clear"])
async def test_misc_1803(clear_all):
    "1803 - deleting or clearing child secrets preserves the parent's cache"
    key = (1803, "key")
    other_key = (1803, "other_key")
    parent_value = "parent_1803"
    other_value = "other_1803"
    oracledb.save_secret(key, parent_value, context_local=True)
    oracledb.save_secret(other_key, other_value, context_local=True)

    async def child():
        if clear_all:
            oracledb.clear_all_secrets(context_local=True)
        else:
            oracledb.save_secret(key, None, context_local=True)
        assert oracledb.get_secret(key, context_local=True) is None
        stored_value = oracledb.get_secret(other_key, context_local=True)
        if clear_all:
            assert stored_value is None
        else:
            assert stored_value == other_value

    await asyncio.create_task(child())
    assert oracledb.get_secret(key, context_local=True) == parent_value
    assert oracledb.get_secret(other_key, context_local=True) == other_value


async def test_misc_1804():
    "1804 - child expiry cleanup removes only the child's cache entry"
    key = (1804, "key")
    expires = datetime.datetime.now(
        datetime.timezone.utc
    ) - datetime.timedelta(1)
    secret = oracledb.save_secret(
        key, "expired_1804", context_local=True, expires=expires
    )

    async def child():
        assert oracledb.get_secret(key, context_local=True) is None
        return contextvars.copy_context()

    child_context = await asyncio.create_task(child())
    # Make the retained secret valid again to observe whether the child
    # removed the entry from the parent's cache as well as its own.
    renewed_value = "renewed_1804"
    secret.value = renewed_value
    assert oracledb.get_secret(key, context_local=True) == renewed_value
    assert (
        child_context.run(oracledb.get_secret, key, context_local=True) is None
    )


async def test_misc_1805():
    "1805 - global secrets remain shared between independent tasks"
    key = (1805, "key")
    global_value = "global_1805"
    local_value = "local_1805"
    ready = asyncio.Event()

    async def writer():
        oracledb.save_secret(key, global_value)
        oracledb.save_secret(key, local_value, context_local=True)
        assert oracledb.get_secret(key, context_local=True) == local_value
        ready.set()

    async def reader():
        await ready.wait()
        assert oracledb.get_secret(key) == global_value
        assert oracledb.get_secret(key, context_local=True) is None

    await asyncio.gather(writer(), reader())
    assert oracledb.get_secret(key) == global_value
    assert oracledb.get_secret(key, context_local=True) is None
