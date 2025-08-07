.. module:: oracledb

.. _module:

****************************
API: python-oracledb Module
****************************

.. _modmeth:

Oracledb Methods
================

.. autofunction:: Binary

.. autofunction:: clientversion

    See :ref:`enablingthick`.

    .. dbapimethodextension::

.. autofunction:: connect

    .. versionchanged:: 3.2.0

        The ``pool_name`` parameter was added.

    .. versionchanged:: 3.0.0

        The ``pool_alias``, ``instance_name``, ``use_sni``,
        ``thick_mode_dsn_passthrough``, and ``extra_auth_params`` parameters
        were added. The ``pool`` parameter was deprecated: use
        :meth:`ConnectionPool.acquire()` instead.

    .. versionchanged:: 2.5.0

        The ``program``, ``machine``, ``terminal``, ``osuser``, and
        ``driver_name`` parameters were added. Support for ``edition`` and
        ``appcontext`` was added to python-oracledb Thin mode.

    .. versionchanged:: 2.3.0

        The default value of the ``retry_delay`` parameter was changed from 0
        seconds to 1 second. The default value of the ``tcp_connect_timeout``
        parameter was changed from 60.0 seconds to 20.0 seconds. The
        ``ssl_version`` parameter was added.

    .. versionchanged:: 2.1.0

        The ``pool_boundary`` and ``use_tcp_fast_open`` parameters were added.

    .. versionchanged:: 2.0.0

        The ``ssl_context`` and ``sdu`` parameters were added.

    .. versionchanged:: 1.4.0

        The ``connection_id_prefix`` parameter was added.

.. autofunction:: connect_async

    .. versionchanged:: 3.2.0

        The ``pool_name`` parameter was added.

    .. versionchanged:: 3.0.0

        The ``pool_alias``, ``instance_name``, ``use_sni``,
        ``thick_mode_dsn_passthrough``, and ``extra_auth_params`` parameters
        were added. The ``pool`` parameter was deprecated: use
        :meth:`AsyncConnectionPool.acquire()` instead.

    .. versionchanged:: 2.5.0

        The ``program``, ``machine``, ``terminal``, ``osuser``, and
        ``driver_name`` parameters were added. Support for ``edition`` and
        ``appcontext`` was added.

    .. versionchanged:: 2.3.0

        The default value of the ``retry_delay`` parameter was changed from 0
        seconds to 1 second. The default value of the ``tcp_connect_timeout``
        parameter was changed from 60.0 seconds to 20.0 seconds. The
        ``ssl_version`` parameter was added.

    .. versionchanged:: 2.1.0

        The ``pool_boundary`` and ``use_tcp_fast_open`` parameters were added.

    .. versionchanged:: 2.0.0

        The ``ssl_context`` and ``sdu`` parameters were added.

    .. versionchanged:: 1.4.0

        The ``connection_id_prefix`` parameter was added.

.. autofunction:: create_pipeline

    .. versionadded:: 2.4.0

.. autofunction:: create_pool

    .. versionchanged:: 3.2.0

        The ``pool_name`` parameter was added.

    .. versionchanged:: 3.0.0

        The ``pool_alias``, ``instance_name``, ``use_sni``,
        ``thick_mode_dsn_passthrough``, and ``extra_auth_params`` parameters
        were added.

    .. versionchanged:: 2.5.0

        The ``program``, ``machine``, ``terminal``, ``osuser``, and
        ``driver_name`` parameters were added. Support for ``edition`` and
        ``appcontext`` was added to python-oracledb Thin mode.

    .. versionchanged:: 2.3.0

        The default value of the ``retry_delay`` parameter was changed from *0*
        seconds to *1* second. The default value of the ``tcp_connect_timeout``
        parameter was changed from *60.0* seconds to *20.0* seconds. The
        ``ping_timeout`` and ``ssl_version`` parameters were added.

    .. versionchanged:: 2.1.0

        The ``pool_boundary`` and ``use_tcp_fast_open`` parameters were added.

    .. versionchanged:: 2.0.0

        The ``ssl_context`` and ``sdu`` parameters were added.

    .. versionchanged:: 1.4.0

        The ``connection_id_prefix`` parameter was added.

.. autofunction:: create_pool_async

    .. versionchanged:: 3.2.0

        The ``pool_name`` parameter was added.

    .. versionchanged:: 3.0.0

        The ``pool_alias``, ``instance_name``, ``use_sni``,
        ``thick_mode_dsn_passthrough``, and ``extra_auth_params`` parameters
        were added.

    .. versionchanged:: 2.5.0

        The ``program``, ``machine``, ``terminal``, ``osuser``, and
        ``driver_name`` parameters were added. Support for ``edition`` and
        ``appcontext`` was added.

    .. versionchanged:: 2.3.0

        The default value of the ``retry_delay`` parameter was changed from 0
        seconds to 1 second. The default value of the ``tcp_connect_timeout``
        parameter was changed from 60.0 seconds to 20.0 seconds. The
        ``ping_timeout`` and ``ssl_version`` parameters were added.

    .. versionchanged:: 2.1.0

        The ``pool_boundary`` and ``use_tcp_fast_open`` parameters were added.

    .. versionchanged:: 2.0.0

        The ``ssl_context`` and ``sdu`` parameters were added.

    .. versionchanged:: 1.4.0

        The ``connection_id_prefix`` parameter was added.

.. autofunction:: Date

.. autofunction:: DateFromTicks

.. autofunction:: enable_thin_mode

    See :ref:`enablingthin` for more information.

    .. versionadded:: 2.5.0

.. autofunction:: from_arrow

    .. versionadded:: 3.3.0

.. autofunction:: get_pool

    See :ref:`connpoolcache` for more information.

    .. versionadded:: 3.0.0

.. autofunction:: init_oracle_client

    .. dbapimethodextension::

    .. versionchanged:: 3.0.0

        At completion of the method, the value of
        :attr:`oracledb.defaults.config_dir <Defaults.config_dir>` may get
        changed by python-oracledb.

    .. versionchanged:: 2.5.0

        The values supplied to the ``lib_dir`` and ``config_dir`` parameters
        are encoded using the encoding returned by `locale.getencoding()
        <https://docs.python.org/3/library/locale.html#locale.getencoding>`__
        for Python 3.11 and higher; for all other versions, the encoding
        "utf-8" is used.  These values may also be supplied as a ``bytes``
        object, in which case they will be used as is.

.. autofunction:: is_thin_mode

    .. dbapimethodextension::

    .. versionadded:: 1.1.0

