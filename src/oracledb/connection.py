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
# connection.py
#
# Contains the Connection class and the factory method connect() used for
# establishing connections to the database.
#
# *** NOTICE *** This file is generated from a template and should not be
# modified directly. See build_from_template.py in the utils subdirectory for
# more information.
# -----------------------------------------------------------------------------

import collections
import functools
import ssl
from typing import Any, Callable, Type, Optional, Union

import oracledb

from . import __name__ as MODULE_NAME

from . import base_impl, driver_mode, errors, thick_impl, thin_impl
from . import pool as pool_module
from .aq import AsyncQueue, Queue, MessageProperties
from .base_impl import DB_TYPE_BLOB, DB_TYPE_CLOB, DB_TYPE_NCLOB, DbType
from .connect_params import ConnectParams
from .cursor import AsyncCursor, Cursor
from .dbobject import DbObjectType, DbObject
from .lob import AsyncLOB, LOB
from .pipeline import Pipeline
from .soda import SodaDatabase
from .subscr import Subscription
from .utils import normalize_sessionless_transaction_id

# named tuple used for representing global transactions
Xid = collections.namedtuple(
    "Xid", ["format_id", "global_transaction_id", "branch_qualifier"]
)


class BaseConnection:
    __module__ = MODULE_NAME
    _impl = None

    def __init__(self):
        self._version = None

    def __repr__(self):
        typ = self.__class__
        cls_name = f"{typ.__module__}.{typ.__qualname__}"
        if self._impl is None:
            return f"<{cls_name} disconnected>"
        elif self.username is None:
            return f"<{cls_name} to externally identified user>"
        return f"<{cls_name} to {self.username}@{self.dsn}>"

    def _verify_connected(self) -> None:
        """
        Verifies that the connection is connected to the database. If it is
        not, an exception is raised.
        """
        if self._impl is None:
            errors._raise_err(errors.ERR_NOT_CONNECTED)

    def _verify_xid(self, xid: Xid) -> None:
        """
        Verifies that the supplied xid is of the correct type.
        """
        if not isinstance(xid, Xid):
            message = "expecting transaction id created with xid()"
            raise TypeError(message)

    @property
    def action(self) -> None:
        raise AttributeError("action is not readable")

    @action.setter
    def action(self, value: str) -> None:
        """
        Specifies the action column in the v$session table. It is a string
        attribute but the value None is also accepted and treated as an empty
        string.
        """
        self._verify_connected()
        self._impl.set_action(value)

    @property
    def autocommit(self) -> bool:
        """
        Specifies whether autocommit mode is on or off. When autocommit mode is
        on, all statements are committed as soon as they have completed
        executing successfully.
        """
        self._verify_connected()
        return self._impl.autocommit

    @autocommit.setter
    def autocommit(self, value: bool) -> None:
        self._verify_connected()
        self._impl.autocommit = value

    def begin_sessionless_transaction(
        self,
        transaction_id: Optional[Union[str, bytes]] = None,
        timeout: int = 60,
        defer_round_trip: bool = False,
    ) -> bytes:
        """
        Begins a new sessionless transaction.

        Parameters:
            transaction_id (str or bytes, optional): A Transaction Identifier.
               If None, a random transaction_id will be generated.
            timeout (int, optional): Timeout value in seconds.
               Must be a positive integer. Defaults to 60 if not provided.
            defer_round_trip (bool, optional):
                If True, the request is not sent immediately but included
                with the next database operation.

        Returns:
            bytes: The normalized transaction_id used for the transaction.
        """
        self._verify_connected()
        normalized_txnid = normalize_sessionless_transaction_id(transaction_id)

        if not isinstance(timeout, int) or timeout <= 0:
            raise TypeError("timeout must be a positive integer")

        self._impl.begin_sessionless_transaction(
            normalized_txnid, timeout, defer_round_trip
        )
        return normalized_txnid

    @property
    def call_timeout(self) -> int:
        """
        Specifies the amount of time (in milliseconds) that a single round-trip
        to the database may take before a timeout will occur. A value of 0
        means that no timeout will take place.
        """
        self._verify_connected()
        return self._impl.get_call_timeout()

    @call_timeout.setter
    def call_timeout(self, value: int) -> None:
        self._verify_connected()
        self._impl.set_call_timeout(value)

    def cancel(self) -> None:
        """
        Break a long-running transaction.
        """
        self._verify_connected()
        self._impl.cancel()

    @property
    def client_identifier(self) -> None:
        raise AttributeError("client_identifier is not readable")

    @client_identifier.setter
    def client_identifier(self, value: str) -> None:
        """
        Specifies the client_identifier column in the v$session table.
        """
        self._verify_connected()
        self._impl.set_client_identifier(value)

    @property
    def clientinfo(self) -> None:
        raise AttributeError("clientinfo is not readable")

    @clientinfo.setter
    def clientinfo(self, value: str) -> None:
        """
        Specifies the client_info column in the v$session table.
        """
        self._verify_connected()
        self._impl.set_client_info(value)

    @property
    def current_schema(self) -> str:
        """
        Specifies the current schema for the session. Setting this value is the
        same as executing the SQL statement "ALTER SESSION SET CURRENT_SCHEMA".
        The attribute is set (and verified) on the next call that does a round
        trip to the server. The value is placed before unqualified database
        objects in SQL statements you then execute.
        """
        self._verify_connected()
        return self._impl.get_current_schema()

    @current_schema.setter
    def current_schema(self, value: str) -> None:
        self._verify_connected()
        self._impl.set_current_schema(value)

    @property
    def dbop(self) -> None:
        raise AttributeError("dbop is not readable")

    @dbop.setter
    def dbop(self, value: str) -> None:
        """
        Specifies the database operation that is to be monitored. This can be
        viewed in the DBOP_NAME column of the V$SQL_MONITOR table.
        """
        self._verify_connected()
        self._impl.set_dbop(value)

    @property
    def dsn(self) -> str:
        """
        Specifies the connection string (TNS entry) of the database to which a
        connection has been established.
        """
        self._verify_connected()
        return self._impl.dsn

    @property
    def econtext_id(self) -> None:
        raise AttributeError("econtext_id is not readable")

    @econtext_id.setter
    def econtext_id(self, value: str) -> None:
        """
        Specifies the execution context id. This value can be found as ecid in
        the v$session table and econtext_id in the auditing tables. The maximum
        length is 64 bytes.
        """
        self._verify_connected()
        self._impl.set_econtext_id(value)

    @property
    def db_domain(self) -> str:
        """
        Specifies the name of the database domain.
        """
        self._verify_connected()
        return self._impl.get_db_domain()

    @property
    def db_name(self) -> str:
        """
        Specifies the name of the database.
        """
        self._verify_connected()
        return self._impl.get_db_name()

    @property
    def session_id(self) -> int:
        """
        Specifies the session identifier.
        """
        self._verify_connected()
        return self._impl.get_session_id()

    @property
    def serial_num(self) -> int:
        """
        Specifies the session serial number.
        """
        self._verify_connected()
        return self._impl.get_serial_num()

    @property
    def edition(self) -> str:
        """
        Specifies the session edition.
        """
        self._verify_connected()
        return self._impl.get_edition()

    @property
    def external_name(self) -> str:
        """
        Specifies the external name that is used by the connection when logging
        distributed transactions.
        """
        self._verify_connected()
        return self._impl.get_external_name()

    @external_name.setter
    def external_name(self, value: str) -> None:
        self._verify_connected()
        self._impl.set_external_name(value)

    @property
    def inputtypehandler(self) -> Callable:
        """
        Specifies a method called for each value that is bound to a statement
        executed on any cursor associated with this connection. The method
        signature is handler(cursor, value, arraysize) and the return value is
        expected to be a variable object or None in which case a default
        variable object will be created. If this attribute is None, the default
        behavior will take place for all values bound to statements.
        """
        self._verify_connected()
        return self._impl.inputtypehandler

    @inputtypehandler.setter
    def inputtypehandler(self, value: Callable) -> None:
        self._verify_connected()
        self._impl.inputtypehandler = value

    @property
    def instance_name(self) -> str:
        """
        Returns the instance name associated with the connection. This is the
        equivalent of the SQL expression:

        sys_context('userenv', 'instance_name')
        """
        self._verify_connected()
        return self._impl.get_instance_name()

    @property
    def internal_name(self) -> str:
        """
        Specifies the internal name that is used by the connection when logging
        distributed transactions.
        """
        self._verify_connected()
        return self._impl.get_internal_name()

    @internal_name.setter
    def internal_name(self, value: str) -> None:
        self._verify_connected()
        self._impl.set_internal_name(value)

    def is_healthy(self) -> bool:
        """
        Returns a boolean indicating the health status of a connection.

        Connections may become unusable in several cases, such as if the
        network socket is broken, if an Oracle error indicates the connection
        is unusable, or after receiving a planned down notification from the
        database.

        This function is best used before starting a new database request on an
        existing standalone connection. Pooled connections internally perform
        this check before returning a connection to the application.

        If this function returns False, the connection should be not be used by
        the application and a new connection should be established instead.

        This function performs a local check. To fully check a connection's
        health, use ping() which performs a round-trip to the database.
        """
        return self._impl is not None and self._impl.get_is_healthy()

    @property
    def ltxid(self) -> bytes:
        """
        Returns the logical transaction id for the connection. It is used
        within Oracle Transaction Guard as a means of ensuring that
        transactions are not duplicated. See the Oracle documentation and the
        provided sample for more information.
        """
        self._verify_connected()
        return self._impl.get_ltxid()

    @property
    def max_identifier_length(self) -> int:
        """
        Returns the maximum length of identifiers supported by the database to
        which this connection has been established.
        """
        self._verify_connected()
        return self._impl.get_max_identifier_length()

    @property
    def max_open_cursors(self) -> int:
        """
        Specifies the maximum number of cursors that the database can have open
        concurrently.
        """
        self._verify_connected()
        return self._impl.get_max_open_cursors()

    @property
    def module(self) -> None:
        raise AttributeError("module is not readable")

    @module.setter
    def module(self, value: str) -> None:
        """
        Specifies the module column in the v$session table. The maximum length
        for this string is 48 and if you exceed this length you will get
        ORA-24960.
        """
        self._verify_connected()
        self._impl.set_module(value)

    def msgproperties(
        self,
        payload: Optional[Union[bytes, str, DbObject]] = None,
        correlation: Optional[str] = None,
        delay: Optional[int] = None,
        exceptionq: Optional[str] = None,
        expiration: Optional[int] = None,
        priority: Optional[int] = None,
        recipients: Optional[list] = None,
    ) -> MessageProperties:
        """
        Create and return a message properties object. If the parameters are
        not None, they act as a shortcut for setting each of the equivalently
        named properties.
        """
        impl = self._impl.create_msg_props_impl()
        props = MessageProperties._from_impl(impl)
        if payload is not None:
            props.payload = payload
        if correlation is not None:
            props.correlation = correlation
        if delay is not None:
            props.delay = delay
        if exceptionq is not None:
            props.exceptionq = exceptionq
        if expiration is not None:
            props.expiration = expiration
        if priority is not None:
            props.priority = priority
        if recipients is not None:
            props.recipients = recipients
        return props

    def queue(
        self,
        name: str,
        payload_type: Optional[Union[DbObjectType, str]] = None,
        *,
        payloadType: Optional[DbObjectType] = None,
    ) -> Queue:
        """
        Creates and returns a queue which is used to enqueue and dequeue
        messages in Advanced Queueing (AQ).

        The name parameter is expected to be a string identifying the queue in
        which messages are to be enqueued or dequeued.

        The payload_type parameter, if specified, is expected to be an
        object type that identifies the type of payload the queue expects.
        If the string "JSON" is specified, JSON data is enqueued and dequeued.
        If not specified, RAW data is enqueued and dequeued.
        """
        self._verify_connected()
        payload_type_impl = None
        is_json = False
        if payloadType is not None:
            if payload_type is not None:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="payloadType",
                    new_name="payload_type",
                )
            payload_type = payloadType
        if payload_type is not None:
            if payload_type == "JSON":
                is_json = True
            elif not isinstance(payload_type, DbObjectType):
                raise TypeError("expecting DbObjectType")
            else:
                payload_type_impl = payload_type._impl
        impl = self._impl.create_queue_impl()
        impl.initialize(self._impl, name, payload_type_impl, is_json)
        return self._create_queue(impl)

    @property
    def outputtypehandler(self) -> Callable:
        """
        Specifies a method called for each column that is going to be fetched
        from any cursor associated with this connection. The method signature
        is handler(cursor, name, defaultType, length, precision, scale) and the
        return value is expected to be a variable object or None in which case
        a default variable object will be created. If this attribute is None,
        the default behavior will take place for all columns fetched from
        cursors associated with this connection.
        """
        self._verify_connected()
        return self._impl.outputtypehandler

    @outputtypehandler.setter
    def outputtypehandler(self, value: Callable) -> None:
        self._verify_connected()
        self._impl.outputtypehandler = value

    def resume_sessionless_transaction(
        self,
        transaction_id: Union[str, bytes],
        timeout: int = 60,
        defer_round_trip: bool = False,
    ) -> bytes:
        """
        Resumes an existing sessionless transaction using the given
        transaction_id.

        Parameters:
            transaction_id (str or bytes): A Transaction Identifier that
              uniquely identifies the sessionless transaction to be
              resumed. This parameter is mandatory.
            timeout (int, optional): Timeout in seconds for the resumed
              transaction. Must be a positive integer. Defaults to 60.
            defer_round_trip (bool, optional):
                If True, the request is not sent immediately but included
                with the next database operation.

        Returns:
            bytes: The normalized transaction_id used to resume the
              sessionless transaction.
        """
        self._verify_connected()
        if transaction_id is None:
            raise ValueError("transaction_id is required for resuming")

        normalized_txnid = normalize_sessionless_transaction_id(transaction_id)

        if not (isinstance(timeout, int) and timeout >= 0):
            raise TypeError("timeout must be a non-negative integer")

        self._impl.resume_sessionless_transaction(
            normalized_txnid, timeout, defer_round_trip
        )
        return normalized_txnid

    @property
    def sdu(self) -> int:
        """
        Specifies the size of the Session Data Unit (SDU) that is being used by
        the connection.
        """
        self._verify_connected()
        return self._impl.get_sdu()

    @property
    def service_name(self) -> str:
        """
        Specifies the name of the service that was used to connect to the
        database.
        """
        self._verify_connected()
        return self._impl.get_service_name()

    @property
    def stmtcachesize(self) -> int:
        """
        Specifies the size of the statement cache. This value can make a
        significant difference in performance (up to 100x) if you have a small
        number of statements that you execute repeatedly.
        """
        self._verify_connected()
        return self._impl.get_stmt_cache_size()

    @stmtcachesize.setter
    def stmtcachesize(self, value: int) -> None:
        self._verify_connected()
        self._impl.set_stmt_cache_size(value)

    @property
    def thin(self) -> bool:
        """
        Returns a boolean indicating if the connection was established in
        python-oracledb's thin mode (True) or thick mode (False).
        """
        self._verify_connected()
        return self._impl.thin

    @property
    def transaction_in_progress(self) -> bool:
        """
        Specifies whether a transaction is currently in progress on the
        database using this connection.
        """
        self._verify_connected()
        return self._impl.get_transaction_in_progress()

    @property
    def username(self) -> str:
        """
        Returns the name of the user which established the connection to the
        database.
        """
        self._verify_connected()
        return self._impl.username

    @property
    def version(self) -> str:
        """
        Returns the version of the database to which the connection has been
        established.
        """
        if self._version is None:
            self._verify_connected()
            self._version = ".".join(str(c) for c in self._impl.server_version)
        return self._version

    @property
    def warning(self) -> errors._Error:
        """
        Returns any warning that was generated when the connection was created,
        or the value None if no warning was generated. The value will be
        cleared for pooled connections after they are returned to the pool.
        """
        self._verify_connected()
        return self._impl.warning

    def xid(
        self,
        format_id: int,
        global_transaction_id: Union[bytes, str],
        branch_qualifier: Union[bytes, str],
    ) -> Xid:
        """
        Returns a global transaction identifier that can be used with the TPC
        (two-phase commit) functions.

        The format_id parameter should be a non-negative 32-bit integer. The
        global_transaction_id and branch_qualifier parameters should be bytes
        (or a string which will be UTF-8 encoded to bytes) of no more than 64
        bytes.
        """
        return Xid(format_id, global_transaction_id, branch_qualifier)


