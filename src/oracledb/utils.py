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

import functools
from typing import Any, Callable, Optional, Union
import uuid

from .arrow_array import ArrowArray
from .dataframe import DataFrame

from . import base_impl
from . import driver_mode
from . import errors
from . import thick_impl


def clientversion() -> tuple:
    """
    This function can only be called when python-oracledb is in Thick mode.
    Using it in Thin mode will throw an exception.
    """
    return thick_impl.clientversion()


def enable_thin_mode():
    """
    Makes python-oracledb be in Thin mode. After this method is called, Thick
    mode cannot be enabled. If python-oracledb is already in Thick mode, then
    calling ``enable_thin_mode()`` will fail. If Thin mode connections have
    already been opened, or a connection pool created in Thin mode, then
    calling ``enable_thin_mode()`` is a no-op.

    Since python-oracledb defaults to Thin mode, almost all applications do not
    need to call this method. However, because it bypasses python-oracledb's
    internal mode-determination heuristic, it may be useful for applications
    with multiple threads that concurrently create :ref:`standalone connections
    <standaloneconnection>` when the application starts.
    """
    with driver_mode.get_manager(requested_thin_mode=True):
        pass


def from_arrow(obj: Any) -> Union[DataFrame, ArrowArray]:
    """
    This method converts a data frame to a
    :ref:`DataFrame <oracledataframeobj>` or
    :ref:`ArrowArray <oraclearrowarrayobj>` instance.

    If ``obj`` supports the Arrow PyCapsule interface ``__arrow_c_stream__``
    method, then ``from_arrow()`` returns the instance as a :ref:`DataFrame
    <oracledataframeobj>`. If ``obj`` does not support that method, but does
    support ``__arrow_c_array__``, then an :ref:`ArrowArray
    <oraclearrowarrayobj>` is returned.
    """
    if hasattr(obj, "__arrow_c_stream__"):
        return DataFrame._from_arrow(obj)
    elif hasattr(obj, "__arrow_c_array__"):
        return ArrowArray._from_arrow(obj)
    msg = "object must implement the PyCapsule stream or array interfaces"
    raise ValueError(msg)


def init_oracle_client(
    lib_dir: Optional[Union[str, bytes]] = None,
    config_dir: Optional[Union[str, bytes]] = None,
    error_url: Optional[str] = None,
    driver_name: Optional[str] = None,
):
    """
    Enables python-oracledb Thick mode by initializing the Oracle Client
    library, see :ref:`enablingthick`. If a standalone connection or pool has
    already been created in Thin mode, ``init_oracle_client()`` will raise an
    exception and python-oracledb will remain in Thin mode.

    If a standalone connection or pool has *not* already been created in Thin
    mode, but ``init_oracle_client()`` raises an exception, python-oracledb
    will remain in Thin mode but further calls to ``init_oracle_client()`` can
    be made, if desired.

    The ``init_oracle_client()`` method can be called multiple times in each
    Python process as long as the arguments are the same each time.

    The ``lib_dir`` parameter is a string or a bytes object that specifies the
    directory containing Oracle Client libraries.  If the ``lib_dir`` parameter
    is set, then the specified directory is the only one searched for the
    Oracle Client libraries; otherwise, the operating system library search
    path is used to locate the Oracle Client library.  If you are using Python
    3.11 and later, then the value specified in this parameter is encoded
    using `locale.getencoding() <https://docs.python.org/3/library/locale.html
    #locale.getencoding>`__.  For all other Python versions, the encoding
    "utf-8" is used.  If a bytes object is specified in this parameter, then
    this value will be used as is without any encoding.

    The ``config_dir`` parameter is a string or a bytes object that specifies
    the directory in which the
    :ref:`Optional Oracle Net Configuration <optnetfiles>` and
    :ref:`Optional Oracle Client Configuration <optclientfiles>` files reside.
    If the ``config_dir`` parameter is set, then the specified directory is
    used to find Oracle Client library configuration files.  This is
    equivalent to setting the environment variable ``TNS_ADMIN`` and overrides
    any value already set in ``TNS_ADMIN``.  If this parameter is not set, the
    :ref:`Oracle standard <usingconfigfiles>` way of locating Oracle Client
    library configuration files is used.  If you are using Python 3.11 and
    later, then the value specified in this parameter is encoded using
    `locale.getencoding() <https://docs.python.org/3/library/locale.html#
    locale.getencoding>`__.  For all other Python versions, the encoding
    "utf-8" is used.  If a bytes object is specified in this parameter, then
    this value will be used as is without any encoding.

    The ``error_url`` parameter is a string that specifies the URL which is
    included in the python-oracledb exception message if the Oracle Client
    libraries cannot be loaded.  If the ``error_url`` parameter is set, then
    the specified value is included in the message of the exception raised
    when the Oracle Client library cannot be loaded; otherwise, the
    :ref:`installation` URL is included.  This parameter lets your application
    display custom installation instructions.

    The ``driver_name`` parameter is a string that specifies the driver name
    value. If the ``driver_name`` parameter is set, then the specified value
    can be found in database views that give information about connections.
    For example, it is in the CLIENT_DRIVER column of the
    V$SESSION_CONNECT_INFO view. From Oracle Database 12.2, the name displayed
    can be 30 characters.  The standard is to set this value to ``"<name> :
    version>"``, where <name> is the name of the driver and <version> is its
    version. There should be a single space character before and after the
    colon. If this parameter is not set, then the value specified in
    :attr:`oracledb.defaults.driver_name <defaults.driver_name>` is used. If
    the value of this attribute is *None*, then the default value in
    python-oracledb Thick mode is like "python-oracledb thk : <version>". See
    :ref:`otherinit`.

    At successful completion of a call to ``oracledb.init_oracle_client()``,
    the attribute :attr:`oracledb.defaults.config_dir <Defaults.config_dir>`
    will be set as determined below (first one wins):

    - the value of the ``oracledb.init_oracle_client()`` parameter
      ``config_dir``, if one was passed.

    - the value of :attr:`oracledb.defaults.config_dir <Defaults.config_dir>`
      if it has one. i.e.
      :attr:`oracledb.defaults.config_dir <Defaults.config_dir>` remains
      unchanged after ``oracledb.init_oracle_client()`` completes.

    - the value of the environment variable ``$TNS_ADMIN``, if it is set.

    - the value of ``$ORACLE_HOME/network/admin`` if the environment variable
      ``$ORACLE_HOME`` is set.

    - the directory of the loaded Oracle Client library, appended with
      ``network/admin``. Note this directory is not determinable on AIX.

    - otherwise the value *None* is used. (Leaving
      :attr:`oracledb.defaults.config_dir <Defaults.config_dir>` unchanged).
    """
    thick_impl.init_oracle_client(lib_dir, config_dir, error_url, driver_name)


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

    @functools.wraps(f)
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

    @functools.wraps(f)
    def wrapped_f(self, *args, **kwargs):
        f(self, *args, **kwargs)
        self._impl.set(kwargs)

    return wrapped_f