.. autofunction:: makedsn

    .. deprecated:: python-oracledb 1.0

    Use the :meth:`oracledb.ConnectParams()` method instead.

    .. dbapimethodextension::

.. autofunction:: register_params_hook

    To unregister a user function, use :meth:`oracledb.unregister_params_hook`.

    See :ref:`registerparamshook`.

    .. dbapimethodextension::

    .. versionadded:: 3.0.0

.. autofunction:: register_password_type

    See :ref:`registerpasswordtype`.

    .. dbapimethodextension::

    .. versionadded:: 3.0.0

.. autofunction:: register_protocol

    See :ref:`registerprotocolhook` for more information.

    .. dbapimethodextension::

    .. versionadded:: 2.5.0

.. autofunction:: Time

.. autofunction:: TimeFromTicks

.. autofunction:: Timestamp

.. autofunction:: TimestampFromTicks

.. autofunction:: unregister_params_hook

    .. dbapimethodextension::

    .. versionadded:: 3.0.0


.. _interval_ym:

Oracledb IntervalYM Class
=========================

Objects of this class are returned for columns of type INTERVAL YEAR TO MONTH
and can be passed to variables of type :data:`oracledb.DB_TYPE_INTERVAL_YM`
The class is a `collections.namedtuple()
<https://docs.python.org/3/library/collections.html#collections.namedtuple>`__
class with two integer attributes, ``years`` and ``months``.

.. versionadded:: 2.2.0


.. _jsonid:

Oracledb JsonId Class
=====================

Objects of this class are returned by :ref:`SODA <soda>` in the ``_id``
attribute of documents stored in native collections when using Oracle Database
23.4 (and later). It is a subclass of the `bytes <https://docs.python.org/3/
library/stdtypes.html#bytes>`__ class.

.. versionadded:: 2.1.0


.. _futureobj:

Oracledb __future__ Object
==========================

Special object that contains attributes which control the behavior of
python-oracledb, allowing for opting in for new features.

.. dbapimethodextension::

.. _constants:

Oracledb Constants
==================

General
-------

.. data:: apilevel

    String constant stating the supported DB API level. Currently '2.0'.


.. data:: paramstyle

    String constant stating the type of parameter marker formatting expected by
    the interface. Currently 'named' as in 'where name = :name'.


.. data:: threadsafety

    Integer constant stating the level of thread safety that the interface
    supports.  Currently 2, which means that threads may share the module and
    connections, but not cursors. Sharing means that a thread may use a
    resource without wrapping it using a mutex semaphore to implement resource
    locking.

.. data:: version
.. data:: __version__

    String constant stating the version of the module. Currently '|release|'.

    .. dbapiattributeextension::


Advanced Queuing: Delivery Modes
--------------------------------

The AQ Delivery mode constants are possible values for the
:attr:`~DeqOptions.deliverymode` attribute of the
:ref:`dequeue options object <deqoptions>` passed as the ``options`` parameter
to the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, and :meth:`AsyncQueue.deqmany()`  methods as well
as the :attr:`~EnqOptions.deliverymode` attribute of the
:ref:`enqueue options object <enqoptions>` passed as the ``options`` parameter
to the :meth:`Queue.enqone()`, :meth:`Queue.enqmany()`,
:meth:`AsyncQueue.enqone()`, and :meth:`AsyncQueue.enqmany()` methods. They are
also possible values for the :attr:`~MessageProperties.deliverymode` attribute
of the :ref:`message properties object <msgproperties>` passed as the
``msgproperties`` parameter to the :meth:`Queue.deqone()`,
:meth:`Queue.deqmany()`, :meth:`AsyncQueue.deqone()`, or
:meth:`AsyncQueue.deqmany()`, and :meth:`Queue.enqone()`,
:meth:`Queue.enqmany()`, :meth:`AsyncQueue.enqone()`, or
:meth:`AsyncQueue.enqmany()` methods.

.. dbapiconstantextension::

.. data:: MSG_BUFFERED

    This constant is used to specify that enqueue or dequeue operations should
    enqueue or dequeue buffered messages, respectively. For multi-consumer
    queues, a `subscriber <https://www.oracle.com/pls/topic/lookup?ctx=dblatest
    &id=GUID-5FB46C6A-BB22-4CDE-B7D6-E242DC8808D8>`__ with buffered delivery
    mode needs to be created prior to enqueuing buffered messages.

    This mode is not supported for bulk array operations in python-oracledb
    Thick mode.

.. data:: MSG_PERSISTENT

    This constant is used to specify that enqueue/dequeue operations should
    enqueue or dequeue persistent messages. This is the default value.


.. data:: MSG_PERSISTENT_OR_BUFFERED

    This constant is used to specify that dequeue operations should dequeue
    either persistent or buffered messages.


Advanced Queuing: Dequeue Modes
-------------------------------

The AQ Dequeue mode constants are possible values for the
:attr:`~DeqOptions.mode` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. data:: DEQ_BROWSE

    This constant is used to specify that dequeue should read the message
    without acquiring any lock on the message (equivalent to a select
    statement).


.. data:: DEQ_LOCKED

    This constant is used to specify that dequeue should read and obtain a
    write lock on the message for the duration of the transaction (equivalent
    to a select for update statement).


.. data:: DEQ_REMOVE

    This constant is used to specify that dequeue should read the message and
    update or delete it. This is the default value.


.. data:: DEQ_REMOVE_NODATA

    This constant is used to specify that dequeue should confirm receipt of the
    message but not deliver the actual message content.


Advanced Queuing: Dequeue Navigation Modes
------------------------------------------

The AQ Dequeue Navigation mode constants are possible values for the
:attr:`~DeqOptions.navigation` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. data:: DEQ_FIRST_MSG

    This constant is used to specify that dequeue should retrieve the first
    available message that matches the search criteria. This resets the
    position to the beginning of the queue.


.. data:: DEQ_NEXT_MSG

    This constant is used to specify that dequeue should retrieve the next
    available message that matches the search criteria. If the previous message
    belongs to a message group, AQ retrieves the next available message that
    matches the search criteria and belongs to the message group. This is the
    default.


.. data:: DEQ_NEXT_TRANSACTION

    This constant is used to specify that dequeue should skip the remainder of
    the transaction group and retrieve the first message of the next
    transaction group. This option can only be used if message grouping is
    enabled for the current queue.


Advanced Queuing: Dequeue Visibility Modes
------------------------------------------

The AQ Dequeue Visibility mode constants are possible values for the
:attr:`~DeqOptions.visibility` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. data:: DEQ_IMMEDIATE

    This constant is used to specify that dequeue should perform its work as
    part of an independent transaction.


