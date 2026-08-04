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
1000 (py314) - Module for testing Python 3.14 templates.
"""

import datetime
import decimal

import pytest


def test_py314_1000(cursor):
    "1000 - test template with one bind variable"
    value = 1000
    cursor.execute(t"select {value} from dual")
    (fetched_value,) = cursor.fetchone()
    assert fetched_value == value


def test_py314_1001(cursor, test_env):
    "1001 - test template with no bind variables"
    cursor.execute(t"select user from dual")
    (fetched_value,) = cursor.fetchone()
    assert fetched_value == test_env.main_user.upper()


def test_py314_1002(cursor):
    "1002 - test template with multiple bind variables"
    value_1 = "str_value"
    value_2 = 1002
    value_3 = 25.25
    cursor.execute(t"select {value_1}, {value_2}, {value_3} from dual")
    assert cursor.fetchone() == (value_1, value_2, value_3)


def test_py314_1003(cursor, test_env):
    "1003 - test template with identifier format specifier"
    name = "user"
    alias = "my user"
    cursor.execute(t"select {name:i} as {alias:i} from dual")
    assert cursor.description[0].name == alias
    (fetched_value,) = cursor.fetchone()
    assert fetched_value == test_env.main_user.upper()


def test_py314_1004(cursor, test_env):
    "1004 - test template with literal format specifier"
    null_value = None
    str_value = "Contains 'quotes'"
    int_value = 1004
    float_value = 12.125
    decimal_value = decimal.Decimal("123.5")
    datetime_value = datetime.datetime(2026, 8, 3, 13, 32, 25)
    date_value = datetime.date(1976, 5, 13)
    cursor.execute(t"""
        select
            {null_value:l},
            {str_value:l},
            {int_value:l},
            {float_value:l},
            {decimal_value:l},
            {datetime_value:l},
            {date_value:l}
        from dual""")
    assert cursor.fetchone() == (
        null_value,
        str_value,
        int_value,
        float_value,
        float(str(decimal_value)),
        datetime_value,
        datetime.datetime.combine(date_value, datetime.time.min),
    )


def test_py314_1005(cursor):
    "1005 - test template with query format specifier"
    empty_value = None
    top_value = 1005
    sub_value = 1005.25
    template_value = t"{sub_value}"
    cursor.execute(
        t"select {top_value}{empty_value:q}, {template_value:q} from dual"
    )
    assert cursor.fetchone() == (top_value, sub_value)


def test_py314_1006(cursor, test_env):
    "1006 - test invalid and unsupported template"
    dummy_value = 5
    with test_env.assert_raises_full_code("DPY-2077"):
        cursor.execute(t"select {dummy_value!s} from dual")
    with test_env.assert_raises_full_code("DPY-2077"):
        cursor.execute(t"select {dummy_value:a} from dual")
    with test_env.assert_raises_full_code("DPY-2076"):
        cursor.execute(t"select {dummy_value} from dual", bad_arg=5)
    with test_env.assert_raises_full_code("DPY-2076"):
        cursor.execute(t"select {dummy_value} from dual", [5])
    with test_env.assert_raises_full_code("DPY-2076"):
        cursor.execute(t"select {dummy_value} from dual", dict(bad_arg=5))
    with pytest.raises(TypeError):
        cursor.execute(t"select {decimal:l} from dual")
