.. _poolparam:

***********************
API: PoolParams Objects
***********************

A PoolParams object can be created with :meth:`oracledb.PoolParams()`. The
PoolParams class is a subclass of the :ref:`ConnectParams Class <connparam>`.
In addition to the parameters and attributes of the ConnectParams class, the
PoolParams class also contains new parameters and attributes.

See :ref:`usingpoolparams` for more information.

.. _poolparamsmeth:

PoolParams Methods
==================

.. method:: PoolParams.copy()

    Creates a copy of the parameters and returns it.

.. method:: PoolParams.get_connect_string()

    Returns the connection string associated with the PoolParams instance.

.. method:: PoolParams.parse_connect_string(connect_string)

    Parses the connect string into its components and stores the parameters.

    The connect string can be an Easy Connect string, name-value pairs, or a
    simple alias which is looked up in ``tnsnames.ora``. Parameters that are
    found in the connect string override any currently stored values.

.. method:: PoolParams.set(min=None, max=None, increment=None, \
        connectiontype=None, getmode=None, homogeneous=None, timeout=None, \
        wait_timeout=None, max_lifetime_session=None, session_callback=None, \
        max_sessions_per_shard=None, soda_metadata_cache=None, \
        ping_interval=None, ping_timeout=None, user=None, proxy_user=None, \
        password=None, newpassword=None, wallet_password=None, \
        access_token=None, host=None, port=None, protocol=None, \
        https_proxy=None, https_proxy_port=None, service_name=None, \
        instance_name=None, sid=None, server_type=None, cclass=None, \
        purity=None, expire_time=None, retry_count=None, retry_delay=None, \
        tcp_connect_timeout=None, ssl_server_dn_match=None, \
        ssl_server_cert_dn=None, wallet_location=None, events=None, \
        externalauth=None, mode=None, disable_oob=None, stmtcachesize=None, \
        edition=None, tag=None, matchanytag=None, config_dir=None, \
        appcontext=[], shardingkey=[], supershardingkey=[], debug_jdwp=None, \
        connection_id_prefix=None, ssl_context=None, sdu=None, \
        pool_boundary=None, use_tcp_fast_open=False, ssl_version=None, \
        program=oracledb.defaults.program, machine=oracledb.defaults.machine, \
        terminal=oracledb.defaults.terminal, osuser=oracledb.defaults.osuser, \
        driver_name=oracledb.defaults.driver_name, use_sni=None, \
        thick_mode_dsn_passthrough=oracledb.defaults.thick_mode_dsn_passthrough, \
        extra_auth_params=None, handle=None)

        Sets one or more of the parameters.

        .. versionchanged:: 3.0.0

            The ``use_sni``, ``thick_mode_dsn_passthrough``,
            ``extra_auth_params`` and ``instance_name`` parameters were added.

        .. versionchanged:: 2.5.0

            The ``program``, ``machine``, ``terminal``, ``osuser``, and
            ``driver_name`` parameters were added. Support for ``edition`` and
            ``appcontext`` was added to python-oracledb Thin mode.

        .. versionchanged:: 2.3.0

            The ``ping_timeout`` and ``ssl_version`` parameters were added.

        .. versionchanged:: 2.1.0

            The ``pool_boundary`` and ``use_tcp_fast_open`` parameters were added.

.. _poolparamsattr:

PoolParams Attributes
=====================