.. data:: DEQ_ON_COMMIT

    This constant is used to specify that dequeue should be part of the current
    transaction. This is the default value.


Advanced Queuing: Dequeue Wait Modes
------------------------------------

The AQ Dequeue Wait mode constants are possible values for the
:attr:`~DeqOptions.wait` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. data:: DEQ_NO_WAIT

    This constant is used to specify that dequeue not wait for messages to be
    available for dequeuing.


.. data:: DEQ_WAIT_FOREVER

    This constant is used to specify that dequeue should wait forever for
    messages to be available for dequeuing. This is the default value.


Advanced Queuing: Enqueue Visibility Modes
------------------------------------------

The AQ Enqueue Visibility mode constants are possible values for the
:attr:`~EnqOptions.visibility` attribute of the
:ref:`enqueue options object <enqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.enqone()`, :meth:`Queue.enqmany()`,
:meth:`AsyncQueue.enqone()`, or :meth:`AsyncQueue.enqmany()` methods.

.. dbapiconstantextension::

.. data:: ENQ_IMMEDIATE

    This constant is used to specify that enqueue should perform its work as
    part of an independent transaction.

    The use of this constant with :ref:`bulk enqueuing <bulkenqdeq>` is only
    supported in python-oracledb :ref:`Thick mode <enablingthick>`.


.. data:: ENQ_ON_COMMIT

    This constant is used to specify that enqueue should be part of the current
    transaction. This is the default value.


Advanced Queuing: Message States
--------------------------------

The AQ Message state constants are possible values for the
:attr:`~MessageProperties.state` attribute of the
:ref:`message properties object <msgproperties>`. This object is the
``msgproperties`` parameter for the :meth:`Queue.deqone()`,
:meth:`Queue.deqmany()`, :meth:`AsyncQueue.deqone()` or
:meth:`AsyncQueue.deqmany()` and :meth:`Queue.enqone()`,
:meth:`Queue.enqmany()`, :meth:`AsyncQueue.enqone()`, or
:meth:`AsyncQueue.enqmany()` methods.

.. dbapiconstantextension::

.. data:: MSG_EXPIRED

    This constant is used to specify that the message has been moved to the
    exception queue.


.. data:: MSG_PROCESSED

    This constant is used to specify that the message has been processed and
    has been retained.


.. data:: MSG_READY

    This constant is used to specify that the message is ready to be processed.


.. data:: MSG_WAITING

    This constant is used to specify that the message delay has not yet been
    reached.


Advanced Queuing: Other Constants
---------------------------------

This section contains other constants that are used for Advanced Queueing.

.. dbapiconstantextension::

.. data:: MSG_NO_DELAY

    This constant is a possible value for the :attr:`~MessageProperties.delay`
    attribute of the :ref:`message properties object <msgproperties>` passed
    as the ``msgproperties`` parameter to the :meth:`Queue.deqone()` or
    :meth:`Queue.deqmany()` and :meth:`Queue.enqone()` or
    :meth:`Queue.enqmany()` methods. It specifies that no delay should be
    imposed and the message should be immediately available for dequeuing. This
    is also the default value.


.. data:: MSG_NO_EXPIRATION

    This constant is a possible value for the
    :attr:`~MessageProperties.expiration` attribute of the
    :ref:`message properties object <msgproperties>` passed as the
    ``msgproperties`` parameter to the :meth:`Queue.deqone()` or
    :meth:`Queue.deqmany()` and :meth:`Queue.enqone()` or
    :meth:`Queue.enqmany()` methods. It specifies that the message never
    expires. This is also the default value.


.. _connection-authorization-modes:

Connection Authorization Modes
------------------------------

The Connection Authorization mode constants belong to the enumeration called
``AuthMode``. They are possible values for the ``mode`` parameters of
:meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.connect_async()`, and :meth:`oracledb.create_pool_async()`.
These constants have deprecated the authorization modes used in the obsolete
cx_Oracle driver.

.. dbapiconstantextension::

.. versionchanged:: 2.3.0

    The integer constants for the connection authorization modes were replaced
    with the enumeration ``AuthMode``.

.. data:: AUTH_MODE_DEFAULT

    This constant is used to specify that default authentication is to take
    place. This is the default value if no mode is passed at all.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.DEFAULT``.

    This constant deprecates the ``DEFAULT_AUTH`` constant that was used in the
    obsolete cx_Oracle driver, and was the default ``mode`` value.

.. data:: AUTH_MODE_PRELIM

    This constant is used to specify that preliminary authentication is to be
    used. This is needed for performing database startup and shutdown.

    It can only be used in python-oracledb Thick mode for standalone
    connections.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.PRELIM``.

    This constant deprecates the ``PRELIM_AUTH`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSASM

    This constant is used to specify that SYSASM access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSASM``.

    This constant deprecates the ``SYSASM`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSBKP

    This constant is used to specify that SYSBACKUP access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSBKP``.

    This constant deprecates the ``SYSBKP`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSDBA

    This constant is used to specify that SYSDBA access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSDBA``.

    This constant deprecates the ``SYSDBA`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSDGD

    This constant is used to specify that SYSDG access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSDGD``.

    This constant deprecates the ``SYSDGD`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSKMT

    This constant is used to specify that SYSKM access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSKMT``.

    This constant deprecates the ``SYSKMT`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSOPER

    This constant is used to specify that SYSOPER access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSOPER``.

    This constant deprecates the ``SYSOPER`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSRAC

    This constant is used to specify that SYSRAC access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSRAC``.

    This constant deprecates the ``SYSRAC`` constant that was used in the
    obsolete cx_Oracle driver.

.. _pipeline-operation-types:

Pipeline Operation Types
------------------------

The Pipeline Operation type constants belong to the enumeration called
``PipelineOpType``. The pipelining constants listed below are used to identify
the type of operation added. They are possible values for the
:attr:`PipelineOp.op_type` attribute.

.. versionadded:: 2.4.0

.. data:: oracledb.PIPELINE_OP_TYPE_CALL_FUNC

    This constant identifies the type of operation as the calling of a stored
    function.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.CALL_FUNC``.

.. data:: oracledb.PIPELINE_OP_TYPE_CALL_PROC

    This constant identifies the type of operation as the calling of a stored
    procedure.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.CALL_PROC``.

.. data:: oracledb.PIPELINE_OP_TYPE_COMMIT

    This constant identifies the type of operation as the performing of a
    commit.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.COMMIT``.

.. data:: oracledb.PIPELINE_OP_TYPE_EXECUTE

    This constant identifies the type of operation as the executing of a
    statement.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.EXECUTE``.