class Connection(BaseConnection):
    __module__ = MODULE_NAME

    def __init__(
        self,
        dsn: Optional[str] = None,
        *,
        pool: Optional["pool_module.ConnectionPool"] = None,
        params: Optional[ConnectParams] = None,
        **kwargs,
    ) -> None:
        """
        Constructor for creating a connection to the database.

        The dsn parameter (data source name) can be a string in the format
        user/password@connect_string or can simply be the connect string (in
        which case authentication credentials such as the username and password
        need to be specified separately). See the documentation on connection
        strings for more information.

        The pool parameter is expected to be a pool object and the use of this
        parameter is the equivalent of calling acquire() on the pool.

        The params parameter is expected to be of type ConnectParams and
        contains connection parameters that will be used when establishing the
        connection. See the documentation on ConnectParams for more
        information. If this parameter is not specified, the additional keyword
        parameters will be used to create an instance of ConnectParams. If both
        the params parameter and additional keyword parameters are specified,
        the values in the keyword parameters have precedence. Note that if a
        dsn is also supplied, then in the python-oracledb Thin mode, the values
        of the parameters specified (if any) within the dsn will override the
        values passed as additional keyword parameters, which themselves
        override the values set in the params parameter object.
        """

        super().__init__()
        self._pool = pool

        # determine if thin mode is being used
        with driver_mode.get_manager() as mode_mgr:
            thin = mode_mgr.thin

            # determine which connection parameters to use
            if params is None:
                params_impl = base_impl.ConnectParamsImpl()
            elif not isinstance(params, ConnectParams):
                errors._raise_err(errors.ERR_INVALID_CONNECT_PARAMS)
            else:
                params_impl = params._impl.copy()
            dsn = params_impl.process_args(dsn, kwargs, thin)

            # see if connection is being acquired from a pool
            if pool is None:
                pool_impl = None
            else:
                pool._verify_open()
                pool_impl = pool._impl

            # create thin or thick implementation object
            if thin:
                if (
                    params_impl.shardingkey is not None
                    or params_impl.supershardingkey is not None
                ):
                    errors._raise_err(
                        errors.ERR_FEATURE_NOT_SUPPORTED,
                        feature="sharding",
                        driver_type="thick",
                    )
                if pool is not None:
                    impl = pool_impl.acquire(params_impl)
                else:
                    impl = thin_impl.ThinConnImpl(dsn, params_impl)
                    impl.connect(params_impl)
            else:
                impl = thick_impl.ThickConnImpl(dsn, params_impl)
                impl.connect(params_impl, pool_impl)
            self._impl = impl

            # invoke callback, if applicable
            if (
                impl.invoke_session_callback
                and pool is not None
                and pool.session_callback is not None
                and callable(pool.session_callback)
            ):
                pool.session_callback(self, params_impl.tag)
                impl.invoke_session_callback = False

    def __del__(self):
        if self._impl is not None:
            self._close(in_del=True)

    def __enter__(self):
        self._verify_connected()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self._impl is not None:
            self._close()

    def _close(self, in_del=False):
        """
        Closes the connection and makes it unusable for further operations. An
        Error exception will be raised if any operation is attempted with this
        connection after this method completes successfully.
        """
        if self._pool is not None:
            pool_impl = self._pool._impl
            if pool_impl is not None:
                pool_impl.return_connection(self._impl, in_del)
        else:
            self._impl.close(in_del)
        self._impl = None

    def _create_queue(self, impl):
        """
        Returns a queue object that the user can use to dequeue and enqueue
        messages.
        """
        return Queue._from_impl(self, impl)

    def _get_oci_attr(
        self, handle_type: int, attr_num: int, attr_type: int
    ) -> Any:
        """
        Returns the value of the specified OCI attribute from the internal
        handle. This is only supported in python-oracledb thick mode and should
        only be used as directed by Oracle.
        """
        self._verify_connected()
        return self._impl._get_oci_attr(handle_type, attr_num, attr_type)

    def _set_oci_attr(
        self, handle_type: int, attr_num: int, attr_type: int, value: Any
    ) -> None:
        """
        Sets the value of the specified OCI attribute on the internal handle.
        This is only supported in python-oracledb thick mode and should only
        be used as directed by Oracle.
        """
        self._verify_connected()
        self._impl._set_oci_attr(handle_type, attr_num, attr_type, value)

    def begin(
        self,
        format_id: int = -1,
        transaction_id: str = "",
        branch_id: str = "",
    ) -> None:
        """
        Deprecated. Use tpc_begin() instead.
        """
        if format_id != -1:
            self.tpc_begin(self.xid(format_id, transaction_id, branch_id))

    @property
    def callTimeout(self) -> int:
        """
        Deprecated. Use property call_timeout instead.
        """
        return self.call_timeout

    @callTimeout.setter
    def callTimeout(self, value: int) -> None:
        self._verify_connected()
        self._impl.set_call_timeout(value)

    def changepassword(self, old_password: str, new_password: str) -> None:
        """
        Changes the password for the user to which the connection is connected.
        """
        self._verify_connected()
        self._impl.change_password(old_password, new_password)

    def close(self) -> None:
        """
        Closes the connection and makes it unusable for further operations. An
        Error exception will be raised if any operation is attempted with this
        connection after this method completes successfully.
        """
        self._verify_connected()
        self._close()

    def commit(self) -> None:
        """
        Commits any pending transactions to the database.
        """
        self._verify_connected()
        self._impl.commit()

    def createlob(
        self, lob_type: DbType, data: Optional[Union[str, bytes]] = None
    ) -> LOB:
        """
        Create and return a new temporary LOB of the specified type.
        """
        self._verify_connected()
        if lob_type not in (DB_TYPE_CLOB, DB_TYPE_NCLOB, DB_TYPE_BLOB):
            message = (
                "parameter should be one of oracledb.DB_TYPE_CLOB, "
                "oracledb.DB_TYPE_BLOB or oracledb.DB_TYPE_NCLOB"
            )
            raise TypeError(message)
        impl = self._impl.create_temp_lob_impl(lob_type)
        lob = LOB._from_impl(impl)
        if data:
            lob.write(data)
        return lob

    def cursor(self, scrollable: bool = False) -> Cursor:
        """
        Returns a cursor associated with the connection.
        """
        self._verify_connected()
        return Cursor(self, scrollable)

    def decode_oson(self, data):
        """
        Decode OSON-encoded bytes and return the object encoded in those bytes.
        """
        self._verify_connected()
        return self._impl.decode_oson(data)

    def encode_oson(self, value):
        """
        Return OSON-encoded bytes encoded from the supplied object.
        """
        self._verify_connected()
        return self._impl.encode_oson(value)

    def fetch_df_all(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        arraysize: Optional[int] = None,
    ):
        """
        Fetch all data as an instance of DataFrame.
        """
        cursor = self.cursor()
        cursor._impl.fetching_arrow = True
        if arraysize is not None:
            cursor.arraysize = arraysize
        cursor.prefetchrows = cursor.arraysize
        cursor.execute(statement, parameters)
        return cursor._impl.fetch_df_all(cursor)

    def fetch_df_batches(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        size: Optional[int] = None,
    ):
        """
        Fetch data in batches. Each batch is an instance of DataFrame
        """
        cursor = self.cursor()
        cursor._impl.fetching_arrow = True
        if size is not None:
            cursor.arraysize = size
        cursor.prefetchrows = cursor.arraysize
        cursor.execute(statement, parameters)
        if size is None:
            yield cursor._impl.fetch_df_all(cursor)
        else:
            yield from cursor._impl.fetch_df_batches(cursor, batch_size=size)

    def getSodaDatabase(self) -> SodaDatabase:
        """
        Return a SODA database object for performing all operations on Simple
        Oracle Document Access (SODA).
        """
        self._verify_connected()
        db_impl = self._impl.create_soda_database_impl(self)
        return SodaDatabase._from_impl(self, db_impl)

    def gettype(self, name: str) -> DbObjectType:
        """
        Return a type object given its name. This can then be used to create
        objects which can be bound to cursors created by this connection.
        """
        self._verify_connected()
        obj_type_impl = self._impl.get_type(self, name)
        return DbObjectType._from_impl(obj_type_impl)

    @property
    def handle(self) -> int:
        """
        Returns the OCI service context handle for the connection. It is
        primarily provided to facilitate testing the creation of a connection
        using the OCI service context handle.

        This property is only relevant to python-oracledb's thick mode.
        """
        self._verify_connected()
        return self._impl.get_handle()

    @property
    def maxBytesPerCharacter(self) -> int:
        """
        Deprecated. Use the constant value 4 instead.
        """
        return 4

    def ping(self) -> None:
        """
        Pings the database to verify the connection is valid.
        """
        self._verify_connected()
        self._impl.ping()

    def prepare(self) -> bool:
        """
        Deprecated. Use tpc_prepare() instead.
        """
        return self.tpc_prepare()

    @property
    def proxy_user(self) -> Union[str, None]:
        """
        Returns the name of the proxy user, if applicable.
        """
        self._verify_connected()
        return self._impl.proxy_user

    def rollback(self) -> None:
        """
        Rolls back any pending transactions.
        """
        self._verify_connected()
        self._impl.rollback()

    def shutdown(self, mode: int = 0) -> None:
        """
        Shutdown the database. In order to do this the connection must be
        connected as SYSDBA or SYSOPER. Two calls must be made unless the mode
        specified is DBSHUTDOWN_ABORT.
        """
        self._verify_connected()
        self._impl.shutdown(mode)

    def startup(
        self,
        force: bool = False,
        restrict: bool = False,
        pfile: Optional[str] = None,
    ) -> None:
        """
        Startup the database. This is equivalent to the SQL*Plus command
        “startup nomount”. The connection must be connected as SYSDBA or
        SYSOPER with the PRELIM_AUTH option specified for this to work.

        The pfile parameter, if specified, is expected to be a string
        identifying the location of the parameter file (PFILE) which will be
        used instead of the stored parameter file (SPFILE).
        """
        self._verify_connected()
        self._impl.startup(force, restrict, pfile)

    def subscribe(
        self,
        namespace: int = oracledb.SUBSCR_NAMESPACE_DBCHANGE,
        protocol: int = oracledb.SUBSCR_PROTO_CALLBACK,
        callback: Optional[Callable] = None,
        timeout: int = 0,
        operations: int = oracledb.OPCODE_ALLOPS,
        port: int = 0,
        qos: int = oracledb.SUBSCR_QOS_DEFAULT,
        ip_address: Optional[str] = None,
        grouping_class: int = oracledb.SUBSCR_GROUPING_CLASS_NONE,
        grouping_value: int = 0,
        grouping_type: int = oracledb.SUBSCR_GROUPING_TYPE_SUMMARY,
        name: Optional[str] = None,
        client_initiated: bool = False,
        *,
        ipAddress: Optional[str] = None,
        groupingClass: int = oracledb.SUBSCR_GROUPING_CLASS_NONE,
        groupingValue: int = 0,
        groupingType: int = oracledb.SUBSCR_GROUPING_TYPE_SUMMARY,
        clientInitiated: bool = False,
    ) -> Subscription:
        """
        Return a new subscription object that receives notification for events
        that take place in the database that match the given parameters.

        The namespace parameter specifies the namespace the subscription uses.
        It can be one of SUBSCR_NAMESPACE_DBCHANGE or SUBSCR_NAMESPACE_AQ.

        The protocol parameter specifies the protocol to use when notifications
        are sent. Currently the only valid value is SUBSCR_PROTO_CALLBACK.

        The callback is expected to be a callable that accepts a single
        parameter. A message object is passed to this callback whenever a
        notification is received.

        The timeout value specifies that the subscription expires after the
        given time in seconds. The default value of 0 indicates that the
        subscription never expires.

        The operations parameter enables filtering of the messages that are
        sent (insert, update, delete). The default value will send
        notifications for all operations. This parameter is only used when the
        namespace is set to SUBSCR_NAMESPACE_DBCHANGE.

        The port parameter specifies the listening port for callback
        notifications from the database server. If not specified, an unused
        port will be selected by the Oracle Client libraries.

        The qos parameter specifies quality of service options. It should be
        one or more of the following flags, OR'ed together:
        SUBSCR_QOS_RELIABLE,
        SUBSCR_QOS_DEREG_NFY,
        SUBSCR_QOS_ROWIDS,
        SUBSCR_QOS_QUERY,
        SUBSCR_QOS_BEST_EFFORT.

        The ip_address parameter specifies the IP address (IPv4 or IPv6) in
        standard string notation to bind for callback notifications from the
        database server. If not specified, the client IP address will be
        determined by the Oracle Client libraries.

        The grouping_class parameter specifies what type of grouping of
        notifications should take place. Currently, if set, this value can
        only be set to the value SUBSCR_GROUPING_CLASS_TIME, which will group
        notifications by the number of seconds specified in the grouping_value
        parameter. The grouping_type parameter should be one of the values
        SUBSCR_GROUPING_TYPE_SUMMARY (the default) or
        SUBSCR_GROUPING_TYPE_LAST.

        The name parameter is used to identify the subscription and is specific
        to the selected namespace. If the namespace parameter is
        SUBSCR_NAMESPACE_DBCHANGE then the name is optional and can be any
        value. If the namespace parameter is SUBSCR_NAMESPACE_AQ, however, the
        name must be in the format '<QUEUE_NAME>' for single consumer queues
        and '<QUEUE_NAME>:<CONSUMER_NAME>' for multiple consumer queues, and
        identifies the queue that will be monitored for messages. The queue
        name may include the schema, if needed.

        The client_initiated parameter is used to determine if client initiated
        connections or server initiated connections (the default) will be
        established. Client initiated connections are only available in Oracle
        Client 19.4 and Oracle Database 19.4 and higher.
        """
        self._verify_connected()
        if ipAddress is not None:
            if ip_address is not None:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="ipAddress",
                    new_name="ip_address",
                )
            ip_address = ipAddress
        if groupingClass != oracledb.SUBSCR_GROUPING_CLASS_NONE:
            if grouping_class != oracledb.SUBSCR_GROUPING_CLASS_NONE:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="groupingClass",
                    new_name="grouping_class",
                )
            grouping_class = groupingClass
        if groupingValue != 0:
            if grouping_value != 0:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="groupingValue",
                    new_name="grouping_value",
                )
            grouping_value = groupingValue
        if groupingType != oracledb.SUBSCR_GROUPING_TYPE_SUMMARY:
            if grouping_type != oracledb.SUBSCR_GROUPING_TYPE_SUMMARY:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="groupingType",
                    new_name="grouping_type",
                )
            grouping_type = groupingType
        if clientInitiated:
            if client_initiated:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="clientInitiated",
                    new_name="client_initiated",
                )
            client_initiated = clientInitiated
        impl = self._impl.create_subscr_impl(
            self,
            callback,
            namespace,
            name,
            protocol,
            ip_address,
            port,
            timeout,
            operations,
            qos,
            grouping_class,
            grouping_value,
            grouping_type,
            client_initiated,
        )
        subscr = Subscription._from_impl(impl)
        impl.subscribe(subscr, self._impl)
        return subscr

    def suspend_sessionless_transaction(self) -> None:
        """
        Suspends the currently active sessionless transaction.

        This temporarily detaches the transaction from the session,
        allowing it to be resumed later using its transaction_id.

        Returns:
            None
        """
        self._verify_connected()
        self._impl.suspend_sessionless_transaction()

    @property
    def tag(self) -> str:
        """
        This property initially contains the actual tag of the session that was
        acquired from a pool. If the connection was not acquired from a pool or
        no tagging parameters were specified (tag and matchanytag) when the
        connection was acquired from the pool, this value will be None. If the
        value is changed, it must be a string containing name=value pairs like
        “k1=v1;k2=v2”.

        If this value is not None when the connection is released back to the
        pool it will be used to retag the session. This value can be overridden
        in the call to SessionPool.release().
        """
        self._verify_connected()
        return self._impl.tag

    @tag.setter
    def tag(self, value: str) -> None:
        self._verify_connected()
        self._impl.tag = value

    def tpc_begin(
        self, xid: Xid, flags: int = oracledb.TPC_BEGIN_NEW, timeout: int = 0
    ) -> None:
        """
        Begins a TPC (two-phase commit) transaction with the given transaction
        id. This method should be called outside of a transaction (i.e. nothing
        may have executed since the last commit() or rollback() was performed).
        """
        self._verify_connected()
        self._verify_xid(xid)
        if flags not in (
            oracledb.TPC_BEGIN_NEW,
            oracledb.TPC_BEGIN_JOIN,
            oracledb.TPC_BEGIN_RESUME,
            oracledb.TPC_BEGIN_PROMOTE,
        ):
            errors._raise_err(errors.ERR_INVALID_TPC_BEGIN_FLAGS)
        self._impl.tpc_begin(xid, flags, timeout)

    def tpc_commit(
        self, xid: Optional[Xid] = None, one_phase: bool = False
    ) -> None:
        """
        Prepare the global transaction for commit. Return a boolean indicating
        if a transaction was actually prepared in order to avoid the error
        ORA-24756 (transaction does not exist).

        When called with no arguments, commits a transaction previously
        prepared with tpc_prepare(). If tpc_prepare() is not called, a single
        phase commit is performed. A transaction manager may choose to do this
        if only a single resource is participating in the global transaction.

        When called with a transaction id, the database commits the given
        transaction. This form should be called outside of a transaction and is
        intended for use in recovery.
        """
        self._verify_connected()
        if xid is not None:
            self._verify_xid(xid)
        self._impl.tpc_commit(xid, one_phase)

    def tpc_end(
        self, xid: Optional[Xid] = None, flags: int = oracledb.TPC_END_NORMAL
    ) -> None:
        """
        Ends (detaches from) a TPC (two-phase commit) transaction.
        """
        self._verify_connected()
        if xid is not None:
            self._verify_xid(xid)
        if flags not in (oracledb.TPC_END_NORMAL, oracledb.TPC_END_SUSPEND):
            errors._raise_err(errors.ERR_INVALID_TPC_END_FLAGS)
        self._impl.tpc_end(xid, flags)

    def tpc_forget(self, xid: Xid) -> None:
        """
        Forgets a TPC (two-phase commit) transaction.
        """
        self._verify_connected()
        self._verify_xid(xid)
        self._impl.tpc_forget(xid)

    def tpc_prepare(self, xid: Optional[Xid] = None) -> bool:
        """
        Prepares a global transaction for commit. After calling this function,
        no further activity should take place on this connection until either
        tpc_commit() or tpc_rollback() have been called.

        A boolean is returned indicating whether a commit is needed or not. If
        a commit is performed when one is not needed the error ORA-24756:
        transaction does not exist is raised.
        """
        self._verify_connected()
        if xid is not None:
            self._verify_xid(xid)
        return self._impl.tpc_prepare(xid)

    def tpc_recover(self) -> list:
        """
        Returns a list of pending transaction ids suitable for use with
        tpc_commit() or tpc_rollback().

        This function requires select privilege on the view
        DBA_PENDING_TRANSACTIONS.
        """
        with self.cursor() as cursor:
            cursor.execute(
                """
                    select
                        formatid,
                        globalid,
                        branchid
                    from dba_pending_transactions"""
            )
            cursor.rowfactory = Xid
            return cursor.fetchall()

    def tpc_rollback(self, xid: Optional[Xid] = None) -> None:
        """
        When called with no arguments, rolls back the transaction previously
        started with tpc_begin().

        When called with a transaction id, the database rolls back the given
        transaction. This form should be called outside of a transaction and is
        intended for use in recovery.
        """
        self._verify_connected()
        if xid is not None:
            self._verify_xid(xid)
        self._impl.tpc_rollback(xid)

    def unsubscribe(self, subscr: Subscription) -> None:
        """
        Unsubscribe from events in the database that were originally subscribed
        to using subscribe(). The connection used to unsubscribe should be the
        same one used to create the subscription, or should access the same
        database and be connected as the same user name.
        """
        self._verify_connected()
        if not isinstance(subscr, Subscription):
            raise TypeError("expecting subscription")
        subscr._impl.unsubscribe(self._impl)