def register_params_hook(hook_function: Callable) -> None:
    """
    Registers a user parameter hook function that will be called internally by
    python-oracledb prior to connection or pool creation. The hook function
    accepts a copy of the parameters that will be used to create the pool or
    standalone connection and may modify them. For example, the cloud native
    authentication plugins modify the "access_token" parameter with a function
    that will acquire the token using information found in the
    "extra_auth_parms" parameter.

    Multiple hooks may be registered. They will be invoked in order of
    registration.
    """
    if hook_function is None or not callable(hook_function):
        raise TypeError("hook_function must be a callable and cannot be None")
    base_impl.REGISTERED_PARAMS_HOOKS.append(hook_function)


def register_password_type(
    password_type: str, hook_function: Callable
) -> None:
    """
    Registers a user password hook function that will be called internally by
    python-oracledb when a password is supplied as a dictionary containing the
    given ``password_type`` as the key "type". The hook function is called for
    passwords specified as the ``password``, ``newpassword`` and
    ``wallet_parameter`` parameters in calls to :meth:`oracledb.connect()`,
    :meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, and
    :meth:`oracledb.create_pool_async()`.

    Your hook function is expected to accept the dictionary supplied by the
    application and return the valid password.

    Calling :meth:`~oracledb.register_password_type()` with the
    ``hook_function`` parameter set to *None* will result in a previously
    registered user function being removed and the default behavior restored.
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
    Registers a user protocol hook function that will be called internally by
    python-oracledb Thin mode prior to connection or pool creation.  The hook
    function will be invoked when :func:`oracledb.connect`,
    :func:`oracledb.create_pool`, :meth:`oracledb.connect_async()`, or
    :meth:`oracledb.create_pool_async()` are called with a ``dsn`` parameter
    value prefixed with the specified protocol. The user function will also be
    invoked when :meth:`ConnectParams.parse_connect_string()` is called in Thin
    or Thick modes with a similar ``connect_string`` parameter value.

    Your hook function is expected to construct valid connection details. For
    example, if a hook function is registered for the "ldaps" protocol, then
    calling :func:`oracledb.connect` with a connection string prefixed with
    "ldaps://" will invoke the function.  The function can then perform LDAP
    lookup to retrieve and set the actual database information that will be
    used internally by python-oracledb to complete the connection creation.

    The ``protocol`` parameter is a string that will be matched against the
    prefix appearing before "://" in connection strings.

    The ``hook_function`` parameter should be a function with the signature::

        hook_function(protocol, protocol_arg, params)

    The hook function will be called with the following arguments:

    - The ``protocol`` parameter is the value that was registered.

    - The ``protocol_arg`` parameter is the section after "://" in the
      connection string used in the connection or pool creation call, or passed
      to :meth:`~ConnectParams.parse_connect_string()`.

    - The ``params`` parameter is an instance of :ref:`ConnectParams
      <connparam>`.

      When your hook function is invoked internally prior to connection or pool
      creation, ``params`` will be the ConnectParams instance originally passed
      to the :func:`oracledb.connect`, :func:`oracledb.create_pool`,
      :meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()`
      call, if such an instance was passed.  Otherwise it will be a new
      ConnectParams instance.  The hook function should parse ``protocol`` and
      ``protocol_arg`` and take any desired action to update ``params``
      :ref:`attributes <connparamsattr>` with appropriate connection
      parameters. Attributes can be set using :meth:`ConnectParams.set()` or
      :meth:`ConnectParams.parse_connect_string()`. The ConnectParams instance
      will then be used to complete the connection or pool creation.

      When your hook function is invoked by
      :meth:`ConnectParams.parse_connect_string()`, then ``params`` will be the
      invoking ConnectParams instance that you can update using
      :meth:`ConnectParams.set()` or
      :meth:`ConnectParams.parse_connect_string()`.

    Internal hook functions for the "tcp" and "tcps" protocols are
    pre-registered but can be overridden if needed. If any other protocol has
    not been registered, then connecting will result in the error ``DPY-4021:
    invalid protocol``.

    Calling :meth:`~oracledb.register_protocol()` with the ``hook_function``
    parameter set to *None* will result in a previously registered user
    function being removed and the default behavior restored.
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
    Unregisters a user parameter function that was earlier registered with a
    call to :meth:`oracledb.register_params_hook()`.
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
