.. _connpool:

***************************
API: ConnectionPool Objects
***************************

The new ConnectionPool class is synonymous with SessionPool. The SessionPool
class is deprecated in python-oracledb.  The preferred function to create pools
is now :meth:`oracledb.create_pool()`.  (The name SessionPool came from the
`Oracle Call Interface (OCI) session pool <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-F9662FFB-EAEF-495C-96FC-49C6D1D9625C>`__. This
implementation is only used in the python-oracledb Thick mode and is not
available in the Thin mode).

.. dbapiobjectextension::

In python-oracledb, the type `pool` will show the class `oracledb.ConnectionPool`.
This only affects the name.

The following code will continue to work providing backward compatibility with
the obsolete cx_Oracle driver:

.. code-block:: python

   issubclass(cls, oracledb.SessionPool) == True

   isinstance(pool, oracledb.SessionPool) == True

The following code will also work:

.. code-block:: python

   issubclass(cls, oracledb.ConnectionPool) == True

   isinstance(pool, oracledb.ConnectionPool) == True

The function :meth:`oracledb.SessionPool` that is used to create pools is
deprecated in python-oracledb 1.0 and has been deprecated by the function
:meth:`oracledb.create_pool`.

.. _connpoolmethods:

ConnectionPool Methods
======================

.. method:: ConnectionPool.acquire(user=None, password=None, cclass=None, \
        purity=oracledb.PURITY_DEFAULT, tag=None, matchanytag=False, \
        shardingkey=[], supershardingkey=[])

    Acquires a connection from the session pool and returns a
    :ref:`connection object <connobj>`.

    If the pool is :ref:`homogeneous <connpooltypes>`, the ``user`` and
    ``password`` parameters cannot be specified. If they are, an exception will
    be raised.

    The ``cclass`` parameter, if specified, should be a string corresponding to
    the connection class for :ref:`drcp`.

    The ``purity`` parameter is expected to be one of
    :data:`~oracledb.PURITY_NEW`, :data:`~oracledb.PURITY_SELF`, or
    :data:`~oracledb.PURITY_DEFAULT`.

    The ``tag`` parameter, if specified, is expected to be a string with
    name=value pairs like "k1=v1;k2=v2" and will limit the connections that can
    be returned from a connection pool unless the ``matchanytag`` parameter is
    set to *True*. In that case, connections with the specified tag will be
    preferred over others, but if no such connections are available, then a
    connection with a different tag may be returned instead. In any case,
    untagged connections will always be returned if no connections with the
    specified tag are available. Connections are tagged when they are
    :meth:`released <ConnectionPool.release>` back to the pool.

    The ``shardingkey`` and ``supershardingkey`` parameters, if specified, are
    expected to be a sequence of values which will be used to identify the
    database shard to connect to. The key values can be strings, numbers,
    bytes, or dates.  See :ref:`connsharding`.

    When using the :ref:`connection pool cache <connpoolcache>`, calling
    :meth:`oracledb.connect()` with a ``pool_alias`` parameter is the same as
    calling ``pool.acquire()``.

.. method:: ConnectionPool.close(force=False)

    Closes the pool now, rather than when the last reference to it is
    released, which makes it unusable for further work.

    If any connections have been acquired and not released back to the pool,
    this method will fail unless the ``force`` parameter is set to *True*.

.. method:: ConnectionPool.drop(connection)

    Drops the connection from the pool which is useful if the connection is no
    longer usable (such as when the session is killed).