.. data:: oracledb.PIPELINE_OP_TYPE_EXECUTE_MANY

    This constant identifies the type of operations as the executing of a
    statement multiple times.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.EXECUTE_MANY``.

.. data:: oracledb.PIPELINE_OP_TYPE_FETCH_ALL

    This constant identifies the type of operation as the executing of a
    query and returning all of the rows from the result set.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.FETCH_ALL``.

.. data:: oracledb.PIPELINE_OP_TYPE_FETCH_MANY

    This constant identifies the type of operation as the executing of a
    query and returning up to the specified number of rows from the result
    set.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.FETCH_MANY``.

.. data:: oracledb.PIPELINE_OP_TYPE_FETCH_ONE

    This constant identifies the type of operation as the executing of a query
    and returning the first row of the result set.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.FETCH_ONE``.

Database Shutdown Modes
-----------------------

The Database Shutdown mode constants are possible values for the ``mode``
parameter of the :meth:`Connection.shutdown()` method.

.. dbapiconstantextension::

.. data:: DBSHUTDOWN_ABORT

    This constant is used to specify that the caller should not wait for
    current processing to complete or for users to disconnect from the
    database. This should only be used in unusual circumstances since database
    recovery may be necessary upon next startup.


.. data:: DBSHUTDOWN_FINAL

    This constant is used to specify that the instance can be truly halted.
    This should only be done after the database has been shutdown with one of
    the other modes (except abort) and the database has been closed and
    dismounted using the appropriate SQL commands.


.. data:: DBSHUTDOWN_IMMEDIATE

    This constant is used to specify that all uncommitted transactions should
    be rolled back and any connected users should be disconnected.


.. data:: DBSHUTDOWN_TRANSACTIONAL

    This constant is used to specify that further connections to the database
    should be prohibited and no new transactions should be allowed. It then
    waits for all active transactions to complete.


.. data:: DBSHUTDOWN_TRANSACTIONAL_LOCAL

    This constant is used to specify that further connections to the database
    should be prohibited and no new transactions should be allowed. It then
    waits for only local active transactions to complete.

.. _eventtypes:

Event Types
-----------

The Event type constants are possible values for the :attr:`Message.type`
attribute of the messages that are sent for subscriptions created by the
:meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: EVENT_AQ

    This constant is used to specify that one or more messages are available
    for dequeuing on the queue specified when the subscription was created.


.. data:: EVENT_DEREG

    This constant is used to specify that the subscription has been
    deregistered and no further notifications will be sent.


.. data:: EVENT_NONE

    This constant is used to specify no information is available about the
    event.


.. data:: EVENT_OBJCHANGE

    This constant is used to specify that a database change has taken place on
    a table registered with the :meth:`Subscription.registerquery()` method.


.. data:: EVENT_QUERYCHANGE

    This constant is used to specify that the result set of a query registered
    with the :meth:`Subscription.registerquery()` method has been changed.


.. data:: EVENT_SHUTDOWN

    This constant is used to specify that the instance is in the process of
    being shut down.


.. data:: EVENT_SHUTDOWN_ANY

    This constant is used to specify that any instance (when running RAC) is in
    the process of being shut down.


.. data:: EVENT_STARTUP

    This constant is used to specify that the instance is in the process of
    being started up.


.. _cqn-operation-codes:

Operation Codes
---------------

The Operation code constants are possible values for the ``operations``
parameter for the :meth:`Connection.subscribe()` method. One or more of these
values can be OR'ed together. These values are also used by the
:attr:`MessageTable.operation` or :attr:`MessageQuery.operation` attributes of
the messages that are sent.

.. dbapiconstantextension::

.. data:: OPCODE_ALLOPS

    This constant is used to specify that messages should be sent for all
    operations.


.. data:: OPCODE_ALLROWS

    This constant is used to specify that the table or query has been
    completely invalidated.


.. data:: OPCODE_ALTER

    This constant is used to specify that messages should be sent when a
    registered table has been altered in some fashion by DDL, or that the
    message identifies a table that has been altered.


.. data:: OPCODE_DELETE

    This constant is used to specify that messages should be sent when data is
    deleted, or that the message identifies a row that has been deleted.


.. data:: OPCODE_DROP

    This constant is used to specify that messages should be sent when a
    registered table has been dropped, or that the message identifies a table
    that has been dropped.


.. data:: OPCODE_INSERT

    This constant is used to specify that messages should be sent when data is
    inserted, or that the message identifies a row that has been inserted.


.. data:: OPCODE_UPDATE

    This constant is used to specify that messages should be sent when data is
    updated, or that the message identifies a row that has been updated.

.. _connpoolmodes:

Connection Pool Get Modes
-------------------------

The Connection Pool Get mode constants belong to the enumeration called
``PoolGetMode``. They are possible values for the ``getmode`` parameters of
:meth:`oracledb.create_pool()`, :meth:`oracledb.create_pool_async()`,
:meth:`PoolParams.set()`, and for related attributes. These constants have
deprecated the Session Pool mode constants that were used in the obsolete
cx_Oracle driver.

.. dbapiconstantextension::

.. versionchanged:: 2.3.0

    The integer constants for the connection pool creation, reconfiguration,
    and acquisition ``getmode`` parameters were replaced with the enumeration
    ``PoolGetMode``.

.. data:: POOL_GETMODE_FORCEGET

    This constant is used to specify that a new connection should be created
    and returned by :meth:`ConnectionPool.acquire()` if there are no free
    connections available in the pool and the pool is already at its maximum
    size.

    When a connection acquired in this mode is eventually released back to the
    pool, it will be dropped and not added to the pool if the pool is still at
    its maximum size.

    This enumerated value can also be identified by
    ``oracledb.PoolGetMode.FORCEGET``.

    This constant deprecates the ``SPOOL_ATTRVAL_FORCEGET`` constant that was
    used in the obsolete cx_Oracle driver.


.. data:: POOL_GETMODE_NOWAIT

    This constant is used to specify that an exception should be raised by
    :meth:`ConnectionPool.acquire()` when all currently created connections are
    already in use and so :meth:`~ConnectionPool.acquire()` cannot immediately
    return a connection. Note the exception may occur even if the pool is
    smaller than its maximum size.

    This enumerated value can also be identified by
    ``oracledb.PoolGetMode.NOWAIT``.

    This constant deprecates the ``SPOOL_ATTRVAL_NOWAIT`` constant that was
    used in the obsolete cx_Oracle driver, and was the default ``getmode``
    value.