def _connection_factory(
    f: Callable[..., Connection],
) -> Callable[..., Connection]:
    """
    Decorator which checks the validity of the supplied keyword parameters by
    calling the original function (which does nothing), then creates and
    returns an instance of the requested Connection class. The base Connection
    class constructor does not check the validity of the supplied keyword
    parameters.
    """

    @functools.wraps(f)
    def connect(
        dsn: Optional[str] = None,
        *,
        pool: Optional["pool_module.ConnectionPool"] = None,
        pool_alias: Optional[str] = None,
        conn_class: Type[Connection] = Connection,
        params: Optional[ConnectParams] = None,
        **kwargs,
    ) -> Connection:
        f(
            dsn=dsn,
            pool=pool,
            pool_alias=pool_alias,
            conn_class=conn_class,
            params=params,
            **kwargs,
        )
        if not issubclass(conn_class, Connection):
            errors._raise_err(errors.ERR_INVALID_CONN_CLASS)
        if pool is not None and pool_alias is not None:
            errors._raise_err(
                errors.ERR_DUPLICATED_PARAMETER,
                deprecated_name="pool",
                new_name="pool_alias",
            )
        if pool_alias is not None:
            pool = pool_module.named_pools.pools.get(pool_alias)
            if pool is None:
                errors._raise_err(
                    errors.ERR_NAMED_POOL_MISSING, alias=pool_alias
                )
        if pool is not None and not isinstance(
            pool, pool_module.ConnectionPool
        ):
            message = "pool must be an instance of oracledb.ConnectionPool"
            raise TypeError(message)
        return conn_class(dsn=dsn, pool=pool, params=params, **kwargs)

    return connect


