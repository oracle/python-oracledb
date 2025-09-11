.. _connpool:

***************************
API: ConnectionPool Objects
***************************

.. currentmodule:: oracledb

ConnectionPool Class
====================

.. autoclass:: ConnectionPool

    The new ConnectionPool class is synonymous with SessionPool. The
    SessionPool class is deprecated in python-oracledb.  The preferred function
    to create pools is now :meth:`oracledb.create_pool()`.  (The name
    SessionPool came from the `Oracle Call Interface (OCI) session pool
    <https://www.oracle.com/pls/topic/
    lookup?ctx=dblatest&id=GUID-F9662FFB-EAEF-495C-96FC-49C6D1D9625C>`__. This
    implementation is only used in python-oracledb Thick mode and is not
    available in Thin mode).

    .. dbapiobjectextension::

In python-oracledb, the type `pool` will show the class
`oracledb.ConnectionPool`.  This only affects the name.

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

.. automethod:: ConnectionPool.acquire

.. automethod:: ConnectionPool.close

.. automethod:: ConnectionPool.drop

.. automethod:: ConnectionPool.reconfigure

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

.. automethod:: ConnectionPool.release

.. _connpoolattr:

ConnectionPool Attributes
=========================

.. autoproperty:: ConnectionPool.busy

.. autoproperty:: ConnectionPool.dsn

.. autoproperty:: ConnectionPool.getmode

.. autoproperty:: ConnectionPool.homogeneous

.. autoproperty:: ConnectionPool.increment

.. autoproperty:: ConnectionPool.max

.. autoproperty:: ConnectionPool.max_lifetime_session

    .. versionchanged:: 3.0.0

        This attribute was added to python-oracledb Thin mode.

.. autoproperty:: ConnectionPool.max_sessions_per_shard

.. autoproperty:: ConnectionPool.min

.. autoproperty:: ConnectionPool.name

.. autoproperty:: ConnectionPool.opened

.. autoproperty:: ConnectionPool.ping_interval

    Prior to cx_Oracle 8.2, the ping interval was fixed at *60* seconds.

.. autoproperty:: ConnectionPool.soda_metadata_cache

.. autoproperty:: ConnectionPool.stmtcachesize

    See :ref:`Statement Caching <stmtcache>` for more information.

.. autoproperty:: ConnectionPool.thin

    See :ref:`vsessconinfo`.

.. autoproperty:: ConnectionPool.timeout

.. autoproperty:: ConnectionPool.username

.. autoproperty:: ConnectionPool.wait_timeout
