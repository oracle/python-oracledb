.. _asyncconnpoolobj:

********************************
API: AsyncConnectionPool Objects
********************************

An AsyncConnectionPool object can be created with
:meth:`oracledb.create_pool_async()`.

.. dbapiobjectextension::

.. versionadded:: 2.0.0

.. note::

    AsyncConnectionPool objects are only supported in the python-oracledb Thin
    mode.

.. _asynconnpoolmeth:

AsyncConnectionPool Methods
===========================

.. method:: AsyncConnectionPool.acquire(user=None, password=None, cclass=None, \
        purity=oracledb.PURITY_DEFAULT, tag=None, matchanytag=False, \
        shardingkey=[], supershardingkey=[])

    Acquires a connection from the pool and returns an
    :ref:`asynchronous connection object <asyncconnobj>`.

    If the pool is :ref:`homogeneous <connpooltypes>`, the ``user`` and
    ``password`` parameters cannot be specified. If they are, an exception will
    be raised.

    The ``cclass`` parameter, if specified, should be a string corresponding to
    the connection class for :ref:`drcp`.

    The ``purity`` parameter is expected to be one of
    :data:`~oracledb.PURITY_NEW`, :data:`~oracledb.PURITY_SELF`, or
    :data:`~oracledb.PURITY_DEFAULT`.

    The ``tag``, ``matchanytag``, ``shardingkey``, and ``supershardingkey``
    parameters are ignored in python-oracledb Thin mode.

.. method:: AsyncConnectionPool.close(force=False)

    Closes the pool now, rather than when the last reference to it is
    released, which makes it unusable for further work.

    If any connections have been acquired and not released back to the pool,
    this method will fail unless the ``force`` parameter is set to *True*.

.. method:: AsyncConnectionPool.drop(connection)

    Drops the connection from the pool which is useful if the connection is no
    longer usable (such as when the session is killed).

.. method:: AsyncConnectionPool.release(connection, tag=None)

    Releases the connection back to the pool now, rather than whenever
    ``__del__`` is called. The connection will be unusable from this point
    forward; an Error exception will be raised if any operation is attempted
    with the connection. Any cursors or LOBs created by the connection will
    also be  marked unusable and an Error exception will be raised if any
    operation is attempted with them.

    Internally, references to the connection are held by cursor objects,
    LOB objects, and so on. Once all of these references are released, the
    connection itself will be released back to the pool automatically. Either
    control references to these related objects carefully or explicitly
    release connections back to the pool in order to ensure sufficient
    resources are available.

    The ``tag`` parameter is ignored in python-oracledb Thin mode.

.. _asyncconnpoolattr:

AsyncConnectionPool Attributes
==============================

.. attribute:: AsyncConnectionPool.busy

    This read-only attribute returns the number of connections currently
    acquired.

.. attribute:: AsyncConnectionPool.dsn

    This read-only attribute returns the TNS entry of the database to which a
    connection has been established.

.. attribute:: AsyncConnectionPool.getmode

    This read-write attribute determines how connections are returned from the
    pool. If :data:`~oracledb.POOL_GETMODE_FORCEGET` is specified, a new
    connection will be returned even if there are no free connections in the
    pool.  :data:`~oracledb.POOL_GETMODE_NOWAIT` will raise an exception if
    there are no free connections are available in the pool. If
    :data:`~oracledb.POOL_GETMODE_WAIT` is specified and there are no free
    connections in the pool, the caller will wait until a free connection is
    available. :data:`~oracledb.POOL_GETMODE_TIMEDWAIT` uses the value of
    :data:`~ConnectionPool.wait_timeout` to determine how long the caller
    should wait for a connection to become available before returning an error.

.. attribute:: AsyncConnectionPool.homogeneous

    This read-only boolean attribute indicates whether the pool is considered
    :ref:`homogeneous <connpooltypes>` or not. If the pool is not homogeneous,
    different authentication can be used for each connection acquired from the
    pool.