.. data:: POOL_GETMODE_WAIT

    This constant is used to specify that :meth:`ConnectionPool.acquire()`
    should wait until a connection is available if there are currently no free
    connections available in the pool.  This is the default value.

    This enumerated value can also be identified by
    ``oracledb.PoolGetMode.WAIT``.

    This constant deprecates the ``SPOOL_ATTRVAL_WAIT`` constant that was used
    in the obsolete cx_Oracle driver.


.. data:: POOL_GETMODE_TIMEDWAIT

    This constant is used to specify that :meth:`ConnectionPool.acquire()`
    should wait for a period of time (defined by the ``wait_timeout``
    parameter) for a connection to become available before returning with an
    error.

    This enumerated value can also be identified by
    ``oracledb.PoolGetMode.TIMEDWAIT``.

    This constant deprecates the ``SPOOL_ATTRVAL_TIMEDWAIT`` constant that was
    used in the obsolete cx_Oracle driver.

.. _drcppurityconsts:

Connection Pool Purity Constants
--------------------------------

The Connection Pool Purity constants belong to the enumeration called
``Purity``. They are possible values for the :ref:`drcp` ``purity`` parameter
of :meth:`oracledb.create_pool()`, :meth:`ConnectionPool.acquire()`,
:meth:`oracledb.connect()`, :meth:`oracledb.create_pool_async()`, and
:meth:`oracledb.connect_async()`. These constants have deprecated the Session
Pool purity constants that were used in the obsolete cx_Oracle driver.

.. dbapiconstantextension::

.. versionchanged:: 2.3.0

    The integer constants for the connection pool get modes were replaced
    with the enumeration ``Purity``.

.. data:: PURITY_DEFAULT

    This constant is used to specify that the purity of the session is the
    default value identified by Oracle (see Oracle's documentation for more
    information). This is the default value.

    This enumerated value can also be identified by
    ``oracledb.Purity.DEFAULT``.

    This constant deprecates the ``ATTR_PURITY_DEFAULT`` constant that was used
    in the obsolete cx_Oracle driver, and was the default ``purity`` value.

.. data:: PURITY_NEW

    This constant is used to specify that the session acquired from the pool
    should be new and not have any prior session state.

    This enumerated value can also be identified by ``oracledb.Purity.NEW``.

    This constant deprecates the ``ATTR_PURITY_NEW`` constant that was used in
    the obsolete cx_Oracle driver.


.. data:: PURITY_SELF

    This constant is used to specify that the session acquired from the pool
    need not be new and may have prior session state.

    This enumerated value can also be identified by ``oracledb.Purity.SELF``.

    This constant deprecates the ``ATTR_PURITY_SELF`` constant that was used in
    the obsolete cx_Oracle driver.

Subscription Grouping Classes
-----------------------------

The Subscription Grouping Class constants are possible values for the
``groupingClass`` parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: SUBSCR_GROUPING_CLASS_TIME

    This constant is used to specify that events are to be grouped by the
    period of time in which they are received.


Subscription Grouping Types
---------------------------

The Subscription Grouping Type constants are possible values for the
``groupingType`` parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: SUBSCR_GROUPING_TYPE_SUMMARY

    This constant is used to specify that when events are grouped a summary of
    the events should be sent instead of the individual events. This is the
    default value.

.. data:: SUBSCR_GROUPING_TYPE_LAST

    This constant is used to specify that when events are grouped the last
    event that makes up the group should be sent instead of the individual
    events.


.. _subscr-namespaces:

Subscription Namespaces
-----------------------

The Subscription Namespace constants are possible values for the ``namespace``
parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: SUBSCR_NAMESPACE_AQ

    This constant is used to specify that notifications should be sent when a
    queue has messages available to dequeue.

.. data:: SUBSCR_NAMESPACE_DBCHANGE

    This constant is used to specify that database change notification or query
    change notification messages are to be sent. This is the default value.


.. _subscr-protocols:

Subscription Protocols
----------------------

The Subscription Protocol constants are possible values for the ``protocol``
parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: SUBSCR_PROTO_CALLBACK

    This constant is used to specify that notifications will be sent to the
    callback routine identified when the subscription was created. It is the
    default value and the only value currently supported.


.. data:: SUBSCR_PROTO_HTTP

    This constant is used to specify that notifications will be sent to an
    HTTP URL when a message is generated. This value is currently not
    supported.


.. data:: SUBSCR_PROTO_MAIL

    This constant is used to specify that notifications will be sent to an
    e-mail address when a message is generated. This value is currently not
    supported.


.. data:: SUBSCR_PROTO_OCI

    This constant is used to specify that notifications will be sent to the
    callback routine identified when the subscription was created. It is the
    default value and the only value currently supported.

    .. deprecated:: python-oracledb 1.0

     Use :data:`~oracledb.SUBSCR_PROTO_CALLBACK` instead.


.. data:: SUBSCR_PROTO_SERVER

    This constant is used to specify that notifications will be sent to a
    PL/SQL procedure when a message is generated. This value is currently not
    supported.


.. _subscr-qos:

Subscription Quality of Service
-------------------------------

The Subscription Quality of Service constants are possible values for the
``qos`` parameter of the :meth:`Connection.subscribe()` method. One or more of
these values can be OR'ed together.

.. dbapiconstantextension::

.. data:: SUBSCR_QOS_BEST_EFFORT

    This constant is used to specify that best effort filtering for query
    result set changes is acceptable. False positive notifications may be
    received.  This behaviour may be suitable for caching applications.


.. data:: SUBSCR_QOS_DEREG_NFY

    This constant is used to specify that the subscription should be
    automatically unregistered after the first notification is received.


.. data:: SUBSCR_QOS_QUERY

    This constant is used to specify that notifications should be sent if the
    result set of the registered query changes. By default, no false positive
    notifications will be generated.


.. data:: SUBSCR_QOS_RELIABLE

    This constant is used to specify that notifications should not be lost in
    the event of database failure.


.. data:: SUBSCR_QOS_ROWIDS

    This constant is used to specify that the rowids of the inserted, updated
    or deleted rows should be included in the message objects that are sent.


.. _types:

DB API Types
------------

.. data:: BINARY

    This type object is used to describe columns in a database that contain
    binary data. The database types :data:`DB_TYPE_RAW` and
    :data:`DB_TYPE_LONG_RAW` will compare equal to this value. If a variable is
    created with this type, the database type :data:`DB_TYPE_RAW` will be used.


