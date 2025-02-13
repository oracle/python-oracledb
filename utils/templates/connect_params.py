# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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
# connect_params.py
#
# Contains the ConnectParams class used for managing the parameters required to
# establish a connection to the database.
#
# # {{ generated_notice }}
# -----------------------------------------------------------------------------

import functools
import ssl
from typing import Union, Callable, Any, Optional

import oracledb

from . import base_impl, utils


class ConnectParams:
    """
    Contains all parameters used for establishing a connection to the
    database.
    """

    __module__ = oracledb.__name__
    __slots__ = ["_impl"]
    _impl_class = base_impl.ConnectParamsImpl

    @utils.params_initer
    def __init__(
        # {{ params_constructor_args }}
    ):
        """
        All parameters are optional. A brief description of each parameter
        follows:

        # {{ args_help_with_defaults }}
        """
        pass

    # {{ params_repr }}

    def _flatten_value(f):
        """
        Helper function used to flatten arrays of values if they only contain a
        single item.
        """

        @functools.wraps(f)
        def wrapped(self):
            values = f(self)
            return values if len(values) > 1 else values[0]

        return wrapped

    # {{ params_properties }}

    def copy(self) -> "ConnectParams":
        """
        Creates a copy of the parameters and returns it.
        """
        params = ConnectParams.__new__(ConnectParams)
        params._impl = self._impl.copy()
        return params

    def get_connect_string(self) -> str:
        """
        Returns a connect string generated from the parameters.
        """
        return self._impl.get_connect_string()

    def get_network_service_names(self) -> list:
        """
        Returns a list of the network service names found in the tnsnames.ora
        file found in the configuration directory associated with the
        parameters. If no such file exists, an error is raised.
        """
        return self._impl.get_network_service_names()

    def parse_connect_string(self, connect_string: str) -> None:
        """
        Parses the connect string into its components and stores the
        parameters.  The connect string could be an Easy Connect string,
        name-value pairs or a simple alias which is looked up in tnsnames.ora.
        Any parameters found in the connect string override any currently
        stored values.
        """
        self._impl.parse_connect_string(connect_string)

    def parse_dsn_with_credentials(self, dsn: str) -> tuple:
        """
        Parses a dsn in the form <user>/<password>@<connect_string> or in the
        form <user>/<password> and returns a 3-tuple containing the parsed
        user, password and connect string. Empty strings are returned as the
        value None. This is done automatically when a value is passed to
        the dsn parameter but no value is passed to the user password when
        creating a standalone connection or connection pool.
        """
        return self._impl.parse_dsn_with_credentials(dsn)

    @utils.params_setter
    def set(
        # {{ params_setter_args }}
    ):
        """
        All parameters are optional. A brief description of each parameter
        follows:

        # {{ args_help_without_defaults }}
        """
        pass

    def set_from_config(self, config: dict) -> None:
        """
        Sets the property values based on the supplied configuration. The
        configuration consists of a dictionary with the following keys, all of
        which are optional: "connect_descriptor", "user", "password" and "pyo".

        If the "connect_descriptor" key is supplied, it is expected to be a
        string, which will be parsed and the properties found within it stored
        in the parameters.

        If the "user" or "password" keys are supplied, and the parameters do
        not already have a user or password, these values will be stored;
        otherwise, they will be ignored. The "user" key is expected to be a
        string. The "password" key may be a string or it may be a dictionary
        containing the keys "type" and "value" which will be used to determine
        the actual password.

        If the "pyo" key is supplied, it is expected to be a dictionary
        containing keys corresponding to property names. Any property names
        accepted by the parameters will be stored; all other values will be
        ignored.
        """
        self._impl.set_from_config(config)
