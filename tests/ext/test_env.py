# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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

dir_name = os.path.dirname(os.path.dirname(__file__))
file_name = os.path.join(dir_name, os.path.basename(__file__))
exec(open(file_name).read(), globals(), locals())

DATABASES_SECTION_NAME = "Databases"


class ExtendedConfig:

    def __init__(self):
        default_file_name = os.path.join(
            os.path.dirname(__file__), "config.ini"
        )
        file_name = os.environ.get(
            "PYO_TEST_EXT_CONFIG_FILE", default_file_name
        )
        self.parser = configparser.ConfigParser()
        self.parser.read(file_name)
        self.section_name = "DEFAULT"
        connect_string_to_use = get_connect_string().upper()  # noqa: F821

        if self.parser.has_section(DATABASES_SECTION_NAME):
            for section_name, connect_string in self.parser.items(
                DATABASES_SECTION_NAME
            ):
                if connect_string.upper() == connect_string_to_use:
                    self.section_name = section_name
                    break


_extended_config = ExtendedConfig()


def get_extended_config_bool(name, fallback=False):
    return _extended_config.parser.getboolean(
        _extended_config.section_name, name, fallback=fallback
    )


def get_extended_config_str(name, fallback=None):
    return _extended_config.parser.get(
        _extended_config.section_name, name, fallback=fallback
    )