.. data:: DATETIME

    This type object is used to describe columns in a database that are dates.
    The database types :data:`DB_TYPE_DATE`, :data:`DB_TYPE_TIMESTAMP`,
    :data:`DB_TYPE_TIMESTAMP_LTZ` and :data:`DB_TYPE_TIMESTAMP_TZ` will all
    compare equal to this value. If a variable is created with this
    type, the database type :data:`DB_TYPE_DATE` will be used.


.. data:: NUMBER

    This type object is used to describe columns in a database that are
    numbers. The database types :data:`DB_TYPE_BINARY_DOUBLE`,
    :data:`DB_TYPE_BINARY_FLOAT`, :data:`DB_TYPE_BINARY_INTEGER` and
    :data:`DB_TYPE_NUMBER` will all compare equal to this value. If a variable
    is created with this type, the database type :data:`DB_TYPE_NUMBER` will be
    used.


.. data:: ROWID

    This type object is used to describe the pseudo column "rowid". The
    database types :data:`DB_TYPE_ROWID` and :data:`DB_TYPE_UROWID` will
    compare equal to this value. If a variable is created with this type, the
    database type :data:`DB_TYPE_VARCHAR` will be used.


.. data:: STRING

    This type object is used to describe columns in a database that are
    strings. The database types :data:`DB_TYPE_CHAR`, :data:`DB_TYPE_LONG`,
    :data:`DB_TYPE_NCHAR`, :data:`DB_TYPE_NVARCHAR` and :data:`DB_TYPE_VARCHAR`
    will all compare equal to this value. If a variable is created with this
    type, the database type :data:`DB_TYPE_VARCHAR` will be used.


.. _dbtypes:

Database Types
--------------

All of these types are extensions to the DB API definition. They are found in
query and object metadata. They can also be used to specify the database type
when binding data.

Also see the table :ref:`supporteddbtypes`.

.. data:: DB_TYPE_BFILE

    Describes columns, attributes or array elements in a database that are of
    type BFILE. It will compare equal to the DB API type :data:`BINARY`.


.. data:: DB_TYPE_BINARY_DOUBLE

    Describes columns, attributes or array elements in a database that are of
    type BINARY_DOUBLE. It will compare equal to the DB API type
    :data:`NUMBER`.


.. data:: DB_TYPE_BINARY_FLOAT

    Describes columns, attributes or array elements in a database that are
    of type BINARY_FLOAT. It will compare equal to the DB API type
    :data:`NUMBER`.


.. data:: DB_TYPE_BINARY_INTEGER

    Describes attributes or array elements in a database that are of type
    BINARY_INTEGER. It will compare equal to the DB API type :data:`NUMBER`.


.. data:: DB_TYPE_BLOB

    Describes columns, attributes or array elements in a database that are of
    type BLOB. It will compare equal to the DB API type :data:`BINARY`.


.. data:: DB_TYPE_BOOLEAN

    Describes attributes or array elements in a database that are of type
    BOOLEAN. It is only available in Oracle 12.1 and higher and only within
    PL/SQL.


.. data:: DB_TYPE_CHAR

    Describes columns, attributes or array elements in a database that are of
    type CHAR. It will compare equal to the DB API type :data:`STRING`.

    Note that these are fixed length string values and behave differently from
    VARCHAR2.


.. data:: DB_TYPE_CLOB

    Describes columns, attributes or array elements in a database that are of
    type CLOB. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_CURSOR

    Describes columns in a database that are of type CURSOR. In PL/SQL, these
    are known as REF CURSOR.


.. data:: DB_TYPE_DATE

    Describes columns, attributes or array elements in a database that are of
    type DATE. It will compare equal to the DB API type :data:`DATETIME`.


.. data:: DB_TYPE_INTERVAL_DS

    Describes columns, attributes or array elements in a database that are of
    type INTERVAL DAY TO SECOND.


.. data:: DB_TYPE_INTERVAL_YM

    Describes columns, attributes or array elements in a database that are of
    type INTERVAL YEAR TO MONTH.


.. data:: DB_TYPE_JSON

    Describes columns in a database that are of type JSON (with Oracle Database
    21 or later).

.. data:: DB_TYPE_LONG

    Describes columns, attributes or array elements in a database that are of
    type LONG. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_LONG_RAW

    Describes columns, attributes or array elements in a database that are of
    type LONG RAW. It will compare equal to the DB API type :data:`BINARY`.


.. data:: DB_TYPE_LONG_NVARCHAR

    This constant can be used in output type handlers when fetching NCLOB
    columns as a string. (Note a type handler is not needed if
    :ref:`oracledb.defaults.fetch_lobs <defaults>` is set to False).  For IN
    binds, this constant can be used to create a bind variable in
    :meth:`Cursor.var()` or via :meth:`Cursor.setinputsizes()`.  The
    ``DB_TYPE_LONG_NVARCHAR`` value won't be shown in query metadata since it
    is not a database type.

    It will compare equal to the DB API type :data:`STRING`.

.. data:: DB_TYPE_NCHAR

    Describes columns, attributes or array elements in a database that are of
    type NCHAR. It will compare equal to the DB API type :data:`STRING`.

    Note that these are fixed length string values and behave differently from
    NVARCHAR2.


.. data:: DB_TYPE_NCLOB

    Describes columns, attributes or array elements in a database that are of
    type NCLOB. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_NUMBER

    Describes columns, attributes or array elements in a database that are of
    type NUMBER. It will compare equal to the DB API type :data:`NUMBER`.


.. data:: DB_TYPE_NVARCHAR

    Describes columns, attributes or array elements in a database that are of
    type NVARCHAR2. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_OBJECT

    Describes columns, attributes or array elements in a database that are an
    instance of a named SQL or PL/SQL type.


.. data:: DB_TYPE_RAW

    Describes columns, attributes or array elements in a database that are of
    type RAW. It will compare equal to the DB API type :data:`BINARY`.


.. data:: DB_TYPE_ROWID

    Describes columns, attributes or array elements in a database that are of
    type ROWID or UROWID. It will compare equal to the DB API type
    :data:`ROWID`.


.. data:: DB_TYPE_TIMESTAMP

    Describes columns, attributes or array elements in a database that are of
    type TIMESTAMP. It will compare equal to the DB API type :data:`DATETIME`.


.. data:: DB_TYPE_TIMESTAMP_LTZ

    Describes columns, attributes or array elements in a database that are of
    type TIMESTAMP WITH LOCAL TIME ZONE. It will compare equal to the DB API
    type :data:`DATETIME`.


.. data:: DB_TYPE_TIMESTAMP_TZ

    Describes columns, attributes or array elements in a database that are of
    type TIMESTAMP WITH TIME ZONE. It will compare equal to the DB API type
    :data:`DATETIME`.