.. method:: ConnectionPool.reconfigure([min, max, increment, getmode, \
        timeout, wait_timeout, max_lifetime_session, max_sessions_per_shard, \
        soda_metadata_cache, stmtcachesize, ping_interval])

    Reconfigures various parameters of a connection pool. The pool size can be
    altered with ``reconfigure()`` by passing values for
    :data:`~ConnectionPool.min`, :data:`~ConnectionPool.max` or
    :data:`~ConnectionPool.increment`.  The :data:`~ConnectionPool.getmode`,
    :data:`~ConnectionPool.timeout`, :data:`~ConnectionPool.wait_timeout`,
    :data:`~ConnectionPool.max_lifetime_session`,
    :data:`~ConnectionPool.max_sessions_per_shard`,
    :data:`~ConnectionPool.soda_metadata_cache`,
    :data:`~ConnectionPool.stmtcachesize` and
    :data:`~ConnectionPool.ping_interval` attributes can be set directly or
    with ``reconfigure()``.

    All parameters are optional. Unspecified parameters will leave those pool
    attributes unchanged. The parameters are processed in two stages. After any
    size change has been processed, reconfiguration on the other parameters is
    done sequentially. If an error such as an invalid value occurs when changing
    one attribute, then an exception will be generated but any already changed
    attributes will retain their new values.

    During reconfiguration of a pool's size, the behavior of
    :meth:`ConnectionPool.acquire()` depends on the ``getmode`` in effect when
    ``acquire()`` is called:

    * With mode :data:`~oracledb.POOL_GETMODE_FORCEGET`, an ``acquire()`` call
      will wait until the pool has been reconfigured.

    * With mode :data:`~oracledb.POOL_GETMODE_TIMEDWAIT`, an ``acquire()`` call
      will try to acquire a connection in the time specified by
      pool.wait_timeout and return an error if the time taken exceeds that
      value.

    * With mode :data:`~oracledb.POOL_GETMODE_WAIT`, an ``acquire()`` call will
      wait until after the pool has been reconfigured and a connection is
      available.

    * With mode :data:`~oracledb.POOL_GETMODE_NOWAIT`, if the number of busy
      connections is less than the pool size, ``acquire()`` will return a new
      connection after pool reconfiguration is complete.

    Closing connections with :meth:`ConnectionPool.release()` or
    :meth:`Connection.close()` will wait until any pool size reconfiguration is
    complete.

    Closing the connection pool with :meth:`ConnectionPool.close()` will wait
    until reconfiguration is complete.

    See :ref:`Connection Pool Reconfiguration <poolreconfiguration>`.

.. method:: ConnectionPool.release(connection, tag=None)

    Releases the connection back to the pool now, rather than whenever __del__
    is called. The connection will be unusable from this point forward; an
    Error exception will be raised if any operation is attempted with the
    connection. Any cursors or LOBs created by the connection will also be
    marked unusable and an Error exception will be raised if any operation is
    attempted with them.

    Internally, references to the connection are held by cursor objects,
    LOB objects, etc. Once all of these references are released, the connection
    itself will be released back to the pool automatically. Either control
    references to these related objects carefully or explicitly release
    connections back to the pool in order to ensure sufficient resources are
    available.

    If the tag is not *None*, it is expected to be a string with name=value
    pairs like "k1=v1;k2=v2" and will override the value in the property
    :attr:`Connection.tag`. If either :attr:`Connection.tag` or the tag
    parameter are not *None*, the connection will be retagged when it is
    released back to the pool.

.. _connpoolattr:

ConnectionPool Attributes
=========================

.. attribute:: ConnectionPool.busy

    This read-only attribute returns the number of connections currently
    acquired.

.. attribute:: ConnectionPool.dsn

    This read-only attribute returns the TNS entry of the database to which a
    connection has been established.

.. attribute:: ConnectionPool.getmode

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

.. attribute:: ConnectionPool.homogeneous

    This read-only boolean attribute indicates whether the pool is considered
    :ref:`homogeneous <connpooltypes>` or not. If the pool is not homogeneous,
    different authentication can be used for each connection acquired from the
    pool.

.. attribute:: ConnectionPool.increment

    This read-only attribute returns the number of connections that will be
    established when additional connections need to be created.

.. attribute:: ConnectionPool.max

    This read-only attribute returns the maximum number of connections that the
    pool can control.

