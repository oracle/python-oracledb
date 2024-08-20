# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
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
# utils.py
#
# Contains utility classes and methods.
# -----------------------------------------------------------------------------

from typing import Union

from . import errors


def params_initer(f):
    """
    Decorator function which is used on the ConnectParams and PoolParams
    classes. It creates the implementation object using the implementation
    class stored on the parameter class. It first, however, calls the original
    method to ensure that the keyword parameters supplied are valid (the
    original method itself does nothing).
    """

    def wrapped_f(self, *args, **kwargs):
        f(self, *args, **kwargs)
        self._impl = self._impl_class()
        if kwargs:
            self._impl.set(kwargs)

    return wrapped_f


def params_setter(f):
    """
    Decorator function which is used on the ConnectParams and PoolParams
    classes. It calls the set() method on the parameter implementation object
    with the supplied keyword arguments. It first, however, calls the original
    method to ensure that the keyword parameters supplied are valid (the
    original method itself does nothing).
    """

    def wrapped_f(self, *args, **kwargs):
        f(self, *args, **kwargs)
        self._impl.set(kwargs)

    return wrapped_f


def verify_stored_proc_args(
    parameters: Union[list, tuple], keyword_parameters: dict
) -> None:
    """
    Verifies that the arguments to a call to a stored procedure or function
    are acceptable.
    """
    if parameters is not None and not isinstance(parameters, (list, tuple)):
        errors._raise_err(errors.ERR_ARGS_MUST_BE_LIST_OR_TUPLE)
    if keyword_parameters is not None and not isinstance(
        keyword_parameters, dict
    ):
        errors._raise_err(errors.ERR_KEYWORD_ARGS_MUST_BE_DICT)
