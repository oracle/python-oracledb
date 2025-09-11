.. _asyncconnpoolobj:

********************************
API: AsyncConnectionPool Objects
********************************

.. currentmodule:: oracledb

AsyncConnectionPool Class
=========================

.. autoclass:: AsyncConnectionPool

    An AsyncConnectionPool object should be created with
    :meth:`oracledb.create_pool_async()`.

    .. dbapiobjectextension::

    .. versionadded:: 2.0.0

    .. note::

        AsyncConnectionPool objects are only supported in python-oracledb Thin
        mode.

.. _asynconnpoolmeth:

AsyncConnectionPool Methods
===========================

.. automethod:: AsyncConnectionPool.acquire

.. automethod:: AsyncConnectionPool.close

.. automethod:: AsyncConnectionPool.drop

.. automethod:: AsyncConnectionPool.release

    .. note::

        Asynchronous connections are not automatically closed at the end of
        scope. This is different to synchronous connection
        behavior. Asynchronous connections should either be explicitly
        released, or have been initially created via a `context manager
        <https://docs.python.org/3/library/stdtypes.html#context-manager-types>`__
        ``with`` statement.

.. _asyncconnpoolattr:

AsyncConnectionPool Attributes
==============================

.. autoproperty:: AsyncConnectionPool.busy

.. autoproperty:: AsyncConnectionPool.dsn

.. autoproperty:: AsyncConnectionPool.getmode

.. autoproperty:: AsyncConnectionPool.homogeneous

.. autoproperty:: AsyncConnectionPool.increment

.. autoproperty:: AsyncConnectionPool.max

.. autoproperty:: AsyncConnectionPool.max_lifetime_session

.. autoproperty:: AsyncConnectionPool.max_sessions_per_shard

.. autoproperty:: AsyncConnectionPool.min

.. autoproperty:: AsyncConnectionPool.name

.. autoproperty:: AsyncConnectionPool.opened

.. autoproperty:: AsyncConnectionPool.ping_interval

.. autoproperty:: AsyncConnectionPool.soda_metadata_cache

.. autoproperty:: AsyncConnectionPool.stmtcachesize

    See :ref:`Statement Caching <stmtcache>` for more information.

.. autoproperty:: AsyncConnectionPool.thin

.. autoproperty:: AsyncConnectionPool.timeout

.. autoproperty:: AsyncConnectionPool.username

.. autoproperty:: AsyncConnectionPool.wait_timeout