.. attribute:: ConnectionPool.max_lifetime_session

    This read-write attribute is the maximum length of time (in seconds) that a
    pooled connection may exist since first being created. A value of *0* means
    there is no limit. Connections become candidates for termination when they
    are acquired or released back to the pool, and have existed for longer than
    ``max_lifetime_session`` seconds. Connections that are in active use will
    not be closed. In python-oracledb Thick mode, Oracle Client libraries 12.1
    or later must be used and, prior to Oracle Client 21, cleanup only occurs
    when the pool is accessed.

    .. versionchanged:: 3.0.0

        This attribute was added to python-oracledb Thin mode.

.. attribute:: ConnectionPool.max_sessions_per_shard

    This read-write attribute returns the number of sessions that can be
    created per shard in the pool. Setting this attribute greater than zero
    specifies the maximum number of sessions in the pool that can be used for
    any given shard in a sharded database. This lets connections in the pool be
    balanced across the shards. A value of *0* will not set any maximum number
    of sessions for each shard. This attribute is only available in Oracle
    Client 18.3 and higher.

.. attribute:: ConnectionPool.min

    This read-only attribute returns the number of connections with which the
    connection pool was created and the minimum number of connections that will
    be controlled by the connection pool.

.. attribute:: ConnectionPool.name

    This read-only attribute returns the name assigned to the pool by Oracle.

.. attribute:: ConnectionPool.opened

    This read-only attribute returns the number of connections currently opened
    by the pool.

.. attribute:: ConnectionPool.ping_interval

    This read-write integer attribute specifies the pool ping interval in
    seconds. When a connection is acquired from the pool, a check is first made
    to see how long it has been since the connection was put into the pool. If
    this idle time exceeds ``ping_interval``, then a :ref:`round-trip
    <roundtrips>` ping to the database is performed. If the connection is
    unusable, it is discarded and a different connection is selected to be
    returned by :meth:`ConnectionPool.acquire()`.  Setting ``ping_interval`` to
    a negative value disables pinging.  Setting it to *0* forces a ping for
    every :meth:`ConnectionPool.acquire()` and is not recommended.

    Prior to cx_Oracle 8.2, the ping interval was fixed at *60* seconds.

.. attribute:: ConnectionPool.soda_metadata_cache

    This read-write boolean attribute returns whether the SODA metadata cache
    is enabled or not. Enabling the cache significantly improves the
    performance of methods :meth:`SodaDatabase.createCollection()` (when not
    specifying a value for the ``metadata`` parameter) and
    :meth:`SodaDatabase.openCollection()`. Note that the cache can become out
    of date if changes to the metadata of cached collections are made
    externally.

.. attribute:: ConnectionPool.stmtcachesize

    This read-write attribute specifies the size of the statement cache that
    will be used for connections obtained from the pool. Once a connection is
    created, that connection’s statement cache size can only be changed by
    setting the ``stmtcachesize`` attribute on the connection itself.

    See :ref:`Statement Caching <stmtcache>` for more information.

.. attribute:: ConnectionPool.thin

    This attribute returns a boolean which indicates the python-oracledb mode
    in which the pool was created. If the value of this attribute is *True*, it
    indicates that the pool was created in the python-oracledb Thin mode. If
    the value of this attribute is *False*, it indicates that the pool was
    created in the python-oracledb Thick mode.

.. attribute:: ConnectionPool.timeout

    This read-write attribute specifies the time (in seconds) after which idle
    connections will be terminated in order to maintain an optimum number of
    open connections. A value of *0* means that no idle connections are
    terminated. Note that in python-oracledb Thick mode with older Oracle
    Client Libraries, the termination only occurs when the pool is accessed.


.. attribute:: ConnectionPool.username

    This read-only attribute returns the name of the user which established the
    connection to the database.

.. attribute:: ConnectionPool.wait_timeout

    This read-write attribute specifies the time (in milliseconds) that the
    caller should wait for a connection to become available in the pool before
    returning with an error. This value is only used if the ``getmode``
    parameter to :meth:`oracledb.create_pool()` was the value
    :data:`oracledb.POOL_GETMODE_TIMEDWAIT`.