.. data:: DB_TYPE_UNKNOWN

    Describes columns, attributes or array elements in a database that are
    of an unknown type.


.. data:: DB_TYPE_UROWID

    Describes columns, attributes or array elements in a database that are of
    type UROWID. It will compare equal to the DB API type :data:`ROWID`.

    .. note::

        This type is not supported in python-oracledb Thick mode.
        See :ref:`querymetadatadiff`.


.. data:: DB_TYPE_VARCHAR

    Describes columns, attributes or array elements in a database that are of
    type VARCHAR2. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_VECTOR

    Describes columns, attributes or array elements in a database that are of
    type VECTOR.

    .. versionadded:: 2.2.0


.. data:: DB_TYPE_XMLTYPE

    Describes columns, attributes or array elements in a database that are of
    type SYS.XMLTYPE.

    .. versionadded:: 2.0.0


.. _dbtypesynonyms:

Database Type Synonyms
----------------------

All of the following constants are deprecated and will be removed in a future
version of python-oracledb.

.. data:: BFILE

    A synonym for :data:`DB_TYPE_BFILE`.

    .. deprecated:: cx_Oracle 8.0


.. data:: BLOB

    A synonym for :data:`DB_TYPE_BLOB`.

    .. deprecated:: cx_Oracle 8.0


.. data:: BOOLEAN

    A synonym for :data:`DB_TYPE_BOOLEAN`.

    .. deprecated:: cx_Oracle 8.0


.. data:: CLOB

    A synonym for :data:`DB_TYPE_CLOB`.

    .. deprecated:: cx_Oracle 8.0

.. data:: CURSOR

    A synonym for :data:`DB_TYPE_CURSOR`.

    .. deprecated:: cx_Oracle 8.0


.. data:: FIXED_CHAR

    A synonym for :data:`DB_TYPE_CHAR`.

    .. deprecated:: cx_Oracle 8.0


.. data:: FIXED_NCHAR

    A synonym for :data:`DB_TYPE_NCHAR`.

    .. deprecated:: cx_Oracle 8.0


.. data:: INTERVAL

    A synonym for :data:`DB_TYPE_INTERVAL_DS`.

    .. deprecated:: cx_Oracle 8.0


.. data:: LONG_BINARY

    A synonym for :data:`DB_TYPE_LONG_RAW`.

    .. deprecated:: cx_Oracle 8.0


.. data:: LONG_STRING

    A synonym for :data:`DB_TYPE_LONG`.

    .. deprecated:: cx_Oracle 8.0


.. data:: NATIVE_FLOAT

    A synonym for :data:`DB_TYPE_BINARY_DOUBLE`.

    .. deprecated:: cx_Oracle 8.0


.. data:: NATIVE_INT

    A synonym for :data:`DB_TYPE_BINARY_INTEGER`.

    .. deprecated:: cx_Oracle 8.0


.. data:: NCHAR

    A synonym for :data:`DB_TYPE_NCHAR`.

    .. deprecated:: cx_Oracle 8.0


.. data:: NCLOB

    A synonym for :data:`DB_TYPE_NCLOB`.

    .. deprecated:: cx_Oracle 8.0


.. data:: OBJECT

    A synonym for :data:`DB_TYPE_OBJECT`.

    .. deprecated:: cx_Oracle 8.0


.. data:: TIMESTAMP

    A synonym for :data:`DB_TYPE_TIMESTAMP`.

    .. deprecated:: cx_Oracle 8.0


Other Types
-----------

All of these types are extensions to the DB API definition.

.. autoclass:: ApiType

    This type object is the Python type of the database API type constants
    :data:`BINARY`, :data:`DATETIME`, :data:`NUMBER`, :data:`ROWID` and
    :data:`STRING`.


.. autoclass:: DbType

    This type object is the Python type of the
    :ref:`database type constants <dbtypes>`.

.. _tpcconstants:

Two-Phase Commit (TPC) Constants
---------------------------------

The constants for the two-phase commit (TPC) functions
:meth:`~Connection.tpc_begin()` and :meth:`~Connection.tpc_end()` are listed
below.

.. data:: TPC_BEGIN_JOIN

    Joins an existing TPC transaction.

.. data:: TPC_BEGIN_NEW

    Creates a new TPC transaction.

.. data:: TPC_BEGIN_PROMOTE

    Promotes a local transaction to a TPC transaction.

.. data:: TPC_BEGIN_RESUME

    Resumes an existing TPC transaction.

.. data:: TPC_END_NORMAL

    Ends the TPC transaction participation normally.

.. data:: TPC_END_SUSPEND

    Suspends the TPC transaction.

.. _vectorformatconstants:

Vector Format Constants
-----------------------

These constants belong to the enumeration called ``VectorFormat`` and are
possible values for the :attr:`FetchInfo.vector_format` attribute.

.. versionadded:: 2.2.0

.. versionchanged:: 2.3.0

    The integer constants for the vector format constants were replaced with
    the enumeration ``VectorFormat``.

.. data:: VECTOR_FORMAT_BINARY

    This constant is used to represent the storage format of VECTOR columns
    using 8-bit unsigned integers.

    This enumerated value can also be identified by
    ``oracledb.VectorFormat.BINARY``.

    .. versionadded:: 2.3.0

.. data:: VECTOR_FORMAT_FLOAT32

    This constant is used to represent the storage format of VECTOR columns
    using 32-bit floating point numbers.

    This enumerated value can also be identified by
    ``oracledb.VectorFormat.FLOAT32``.

.. data:: VECTOR_FORMAT_FLOAT64

    This constant is used to represent the storage format of VECTOR columns
    using 64-bit floating point numbers.

    This enumerated value can also be identified by
    ``oracledb.VectorFormat.FLOAT64``.

.. data:: VECTOR_FORMAT_INT8

    This constant is used to represent the storage format of VECTOR columns
    using 8-bit signed integers.

    This enumerated value can also be identified by
    ``oracledb.VectorFormat.INT8``.

.. _exceptions:

Oracledb Exceptions
===================

See :ref:`exception` for usage information.

.. exception:: Warning

    Exception raised for important warnings and defined by the DB API but not
    actually used by python-oracledb.

.. exception:: Error

    Exception that is the base class of all other exceptions defined by
    python-oracledb and is a subclass of the Python StandardError exception
    (defined in the module exceptions).

.. exception:: InterfaceError

    Exception raised for errors that are related to the database interface
    rather than the database itself. It is a subclass of Error.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 1000 - 1999.

