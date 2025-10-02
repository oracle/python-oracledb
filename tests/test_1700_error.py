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
1700 - Module for testing error objects
"""

import pytest
import pickle

import oracledb


def test_1700(cursor):
    "1700 - test parse error returns offset correctly"
    with pytest.raises(oracledb.Error) as excinfo:
        cursor.execute("begin t_Missing := 5; end;")
    (error_obj,) = excinfo.value.args
    assert error_obj.full_code == "ORA-06550"
    assert error_obj.offset == 6


def test_1701(cursor):
    "1701 - test picking/unpickling an error object"
    with pytest.raises(oracledb.Error) as excinfo:
        cursor.execute(
            """
            begin
                raise_application_error(-20101, 'Test!');
            end;
            """
        )
    (error_obj,) = excinfo.value.args
    assert isinstance(error_obj, oracledb._Error)
    assert "Test!" in error_obj.message
    assert error_obj.code == 20101
    assert error_obj.offset == 0
    assert isinstance(error_obj.isrecoverable, bool)
    assert not error_obj.isrecoverable
    new_error_obj = pickle.loads(pickle.dumps(error_obj))
    assert isinstance(new_error_obj, oracledb._Error)
    assert new_error_obj.message == error_obj.message
    assert new_error_obj.code == error_obj.code
    assert new_error_obj.offset == error_obj.offset
    assert new_error_obj.context == error_obj.context
    assert new_error_obj.isrecoverable == error_obj.isrecoverable


def test_1702(conn):
    "1702 - test generation of full_code for ORA, DPI and DPY errors"
    cursor = conn.cursor()
    with pytest.raises(oracledb.Error) as excinfo:
        cursor.execute(None)
    (error_obj,) = excinfo.value.args
    assert error_obj.full_code == "DPY-2001"
    if not conn.thin:
        with pytest.raises(oracledb.Error) as excinfo:
            cursor.execute("truncate table TestTempTable")
            int_var = cursor.var(int)
            str_var = cursor.var(str, 2)
            cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (1, 'Longer than two chars')
                returning IntCol, StringCol1
                into :int_var, :str_var
                """,
                int_var=int_var,
                str_var=str_var,
            )
        (error_obj,) = excinfo.value.args
        assert error_obj.full_code == "DPI-1037"


def test_1703(conn, test_env):
    "1703 - test generation of error help portal URL"
    if not test_env.has_client_version(23):
        pytest.skip("unsupported client")
    cursor = conn.cursor()
    with pytest.raises(oracledb.Error) as excinfo:
        cursor.execute("select 1 / 0 from dual")
    (error_obj,) = excinfo.value.args
    to_check = "Help: https://docs.oracle.com/error-help/db/ora-01476/"
    assert to_check in error_obj.message


def test_1704(cursor):
    "1704 - verify warning is generated when creating a procedure"
    proc_name = "bad_proc_1704"
    assert cursor.warning is None
    cursor.execute(
        f"""
        create or replace procedure {proc_name} as
        begin
            null
        end;
        """
    )
    assert cursor.warning.full_code == "DPY-7000"
    cursor.execute(
        f"""
        create or replace procedure {proc_name} as
        begin
            null;
        end;
        """
    )
    assert cursor.warning is None
    cursor.execute(f"drop procedure {proc_name}")


def test_1705(cursor):
    "1705 - verify warning is generated when creating a function"
    func_name = "bad_func_1705"
    cursor.execute(
        f"""
        create or replace function {func_name}
        return number as
        begin
            return null
        end;
        """
    )
    assert cursor.warning.full_code == "DPY-7000"
    cursor.execute(f"drop function {func_name}")
    assert cursor.warning is None


def test_1706(cursor):
    "1706 - verify warning is generated when creating a type"
    type_name = "bad_type_1706"
    cursor.execute(
        f"""
        create or replace type {type_name} as object (
            x bad_type
        );
        """
    )
    assert cursor.warning.full_code == "DPY-7000"
    cursor.execute(f"drop type {type_name}")
    assert cursor.warning is None


def test_1707(cursor):
    "1707 - verify warning is generated with executemany()"
    proc_name = "bad_proc_1707"
    assert cursor.warning is None
    cursor.executemany(
        f"""
        create or replace procedure {proc_name} as
        begin
            null
        end;
        """,
        1,
    )
    assert cursor.warning.full_code == "DPY-7000"
    cursor.execute(
        f"""
        create or replace procedure {proc_name} as
        begin
            null;
        end;
        """
    )
    assert cursor.warning is None
    cursor.execute(f"drop procedure {proc_name}")


def test_1708(cursor):
    "1708 - user defined errors do not generate error help portal URL"
    for code in (20000, 20500, 20999):
        with pytest.raises(oracledb.Error) as excinfo:
            cursor.execute(
                f"""
                begin
                    raise_application_error(-{code}, 'User defined error');
                end;
                """
            )
        error_obj = excinfo.value.args[0]
        assert error_obj.code == code
        assert error_obj.full_code == f"ORA-{code}"
        assert "Help:" not in error_obj.message


def test_1709(skip_if_drcp, conn, test_env):
    "1709 - error from killed connection is deemed recoverable"
    admin_conn = test_env.get_admin_connection()
    conn = test_env.get_connection()
    sid, serial = test_env.get_sid_serial(conn)
    with admin_conn.cursor() as admin_cursor:
        sql = f"alter system kill session '{sid},{serial}'"
        admin_cursor.execute(sql)
    with test_env.assert_raises_full_code("DPY-4011") as excinfo:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
    assert excinfo.error_obj.isrecoverable