@_connection_factory
def connect(
    dsn: Optional[str] = None,
    *,
    pool: Optional["pool_module.ConnectionPool"] = None,
    pool_alias: Optional[str] = None,
    conn_class: Type[Connection] = Connection,
    params: Optional[ConnectParams] = None,
    user: Optional[str] = None,
    proxy_user: Optional[str] = None,
    password: Optional[str] = None,
    newpassword: Optional[str] = None,
    wallet_password: Optional[str] = None,
    access_token: Optional[Union[str, tuple, Callable]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    protocol: Optional[str] = None,
    https_proxy: Optional[str] = None,
    https_proxy_port: Optional[int] = None,
    service_name: Optional[str] = None,
    instance_name: Optional[str] = None,
    sid: Optional[str] = None,
    server_type: Optional[str] = None,
    cclass: Optional[str] = None,
    purity: Optional[oracledb.Purity] = None,
    expire_time: Optional[int] = None,
    retry_count: Optional[int] = None,
    retry_delay: Optional[int] = None,
    tcp_connect_timeout: Optional[float] = None,
    ssl_server_dn_match: Optional[bool] = None,
    ssl_server_cert_dn: Optional[str] = None,
    wallet_location: Optional[str] = None,
    events: Optional[bool] = None,
    externalauth: Optional[bool] = None,
    mode: Optional[oracledb.AuthMode] = None,
    disable_oob: Optional[bool] = None,
    stmtcachesize: Optional[int] = None,
    edition: Optional[str] = None,
    tag: Optional[str] = None,
    matchanytag: Optional[bool] = None,
    config_dir: Optional[str] = None,
    appcontext: Optional[list] = None,
    shardingkey: Optional[list] = None,
    supershardingkey: Optional[list] = None,
    debug_jdwp: Optional[str] = None,
    connection_id_prefix: Optional[str] = None,
    ssl_context: Optional[Any] = None,
    sdu: Optional[int] = None,
    pool_boundary: Optional[str] = None,
    use_tcp_fast_open: Optional[bool] = None,
    ssl_version: Optional[ssl.TLSVersion] = None,
    program: Optional[str] = None,
    machine: Optional[str] = None,
    terminal: Optional[str] = None,
    osuser: Optional[str] = None,
    driver_name: Optional[str] = None,
    use_sni: Optional[bool] = None,
    thick_mode_dsn_passthrough: Optional[bool] = None,
    extra_auth_params: Optional[dict] = None,
    pool_name: Optional[str] = None,
    handle: Optional[int] = None,
) -> Connection:
    """
    Factory function which creates a connection to the database and returns it.

    The dsn parameter (data source name) can be a string in the format
    user/password@connect_string or can simply be the connect string (in
    which case authentication credentials such as the username and password
    need to be specified separately). See the documentation on connection
    strings for more information.

    The pool parameter is expected to be a pool object and the use of this
    parameter is the equivalent of calling pool.acquire().

    The conn_class parameter is expected to be Connection or a subclass of
    Connection.

    The params parameter is expected to be of type ConnectParams and contains
    connection parameters that will be used when establishing the connection.
    See the documentation on ConnectParams for more information. If this
    parameter is not specified, the additional keyword parameters will be used
    to create an instance of ConnectParams. If both the params parameter and
    additional keyword parameters are specified, the values in the keyword
    parameters have precedence. Note that if a dsn is also supplied,
    then in the python-oracledb Thin mode, the values of the parameters
    specified (if any) within the dsn will override the values passed as
    additional keyword parameters, which themselves override the values set in
    the params parameter object.

    The following parameters are all optional. A brief description of each
    parameter follows:

    - user: the name of the user to connect to (default: None)

    - proxy_user: the name of the proxy user to connect to. If this value is
      not specified, it will be parsed out of user if user is in the form
      "user[proxy_user]" (default: None)

    - password: the password for the user (default: None)

    - newpassword: the new password for the user. The new password will take
      effect immediately upon a successful connection to the database (default:
      None)

    - wallet_password: the password to use to decrypt the wallet, if it is
      encrypted. This value is only used in thin mode (default: None)

    - access_token: expected to be a string or a 2-tuple or a callable. If it
      is a string, it specifies an Azure AD OAuth2 token used for Open
      Authorization (OAuth 2.0) token based authentication. If it is a 2-tuple,
      it specifies the token and private key strings used for Oracle Cloud
      Infrastructure (OCI) Identity and Access Management (IAM) token based
      authentication. If it is a callable, it returns either a string or a
      2-tuple used for OAuth 2.0 or OCI IAM token based authentication and is
      useful when the pool needs to expand and create new connections but the
      current authentication token has expired (default: None)

    - host: the name or IP address of the machine hosting the database or the
      database listener (default: None)

    - port: the port number on which the database listener is listening
      (default: 1521)

    - protocol: one of the strings "tcp" or "tcps" indicating whether to use
      unencrypted network traffic or encrypted network traffic (TLS) (default:
      "tcp")

    - https_proxy: the name or IP address of a proxy host to use for tunneling
      secure connections (default: None)

    - https_proxy_port: the port on which to communicate with the proxy host
      (default: 0)

    - service_name: the service name of the database (default: None)

    - instance_name: the instance name of the database (default: None)

    - sid: the system identifier (SID) of the database. Note using a
      service_name instead is recommended (default: None)

    - server_type: the type of server connection that should be established. If
      specified, it should be one of "dedicated", "shared" or "pooled"
      (default: None)

    - cclass: connection class to use for Database Resident Connection Pooling
      (DRCP) (default: None)

    - purity: purity to use for Database Resident Connection Pooling (DRCP)
      (default: oracledb.PURITY_DEFAULT)

    - expire_time: an integer indicating the number of minutes between the
      sending of keepalive probes. If this parameter is set to a value greater
      than zero it enables keepalive (default: 0)

    - retry_count: the number of times that a connection attempt should be
      retried before the attempt is terminated (default: 0)

    - retry_delay: the number of seconds to wait before making a new connection
      attempt (default: 1)

    - tcp_connect_timeout: a float indicating the maximum number of seconds to
      wait for establishing a connection to the database host (default: 20.0)

    - ssl_server_dn_match: boolean indicating whether the server certificate
      distinguished name (DN) should be matched in addition to the regular
      certificate verification that is performed. Note that if the
      ssl_server_cert_dn parameter is not privided, host name matching is
      performed instead (default: True)

    - ssl_server_cert_dn: the distinguished name (DN) which should be matched
      with the server. This value is ignored if the ssl_server_dn_match
      parameter is not set to the value True. If specified this value is used
      for any verfication. Otherwise the hostname will be used (default: None)

    - wallet_location: the directory where the wallet can be found. In thin
      mode this must be the directory containing the PEM-encoded wallet file
      ewallet.pem. In thick mode this must be the directory containing the file
      cwallet.sso (default: None)

    - events: boolean specifying whether events mode should be enabled. This
      value is only used in thick mode and is needed for continuous query
      notification and high availability event notifications (default: False)

    - externalauth: a boolean indicating whether to use external authentication
      (default: False)

    - mode: authorization mode to use. For example oracledb.AUTH_MODE_SYSDBA
      (default: oracledb.AUTH_MODE_DEFAULT)

    - disable_oob: boolean indicating whether out-of-band breaks should be
      disabled. This value is only used in thin mode. It has no effect on
      Windows which does not support this functionality (default: False)

    - stmtcachesize: identifies the initial size of the statement cache
      (default: oracledb.defaults.stmtcachesize)

    - edition: edition to use for the connection. This parameter cannot be used
      simultaneously with the cclass parameter (default: None)

    - tag: identifies the type of connection that should be returned from a
      pool. This value is only used in thick mode (default: None)

    - matchanytag: boolean specifying whether any tag can be used when
      acquiring a connection from the pool. This value is only used in thick
      mode (default: False)

    - config_dir: directory in which the optional tnsnames.ora configuration
      file is located. This value is only used in thin mode. For thick mode use
      the config_dir parameter of init_oracle_client() (default:
      oracledb.defaults.config_dir)

    - appcontext: application context used by the connection. It should be a
      list of 3-tuples (namespace, name, value) and each entry in the tuple
      should be a string. This value is only used in thick mode (default: None)

    - shardingkey: a list of strings, numbers, bytes or dates that identify the
      database shard to connect to. This value is only used in thick mode
      (default: None)

    - supershardingkey: a list of strings, numbers, bytes or dates that
      identify the database shard to connect to. This value is only used in
      thick mode (default: None)

    - debug_jdwp: a string with the format "host=<host>;port=<port>" that
      specifies the host and port of the PL/SQL debugger. This value is only
      used in thin mode. For thick mode set the ORA_DEBUG_JDWP environment
      variable (default: None)

    - connection_id_prefix: an application specific prefix that is added to the
      connection identifier used for tracing (default: None)

    - ssl_context: an SSLContext object used for connecting to the database
      using TLS.  This SSL context will be modified to include the private key
      or any certificates found in a separately supplied wallet. This parameter
      should only be specified if the default SSLContext object cannot be used
      (default: None)

    - sdu: the requested size of the Session Data Unit (SDU), in bytes. The
      value tunes internal buffers used for communication to the database.
      Bigger values can increase throughput for large queries or bulk data
      loads, but at the cost of higher memory use. The SDU size that will
      actually be used is negotiated down to the lower of this value and the
      database network SDU configuration value (default: 8192)

    - pool_boundary: one of the values "statement" or "transaction" indicating
      when pooled DRCP connections can be returned to the pool. This requires
      the use of DRCP with Oracle Database 23.4 or higher (default: None)

    - use_tcp_fast_open: boolean indicating whether to use TCP fast open. This
      is an Oracle Autonomous Database Serverless (ADB-S) specific property for
      clients connecting from within OCI Cloud network. Please refer to the
      ADB-S documentation for more information (default: False)

    - ssl_version: one of the values ssl.TLSVersion.TLSv1_2 or
      ssl.TLSVersion.TLSv1_3 indicating which TLS version to use (default:
      None)

    - program: the name of the executable program or application connected to
      the Oracle Database (default: oracledb.defaults.program)

    - machine: the machine name of the client connecting to the Oracle Database
      (default: oracledb.defaults.machine)

    - terminal: the terminal identifier from which the connection originates
      (default: oracledb.defaults.terminal)

    - osuser: the operating system user that initiates the database connection
      (default: oracledb.defaults.osuser)

    - driver_name: the driver name used by the client to connect to the Oracle
      Database (default: oracledb.defaults.driver_name)

    - use_sni: boolean indicating whether to use the TLS SNI extension to
      bypass the second TLS neogiation that would otherwise be required
      (default: False)

    - thick_mode_dsn_passthrough: boolean indicating whether to pass the
      connect string to the Oracle Client libraries unchanged without parsing
      by the driver. Setting this to False makes thick and thin mode
      applications behave similarly regarding connection string parameter
      handling and locating any optional tnsnames.ora configuration file
      (default: oracledb.defaults.thick_mode_dsn_passthrough)

    - extra_auth_params: a dictionary containing configuration parameters
      necessary for Oracle Database authentication using plugins, such as the
      Azure and OCI cloud-native authentication plugins (default: None)

    - pool_name: the name of the DRCP pool when using multi-pool DRCP with
      Oracle Database 23.4 or higher (default: None)

    - handle: an integer representing a pointer to a valid service context
      handle. This value is only used in thick mode. It should be used with
      extreme caution (default: 0)
    """
    pass


class AsyncConnection(BaseConnection):
    __module__ = MODULE_NAME

    def __init__(
        self,
        dsn: str,
        pool: pool_module.AsyncConnectionPool,
        params: ConnectParams,
        kwargs: dict,
    ) -> None:
        """
        Constructor for asynchronous connection pool. Not intended to be used
        directly but only indirectly through async_connect().
        """
        super().__init__()
        self._pool = pool
        self._connect_coroutine = self._connect(dsn, pool, params, kwargs)

    def __await__(self):
        coroutine = self._connect_coroutine
        self._connect_coroutine = None
        return coroutine.__await__()

    async def __aenter__(self):
        if self._connect_coroutine is not None:
            await self._connect_coroutine
        else:
            self._verify_connected()
        return self

    async def __aexit__(self, *exc_info):
        if self._impl is not None:
            await self._close()

    async def _close(self, in_del=False):
        """
        Closes the connection and makes it unusable for further operations. An
        Error exception will be raised if any operation is attempted with this
        connection after this method completes successfully.
        """
        if self._pool is not None:
            pool_impl = self._pool._impl
            if pool_impl is not None:
                await pool_impl.return_connection(self._impl, in_del)
        else:
            await self._impl.close(in_del)
        self._impl = None

    async def _connect(self, dsn, pool, params, kwargs):
        """
        Internal method for establishing a connection to the database using
        asyncio.
        """

        # mandate that thin mode is required; with asyncio, only thin mode is
        # supported and only one thread is executing, so the manager can be
        # manipulated directly
        driver_mode.manager.thin_mode = True

        # determine which connection parameters to use
        if params is None:
            params_impl = base_impl.ConnectParamsImpl()
        elif not isinstance(params, ConnectParams):
            errors._raise_err(errors.ERR_INVALID_CONNECT_PARAMS)
        else:
            params_impl = params._impl.copy()
        dsn = params_impl.process_args(dsn, kwargs, thin=True)

        # see if connection is being acquired from a pool
        if pool is None:
            pool_impl = None
        elif not isinstance(pool, pool_module.AsyncConnectionPool):
            message = (
                "pool must be an instance of oracledb.AsyncConnectionPool"
            )
            raise TypeError(message)
        else:
            pool._verify_open()
            pool_impl = pool._impl

        # create implementation object
        if pool is not None:
            impl = await pool_impl.acquire(params_impl)
        else:
            impl = thin_impl.AsyncThinConnImpl(dsn, params_impl)
            await impl.connect(params_impl)
        self._impl = impl

        # invoke callback, if applicable
        if (
            impl.invoke_session_callback
            and pool is not None
            and pool.session_callback is not None
            and callable(pool.session_callback)
        ):
            await pool.session_callback(self, params_impl.tag)
            impl.invoke_session_callback = False

        return self

    def _create_queue(self, impl):
        """
        Returns a queue object that the user can use to dequeue and enqueue
        messages.
        """
        return AsyncQueue._from_impl(self, impl)

    def _verify_can_execute(
        self, parameters: Any, keyword_parameters: Any
    ) -> Any:
        """
        Verifies that the connection can be used to execute
        Verifies that the connection is connected to the database. If it is
        not, an exception is raised.
        """
        self._verify_connected()
        if keyword_parameters:
            if parameters:
                errors._raise_err(errors.ERR_ARGS_AND_KEYWORD_ARGS)
            return keyword_parameters
        elif parameters is not None and not isinstance(
            parameters, (list, tuple, dict)
        ):
            errors._raise_err(errors.ERR_WRONG_EXECUTE_PARAMETERS_TYPE)
        return parameters

    async def begin_sessionless_transaction(
        self,
        transaction_id: Optional[Union[str, bytes]] = None,
        timeout: int = 60,
        defer_round_trip: bool = False,
    ) -> bytes:
        """
        Begins a new sessionless transaction.

        Parameters:
            transaction_id (str or bytes, optional): A Transaction Identifier.
               If None, a random transaction_id will be generated.
            timeout (int, optional): Timeout value in seconds.
               Must be a positive integer. Defaults to 60 if not provided.
            defer_round_trip (bool, optional):
                If True, the request is not sent immediately but included
                with the next database operation.

        Returns:
            bytes: The normalized transaction_id used for the transaction.
        """
        self._verify_connected()
        normalized_txnid = normalize_sessionless_transaction_id(transaction_id)

        if not isinstance(timeout, int) or timeout <= 0:
            raise TypeError("timeout must be a positive integer")

        await self._impl.begin_sessionless_transaction(
            normalized_txnid, timeout, defer_round_trip
        )
        return normalized_txnid

    async def callfunc(
        self,
        name: str,
        return_type: Any,
        parameters: Optional[Union[list, tuple]] = None,
        keyword_parameters: Optional[dict] = None,
    ) -> Any:
        """
        Call a PL/SQL function with the given name.

        This is a shortcut for creating a cursor, calling the stored function
        with the cursor and then closing the cursor.
        """
        with self.cursor() as cursor:
            return await cursor.callfunc(
                name, return_type, parameters, keyword_parameters
            )

    async def callproc(
        self,
        name: str,
        parameters: Optional[Union[list, tuple]] = None,
        keyword_parameters: Optional[dict] = None,
    ) -> list:
        """
        Call a PL/SQL procedure with the given name.

        This is a shortcut for creating a cursor, calling the stored procedure
        with the cursor and then closing the cursor.
        """
        with self.cursor() as cursor:
            return await cursor.callproc(name, parameters, keyword_parameters)

    async def changepassword(
        self, old_password: str, new_password: str
    ) -> None:
        """
        Changes the password for the user to which the connection is connected.
        """
        self._verify_connected()
        await self._impl.change_password(old_password, new_password)

    async def close(self) -> None:
        """
        Closes the connection.
        """
        self._verify_connected()
        await self._close()

    async def commit(self) -> None:
        """
        Commits any pending transaction to the database.
        """
        self._verify_connected()
        await self._impl.commit()

    async def createlob(
        self, lob_type: DbType, data: Optional[Union[str, bytes]] = None
    ) -> AsyncLOB:
        """
        Create and return a new temporary LOB of the specified type.
        """
        self._verify_connected()
        if lob_type not in (DB_TYPE_CLOB, DB_TYPE_NCLOB, DB_TYPE_BLOB):
            message = (
                "parameter should be one of oracledb.DB_TYPE_CLOB, "
                "oracledb.DB_TYPE_BLOB or oracledb.DB_TYPE_NCLOB"
            )
            raise TypeError(message)
        impl = await self._impl.create_temp_lob_impl(lob_type)
        lob = AsyncLOB._from_impl(impl)
        if data:
            await lob.write(data)
        return lob

    def cursor(self, scrollable: bool = False) -> AsyncCursor:
        """
        Returns a cursor associated with the connection.
        """
        self._verify_connected()
        return AsyncCursor(self, scrollable)

    async def execute(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
    ) -> None:
        """
        Execute a statement against the database.

        This is a shortcut for creating a cursor, executing a statement with
        the cursor and then closing the cursor.
        """
        with self.cursor() as cursor:
            await cursor.execute(statement, parameters)

    async def executemany(
        self, statement: Union[str, None], parameters: Any
    ) -> None:
        """
        Prepare a statement for execution against a database and then execute
        it against all parameter mappings or sequences found in the sequence
        parameters.

        This is a shortcut for creating a cursor, calling executemany() on the
        cursor and then closing the cursor.
        """
        with self.cursor() as cursor:
            await cursor.executemany(statement, parameters)

    async def fetchall(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        arraysize: Optional[int] = None,
        rowfactory: Optional[Callable] = None,
    ) -> list:
        """
        Executes a query and returns all of the rows. After the rows are
        fetched, the cursor is closed.
        """
        with self.cursor() as cursor:
            if arraysize is not None:
                cursor.arraysize = arraysize
            cursor.prefetchrows = cursor.arraysize
            await cursor.execute(statement, parameters)
            cursor.rowfactory = rowfactory
            return await cursor.fetchall()

    async def fetch_df_all(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        arraysize: Optional[int] = None,
    ):
        """
        Fetch all data as an instance of DataFrame.
        """
        cursor = self.cursor()
        cursor._impl.fetching_arrow = True
        if arraysize is not None:
            cursor.arraysize = arraysize
        cursor.prefetchrows = cursor.arraysize
        await cursor.execute(statement, parameters)
        return await cursor._impl.fetch_df_all(cursor)

    async def fetch_df_batches(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        size: Optional[int] = None,
    ):
        """
        Fetch data in batches. Each batch is an instance of DataFrame
        """
        cursor = self.cursor()
        cursor._impl.fetching_arrow = True
        if size is not None:
            cursor.arraysize = size
        cursor.prefetchrows = cursor.arraysize
        await cursor.execute(statement, parameters)
        if size is None:
            yield await cursor._impl.fetch_df_all(cursor)
        else:
            async for df in cursor._impl.fetch_df_batches(cursor, size):
                yield df

    async def fetchmany(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        num_rows: Optional[int] = None,
        rowfactory: Optional[Callable] = None,
    ) -> list:
        """
        Executes a query and returns up to the specified number of rows. After
        the rows are fetched, the cursor is closed.
        """
        with self.cursor() as cursor:
            if num_rows is None:
                num_rows = cursor.arraysize
            elif num_rows <= 0:
                return []
            cursor.arraysize = cursor.prefetchrows = num_rows
            await cursor.execute(statement, parameters)
            cursor.rowfactory = rowfactory
            return await cursor.fetchmany(num_rows)

    async def fetchone(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        rowfactory: Optional[Callable] = None,
    ) -> Any:
        """
        Executes a query and returns the first row of the result set if one
        exists (or None if no rows exist). After the row is fetched the cursor
        is closed.
        """
        with self.cursor() as cursor:
            cursor.prefetchrows = cursor.arraysize = 1
            await cursor.execute(statement, parameters)
            cursor.rowfactory = rowfactory
            return await cursor.fetchone()

    async def gettype(self, name: str) -> DbObjectType:
        """
        Return a type object given its name. This can then be used to create
        objects which can be bound to cursors created by this connection.
        """
        self._verify_connected()
        obj_type_impl = await self._impl.get_type(self, name)
        return DbObjectType._from_impl(obj_type_impl)

    async def ping(self) -> None:
        """
        Pings the database to verify the connection is valid.
        """
        self._verify_connected()
        await self._impl.ping()

    async def resume_sessionless_transaction(
        self,
        transaction_id: Union[str, bytes],
        timeout: int = 60,
        defer_round_trip: bool = False,
    ) -> bytes:
        """
        Resumes an existing sessionless transaction using the given
        transaction_id.

        Parameters:
            transaction_id (str or bytes): A Transaction Identifier that
              uniquely identifies the sessionless transaction to be
              resumed. This parameter is mandatory.
            timeout (int, optional): Timeout in seconds for the resumed
              transaction. Must be a positive integer. Defaults to 60.
            defer_round_trip (bool, optional):
                If True, the request is not sent immediately but included
                with the next database operation.

        Returns:
            bytes: The normalized transaction_id used to resume the
              sessionless transaction.
        """
        self._verify_connected()
        if transaction_id is None:
            raise ValueError("transaction_id is required for resuming")

        normalized_txnid = normalize_sessionless_transaction_id(transaction_id)

        if not (isinstance(timeout, int) and timeout >= 0):
            raise TypeError("timeout must be a non-negative integer")

        await self._impl.resume_sessionless_transaction(
            normalized_txnid, timeout, defer_round_trip
        )
        return normalized_txnid

    async def rollback(self) -> None:
        """
        Rolls back any pending transaction.
        """
        self._verify_connected()
        await self._impl.rollback()

    async def run_pipeline(
        self,
        pipeline: Pipeline,
        continue_on_error: bool = False,
    ) -> list:
        """
        Runs all of the operations in the pipeline on the connection. If the
        database is Oracle Database 23ai or higher, the operations will be
        performed in a single round trip, subject to the following caveats:
            - queries that contain LOBs require an additional round trip
            - queries that contain DbObject values may require multiple round
              trips
            - queries that fetch all of the rows may require multiple round
              trips
        For all other databases, the operations will be performed in the same
        way as they would be performed independently of the pipeline.
        """
        self._verify_connected()
        results = [op._create_result() for op in pipeline.operations]
        if self._impl.supports_pipelining() and len(results) > 1:
            await self._impl.run_pipeline_with_pipelining(
                self, results, continue_on_error
            )
        else:
            await self._impl.run_pipeline_without_pipelining(
                self, results, continue_on_error
            )
        return results

    async def suspend_sessionless_transaction(self) -> None:
        """
        Suspends the currently active sessionless transaction.

        This temporarily detaches the transaction from the session,
        allowing it to be resumed later using its transaction_id.

        Returns:
            None
        """
        self._verify_connected()
        await self._impl.suspend_sessionless_transaction()

    async def tpc_begin(
        self, xid: Xid, flags: int = oracledb.TPC_BEGIN_NEW, timeout: int = 0
    ) -> None:
        """
        Begins a TPC (two-phase commit) transaction with the given transaction
        id. This method should be called outside of a transaction (i.e. nothing
        may have executed since the last commit() or rollback() was performed).
        """
        self._verify_connected()
        self._verify_xid(xid)
        if flags not in (
            oracledb.TPC_BEGIN_NEW,
            oracledb.TPC_BEGIN_JOIN,
            oracledb.TPC_BEGIN_RESUME,
            oracledb.TPC_BEGIN_PROMOTE,
        ):
            errors._raise_err(errors.ERR_INVALID_TPC_BEGIN_FLAGS)
        await self._impl.tpc_begin(xid, flags, timeout)

    async def tpc_commit(
        self, xid: Optional[Xid] = None, one_phase: bool = False
    ) -> None:
        """
        Prepare the global transaction for commit. Return a boolean indicating
        if a transaction was actually prepared in order to avoid the error
        ORA-24756 (transaction does not exist).

        When called with no arguments, commits a transaction previously
        prepared with tpc_prepare(). If tpc_prepare() is not called, a single
        phase commit is performed. A transaction manager may choose to do this
        if only a single resource is participating in the global transaction.

        When called with a transaction id, the database commits the given
        transaction. This form should be called outside of a transaction and is
        intended for use in recovery.
        """
        self._verify_connected()
        if xid is not None:
            self._verify_xid(xid)
        await self._impl.tpc_commit(xid, one_phase)

    async def tpc_end(
        self, xid: Optional[Xid] = None, flags: int = oracledb.TPC_END_NORMAL
    ) -> None:
        """
        Ends (detaches from) a TPC (two-phase commit) transaction.
        """
        self._verify_connected()
        if xid is not None:
            self._verify_xid(xid)
        if flags not in (oracledb.TPC_END_NORMAL, oracledb.TPC_END_SUSPEND):
            errors._raise_err(errors.ERR_INVALID_TPC_END_FLAGS)
        await self._impl.tpc_end(xid, flags)

    async def tpc_forget(self, xid: Xid) -> None:
        """
        Forgets a TPC (two-phase commit) transaction.
        """
        self._verify_connected()
        self._verify_xid(xid)
        await self._impl.tpc_forget(xid)

    async def tpc_prepare(self, xid: Optional[Xid] = None) -> bool:
        """
        Prepares a global transaction for commit. After calling this function,
        no further activity should take place on this connection until either
        tpc_commit() or tpc_rollback() have been called.

        A boolean is returned indicating whether a commit is needed or not. If
        a commit is performed when one is not needed the error ORA-24756:
        transaction does not exist is raised.
        """
        self._verify_connected()
        if xid is not None:
            self._verify_xid(xid)
        return await self._impl.tpc_prepare(xid)

    async def tpc_recover(self) -> list:
        """
        Returns a list of pending transaction ids suitable for use with
        tpc_commit() or tpc_rollback().

        This function requires select privilege on the view
        DBA_PENDING_TRANSACTIONS.
        """
        with self.cursor() as cursor:
            await cursor.execute(
                """
                    select
                        formatid,
                        globalid,
                        branchid
                    from dba_pending_transactions"""
            )
            cursor.rowfactory = Xid
            return await cursor.fetchall()

    async def tpc_rollback(self, xid: Optional[Xid] = None) -> None:
        """
        When called with no arguments, rolls back the transaction previously
        started with tpc_begin().

        When called with a transaction id, the database rolls back the given
        transaction. This form should be called outside of a transaction and is
        intended for use in recovery.
        """
        self._verify_connected()
        if xid is not None:
            self._verify_xid(xid)
        await self._impl.tpc_rollback(xid)


def _async_connection_factory(
    f: Callable[..., AsyncConnection],
) -> Callable[..., AsyncConnection]:
    """
    Decorator which checks the validity of the supplied keyword parameters by
    calling the original function (which does nothing), then creates and
    returns an instance of the requested AsyncConnection class.
    """

    @functools.wraps(f)
    def connect_async(
        dsn: Optional[str] = None,
        *,
        pool: Optional["pool_module.AsyncConnectionPool"] = None,
        pool_alias: Optional[str] = None,
        conn_class: Type[AsyncConnection] = AsyncConnection,
        params: Optional[ConnectParams] = None,
        **kwargs,
    ) -> AsyncConnection:
        # check arguments
        f(
            dsn=dsn,
            pool=pool,
            pool_alias=pool_alias,
            conn_class=conn_class,
            params=params,
            **kwargs,
        )
        if not issubclass(conn_class, AsyncConnection):
            errors._raise_err(errors.ERR_INVALID_CONN_CLASS)

        if pool is not None and pool_alias is not None:
            errors._raise_err(
                errors.ERR_DUPLICATED_PARAMETER,
                deprecated_name="pool",
                new_name="pool_alias",
            )
        if pool_alias is not None:
            pool = pool_module.named_pools.pools.get(pool_alias)
            if pool is None:
                errors._raise_err(
                    errors.ERR_NAMED_POOL_MISSING, alias=pool_alias
                )
        if pool is not None and not isinstance(
            pool, pool_module.AsyncConnectionPool
        ):
            message = (
                "pool must be an instance of oracledb.AsyncConnectionPool"
            )
            raise TypeError(message)
        if params is not None and not isinstance(params, ConnectParams):
            errors._raise_err(errors.ERR_INVALID_CONNECT_PARAMS)

        # build connection class and call the implementation connect to
        # actually establish the connection
        oracledb.enable_thin_mode()
        return conn_class(dsn, pool, params, kwargs)

    return connect_async


@_async_connection_factory
def connect_async(
    dsn: Optional[str] = None,
    *,
    pool: Optional["pool_module.AsyncConnectionPool"] = None,
    pool_alias: Optional[str] = None,
    conn_class: Type[AsyncConnection] = AsyncConnection,
    params: Optional[ConnectParams] = None,
    user: Optional[str] = None,
    proxy_user: Optional[str] = None,
    password: Optional[str] = None,
    newpassword: Optional[str] = None,
    wallet_password: Optional[str] = None,
    access_token: Optional[Union[str, tuple, Callable]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    protocol: Optional[str] = None,
    https_proxy: Optional[str] = None,
    https_proxy_port: Optional[int] = None,
    service_name: Optional[str] = None,
    instance_name: Optional[str] = None,
    sid: Optional[str] = None,
    server_type: Optional[str] = None,
    cclass: Optional[str] = None,
    purity: Optional[oracledb.Purity] = None,
    expire_time: Optional[int] = None,
    retry_count: Optional[int] = None,
    retry_delay: Optional[int] = None,
    tcp_connect_timeout: Optional[float] = None,
    ssl_server_dn_match: Optional[bool] = None,
    ssl_server_cert_dn: Optional[str] = None,
    wallet_location: Optional[str] = None,
    events: Optional[bool] = None,
    externalauth: Optional[bool] = None,
    mode: Optional[oracledb.AuthMode] = None,
    disable_oob: Optional[bool] = None,
    stmtcachesize: Optional[int] = None,
    edition: Optional[str] = None,
    tag: Optional[str] = None,
    matchanytag: Optional[bool] = None,
    config_dir: Optional[str] = None,
    appcontext: Optional[list] = None,
    shardingkey: Optional[list] = None,
    supershardingkey: Optional[list] = None,
    debug_jdwp: Optional[str] = None,
    connection_id_prefix: Optional[str] = None,
    ssl_context: Optional[Any] = None,
    sdu: Optional[int] = None,
    pool_boundary: Optional[str] = None,
    use_tcp_fast_open: Optional[bool] = None,
    ssl_version: Optional[ssl.TLSVersion] = None,
    program: Optional[str] = None,
    machine: Optional[str] = None,
    terminal: Optional[str] = None,
    osuser: Optional[str] = None,
    driver_name: Optional[str] = None,
    use_sni: Optional[bool] = None,
    thick_mode_dsn_passthrough: Optional[bool] = None,
    extra_auth_params: Optional[dict] = None,
    pool_name: Optional[str] = None,
    handle: Optional[int] = None,
) -> AsyncConnection:
    """
    Factory function which creates a connection to the database and returns it.

    The dsn parameter (data source name) can be a string in the format
    user/password@connect_string or can simply be the connect string (in
    which case authentication credentials such as the username and password
    need to be specified separately). See the documentation on connection
    strings for more information.

    The pool parameter is expected to be a pool object and the use of this
    parameter is the equivalent of calling pool.acquire().

    The conn_class parameter is expected to be AsyncConnection or a subclass of
    AsyncConnection.

    The params parameter is expected to be of type ConnectParams and contains
    connection parameters that will be used when establishing the connection.
    See the documentation on ConnectParams for more information. If this
    parameter is not specified, the additional keyword parameters will be used
    to create an instance of ConnectParams. If both the params parameter and
    additional keyword parameters are specified, the values in the keyword
    parameters have precedence. Note that if a dsn is also supplied,
    then in the python-oracledb Thin mode, the values of the parameters
    specified (if any) within the dsn will override the values passed as
    additional keyword parameters, which themselves override the values set in
    the params parameter object.

    The following parameters are all optional. A brief description of each
    parameter follows:

    - user: the name of the user to connect to (default: None)

    - proxy_user: the name of the proxy user to connect to. If this value is
      not specified, it will be parsed out of user if user is in the form
      "user[proxy_user]" (default: None)

    - password: the password for the user (default: None)

    - newpassword: the new password for the user. The new password will take
      effect immediately upon a successful connection to the database (default:
      None)

    - wallet_password: the password to use to decrypt the wallet, if it is
      encrypted. This value is only used in thin mode (default: None)

    - access_token: expected to be a string or a 2-tuple or a callable. If it
      is a string, it specifies an Azure AD OAuth2 token used for Open
      Authorization (OAuth 2.0) token based authentication. If it is a 2-tuple,
      it specifies the token and private key strings used for Oracle Cloud
      Infrastructure (OCI) Identity and Access Management (IAM) token based
      authentication. If it is a callable, it returns either a string or a
      2-tuple used for OAuth 2.0 or OCI IAM token based authentication and is
      useful when the pool needs to expand and create new connections but the
      current authentication token has expired (default: None)

    - host: the name or IP address of the machine hosting the database or the
      database listener (default: None)

    - port: the port number on which the database listener is listening
      (default: 1521)

    - protocol: one of the strings "tcp" or "tcps" indicating whether to use
      unencrypted network traffic or encrypted network traffic (TLS) (default:
      "tcp")

    - https_proxy: the name or IP address of a proxy host to use for tunneling
      secure connections (default: None)

    - https_proxy_port: the port on which to communicate with the proxy host
      (default: 0)

    - service_name: the service name of the database (default: None)

    - instance_name: the instance name of the database (default: None)

    - sid: the system identifier (SID) of the database. Note using a
      service_name instead is recommended (default: None)

    - server_type: the type of server connection that should be established. If
      specified, it should be one of "dedicated", "shared" or "pooled"
      (default: None)

    - cclass: connection class to use for Database Resident Connection Pooling
      (DRCP) (default: None)

    - purity: purity to use for Database Resident Connection Pooling (DRCP)
      (default: oracledb.PURITY_DEFAULT)

    - expire_time: an integer indicating the number of minutes between the
      sending of keepalive probes. If this parameter is set to a value greater
      than zero it enables keepalive (default: 0)

    - retry_count: the number of times that a connection attempt should be
      retried before the attempt is terminated (default: 0)

    - retry_delay: the number of seconds to wait before making a new connection
      attempt (default: 1)

    - tcp_connect_timeout: a float indicating the maximum number of seconds to
      wait for establishing a connection to the database host (default: 20.0)

    - ssl_server_dn_match: boolean indicating whether the server certificate
      distinguished name (DN) should be matched in addition to the regular
      certificate verification that is performed. Note that if the
      ssl_server_cert_dn parameter is not privided, host name matching is
      performed instead (default: True)

    - ssl_server_cert_dn: the distinguished name (DN) which should be matched
      with the server. This value is ignored if the ssl_server_dn_match
      parameter is not set to the value True. If specified this value is used
      for any verfication. Otherwise the hostname will be used (default: None)

    - wallet_location: the directory where the wallet can be found. In thin
      mode this must be the directory containing the PEM-encoded wallet file
      ewallet.pem. In thick mode this must be the directory containing the file
      cwallet.sso (default: None)

    - events: boolean specifying whether events mode should be enabled. This
      value is only used in thick mode and is needed for continuous query
      notification and high availability event notifications (default: False)

    - externalauth: a boolean indicating whether to use external authentication
      (default: False)

    - mode: authorization mode to use. For example oracledb.AUTH_MODE_SYSDBA
      (default: oracledb.AUTH_MODE_DEFAULT)

    - disable_oob: boolean indicating whether out-of-band breaks should be
      disabled. This value is only used in thin mode. It has no effect on
      Windows which does not support this functionality (default: False)

    - stmtcachesize: identifies the initial size of the statement cache
      (default: oracledb.defaults.stmtcachesize)

    - edition: edition to use for the connection. This parameter cannot be used
      simultaneously with the cclass parameter (default: None)

    - tag: identifies the type of connection that should be returned from a
      pool. This value is only used in thick mode (default: None)

    - matchanytag: boolean specifying whether any tag can be used when
      acquiring a connection from the pool. This value is only used in thick
      mode (default: False)

    - config_dir: directory in which the optional tnsnames.ora configuration
      file is located. This value is only used in thin mode. For thick mode use
      the config_dir parameter of init_oracle_client() (default:
      oracledb.defaults.config_dir)

    - appcontext: application context used by the connection. It should be a
      list of 3-tuples (namespace, name, value) and each entry in the tuple
      should be a string. This value is only used in thick mode (default: None)

    - shardingkey: a list of strings, numbers, bytes or dates that identify the
      database shard to connect to. This value is only used in thick mode
      (default: None)

    - supershardingkey: a list of strings, numbers, bytes or dates that
      identify the database shard to connect to. This value is only used in
      thick mode (default: None)

    - debug_jdwp: a string with the format "host=<host>;port=<port>" that
      specifies the host and port of the PL/SQL debugger. This value is only
      used in thin mode. For thick mode set the ORA_DEBUG_JDWP environment
      variable (default: None)

    - connection_id_prefix: an application specific prefix that is added to the
      connection identifier used for tracing (default: None)

    - ssl_context: an SSLContext object used for connecting to the database
      using TLS.  This SSL context will be modified to include the private key
      or any certificates found in a separately supplied wallet. This parameter
      should only be specified if the default SSLContext object cannot be used
      (default: None)

    - sdu: the requested size of the Session Data Unit (SDU), in bytes. The
      value tunes internal buffers used for communication to the database.
      Bigger values can increase throughput for large queries or bulk data
      loads, but at the cost of higher memory use. The SDU size that will
      actually be used is negotiated down to the lower of this value and the
      database network SDU configuration value (default: 8192)

    - pool_boundary: one of the values "statement" or "transaction" indicating
      when pooled DRCP connections can be returned to the pool. This requires
      the use of DRCP with Oracle Database 23.4 or higher (default: None)

    - use_tcp_fast_open: boolean indicating whether to use TCP fast open. This
      is an Oracle Autonomous Database Serverless (ADB-S) specific property for
      clients connecting from within OCI Cloud network. Please refer to the
      ADB-S documentation for more information (default: False)

    - ssl_version: one of the values ssl.TLSVersion.TLSv1_2 or
      ssl.TLSVersion.TLSv1_3 indicating which TLS version to use (default:
      None)

    - program: the name of the executable program or application connected to
      the Oracle Database (default: oracledb.defaults.program)

    - machine: the machine name of the client connecting to the Oracle Database
      (default: oracledb.defaults.machine)

    - terminal: the terminal identifier from which the connection originates
      (default: oracledb.defaults.terminal)

    - osuser: the operating system user that initiates the database connection
      (default: oracledb.defaults.osuser)

    - driver_name: the driver name used by the client to connect to the Oracle
      Database (default: oracledb.defaults.driver_name)

    - use_sni: boolean indicating whether to use the TLS SNI extension to
      bypass the second TLS neogiation that would otherwise be required
      (default: False)

    - thick_mode_dsn_passthrough: boolean indicating whether to pass the
      connect string to the Oracle Client libraries unchanged without parsing
      by the driver. Setting this to False makes thick and thin mode
      applications behave similarly regarding connection string parameter
      handling and locating any optional tnsnames.ora configuration file
      (default: oracledb.defaults.thick_mode_dsn_passthrough)

    - extra_auth_params: a dictionary containing configuration parameters
      necessary for Oracle Database authentication using plugins, such as the
      Azure and OCI cloud-native authentication plugins (default: None)

    - pool_name: the name of the DRCP pool when using multi-pool DRCP with
      Oracle Database 23.4 or higher (default: None)

    - handle: an integer representing a pointer to a valid service context
      handle. This value is only used in thick mode. It should be used with
      extreme caution (default: 0)
    """
    pass
