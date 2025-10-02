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
E2500 - Module for testing caching of configurations from config stores. No
special setup is required but the tests here will only be run if the
run_long_tests value is enabled.
"""

import time

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(skip_unless_run_long_tests):
    pass


def test_ext_2500(test_env):
    "E2500 - test config is cached"
    sdu = 4096
    protocol = "proto-test"
    connect_string = f"{protocol}://test_ext_2500"
    config = dict(
        connect_descriptor=test_env.connect_string,
        pyo=dict(sdu=sdu),
    )

    def hook(passed_protocol, passed_protocol_arg, passed_params):
        passed_params.set_from_config(config)
        config["pyo"]["sdu"] *= 2

    oracledb.register_protocol(protocol, hook)
    try:
        for i in range(2):
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            assert params.sdu == sdu
    finally:
        oracledb.register_protocol(protocol, None)


def test_ext_2501(test_env):
    "E2501 - test config cache is disabled with config_time_to_live = 0"
    sdu = 4096
    protocol = "proto-test"
    connect_string = f"{protocol}://test_ext_2501"
    config = dict(
        connect_descriptor=test_env.connect_string,
        config_time_to_live=0,
        pyo=dict(sdu=sdu),
    )

    def hook(passed_protocol, passed_protocol_arg, passed_params):
        passed_params.set_from_config(config)
        config["pyo"]["sdu"] *= 2

    oracledb.register_protocol(protocol, hook)
    try:
        for i in range(2):
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            assert params.sdu == sdu + i * sdu
    finally:
        oracledb.register_protocol(protocol, None)


def test_ext_2502(test_env):
    "E2502 - test config cache expiry time"
    sdu = 4096
    protocol = "proto-test"
    connect_string = f"{protocol}://test_ext_2502"
    config = dict(
        connect_descriptor=test_env.connect_string,
        config_time_to_live=2,
        pyo=dict(sdu=sdu),
    )

    def hook(passed_protocol, passed_protocol_arg, passed_params):
        passed_params.set_from_config(config)
        config["pyo"]["sdu"] *= 2

    oracledb.register_protocol(protocol, hook)
    try:
        expected_sdu = sdu
        for i in range(7):
            if i == 3 or i == 6:
                expected_sdu *= 2
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            assert params.sdu == expected_sdu
            time.sleep(0.75)
    finally:
        oracledb.register_protocol(protocol, None)


def test_ext_2503(test_env):
    "E2503 - test config cache soft/hard expiry time"
    sdu = 4096
    protocol = "proto-test"
    connect_string = f"{protocol}://test_ext_2503"
    config = dict(
        connect_descriptor=test_env.connect_string,
        config_time_to_live=2,
        config_time_to_live_grace_period=3,
        pyo=dict(sdu=sdu),
    )

    def hook(passed_protocol, passed_protocol_arg, passed_params):
        if config["pyo"]["sdu"] > sdu:
            raise Exception("Arbitrary exception!")
        passed_params.set_from_config(config)
        config["pyo"]["sdu"] *= 2

    oracledb.register_protocol(protocol, hook)
    try:
        for i in range(2):
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
            assert params.sdu == sdu
            time.sleep(3)
        with test_env.assert_raises_full_code("DPY-2056"):
            params = oracledb.ConnectParams()
            params.parse_connect_string(connect_string)
    finally:
        oracledb.register_protocol(protocol, None)
