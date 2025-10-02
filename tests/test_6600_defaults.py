# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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
6600 - Module for testing oracledb.defaults
"""

import decimal
import os
import tempfile

import oracledb


def _verify_network_name_attr(test_env, name):
    """
    Verify that a default attribute is handled properly in both valid
    and invalid cases.
    """
    for value, ok in [
        ("valid_value", True),
        ("'contains_quotes'", False),
        ('"contains_double_quotes"', False),
        ("contains_opening_paren (", False),
        ("contains_closing_paren )", False),
        ("contains_equals =", False),
        ("contains_trailing_slash\\", False),
    ]:
        args = {}
        args[name] = value
        if ok:
            with test_env.defaults_context_manager(name, value):
                cp = oracledb.ConnectParams(**args)
                assert getattr(cp, name) == value
        else:
            with test_env.assert_raises_full_code("DPY-3029"):
                with test_env.defaults_context_manager(name, value):
                    pass


def test_6600(test_env):
    "6600 - test setting defaults.arraysize"
    with test_env.defaults_context_manager("arraysize", 50):
        conn = test_env.get_connection()
        cursor = conn.cursor()
        assert cursor.arraysize == oracledb.defaults.arraysize


def test_6601(cursor, test_env):
    "6601 - test getting decimals with defaults.fetch_decimals=True"
    with test_env.defaults_context_manager("fetch_decimals", True):
        cursor.execute("select 9 from dual")
        (result,) = cursor.fetchone()
        assert isinstance(result, decimal.Decimal)


def test_6602(cursor, test_env):
    "6602 - test getting string lob with defaults.fetch_lobs=False"
    with test_env.defaults_context_manager("fetch_lobs", False):
        cursor.execute("select to_clob('Hello world') from dual")
        (result,) = cursor.fetchone()
        assert isinstance(result, str)


def test_6603(test_env):
    "6603 - test setting defaults.prefetchrows"
    with test_env.defaults_context_manager("prefetchrows", 20):
        conn = test_env.get_connection()
        cursor = conn.cursor()
        assert cursor.prefetchrows == oracledb.defaults.prefetchrows


def test_6604(test_env):
    "6604 - test setting defaults.stmtcachesize (pool)"
    new_stmtcachesize = 15
    with test_env.defaults_context_manager("stmtcachesize", 40):
        pool = test_env.get_pool()
        assert pool.stmtcachesize == oracledb.defaults.stmtcachesize
        conn = pool.acquire()
        assert conn.stmtcachesize == oracledb.defaults.stmtcachesize
        pool = test_env.get_pool(stmtcachesize=new_stmtcachesize)
        assert pool.stmtcachesize == new_stmtcachesize
        conn = pool.acquire()
        assert conn.stmtcachesize == new_stmtcachesize


def test_6605(test_env):
    "6605 - test setting defaults.stmtcachesize (standalone connection)"
    new_stmtcachesize = 25
    with test_env.defaults_context_manager("stmtcachesize", 50):
        conn = test_env.get_connection()
        assert conn.stmtcachesize == oracledb.defaults.stmtcachesize
        conn = test_env.get_connection(stmtcachesize=new_stmtcachesize)
        assert conn.stmtcachesize == new_stmtcachesize


def test_6606(cursor, test_env):
    "6606 - fetch_lobs does not affect LOBS returned as OUT binds"
    with test_env.defaults_context_manager("fetch_lobs", False):
        var = cursor.var(oracledb.DB_TYPE_CLOB)
        cursor.execute(
            "begin :value := to_clob('test clob'); end;",
            value=var,
        )
        assert isinstance(var.getvalue(), oracledb.LOB)


def test_6607(test_env):
    "6607 - test setting defaults.config_dir"
    with tempfile.TemporaryDirectory() as temp_dir:
        new_temp_dir = os.path.join(temp_dir, "subdir")
        with test_env.defaults_context_manager("config_dir", temp_dir):
            assert oracledb.defaults.config_dir == temp_dir
            params = oracledb.ConnectParams()
            assert params.config_dir == temp_dir
            params = oracledb.ConnectParams(config_dir=new_temp_dir)
            assert params.config_dir == new_temp_dir


def test_6608(test_env):
    "6608 - test setting defaults.stmtcachesize (ConnectParams)"
    new_stmtcachesize = 35
    with test_env.defaults_context_manager("stmtcachesize", 60):
        params = oracledb.ConnectParams()
        assert params.stmtcachesize == oracledb.defaults.stmtcachesize
        params = oracledb.ConnectParams(stmtcachesize=new_stmtcachesize)
        assert params.stmtcachesize == new_stmtcachesize


def test_6609(test_env):
    "6609 - test defaults.stmtcachesize persists after setting it again"
    value = 50
    new_value = 29
    with test_env.defaults_context_manager("stmtcachesize", value):
        pool = test_env.get_pool()
        pooled_conn = pool.acquire()
        params = oracledb.ConnectParams()
        standalone_conn = test_env.get_connection()
        with test_env.defaults_context_manager("stmtcachesize", new_value):
            assert pool.stmtcachesize == value
            assert pooled_conn.stmtcachesize == value
            assert params.stmtcachesize == value
            assert standalone_conn.stmtcachesize == value
            pool = test_env.get_pool()
            pooled_conn = pool.acquire()
            params = oracledb.ConnectParams()
            standalone_conn = test_env.get_connection()
            assert pool.stmtcachesize == new_value
            assert pooled_conn.stmtcachesize == new_value
            assert params.stmtcachesize == new_value
            assert standalone_conn.stmtcachesize == new_value


def test_6610(test_env):
    "6610 - test setting defaults.terminal"
    with test_env.defaults_context_manager("terminal", "newterminal"):
        params = oracledb.ConnectParams()
        assert params.terminal == oracledb.defaults.terminal


def test_6611(test_env):
    "6611 - test setting defaults.driver_name"
    with test_env.defaults_context_manager("driver_name", "newdriver"):
        params = oracledb.ConnectParams()
        assert params.driver_name == oracledb.defaults.driver_name


def test_6612(test_env):
    "6612 - test setting defaults.program attribute"
    _verify_network_name_attr(test_env, "program")


def test_6613(test_env):
    "6613 - test setting defaults.machine attribute"
    _verify_network_name_attr(test_env, "machine")


def test_6614(test_env):
    "6614 - test setting defaults.osuser attribute"
    _verify_network_name_attr(test_env, "osuser")


def test_6615(skip_unless_thin_mode, test_env):
    "6615 - test program with two pools"
    default_value = "defaultprogram"
    new_value = "newprogram"
    verify_sql = (
        "select program from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    with test_env.defaults_context_manager("program", default_value):

        # create pool using default value
        pool = test_env.get_pool()
        with pool.acquire() as conn:
            with conn.cursor() as cursor:
                cursor.execute(verify_sql)
                (fetched_value,) = cursor.fetchone()
                assert fetched_value == default_value
        pool.close()

        # create pool using new value
        pool = test_env.get_pool(program=new_value)
        with pool.acquire() as conn:
            with conn.cursor() as cursor:
                cursor.execute(verify_sql)
                (fetched_value,) = cursor.fetchone()
                assert fetched_value == new_value
        pool.close()
