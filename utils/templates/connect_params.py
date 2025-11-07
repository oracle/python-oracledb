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

from .base import BaseMetaClass
from . import base_impl, utils


class ConnectParams(metaclass=BaseMetaClass):
    """
    Contains all parameters used for establishing a connection to the
    database.
    """

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
        Creates a copy of the ConnectParams instance and returns it.
        """
        params = ConnectParams.__new__(ConnectParams)
        params._impl = self._impl.copy()
        return params

    def get_connect_string(self) -> str:
        """
        Returns the connection string associated with the instance.
        """
        return self._impl.get_connect_string()

    def get_network_service_names(self) -> list:
        """
        Returns a list of the network service names found in the
        :ref:`tnsnames.ora <optnetfiles>` file which is inside the directory
        that can be identified by the attribute
        :attr:`~ConnectParams.config_dir`.  If a tnsnames.ora file does not
        exist, then an exception is raised.
        """
        return self._impl.get_network_service_names()

    def parse_connect_string(self, connect_string: str) -> None:
        """
        Parses the connect string into its components and stores the
        parameters.

        The ``connect string`` parameter can be an Easy Connect string,
        name-value pairs, or a simple alias which is looked up in
        ``tnsnames.ora``. Parameters that are found in the connect string
        override any currently stored values.
        """
        self._impl.parse_connect_string(connect_string)

    def parse_dsn_with_credentials(self, dsn: str) -> tuple:
        """
        Parses a DSN in the form <user>/<password>@<connect_string> or in the
        form <user>/<password> and returns a 3-tuple containing the parsed
        user, password and connect string. Empty strings are returned as the
        value *None*.
        """
        return self._impl.parse_dsn_with_credentials(dsn)

    @utils.params_setter
    def set(
        # {{ params_setter_args }}
    ):
        """
        Sets the values for one or more of the parameters of a ConnectParams
        object.  All parameters are optional. A brief description of each
        parameter follows:

        # {{ args_help_without_defaults }}
        """
        pass

    def set_from_config(self, config: dict) -> None:
        """
        Sets the property values based on the specified configuration. This
        method is intended for use with Centralized Configuration Providers.

        The ``config`` parameter is a dictionary which consists of the
        following optional keys: "connect_descriptor", "user", "password", and
        "pyo".

        If the key "connect_descriptor" is specified, it is expected to be a
        string, which will be parsed and the properties found within it are
        stored in the ConnectParams instance.

        If the keys "user" or "password" are specified, and the parameters do
        not already have a user or password set, these values will be stored;
        otherwise, they will be ignored. The key "user" is expected to be a
        string. The "key" password may be a string or it may be a dictionary
        which will be examined by a :ref:`registered password type handler
        <registerpasswordtype>` to determine the actual password.

        If the key "pyo" is specified, it is expected to be a dictionary
        containing keys corresponding to property names. Any property names
        accepted by the ConnectParams class will be stored in the ConnectParams
        instance; all other values will be ignored.
        """
        self._impl.set_from_config(config)
