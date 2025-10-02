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

# -----------------------------------------------------------------------------
# Loads the test environment found in the base directory and then extends it
# with some methods used to determine which extended tests to run.
# -----------------------------------------------------------------------------

import configparser
import os
import pytest

DATABASES_SECTION_NAME = "Databases"


@pytest.fixture(scope="session")
def extended_config(test_env):
    return ExtendedConfig(test_env)


@pytest.fixture
def skip_unless_has_orapki(extended_config):
    if not extended_config.get_bool_value("has_orapki"):
        pytest.skip("extended configuration has_orapki is disabled")


@pytest.fixture
def skip_unless_local_database(extended_config):
    if not extended_config.get_bool_value("local_database"):
        pytest.skip("extended configuration local_database is disabled")


@pytest.fixture
def skip_unless_run_long_tests(extended_config):
    if not extended_config.get_bool_value("run_long_tests"):
        pytest.skip("extended configuration run_long_tests is disabled")


class ExtendedConfig:

    def __init__(self, test_env):
        default_file_name = os.path.join(
            os.path.dirname(__file__), "config.ini"
        )
        file_name = os.environ.get(
            "PYO_TEST_EXT_CONFIG_FILE", default_file_name
        )
        self.parser = configparser.ConfigParser()
        self.parser.read(file_name)
        self.section_name = "DEFAULT"
        if self.parser.has_section(DATABASES_SECTION_NAME):
            for section_name, connect_string in self.parser.items(
                DATABASES_SECTION_NAME
            ):
                if connect_string.upper() == test_env.connect_string.upper():
                    self.section_name = section_name
                    break

    def get_bool_value(self, name, fallback=False):
        """
        Returns a boolean for a specifically named value.
        """
        return self.parser.getboolean(
            self.section_name, name, fallback=fallback
        )
