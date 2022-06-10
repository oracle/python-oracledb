#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
# pool.py
#
# Contains the ConnectionPool class and the factory method create_pool() used
# for creating connection pools.
#------------------------------------------------------------------------------

import functools
from typing import Callable, Type

import oracledb

from . import errors, exceptions, utils
from . import base_impl, thick_impl, thin_impl
from . import connection as connection_module
from . import driver_mode
from .connect_params import ConnectParams
from .pool_params import PoolParams
from .defaults import defaults

class ConnectionPool:
    __module__ = oracledb.__name__

    def __init__(self, dsn: str=None, *,
                 params: PoolParams=None,
                 **kwargs) -> None:
        """
        Constructor for creating a connection pool. Connection pooling creates
        a pool of available connections to the database, allowing applications
        to acquire a connection very quickly. It is of primary use in a server
        where connections are requested in rapid succession and used for a
        short period of time, for example in a web server.

        The dsn parameter (data source name) can be a string in the format
        user/password@connect_string or can simply be the connect string (in
        which case authentication credentials such as the username and password
        need to be specified separately). See the documentation on connection
        strings for more information.

        The params parameter is expected to be of type PoolParams and contains
        parameters that are used to create the pool. See the documentation on
        PoolParams for more information. If this parameter is not specified, the
        additional keyword parameters will be used to create an instance of
        PoolParams. If both the params parameter and additional keyword
        parameters are specified, the values in the keyword parameters have
        precedence. Note that if a dsn is also supplied, then in the
        python-oracledb Thin mode, the values of the parameters specified
        (if any) within the dsn will override the values passed as additional
        keyword parameters, which themselves override the values set in the
        params parameter object.
        """
        self._impl = None
        if params is None:
            params_impl = base_impl.PoolParamsImpl()
        elif not isinstance(params, PoolParams):
            errors._raise_err(errors.ERR_INVALID_POOL_PARAMS)
        else:
            params_impl = params._impl.copy()
        if kwargs:
            params_impl.set(kwargs)
        self._connection_type = \
                params_impl.connectiontype or connection_module.Connection
        thin = driver_mode.check_and_return_mode()
        if dsn is not None:
            dsn = params_impl.parse_dsn(dsn, thin)
        if dsn is None:
            dsn = params_impl.get_connect_string()
        if thin:
            impl = thin_impl.ThinPoolImpl(dsn, params_impl)
        else:
            impl = thick_impl.ThickPoolImpl(dsn, params_impl)
        self._impl = impl
        self.session_callback = params_impl.session_callback

    def __del__(self):
        if self._impl is not None:
            self._impl.close(True)
            self._impl = None

    def _verify_open(self) -> None:
        """
        Verifies that the pool is open and able to perform its work.
        """
        if self._impl is None:
            errors._raise_err(errors.ERR_POOL_NOT_OPEN)

    def acquire(self,
                user: str=None,
                password: str=None,
                cclass: str=None,
                purity: int=oracledb.PURITY_DEFAULT,
                tag: str=None,
                matchanytag: bool=False,
                shardingkey: list=None,
                supershardingkey: list=None) -> Type["connection_module.Connection"]:
        """
        Acquire a connection from the pool and return it.

        If the pool is homogeneous, the user and password parameters cannot be
        specified. If they are, an exception will be raised.

        The cclass parameter, if specified, should be a string corresponding to
        the connection class for database resident connection pooling (DRCP).

        The purity parameter is expected to be one of PURITY_DEFAULT,
        PURITY_NEW, or PURITY_SELF.

        The tag parameter, if specified, is expected to be a string with
        name=value pairs like “k1=v1;k2=v2” and will limit the connections that
        can be returned from a pool unless the matchanytag parameter is
        set to True. In that case connections with the specified tag will be
        preferred over others, but if no such connections are available a
        connection with a different tag may be returned instead. In any case,
        untagged connections will always be returned if no connections with the
        specified tag are available. Connections are tagged when they are
        released back to the pool.

        The shardingkey and supershardingkey parameters, if specified, are
        expected to be a sequence of values which will be used to identify the
        database shard to connect to. The key values can be strings, numbers,
        bytes or dates.
        """
        self._verify_open()
        return self._connection_type(user=user, password=password,
                                     cclass=cclass, purity=purity, tag=tag,
                                     matchanytag=matchanytag,
                                     shardingkey=shardingkey,
                                     supershardingkey=supershardingkey,
                                     pool=self)

    @property
    def busy(self) -> int:
        """
        Returns the number of connections that have been acquired from the pool
        and have not yet been returned to the pool.
        """
        self._verify_open()
        return self._impl.get_busy_count()

    def close(self, force: bool=False) -> None:
        """
        Close the pool now, rather than when the last reference to it is
        released, which makes it unusable for further work.

        If any connections have been acquired and not released back to the
        pool, this method will fail unless the force parameter is set to True.
        """
        self._verify_open()
        self._impl.close(force)
        self._impl = None

    def drop(self, connection: Type["connection_module.Connection"]) -> None:
        """
        Drop the connection from the pool, which is useful if the connection is
        no longer usable (such as when the database session is killed).
        """
        self._verify_open()
        if not isinstance(connection, connection_module.Connection):
            message = "connection must be an instance of " \
                      "oracledb.Connection"
            raise TypeError(message)
        connection._verify_connected()
        self._impl.drop(connection._impl)
        connection._impl = None

    @property
    def dsn(self) -> str:
        """
        Returns the connection string (TNS entry) of the database to which
        connections in the pool have been established.
        """
        self._verify_open()
        return self._impl.dsn

    @property
    def getmode(self) -> int:
        self._verify_open()
        return self._impl.get_getmode()

    @getmode.setter
    def getmode(self, value: int) -> None:
        self._verify_open()
        self._impl.set_getmode(value)

    @property
    def homogeneous(self) -> bool:
        """
        Returns a boolean indicating if the pool is homogeneous or not. If the
        pool is not homogeneous, different authentication can be used for each
        connection acquired from the pool.
        """
        self._verify_open()
        return self._impl.homogeneous

    @property
    def increment(self) -> int:
        """
        Returns the number of connections that will be created when additional
        connections need to be created to satisfy requests.
        """
        self._verify_open()
        return self._impl.increment

    @property
    def max(self) -> int:
        """
        Returns the maximum number of connections that the pool can control.
        """
        self._verify_open()
        return self._impl.max

    @property
    def max_lifetime_session(self) -> int:
        """
        Returns the maximum length of time (in seconds) that a pooled
        connection may exist. Connections that are in use will not be closed.
        They become candidates for termination only when they are released back
        to the pool and have existed for longer than max_lifetime_session
        seconds. Note that termination only occurs when the pool is accessed. A
        value of 0 means that there is no maximum length of time that a pooled
        connection may exist. This attribute is only available in Oracle
        Database 12.1.
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
        Returns the number of sessions that can be created per shard in the
        pool.  Setting this attribute greater than zero specifies the maximum
        number of sessions in the pool that can be used for any given shard in
        a sharded database. This lets connections in the pool be balanced
        across the shards.  A value of zero will not set any maximum number of
        sessions for each shard.  This attribute is only available in Oracle
        Client 18.3 and higher.
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
        Returns the minimum number of connections that the pool will control.
        These are created when the pool is first created.
        """
        self._verify_open()
        return self._impl.min

    @property
    def name(self) -> str:
        """
        Returns the name assigned to the pool by Oracle. This attribute is only
        relevant in python-oracledb thick mode.
        """
        self._verify_open()
        return self._impl.name

    @property
    def opened(self) -> int:
        """
        Returns the number of connections currently opened by the pool.
        """
        self._verify_open()
        return self._impl.get_open_count()

    @property
    def ping_interval(self) -> int:
        """
        Returns the pool ping interval in seconds. When a connection is
        acquired from the pool, a check is first made to see how long it
        has been since the connection was put into the pool. If
        this idle time exceeds ping_interval, then a round-trip ping to the
        database is performed. If the connection is unusable, it is discarded
        and a different connection is selected to be returned by
        SessionPool.acquire(). Setting ping_interval to a negative value
        disables pinging. Setting it to 0 forces a ping for every aquire()
        and is not recommended.
        """
        self._verify_open()
        return self._impl.get_ping_interval()

    @ping_interval.setter
    def ping_interval(self, value: int) -> None:
        self._impl.set_ping_interval(value)

    def release(self, connection: Type["connection_module.Connection"],
                tag: str=None) -> None:
        """
        Release the connection back to the pool now, rather than whenever
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

        If the tag is not None, it is expected to be a string with name=value
        pairs like “k1=v1;k2=v2” and will override the value in the property
        Connection.tag. If either Connection.tag or the tag parameter are not
        None, the connection will be retagged when it is released back to the
        pool.
        """
        self._verify_open()
        if not isinstance(connection, connection_module.Connection):
            message = "connection must be an instance of " \
                      "oracledb.Connection"
            raise TypeError(message)
        if tag is not None:
            connection.tag = tag
        connection.close()

    def reconfigure(self,
                    min: int=None,
                    max: int=None,
                    increment: int=None,
                    getmode: int=None,
                    timeout: int=None,
                    wait_timeout: int=None,
                    max_lifetime_session: int=None,
                    max_sessions_per_shard: int=None,
                    soda_metadata_cache: bool=None,
                    stmtcachesize: int=None,
                    ping_interval: int=None) -> None:
        """
        Reconfigures various parameters of a connection pool. The pool size
        can be altered with reconfigure() by passing values for min, max
        or increment. The getmode, timeout, wait_timeout,
        max_lifetime_session, max_sessions_per_shard, soda_metadata_cache,
        stmtcachesize and ping_interval can be set directly or by using
        reconfigure(). All parameters are optional. Unspecified parameters
        will leave those pool attributes unchanged. The parameters are
        processed in two stages. After any size change has been processed,
        reconfiguration on the other parameters is done sequentially. If
        an error such as an invalid value occurs when changing one attribute,
        then an exception will be generated but any already changed
        attributes will retain their new values.

        During reconfiguration of a pool's size, the behavior of acquire()
        depends on the getmode in effect when acquire() is called:

        * With mode POOL_GETMODE_FORCEGET, an acquire() call will wait until
          the pool has been reconfigured.

        * With mode POOL_GETMODE__TIMEDWAIT, an acquire() call will try to
          acquire a connection in the time specified by pool.wait_timeout and
          return an error if the time taken exceeds that value.

        * With mode POOL_GETMODE_WAIT, an acquire() call will wait until after
          the pool has been reconfigured and a connection is available.

        * With mode POOL_GETMODE_NOWAIT, if the number of busy connections is
          less than the pool size, acquire() will return a new connection
          after pool reconfiguration is complete.

        Closing connections with pool.release() or connection.close() will
        wait until any pool size reconfiguration is complete.

        Closing the connection pool with pool.close() will wait until
        reconfiguration is complete.
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

    @property
    def soda_metadata_cache(self) -> bool:
        """
        Specifies whether the SODA metadata cache is enabled or not. Enabling
        the cache significantly improves the performance of methods
        SodaDatabase.createCollection() (when not specifying a value for the
        metadata parameter) and SodaDatabase.openCollection(). Note that the
        cache can become out of date if changes to the metadata of cached
        collections are made externally.
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
        Specifies the size of the statement cache that will be used as the
        starting point for any connections that are created by the pool. Once a
        connection is created, that connection’s statement cache size can only
        be changed by setting the stmtcachesize attribute on the connection
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
        Returns a boolean indicating if the pool was created in
        python-oracledb's thin mode (True) or thick mode (False).
        """
        self._verify_open()
        return isinstance(self._impl, thin_impl.ThinPoolImpl)

    @property
    def timeout(self) -> int:
        """
        Specifies the time (in seconds) after which idle connections will be
        terminated in order to maintain an optimum number of open connections.
        A value of 0 means that no idle connections are terminated. Note that
        in thick mode with older Oracle Client libraries termination only
        occurs when the pool is accessed.
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
        Returns the name of the user which was used to create the pool.
        """
        self._verify_open()
        return self._impl.username

    @property
    def wait_timeout(self) -> int:
        """
        Specifies the time (in milliseconds) that the caller should wait for a
        connection to become available in the pool before returning with an
        error.  This value is only used if the getmode parameter used to create
        the pool was POOL_GETMODE_TIMEDWAIT.
        """
        self._verify_open()
        return self._impl.get_wait_timeout()

    @wait_timeout.setter
    def wait_timeout(self, value: int) -> None:
        self._verify_open()
        self._impl.set_wait_timeout(value)


def _pool_factory(f):
    """
    Decorator which checks the validity of the supplied keyword parameters by
    calling the original function (which does nothing), then creates and
    returns an instance of the requested ConnectionPool class. The base
    ConnectionPool class constructor does not check the validity of the
    supplied keyword parameters.
    """
    @functools.wraps(f)
    def create_pool(dsn: str=None, *,
                pool_class: Type[ConnectionPool]=ConnectionPool,
                params: PoolParams=None,
                **kwargs) -> ConnectionPool:
        f(dsn=dsn, pool_class=pool_class, params=params, **kwargs)
        if not issubclass(pool_class, ConnectionPool):
            errors._raise_err(errors.INVALID_POOL_CLASS)
        return pool_class(dsn, params=params, **kwargs)
    return create_pool


@_pool_factory
def create_pool(dsn: str=None, *,
                pool_class: Type[ConnectionPool]=ConnectionPool,
                params: PoolParams=None,

                # pool creation parameters
                min: int=None,
                max: int=None,
                increment: int=None,
                connectiontype: Type["connection_module.Connection"]=None,
                getmode: int=None,
                homogeneous: bool=True,
                externalauth: bool=None,
                timeout: int=0,
                wait_timeout: int=0,
                max_lifetime_session: int=0,
                session_callback: Callable=None,
                max_sessions_per_shard: int=0,
                soda_metadata_cache: bool=None,
                ping_interval: int=None,

                # credentials
                user: str=None,
                proxy_user: str=None,
                password: str=None,
                newpassword: str=None,
                wallet_password: str=None,

                # connect string parameters
                host: str=None,
                port: int=None,
                protocol: str=None,
                https_proxy: str=None,
                https_proxy_port: int=None,
                service_name: str=None,
                sid: str=None,
                server_type: str=None,
                cclass: str=None,
                purity: int=None,
                expire_time: int=None,
                retry_count: int=None,
                retry_delay: int=None,
                tcp_connect_timeout: float=None,
                ssl_server_dn_match: bool=None,
                ssl_server_cert_dn: str=None,
                wallet_location: str=None,

                # other parameters
                events: bool=None,
                mode: int=None,
                disable_oob: bool=None,
                stmtcachesize: int=None,
                edition: str=None,
                tag: str=None,
                matchanytag: bool=None,
                config_dir: str=None,
                appcontext: list=None,
                shardingkey: list=None,
                supershardingkey: list=None,
                debug_jdwp: str=None,
                handle: int=None,

                # deprecated parameters
                waitTimeout: int=None,
                maxLifetimeSession: int=None,
                maxSessionsPerShard: int=None,
                sessionCallback: Callable=None,

                # deprecated (ignored) parameters
                threaded: bool=None,
                encoding: str=None,
                nencoding: str=None) -> ConnectionPool:
    """
    Creates a connection pool with the supplied parameters and returns it.

    The dsn parameter (data source name) can be a string in the format
    user/password@connect_string or can simply be the connect string (in
    which case authentication credentials such as the username and password
    need to be specified separately). See the documentation on connection
    strings for more information.

    The pool_class parameter is expected to be ConnectionPool or a subclass of
    ConnectionPool.

    The params parameter is expected to be of type PoolParams and contains
    parameters that are used to create the pool. See the documentation on
    PoolParams for more information. If this parameter is not specified, the
    additional keyword parameters will be used to create an instance of
    PoolParams. If both the params parameter and additional keyword parameters
    are specified, the values in the keyword parameters have precedence.
    Note that if a dsn is also supplied, then in the python-oracledb Thin mode,
    the values of the parameters specified (if any) within the dsn will override
    the values passed as additional keyword parameters, which themselves
    override the values set in the params parameter object.
    """
    pass
