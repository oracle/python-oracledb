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
# defaults.py
#
# Contains the Defaults class used for managing default values used throughout
# the module.
# -----------------------------------------------------------------------------

from . import base_impl
from . import errors
from .base import BaseMetaClass


class Defaults(metaclass=BaseMetaClass):
    """
    A singleton Defaults object contains attributes to adjust default
    behaviors of python-oracledb. It is accessed using the :data:`defaults`
    attribute of the imported module.
    """

    def __init__(self) -> None:
        self._impl = base_impl.DEFAULTS

    @property
    def arraysize(self) -> int:
        """
        This read-write attribute specifies the default arraysize to use when
        cursors are created.

        It is an attribute for tuning the performance of fetching rows from
        Oracle Database. It does not affect data insertion.

        This value is the default for :attr:`Cursor.arraysize` and
        :attr:`AsyncCursor.arraysize`.

        This attribute has an initial value of *100*.
        """
        return self._impl.arraysize

    @arraysize.setter
    def arraysize(self, value: int):
        self._impl.arraysize = value

    @property
    def config_dir(self) -> str:
        """
        This read-write attribute specifies the directory in which the optional
        configuration file ``tnsnames.ora`` will be read in python-oracledb
        Thin mode. It is also used in Thick mode if
        :attr:`Defaults.thick_mode_dsn_passthrough` is *False*.

        At time of ``import oracledb`` the value of
        ``oracledb.defaults.config_dir`` will be set to (first one wins):

        - the value of ``$TNS_ADMIN``, if ``TNS_ADMIN`` is set.

        - ``$ORACLE_HOME/network/admin``, if ``$ORACLE_HOME`` is set.

        Otherwise, ``oracledb.defaults.config_dir`` will not be set.

        At completion of a call to :meth:`oracledb.init_oracle_client()` in
        python-oracledb Thick mode, the value of ``config_dir`` may get
        changed.
        """
        return self._impl.config_dir

    @config_dir.setter
    def config_dir(self, value: str):
        self._impl.config_dir = value

    @property
    def fetch_lobs(self) -> bool:
        """
        This read-write attribute specifies whether queries that contain LOBs
        should return LOB objects or their contents instead.

        When the value of this attribute is *True*, then queries to LOB columns
        return LOB locators. When the value of this attribute is *False*, then
        CLOBs and NCLOBs are fetched as strings, and BLOBs are fetched as
        bytes. If LOBs are larger than 1 GB, then this attribute should be set
        to *True* and the LOBs should be streamed.

        The value of ``oracledb.defaults.fetch_lobs`` does not affect LOBs
        returned as OUT binds.

        The value of ``fetch_lobs`` can be overridden at statement execution by
        passing an equivalent parameter.

        An output type handler such as the one previously required in the
        obsolete cx_Oracle driver can alternatively be used to adjust the
        returned type.  If a type handler exists and returns a variable (that
        is, `cursor.var(...)`), then that return variable is used. If the type
        handler returns *None*, then the value of
        ``oracledb.defaults.fetch_lobs`` is used.

        This attribute has an initial value of *True*.
        """
        return self._impl.fetch_lobs

    @fetch_lobs.setter
    def fetch_lobs(self, value: bool):
        self._impl.fetch_lobs = value

    @property
    def fetch_decimals(self) -> bool:
        """
        This read-write attribute specifies whether queries that contain
        numbers should be fetched as Python decimal.Decimal objects or floating
        point numbers. This can help avoid issues with converting numbers from
        Oracle Database's decimal format to Python's binary format.

        The value of ``fetch_decimals`` can be overridden at statement
        execution by passing an equivalent parameter.

        An output type handler such as previously required in the obsolete
        cx_Oracle driver can alternatively be used to adjust the returned type.
        If a type handler exists and returns a variable (that is,
        ``cursor.var(...)``), then that return variable is used. If the type
        handler returns *None*, then the value of
        ``oracledb.defaults.fetch_decimals`` is used to determine whether to
        return ``decimal.Decimal`` values.

        This attribute has an initial value of *False*.
        """
        return self._impl.fetch_decimals

    @fetch_decimals.setter
    def fetch_decimals(self, value: bool):
        self._impl.fetch_decimals = value

    @property
    def prefetchrows(self) -> int:
        """
        This read-write attribute specifies the default number of rows to
        prefetch when cursors are executed.

        This is an attribute for tuning the performance of fetching rows from
        Oracle Database. It does not affect data insertion.

        This value is the default for :attr:`Cursor.prefetchrows` and
        :attr:`AsyncCursor.prefetchrows`.

        This attribute is ignored when using :meth:`Connection.fetch_df_all()`
        or :meth:`Connection.fetch_df_batches()` since these methods always set
        the internal prefetch size to their relevant ``arraysize`` or ``size``
        parameter value.

        This attribute has an initial value of *2*.
        """
        return self._impl.prefetchrows

    @prefetchrows.setter
    def prefetchrows(self, value: int):
        self._impl.prefetchrows = value

    @property
    def stmtcachesize(self) -> int:
        """
        This read-write attribute specifies the default size of the statement
        cache.

        This is an attribute for tuning statement execution performance when a
        statement is executed more than once.

        This value is the default for :attr:`Connection.stmtcachesize`,
        :attr:`ConnectionPool.stmtcachesize`,
        :attr:`AsyncConnection.stmtcachesize`, and
        :attr:`AsyncConnectionPool.stmtcachesize`.

        This attribute has an initial value of *20*.
        """
        return self._impl.stmtcachesize

    @stmtcachesize.setter
    def stmtcachesize(self, value: int):
        self._impl.stmtcachesize = value

    @property
    def program(self) -> str:
        """
        This read-write attribute is a string recorded by Oracle Database
        as the program from which the connection originates.  This is the value
        used in the PROGRAM column of the V$SESSION view.

        This attribute has an initial value that is populated by
        `sys.executable <https://docs.python.org/3/library/sys.html#
        sys.executable>`__.

        This attribute is only used in python-oracledb Thin mode.
        """
        return self._impl.program

    @program.setter
    def program(self, value: str):
        if base_impl.sanitize(value) != value:
            errors._raise_err(errors.ERR_INVALID_NETWORK_NAME, name="program")
        self._impl.program = value

    @property
    def machine(self) -> str:
        """
        This read-write attribute is a string recorded by Oracle Database as
        the name of machine from which the connection originates. This is the
        value used in the MACHINE column of the V$SESSION view.

        This attribute takes the host name where the application is running as
        its initial value.

        This attribute is only used in python-oracledb Thin mode.
        """
        return self._impl.machine

    @machine.setter
    def machine(self, value: str):
        if base_impl.sanitize(value) != value:
            errors._raise_err(errors.ERR_INVALID_NETWORK_NAME, name="machine")
        self._impl.machine = value

    @property
    def terminal(self) -> str:
        """
        This read-write attribute specifies the terminal identifier from which
        the connection originates. This is the value used in the TERMINAL
        column of the V$SESSION view.

        This attribute has an initial value of "unknown".

        This attribute is only used in python-oracledb Thin mode.
        """
        return self._impl.terminal

    @terminal.setter
    def terminal(self, value: str):
        self._impl.terminal = value

    @property
    def osuser(self) -> str:
        """
        This read-write attribute is a string recorded by Oracle Database
        as the operating system user who originated the connection. This is the
        value used in the OSUSER column of the V$SESSION view.

        This attribute takes the login name of the user as its initial value.

        This attribute is only used in python-oracledb Thin mode.
        """
        return self._impl.osuser

    @osuser.setter
    def osuser(self, value: str):
        if base_impl.sanitize(value) != value:
            errors._raise_err(errors.ERR_INVALID_NETWORK_NAME, name="osuser")
        self._impl.osuser = value

    @property
    def driver_name(self) -> str:
        """
        This read-write attribute is a string recorded by Oracle Database
        as the name of the driver which originated the connection. This is the
        value used in the CLIENT_DRIVER column of the V$SESSION_CONNECT_INFO
        view.

        This attribute has an initial value of *None*. It is used as required
        in python-oracledb Thick and Thin mode.

        In python-oracledb Thick mode, this attribute is used if the
        ``driver_name`` parameter is not specified in
        :meth:`oracledb.init_oracle_client()`. In Thin mode, this attribute is
        used if the ``driver_name`` parameter is not specified in
        :meth:`oracledb.connect()`, :meth:`oracledb.connect_async()`,
        :meth:`oracledb.create_pool()`, or
        :meth:`oracledb.create_pool_async()`. If the value of this attribute is
        *None*, the value set when connecting in python-oracledb Thick mode is
        like "python-oracledb thk : <version>" and in Thin mode is like
        "python-oracledb thn : <version>".
        """
        return self._impl.driver_name

    @driver_name.setter
    def driver_name(self, value: str):
        self._impl.driver_name = value

    @property
    def thick_mode_dsn_passthrough(self) -> bool:
        """
        This read-write attribute determines whether
        connection strings passed as the ``dsn`` parameter to
        :meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
        :meth:`oracledb.connect_async()`, and
        :meth:`oracledb.create_pool_async()` in python-oracledb Thick mode will
        be parsed by Oracle Client libraries or by python-oracledb itself.

        The value of ``thick_mode_dsn_passthrough`` is ignored in
        python-oracledb Thin mode, which always parses all connect strings
        (including reading a tnsnames.ora file, if required).

        This attribute has an initial value of *True*.
        """
        return self._impl.thick_mode_dsn_passthrough

    @thick_mode_dsn_passthrough.setter
    def thick_mode_dsn_passthrough(self, value: str):
        self._impl.thick_mode_dsn_passthrough = value


defaults = Defaults()
