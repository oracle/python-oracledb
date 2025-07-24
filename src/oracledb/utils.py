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

# -----------------------------------------------------------------------------
# utils.py
#
# Contains utility classes and methods.
# -----------------------------------------------------------------------------

from typing import Any, Callable, Optional, Union

from .arrow_array import ArrowArray
from .dataframe import DataFrame

from . import base_impl
from . import driver_mode
from . import errors
import uuid


def enable_thin_mode():
    """
    Makes python-oracledb be in Thin mode. After this method is called, Thick
    mode cannot be enabled. If python-oracledb is already in Thick mode, then
    calling ``enable_thin_mode()`` will fail. If connections have already been
    opened, or a connection pool created, in Thin mode, then calling
    ``enable_thin_mode()`` is a no-op.

    Since python-oracledb defaults to Thin mode, almost all applications do not
    need to call this method. However, because it bypasses python-oracledb's
    internal mode-determination heuristic, it may be useful for applications
    that are using standalone connections in multiple threads to concurrently
    create connections when the application starts.
    """
    with driver_mode.get_manager(requested_thin_mode=True):
        pass


def from_arrow(obj: Any) -> Union[DataFrame, ArrowArray]:
    """
    Uses the Arrow PyCapsule interface to return either a DataFrame or
    ArrowArray object, depending on what interface is supported by the object
    that is supplied to the function.
    """
    if hasattr(obj, "__arrow_c_stream__"):
        return DataFrame._from_arrow(obj)
    elif hasattr(obj, "__arrow_c_array__"):
        return ArrowArray._from_arrow(obj)
    msg = "object must implement the PyCapsule stream or array interfaces"
    raise ValueError(msg)


def normalize_sessionless_transaction_id(
    value: Optional[Union[bytes, str]] = None,
) -> bytes:
    """
    Normalize and validate the transaction_id.

    - If `value` is a string, it's UTF-8 encoded.
    - If `value` is None, a UUID4-based transaction_id is generated.
    - If `value` is not str/bytes/None, raises TypeError.
    - If transaction_id exceeds 64 bytes, raises ValueError.

    Returns:
        bytes: Normalized transaction_id
    """
    if value is None:
        value = uuid.uuid4().bytes
    elif isinstance(value, str):
        value = value.encode("utf-8")
    elif not isinstance(value, bytes):
        raise TypeError("invalid transaction_id: must be str, bytes, or None")

    if len(value) > 64:
        raise ValueError(
            f"transaction_id size exceeds 64 bytes (got {len(value)})"
        )

    return value


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


def register_params_hook(hook_function: Callable) -> None:
    """
    Registers a user function to be called internally prior to connection or
    pool creation. The hook function accepts a copy of the parameters that will
    be used to create the pool or standalone connection and may modify them.
    For example, the cloud native authentication plugins modify the
    "access_token" parameter with a function that will acquire the token using
    information found in the "extra_auth_parms" parameter.
    """
    if hook_function is None or not callable(hook_function):
        raise TypeError("hook_function must be a callable and cannot be None")
    base_impl.REGISTERED_PARAMS_HOOKS.append(hook_function)


def register_password_type(
    password_type: str, hook_function: Callable
) -> None:
    """
    Registers a user function to be called when a password is provided as a
    dictionary containing a key "type" with the specified value. The hook
    function is expected to use the dictionary and return the password value.
    If the supplied function is None, the registration is removed.
    """
    if not isinstance(password_type, str):
        raise TypeError("password_type must be a string")
    if hook_function is not None and not callable(hook_function):
        raise TypeError("hook_function must be a callable")
    password_type = password_type.lower()
    if hook_function is None:
        base_impl.REGISTERED_PASSWORD_TYPES.pop(password_type)
    else:
        base_impl.REGISTERED_PASSWORD_TYPES[password_type] = hook_function


def register_protocol(protocol: str, hook_function: Callable) -> None:
    """
    Registers a user function to be called prior to connection or pool creation
    when an Easy Connect connection string prefixed with the specified protocol
    is being parsed internally by python-oracledb in Thin mode. The registered
    function will also be invoked by ConnectParams.parse_connect_string() in
    Thin and Thick modes. Your hook function is expected to find or construct a
    valid connection string. If the supplied function is None, the registration
    is removed.
    """
    if not isinstance(protocol, str):
        raise TypeError("protocol must be a string")
    if hook_function is not None and not callable(hook_function):
        raise TypeError("hook_function must be a callable")
    protocol = protocol.lower()
    if hook_function is None:
        base_impl.REGISTERED_PROTOCOLS.pop(protocol)
    else:
        base_impl.REGISTERED_PROTOCOLS[protocol] = hook_function


def unregister_params_hook(hook_function: Callable) -> None:
    """
    Unregisters a user function that was earlier registered with a call to
    register_params_hook().
    """
    base_impl.REGISTERED_PARAMS_HOOKS.remove(hook_function)


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
