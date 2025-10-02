# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
7300 - Module for testing unsupported features in Thin mode
"""

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(skip_unless_thin_mode):
    pass


def test_7300(test_env):
    "7300 - test getting and setting thick attributes"
    pool = test_env.get_pool()
    with test_env.assert_raises_full_code("DPY-3001"):
        pool.soda_metadata_cache
    with test_env.assert_raises_full_code("DPY-3001"):
        pool.soda_metadata_cache = True
    with test_env.assert_raises_full_code("DPY-3001"):
        pool.max_sessions_per_shard
    with test_env.assert_raises_full_code("DPY-3001"):
        pool.max_sessions_per_shard = 2


def test_7302(test_env):
    "7302 - test connection with sharding and supersharding keys"
    with test_env.assert_raises_full_code("DPY-3001"):
        test_env.get_connection(shardingkey=[27])
    with test_env.assert_raises_full_code("DPY-3001"):
        test_env.get_connection(supershardingkey=[17, 23])


def test_7303(test_env):
    "7303 - test connect() without a connect string (bequeath)"
    with test_env.assert_raises_full_code("DPY-3001"):
        oracledb.connect(
            user=test_env.main_user,
            password=test_env.main_password,
        )


def test_7304(test_env):
    "7304 - test acquire() from a pool with a session tag"
    pool = test_env.get_pool()
    with test_env.assert_raises_full_code("DPY-3001"):
        pool.acquire(tag="unimportant")