.. attribute:: PoolParams.connectiontype

    This read-only attribute specifies the class of the connection that should
    be returned during calls to :meth:`ConnectionPool.acquire()`. It must be
    Connection or a subclass of Connection. This attribute is of type
    Type["oracledb.connection"].  The default value is ``oracledb.Connection``.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: PoolParams.getmode

    This read-write attribute is an integer that determines the behavior of
    :meth:`ConnectionPool.acquire()`. The value of this attribute can be one of
    the constants :data:`oracledb.POOL_GETMODE_WAIT`,
    :data:`oracledb.POOL_GETMODE_NOWAIT`, :data:`oracledb.POOL_GETMODE_FORCEGET`,
    or :data:`oracledb.POOL_GETMODE_TIMEDWAIT`.  The default value is
    :data:`oracledb.POOL_GETMODE_WAIT`.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: PoolParams.homogeneous

    This read-only attribute is a boolean which indicates whether the
    connections are :ref:`homogeneous <connpooltypes>` (same user) or
    heterogeneous (multiple users).  The default value is *True*.

    This attribute is only supported in python-oracledb Thick mode. The
    python-oracledb Thin mode supports only homogeneous modes.

.. attribute:: PoolParams.increment

    This read-only attribute specifies the number of connections that should
    be added to the pool whenever a new connection needs to be created. The
    default value is *1*.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: PoolParams.min

    This read-only attribute is an integer that specifies the minimum number
    of connections that the pool should contain. The default value is *1*.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: PoolParams.max

    This read-only attribute specifies the maximum number of connections that
    the pool should contain. The default value is *2*.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: PoolParams.max_lifetime_session

    This read-only attribute is the maximum length of time (in seconds) that a
    pooled connection may exist since first being created. A value of *0* means
    there is no limit. Connections become candidates for termination when they
    are acquired or released back to the pool, and have existed for longer than
    ``max_lifetime_session`` seconds. Connections that are in active use will
    not be closed. In python-oracledb Thick mode, Oracle Client libraries 12.1
    or later must be used and, prior to Oracle Client 21, cleanup only occurs
    when the pool is accessed.

.. attribute:: PoolParams.max_sessions_per_shard

    This read-only attribute is an integer that determines the maximum number
    of connections that may be associated with a particular shard. The default
    value is *0*.

    This attribute is only supported in python-oracledb Thick mode.

.. attribute:: PoolParams.ping_interval

    This read-only attribute is an integer that specifies the length of time
    (in seconds) after which an unused connection in the pool will be a
    candidate for pinging when :meth:`ConnectionPool.acquire()` is called.
    If the ping to the database indicates that the connection is not alive,
    then a replacement connection will be returned by
    :meth:`ConnectionPool.acquire()`.  If the ``ping_interval`` is a negative
    value, then the ping functionality will be disabled. The default value is
    *60* seconds.

  This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: PoolParams.ping_timeout

    This read-only attribute is an integer that specifies the maximum length of
    time (in milliseconds) that :meth:`ConnectionPool.acquire()` waits for a
    connection to respond to any internal ping to the database. If the ping
    does not respond within the specified time, then the connection is
    destroyed and :meth:`~ConnectionPool.acquire()` returns a different
    connection. The default value is *5000* milliseconds.

    This attribute is supported in both python-oracledb Thin and Thick modes.

  .. versionadded:: 2.3.0

.. attribute:: PoolParams.session_callback

    This read-only attribute specifies a callback that is invoked when a
    connection is returned from the pool for the first time, or when the
    connection tag differs from the one requested.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: PoolParams.soda_metadata_cache

    This read-only attribute is a boolean that indicates whether SODA
    metadata cache should be enabled or not. The default value is *False*.

    This attribute is only supported in python-oracledb Thick mode.

.. attribute:: PoolParams.timeout

    This read-only attribute is an integer that specifies the length of time
    (in seconds) that a connection may remain idle in the pool before it is
    terminated. This applies only when the pool has more than ``min``
    connections open, allowing it to shrink to the specified minimum size. The
    default value is *0* seconds. A value of *0* means that there is no maximum
    time.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: PoolParams.wait_timeout

    This read-only attribute is an integer that specifies the length of time
    (in milliseconds) that a caller should wait when acquiring a connection
    from the pool with :attr:`~PoolParams.getmode` set to
    :data:`~oracledb.POOLGETMODE_TIMEDWAIT`. The default value is *0*
    milliseconds.

    This attribute is supported in both python-oracledb Thin and Thick modes.