.. attribute:: AsyncConnectionPool.increment

    This read-only attribute returns the number of connections that will be
    established when additional connections need to be created.

.. attribute:: AsyncConnectionPool.max

    This read-only attribute returns the maximum number of connections that the
    pool can control.

.. attribute:: AsyncConnectionPool.max_lifetime_session

    This read-write attribute is the maximum length of time (in seconds) that a
    pooled connection may exist since first being created. A value of *0* means
    there is no limit. Connections become candidates for termination when they
    are acquired or released back to the pool, and have existed for longer than
    ``max_lifetime_session`` seconds. Connections that are in active use will
    not be closed. In python-oracledb Thick mode, Oracle Client libraries 12.1
    or later must be used and, prior to Oracle Client 21, cleanup only occurs
    when the pool is accessed.

.. attribute:: AsyncConnectionPool.max_sessions_per_shard

    This read-write attribute returns the number of sessions that can be
    created per shard in the pool. This attribute cannot be used in
    python-oracledb Thin mode.

.. attribute:: AsyncConnectionPool.min

    This read-only attribute returns the number of connections with which the
    connection pool was created and the minimum number of connections that will
    be controlled by the connection pool.

.. attribute:: AsyncConnectionPool.name

    This read-only attribute returns the name assigned to the pool by Oracle.

.. attribute:: AsyncConnectionPool.opened

    This read-only attribute returns the number of connections currently opened
    by the pool.

.. attribute:: AsyncConnectionPool.ping_interval

    This read-write integer attribute specifies the pool ping interval in
    seconds. When a connection is acquired from the pool, a check is first made
    to see how long it has been since the connection was put into the pool. If
    this idle time exceeds ``ping_interval``, then a :ref:`round-trip
    <roundtrips>` ping to the database is performed. If the connection is
    unusable, it is discarded and a different connection is selected to be
    returned by :meth:`AsyncConnectionPool.acquire()`.  Setting
    ``ping_interval`` to a negative value disables pinging.  Setting it to *0*
    forces a ping for every :meth:`AsyncConnectionPool.acquire()` and is not
    recommended.

.. attribute:: AsyncConnectionPool.soda_metadata_cache

    This read-write boolean attribute returns whether the SODA metadata cache
    is enabled or not. This attribute cannot be used in python-oracledb Thin
    mode.

.. attribute:: AsyncConnectionPool.stmtcachesize

    This read-write attribute specifies the size of the statement cache that
    will be used for connections obtained from the pool. Once a connection is
    created, that connection’s statement cache size can only be changed by
    setting the ``stmtcachesize`` attribute on the connection itself.

    See :ref:`Statement Caching <stmtcache>` for more information.

.. attribute:: AsyncConnectionPool.thin

    This attribute returns a boolean which indicates the python-oracledb mode
    in which the pool was created. If the value of this attribute is *True*, it
    indicates that the pool was created in the python-oracledb Thin mode. If
    the value of this attribute is *False*, it indicates that the pool was
    created in the python-oracledb Thick mode.

.. attribute:: AsyncConnectionPool.timeout

    This read-only attribute is an integer that specifies the length of time
    (in seconds) that a connection may remain idle in the pool before it is
    terminated. This applies only when the pool has more than ``min``
    connections open, allowing it to shrink to the specified minimum size. The
    default value is *0* seconds. A value of *0* means that there is no maximum
    time.

.. attribute:: AsyncConnectionPool.username

    This read-only attribute returns the name of the user which established the
    connection to the database.

.. attribute:: AsyncConnectionPool.wait_timeout

    This read-write attribute specifies the time (in milliseconds) that the
    caller should wait for a connection to become available in the pool before
    returning with an error. This value is only used if the ``getmode``
    parameter to :meth:`oracledb.create_pool_async()` was the value
    :data:`oracledb.POOL_GETMODE_TIMEDWAIT`.
