#------------------------------------------------------------------------------
# Copyright (c) 2022, Oracle and/or its affiliates.
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
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# pool_params.py
#
# Contains the PoolParams class used for managing the parameters required to
# create a connection pool.
#
#{{ generated_notice }}
#------------------------------------------------------------------------------

from typing import Callable, Type, Union

import oracledb

from . import base_impl, constants, errors, utils
from . import connection as connection_module
from .connect_params import ConnectParams

class PoolParams(ConnectParams):
    """
    Contains all parameters used for creating a connection pool.
    """
    __module__ = oracledb.__name__
    __slots__ = ["_impl"]
    _impl_class = base_impl.PoolParamsImpl

#{{ __init__ }}

#{{ __repr__ }}

#{{ properties }}

    def copy(self) -> Type["PoolParams"]:
        """
        Creates a copy of the parameters and returns it.
        """
        params = PoolParams.__new__(PoolParams)
        params._impl = self._impl.copy()
        return params

#{{ set }}
