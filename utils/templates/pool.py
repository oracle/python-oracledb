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
# pool.py
#
# Contains the ConnectionPool class and the factory method create_pool() used
# for creating connection pools.
#
# # {{ generated_notice }}
# -----------------------------------------------------------------------------

import functools
import ssl
import threading
from typing import Callable, Type, Union, Any, Optional

import oracledb

from . import base_impl, thick_impl, thin_impl
from . import connection as connection_module
from . import driver_mode
from . import errors
from .base import BaseMetaClass
from .pool_params import PoolParams


class BaseConnectionPool(metaclass=BaseMetaClass):
    _impl = None

    def __init__(
        self,
        dsn: Optional[str] = None,
        *,
        params: Optional[PoolParams] = None,
        cache_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Constructor for creating a connection pool.
        """
        if params is None:
            params_impl = base_impl.PoolParamsImpl()
        elif not isinstance(params, PoolParams):
            errors._raise_err(errors.ERR_INVALID_POOL_PARAMS)
        else:
            params_impl = params._impl.copy()
        with driver_mode.get_manager() as mode_mgr:
            thin = mode_mgr.thin
            dsn = params_impl.process_args(dsn, kwargs, thin)
            self._set_connection_type(params_impl.connectiontype)
            self._cache_name = cache_name
            if cache_name is not None:
                named_pools.add_pool(cache_name, self)
            try:
                if issubclass(
                    self._connection_type, connection_module.AsyncConnection
                ):
                    impl = thin_impl.AsyncThinPoolImpl(dsn, params_impl)
                elif thin:
                    impl = thin_impl.ThinPoolImpl(dsn, params_impl)
                else:
                    impl = thick_impl.ThickPoolImpl(dsn, params_impl)
                self._impl = impl
                self.session_callback = params_impl.session_callback
            except:
                if cache_name is not None:
                    del named_pools.pools[cache_name]
                raise

    def _verify_open(self) -> None:
        """
        Verifies that the pool is open and able to perform its work.
        """
        if self._impl is None:
            errors._raise_err(errors.ERR_POOL_NOT_OPEN)

    @property
    def busy(self) -> int:
        """
        This read-only attribute returns the number of connections currently
        acquired.
        """
        self._verify_open()
        return self._impl.get_busy_count()

    @property
    def dsn(self) -> str:
        """
        This read-only attribute returns the TNS entry of the database to which
        a connection has been established.
        """
        self._verify_open()
        return self._impl.dsn

    @property
    def getmode(self) -> oracledb.PoolGetMode:
        """
        This read-write attribute determines how connections are returned from
        the pool. If :data:`~oracledb.POOL_GETMODE_FORCEGET` is specified, a
        new connection will be returned even if there are no free connections
        in the pool.  :data:`~oracledb.POOL_GETMODE_NOWAIT` will raise an
        exception if there are no free connections are available in the pool.
        If :data:`~oracledb.POOL_GETMODE_WAIT` is specified and there are no
        free connections in the pool, the caller will wait until a free
        connection is available. :data:`~oracledb.POOL_GETMODE_TIMEDWAIT` uses
        the value of :data:`~ConnectionPool.wait_timeout` to determine how long
        the caller should wait for a connection to become available before
        returning an error.
        """
        self._verify_open()
        return oracledb.PoolGetMode(self._impl.get_getmode())

    @getmode.setter
    def getmode(self, value: oracledb.PoolGetMode) -> None:
        self._verify_open()
        self._impl.set_getmode(value)

    @property
    def homogeneous(self) -> bool:
        """
        This read-only boolean attribute indicates whether the pool is
        considered :ref:`homogeneous <connpooltypes>` or not. If the pool is
        not homogeneous, different authentication can be used for each
        connection acquired from the pool.
        """
        self._verify_open()
        return self._impl.homogeneous

    @property
    def increment(self) -> int:
        """
        This read-only attribute returns the number of connections that will be
        established when additional connections need to be created.
        """
        self._verify_open()
        return self._impl.increment

    @property
    def max(self) -> int:
        """
        This read-only attribute returns the maximum number of connections that
        the pool can control.
        """
        self._verify_open()
        return self._impl.max

    @property
    def max_lifetime_session(self) -> int:
        """
        This read-write attribute is the maximum length of time (in seconds)
        that a pooled connection may exist since first being created. A value
        of *0* means there is no limit. Connections become candidates for
        termination when they are acquired or released back to the pool, and
        have existed for longer than ``max_lifetime_session`` seconds.
        Connections that are in active use will not be closed. In
        python-oracledb Thick mode, Oracle Client libraries 12.1 or later must
        be used and, prior to Oracle Client 21, cleanup only occurs when the
        pool is accessed.
        """
        self._verify_open()
        return self._impl.get_max_lifetime_session()

    @max_lifetime_session.setter
    def max_lifetime_session(self, value: int) -> None:
        self._verify_open()
        self._impl.set_max_lifetime_session(value)

    @property
    def max_sessions_per_shard(self) -> int:
        """
        This read-write attribute returns the number of sessions that can be
        created per shard in the pool. Setting this attribute greater than zero
        specifies the maximum number of sessions in the pool that can be used
        for any given shard in a sharded database. This lets connections in the
        pool be balanced across the shards. A value of *0* will not set any
        maximum number of sessions for each shard. This attribute is only
        available in Oracle Client 18.3 and higher.
        """
        self._verify_open()
        return self._impl.get_max_sessions_per_shard()

    @max_sessions_per_shard.setter
    def max_sessions_per_shard(self, value: int) -> None:
        self._verify_open()
        self._impl.set_max_sessions_per_shard(value)

    @property
    def min(self) -> int:
        """
        This read-only attribute returns the number of connections with which
        the connection pool was created and the minimum number of connections
        that will be controlled by the connection pool.
        """
        self._verify_open()
        return self._impl.min

    @property
    def name(self) -> str:
        """
        This read-only attribute returns the name assigned to the pool by
        Oracle.
        """
        self._verify_open()
        return self._impl.name

    @property
    def opened(self) -> int:
        """
        This read-only attribute returns the number of connections currently
        opened by the pool.
        """
        self._verify_open()
        return self._impl.get_open_count()

    @property
    def ping_interval(self) -> int:
        """
        This read-write integer attribute specifies the pool ping interval in
        seconds. When a connection is acquired from the pool, a check is first
        made to see how long it has been since the connection was put into the
        pool. If this idle time exceeds ``ping_interval``, then a
        :ref:`round-trip <roundtrips>` ping to the database is performed. If
        the connection is unusable, it is discarded and a different connection
        is selected to be returned by :meth:`acquire()`.  Setting
        ``ping_interval`` to a negative value disables pinging.  Setting it to
        *0* forces a ping for every :meth:`acquire()` and is not recommended.
        """
        self._verify_open()
        return self._impl.get_ping_interval()

    @ping_interval.setter
    def ping_interval(self, value: int) -> None:
        self._impl.set_ping_interval(value)

    @property
    def soda_metadata_cache(self) -> bool:
        """
        This read-write boolean attribute returns whether the SODA metadata
        cache is enabled or not. Enabling the cache significantly improves the
        performance of methods :meth:`SodaDatabase.createCollection()` (when
        not specifying a value for the ``metadata`` parameter) and
        :meth:`SodaDatabase.openCollection()`. Note that the cache can become
        out of date if changes to the metadata of cached collections are made
        externally.
        """
        self._verify_open()
        return self._impl.get_soda_metadata_cache()

    @soda_metadata_cache.setter
    def soda_metadata_cache(self, value: bool) -> None:
        if not isinstance(value, bool):
            message = "soda_metadata_cache must be a boolean value."
            raise TypeError(message)
        self._verify_open()
        self._impl.set_soda_metadata_cache(value)

    @property
    def stmtcachesize(self) -> int:
        """
        This read-write attribute specifies the size of the statement cache
        that will be used for connections obtained from the pool. Once a
        connection is created, that connection’s statement cache size can only
        be changed by setting the ``stmtcachesize`` attribute on the connection
        itself.
        """
        self._verify_open()
        return self._impl.get_stmt_cache_size()

    @stmtcachesize.setter
    def stmtcachesize(self, value: int) -> None:
        self._verify_open()
        self._impl.set_stmt_cache_size(value)

    @property
    def thin(self) -> bool:
        """
        This read-only attribute returns a boolean indicating if
        python-oracledb is in Thin mode (*True*) or Thick mode (*False*).
        """
        self._verify_open()
        return not isinstance(self._impl, thick_impl.ThickPoolImpl)

    @property
    def timeout(self) -> int:
        """
        This read-write attribute specifies the time (in seconds) after which
        idle connections will be terminated in order to maintain an optimum
        number of open connections. A value of *0* means that no idle
        connections are terminated. Note that in python-oracledb Thick mode
        with older Oracle Client Libraries, the termination only occurs when
        the pool is accessed.
        """
        self._verify_open()
        return self._impl.get_timeout()

    @timeout.setter
    def timeout(self, value: int) -> None:
        self._verify_open()
        self._impl.set_timeout(value)

    @property
    def tnsentry(self) -> str:
        """
        Deprecated. Use dsn instead.
        """
        return self.dsn

    @property
    def username(self) -> str:
        """
        This read-only attribute returns the name of the user which established
        the connection to the database.
        """
        self._verify_open()
        return self._impl.username

    @property
    def wait_timeout(self) -> int:
        """
        This read-write attribute specifies the time (in milliseconds) that the
        caller should wait for a connection to become available in the pool
        before returning with an error. This value is only used if the
        ``getmode`` parameter to :meth:`oracledb.create_pool()` was the value
        :data:`oracledb.POOL_GETMODE_TIMEDWAIT`.
        """
        self._verify_open()
        return self._impl.get_wait_timeout()

    @wait_timeout.setter
    def wait_timeout(self, value: int) -> None:
        self._verify_open()
        self._impl.set_wait_timeout(value)


class ConnectionPool(BaseConnectionPool):

    def __del__(self):
        if self._impl is not None:
            self._impl.close(True)
            self._impl = None

    def _set_connection_type(self, conn_class):
        """
        Called internally when the pool is created to ensure that the correct
        connection class is used for all connections created by the pool.
        """
        if conn_class is None:
            conn_class = connection_module.Connection
        elif not issubclass(
            conn_class, connection_module.Connection
        ) or issubclass(conn_class, connection_module.AsyncConnection):
            errors._raise_err(errors.ERR_INVALID_CONN_CLASS)
        self._connection_type = conn_class

    def acquire(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        cclass: Optional[str] = None,
        purity: int = oracledb.PURITY_DEFAULT,
        tag: Optional[str] = None,
        matchanytag: bool = False,
        shardingkey: Optional[list] = None,
        supershardingkey: Optional[list] = None,
    ) -> "connection_module.Connection":
        """
        Acquires a connection from the session pool and returns a
        :ref:`connection object <connobj>`.

        If the pool is :ref:`homogeneous <connpooltypes>`, the ``user`` and
        ``password`` parameters cannot be specified. If they are, an exception
        will be raised.

        The ``cclass`` parameter, if specified, should be a string
        corresponding to the connection class for :ref:`drcp`.

        The ``purity`` parameter is expected to be one of
        :data:`~oracledb.PURITY_NEW`, :data:`~oracledb.PURITY_SELF`, or
        :data:`~oracledb.PURITY_DEFAULT`.

        The ``tag`` parameter, if specified, is expected to be a string with
        name=value pairs like "k1=v1;k2=v2" and will limit the connections that
        can be returned from a connection pool unless the ``matchanytag``
        parameter is set to *True*. In that case, connections with the
        specified tag will be preferred over others, but if no such connections
        are available, then a connection with a different tag may be returned
        instead. In any case, untagged connections will always be returned if
        no connections with the specified tag are available. Connections are
        tagged when they are :meth:`released <ConnectionPool.release>` back to
        the pool.

        The ``shardingkey`` and ``supershardingkey`` parameters, if specified,
        are expected to be a sequence of values which will be used to identify
        the database shard to connect to. The key values can be strings,
        numbers, bytes, or dates.  See :ref:`connsharding`.

        When using the :ref:`connection pool cache <connpoolcache>`, calling
        :meth:`oracledb.connect()` with a ``pool_alias`` parameter is the same
        as calling ``pool.acquire()``.
        """
        self._verify_open()

        return oracledb.connect(
            conn_class=self._connection_type,
            user=user,
            password=password,
            cclass=cclass,
            purity=purity,
            tag=tag,
            matchanytag=matchanytag,
            shardingkey=shardingkey,
            supershardingkey=supershardingkey,
            pool=self,
        )

    def close(self, force: bool = False) -> None:
        """
        Closes the pool now, rather than when the last reference to it is
        released, which makes it unusable for further work.

        If any connections have been acquired and not released back to the
        pool, this method will fail unless the ``force`` parameter is set to
        *True*.
        """
        self._verify_open()
        self._impl.close(force)
        if self._cache_name is not None:
            named_pools.remove_pool(self._cache_name)
        self._impl = None

    def drop(self, connection: "connection_module.Connection") -> None:
        """
        Drops the connection from the pool which is useful if the connection is
        no longer usable (such as when the session is killed).
        """
        self._verify_open()
        if not isinstance(connection, connection_module.Connection):
            message = "connection must be an instance of oracledb.Connection"
            raise TypeError(message)
        connection._verify_connected()
        self._impl.drop(connection._impl)
        connection._impl = None

    def reconfigure(
        self,
        min: Optional[int] = None,
        max: Optional[int] = None,
        increment: Optional[int] = None,
        getmode: Optional[int] = None,
        timeout: Optional[int] = None,
        wait_timeout: Optional[int] = None,
        max_lifetime_session: Optional[int] = None,
        max_sessions_per_shard: Optional[int] = None,
        soda_metadata_cache: Optional[bool] = None,
        stmtcachesize: Optional[int] = None,
        ping_interval: Optional[int] = None,
    ) -> None:
        """
        Reconfigures various parameters of a connection pool. The pool size can
        be altered with ``reconfigure()`` by passing values for
        :data:`~ConnectionPool.min`, :data:`~ConnectionPool.max` or
        :data:`~ConnectionPool.increment`.  The
        :data:`~ConnectionPool.getmode`, :data:`~ConnectionPool.timeout`,
        :data:`~ConnectionPool.wait_timeout`,
        :data:`~ConnectionPool.max_lifetime_session`,
        :data:`~ConnectionPool.max_sessions_per_shard`,
        :data:`~ConnectionPool.soda_metadata_cache`,
        :data:`~ConnectionPool.stmtcachesize` and
        :data:`~ConnectionPool.ping_interval` attributes can be set directly or
        with ``reconfigure()``.

        All parameters are optional. Unspecified parameters will leave those
        pool attributes unchanged. The parameters are processed in two stages.
        After any size change has been processed, reconfiguration on the other
        parameters is done sequentially. If an error such as an invalid value
        occurs when changing one attribute, then an exception will be generated
        but any already changed attributes will retain their new values.

        During reconfiguration of a pool's size, the behavior of
        :meth:`ConnectionPool.acquire()` depends on the ``getmode`` in effect
        when ``acquire()`` is called:

        * With mode :data:`~oracledb.POOL_GETMODE_FORCEGET`, an ``acquire()``
          call will wait until the pool has been reconfigured.

        * With mode :data:`~oracledb.POOL_GETMODE_TIMEDWAIT`, an ``acquire()``
          call will try to acquire a connection in the time specified by
          pool.wait_timeout and return an error if the time taken exceeds that
          value.

        * With mode :data:`~oracledb.POOL_GETMODE_WAIT`, an ``acquire()`` call
          will wait until after the pool has been reconfigured and a connection
          is available.

        * With mode :data:`~oracledb.POOL_GETMODE_NOWAIT`, if the number of
          busy connections is less than the pool size, ``acquire()`` will
          return a new connection after pool reconfiguration is complete.

        Closing connections with :meth:`ConnectionPool.release()` or
        :meth:`Connection.close()` will wait until any pool size
        reconfiguration is complete.

        Closing the connection pool with :meth:`ConnectionPool.close()` will
        wait until reconfiguration is complete.
        """

        if min is None:
            min = self.min
        if max is None:
            max = self.max
        if increment is None:
            increment = self.increment
        if self.min != min or self.max != max or self.increment != increment:
            self._impl.reconfigure(min, max, increment)
        if getmode is not None:
            self.getmode = getmode
        if timeout is not None:
            self.timeout = timeout
        if wait_timeout is not None:
            self.wait_timeout = wait_timeout
        if max_lifetime_session is not None:
            self.max_lifetime_session = max_lifetime_session
        if max_sessions_per_shard is not None:
            self.max_sessions_per_shard = max_sessions_per_shard
        if soda_metadata_cache is not None:
            self.soda_metadata_cache = soda_metadata_cache
        if stmtcachesize is not None:
            self.stmtcachesize = stmtcachesize
        if ping_interval is not None:
            self.ping_interval = ping_interval

    def release(
        self,
        connection: "connection_module.Connection",
        tag: Optional[str] = None,
    ) -> None:
        """
        Releases the connection back to the pool now, rather than whenever
        __del__ is called. The connection will be unusable from this point
        forward; an Error exception will be raised if any operation is
        attempted with the connection. Any cursors or LOBs created by the
        connection will also be marked unusable and an Error exception will be
        raised if any operation is attempted with them.

        Internally, references to the connection are held by cursor objects,
        LOB objects, etc. Once all of these references are released, the
        connection itself will be released back to the pool automatically.
        Either control references to these related objects carefully or
        explicitly release connections back to the pool in order to ensure
        sufficient resources are available.

        If the tag is not *None*, it is expected to be a string with name=value
        pairs like "k1=v1;k2=v2" and will override the value in the property
        :attr:`Connection.tag`. If either :attr:`Connection.tag` or the tag
        parameter are not *None*, the connection will be retagged when it is
        released back to the pool.
        """
        self._verify_open()
        if not isinstance(connection, connection_module.Connection):
            message = "connection must be an instance of oracledb.Connection"
            raise TypeError(message)
        connection._verify_connected()
        if tag is not None:
            connection.tag = tag
        self._impl.return_connection(connection._impl)
        connection._impl = None


def _pool_factory(
    f: Callable[..., ConnectionPool],
) -> Callable[..., ConnectionPool]:
    """
    Decorator which checks the validity of the supplied keyword parameters by
    calling the original function (which does nothing), then creates and
    returns an instance of the requested ConnectionPool class. The base
    ConnectionPool class constructor does not check the validity of the
    supplied keyword parameters.
    """

    @functools.wraps(f)
    def create_pool(
        dsn: Optional[str] = None,
        *,
        pool_class: Type[ConnectionPool] = ConnectionPool,
        pool_alias: Optional[str] = None,
        params: Optional[PoolParams] = None,
        **kwargs,
    ) -> ConnectionPool:
        f(
            dsn=dsn,
            pool_class=pool_class,
            pool_alias=pool_alias,
            params=params,
            **kwargs,
        )
        if not issubclass(pool_class, ConnectionPool):
            errors._raise_err(errors.ERR_INVALID_POOL_CLASS)
        return pool_class(dsn, params=params, cache_name=pool_alias, **kwargs)

    return create_pool


@_pool_factory
def create_pool(
    dsn: Optional[str] = None,
    *,
    pool_class: Type[ConnectionPool] = ConnectionPool,
    pool_alias: Optional[str] = None,
    params: Optional[PoolParams] = None,
    # {{ args_with_defaults }}
) -> ConnectionPool:
    """
    Creates a connection pool with the supplied parameters and returns it.

    The ``dsn`` parameter (data source name) can be a string in the format
    user/password@connect_string or can simply be the connect string (in
    which case authentication credentials such as the username and password
    need to be specified separately). See the documentation on connection
    strings for more information.

    The ``pool_class`` parameter is expected to be ConnectionPool or a subclass
    of ConnectionPool.

    The ``pool_alias`` parameter is expected to be a string representing the
    name used to store and reference the pool in the python-oracledb connection
    pool cache. If this parameter is not specified, then the pool will not be
    added to the cache. The value of this parameter can be used with the
    :meth:`oracledb.get_pool()` and :meth:`oracledb.connect()` methods to
    access the pool.

    The ``params`` parameter is expected to be of type PoolParams and contains
    parameters that are used to create the pool. See the documentation on
    PoolParams for more information. If this parameter is not specified, the
    additional keyword parameters will be used to create an instance of
    PoolParams. If both the ``params`` parameter and additional keyword
    parameters are specified, the values in the keyword parameters have
    precedence. Note that if a ``dsn`` is also supplied, then in
    python-oracledb Thin mode, the values of the parameters specified (if any)
    within the dsn will override the values passed as additional keyword
    parameters, which themselves override the values set in the ``params``
    parameter object.

    The following parameters are all optional. A brief description of each
    parameter follows:

    # {{ args_help_with_defaults }}
    """
    pass


class AsyncConnectionPool(BaseConnectionPool):

    def _set_connection_type(self, conn_class):
        """
        Called internally when the pool is created to ensure that the correct
        connection class is used for all connections created by the pool.
        """
        if conn_class is None:
            conn_class = connection_module.AsyncConnection
        elif not issubclass(conn_class, connection_module.AsyncConnection):
            errors._raise_err(errors.ERR_INVALID_CONN_CLASS)
        self._connection_type = conn_class

    def acquire(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        cclass: Optional[str] = None,
        purity: int = oracledb.PURITY_DEFAULT,
        tag: Optional[str] = None,
        matchanytag: bool = False,
        shardingkey: Optional[list] = None,
        supershardingkey: Optional[list] = None,
    ) -> "connection_module.AsyncConnection":
        """
        Acquires a connection from the pool and returns an :ref:`asynchronous
        connection object <asyncconnobj>`.

        If the pool is :ref:`homogeneous <connpooltypes>`, the ``user`` and
        ``password`` parameters cannot be specified. If they are, an exception
        will be raised.

        The ``cclass`` parameter, if specified, should be a string
        corresponding to the connection class for :ref:`drcp`.

        The ``purity`` parameter is expected to be one of
        :data:`~oracledb.PURITY_NEW`, :data:`~oracledb.PURITY_SELF`, or
        :data:`~oracledb.PURITY_DEFAULT`.

        The ``tag``, ``matchanytag``, ``shardingkey``, and ``supershardingkey``
        parameters are ignored in python-oracledb Thin mode.
        """
        self._verify_open()

        return oracledb.connect_async(
            conn_class=self._connection_type,
            user=user,
            password=password,
            cclass=cclass,
            purity=purity,
            tag=tag,
            matchanytag=matchanytag,
            shardingkey=shardingkey,
            supershardingkey=supershardingkey,
            pool=self,
        )

    async def close(self, force: bool = False) -> None:
        """
        Closes the pool now, rather than when the last reference to it is
        released, which makes it unusable for further work.

        If any connections have been acquired and not released back to the
        pool, this method will fail unless the ``force`` parameter is set to
        *True*.
        """
        self._verify_open()
        await self._impl.close(force)
        if self._cache_name is not None:
            named_pools.remove_pool(self._cache_name)
        self._impl = None

    async def drop(self, connection: "connection_module.Connection") -> None:
        """
        Drops the connection from the pool which is useful if the connection is
        no longer usable (such as when the session is killed).
        """
        self._verify_open()
        if not isinstance(connection, connection_module.AsyncConnection):
            message = (
                "connection must be an instance of oracledb.AsyncConnection"
            )
            raise TypeError(message)
        connection._verify_connected()
        await self._impl.drop(connection._impl)
        connection._impl = None

    async def release(
        self,
        connection: "connection_module.AsyncConnection",
        tag: Optional[str] = None,
    ) -> None:
        """
        Releases the connection back to the pool now. The connection will be
        unusable from this point forward. An Error exception will be raised if
        any operation is attempted with the connection. Any cursors or LOBs
        created by the connection will also be marked unusable and an Error
        exception will be raised if any operation is attempted with them.

        The ``tag`` parameter is ignored in python-oracledb Thin mode.
        """
        self._verify_open()
        if not isinstance(connection, connection_module.AsyncConnection):
            message = (
                "connection must be an instance of oracledb.AsyncConnection"
            )
            raise TypeError(message)
        if tag is not None:
            connection.tag = tag
        await self._impl.return_connection(connection._impl)
        connection._impl = None


def _async_pool_factory(
    f: Callable[..., AsyncConnectionPool],
) -> Callable[..., AsyncConnectionPool]:
    """
    Decorator which checks the validity of the supplied keyword parameters by
    calling the original function (which does nothing), then creates and
    returns an instance of the requested ConnectionPool class. The base
    ConnectionPool class constructor does not check the validity of the
    supplied keyword parameters.
    """

    @functools.wraps(f)
    def create_pool_async(
        dsn: Optional[str] = None,
        *,
        pool_class: Type[ConnectionPool] = AsyncConnectionPool,
        pool_alias: Optional[str] = None,
        params: Optional[PoolParams] = None,
        **kwargs,
    ) -> AsyncConnectionPool:
        f(
            dsn=dsn,
            pool_class=pool_class,
            pool_alias=pool_alias,
            params=params,
            **kwargs,
        )
        oracledb.enable_thin_mode()
        if not issubclass(pool_class, AsyncConnectionPool):
            errors._raise_err(errors.ERR_INVALID_POOL_CLASS)
        return pool_class(dsn, params=params, cache_name=pool_alias, **kwargs)

    return create_pool_async


@_async_pool_factory
def create_pool_async(
    dsn: Optional[str] = None,
    *,
    pool_class: Type[ConnectionPool] = AsyncConnectionPool,
    pool_alias: Optional[str] = None,
    params: Optional[PoolParams] = None,
    # {{ async_args_with_defaults }}
) -> AsyncConnectionPool:
    """
    Creates a connection pool with the supplied parameters and returns it.

    The ``dsn`` parameter (data source name) can be a string in the format
    user/password@connect_string or can simply be the connect string (in
    which case authentication credentials such as the username and password
    need to be specified separately). See the documentation on connection
    strings for more information.

    The ``pool_class`` parameter is expected to be AsyncConnectionPool or a
    subclass of AsyncConnectionPool.

    The ``pool_alias`` parameter is expected to be a string representing the
    name used to store and reference the pool in the python-oracledb connection
    pool cache. If this parameter is not specified, then the pool will not be
    added to the cache. The value of this parameter can be used with the
    :meth:`oracledb.get_pool()` and :meth:o`racledb.connect_async()` methods to
    access the pool.

    The ``params`` parameter is expected to be of type PoolParams and contains
    parameters that are used to create the pool. See the documentation on
    PoolParams for more information. If this parameter is not specified, the
    additional keyword parameters will be used to create an instance of
    PoolParams. If both the ``params`` parameter and additional keyword
    parameters are specified, the values in the keyword parameters have
    precedence. Note that if a ``dsn`` is also supplied, then in
    python-oracledb Thin mode, the values of the parameters specified (if any)
    within the ``dsn`` will override the values passed as additional keyword
    parameters, which themselves override the values set in the ``params``
    parameter object.

    The following parameters are all optional. A brief description of each
    parameter follows:

    # {{ async_args_help_with_defaults }}
    """
    pass


class NamedPools:

    def __init__(self):
        self.lock = threading.Lock()
        self.pools = {}

    def add_pool(self, alias, pool):
        """
        Adds a pool to the cache. An exception is raised if a pool is already
        cached with the given alias.
        """
        if not isinstance(alias, str):
            raise TypeError("pool_alias must be a string")
        with self.lock:
            if alias in self.pools:
                errors._raise_err(errors.ERR_NAMED_POOL_EXISTS, alias=alias)
            self.pools[alias] = pool

    def remove_pool(self, alias):
        """
        Removes the pool with the given alias from the cache. An exception is
        raised if there is no pool cached with the given alias.
        """
        with self.lock:
            if alias not in self.pools:
                errors._raise_err(errors.ERR_NAMED_POOL_MISSING, alias=alias)
            del self.pools[alias]


named_pools = NamedPools()


def get_pool(
    pool_alias: str,
) -> Union[ConnectionPool, AsyncConnectionPool, None]:
    """
    Returns a :ref:`ConnectionPool object <connpool>` from the python-oracledb
    pool cache. The pool must have been previously created by passing the same
    ``pool_alias`` value to :meth:`oracledb.create_pool()` or
    :meth:`oracledb.create_pool_async()`.

    If a pool with the given name does not exist, *None* is returned.
    """
    return named_pools.pools.get(pool_alias)