.. exception:: DatabaseError

    Exception raised for errors that are related to the database. It is a
    subclass of Error.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 4000 - 4999.

.. exception:: DataError

    Exception raised for errors that are due to problems with the processed
    data. It is a subclass of DatabaseError.

    Exception messages of this class are generated by the database and will
    have a prefix such as ORA

.. exception:: OperationalError

    Exception raised for errors that are related to the operation of the
    database but are not necessarily under the control of the programmer. It is
    a subclass of DatabaseError.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 6000 - 6999.

.. exception:: IntegrityError

    Exception raised when the relational integrity of the database is affected.
    It is a subclass of DatabaseError.

    Exception messages of this class are generated by the database and will
    have a prefix such as ORA

.. exception:: InternalError

    Exception raised when the database encounters an internal error. It is a
    subclass of DatabaseError.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 5000 - 5999.

.. exception:: ProgrammingError

    Exception raised for programming errors. It is a subclass of DatabaseError.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 2000 - 2999.

.. exception:: NotSupportedError

    Exception raised when a method or database API was used which is not
    supported by the database. It is a subclass of DatabaseError.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 3000 - 3999.

.. _exchandling:

Oracledb _Error Objects
=======================

See :ref:`exception` for usage information.

.. note::

    PEP 249 (Python Database API Specification v2.0) says the following about
    exception values:

        [...] The values of these exceptions are not defined. They should
        give the user a fairly good idea of what went wrong, though. [...]

    With python-oracledb every exception object has exactly one argument in the
    ``args`` tuple. This argument is an ``oracledb._Error`` object which has
    the following six read-only attributes.

.. attribute:: _Error.code

    Integer attribute representing the Oracle error number (ORA-XXXXX).

.. attribute:: _Error.offset

    Integer attribute representing the error offset when applicable.

.. attribute:: _Error.full_code

    String attribute representing the top-level error prefix and the
    code that is shown in the :attr:`_Error.message`.

.. attribute:: _Error.message

    String attribute representing the Oracle message of the error. This message
    may be localized by the environment of the Oracle connection.

.. attribute:: _Error.context

    String attribute representing the context in which the exception was
    raised.

.. attribute:: _Error.isrecoverable

    Boolean attribute representing whether the error is recoverable or not.
    This requires Oracle Database 12.1 (or later). If python-oracledb Thick
    mode is used, then Oracle Client 12.1 (or later) is also required.

    See :ref:`tg` for more information.

.. _oracledbplugins:

Oracledb Plugins
================

The `namespace package <https://packaging.python.org/en/latest/guides/
packaging-namespace-packages/#native-namespace-packages>`__
``oracledb.plugins`` can contain plugins to extend the capability of
python-oracledb.  See :ref:`customplugins`. Note that the namespace
``oracledb.plugins.ldap_support`` is reserved for future use by the
python-oracledb project.

To use the python-oracledb plugins in your application, import using
``import oracledb.plugins.<name of plugin>``, for example::

    import oracledb.plugins.oci_config_provider

.. versionadded:: 3.0.0

.. _configociplugin:

Oracle Cloud Infrastructure (OCI) Object Storage Configuration Provider Plugin
------------------------------------------------------------------------------

``oci_config_provider`` is a plugin that can be imported to provide access to
database connection credentials and application configuration information
stored in the :ref:`OCI Object Storage configuration provider
<ociobjstorageprovider>`.

This plugin is implemented as a :ref:`connection protocol hook function
<registerprotocolhook>` to handle connection strings which have the prefix
``config-ociobject``, see :ref:`OCI Object Storage connection strings
<connstringoci>`. The plugin parses these connection strings and gets the
stored configuration information. Python-oracledb then uses this information to
connect to Oracle Database.

To use this plugin in python-oracledb Thick mode, you must set
:attr:`oracledb.defaults.thick_mode_dsn_passthrough
<Defaults.thick_mode_dsn_passthrough>` to *False*. Alternatively use
:meth:`ConnectParams.parse_connect_string()`, see :ref:`usingconnparams`.

See :ref:`ociobjstorageprovider` for more information.

.. versionadded:: 3.0.0

.. _configazureplugin:

Azure App Configuration Provider Plugin
---------------------------------------

``azure_config_provider`` is a plugin that can be imported to provide access to
database connection credentials and application configuration information
stored in the :ref:`Azure App Configuration provider
<azureappstorageprovider>`.

This plugin is implemented as a :ref:`connection protocol hook function
<registerprotocolhook>` to handle connection strings which have the prefix
``config-azure``, see :ref:`Azure App Configuration connection strings
<connstringazure>`. The plugin parses these connection strings and gets the
stored configuration information. Python-oracledb then uses this information to
connect to Oracle Database.

To use this plugin in python-oracledb Thick mode, you must set
:attr:`oracledb.defaults.thick_mode_dsn_passthrough
<Defaults.thick_mode_dsn_passthrough>` to *False*. Alternatively use
:meth:`ConnectParams.parse_connect_string()`, see :ref:`usingconnparams`.

See :ref:`azureappstorageprovider` for more information.

.. versionadded:: 3.0.0

.. _ocicloudnativeauthplugin:

Oracle Cloud Infrastructure (OCI) Cloud Native Authentication Plugin
--------------------------------------------------------------------

``oci_tokens`` is a plugin that can be imported to use the `Oracle Cloud
Infrastructure (OCI) Software Development Kit (SDK)
<https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm>`__ for
generating access tokens when authenticating with OCI Identity and Access
Management (IAM) token-based authentication.

This plugin is implemented as a :ref:`parameter hook function
<registerparamshook>` which uses the ``extra_auth_params`` parameter values of
your connection and pool creation calls to generate OCI IAM access tokens.
Python-oracledb then uses these tokens to connect to Oracle Database.

See :ref:`cloudnativeauthoci` for more information.

.. versionadded:: 3.0.0

.. _azurecloudnativeauthplugin:

Azure Cloud Native Authentication Plugin
----------------------------------------

``azure_tokens`` is a plugin that can be imported to use the `Microsoft
Authentication Library (MSAL)
<https://learn.microsoft.com/en-us/entra/msal/python/?view=msal-py- latest>`__
for generating access tokens when authenticating with OAuth 2.0 token-based
authentication.

This plugin is implemented as a :ref:`parameter hook function
<registerparamshook>` which uses the ``extra_auth_params`` parameter values of
your connection and pool creation calls to generate OAuth2 access tokens.
Python-oracledb then uses these tokens to connect to Oracle Database.

See :ref:`cloudnativeauthoauth` for more information.

.. versionadded:: 3.0.0
