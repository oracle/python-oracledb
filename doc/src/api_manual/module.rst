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

    See :ref:`vsessconinfo`.

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


.. _moduleattributes:

Oracledb Attributes
===================

.. autodata:: apilevel

.. autodata:: defaults
    :no-value:

    See :ref:`settingdefaults`.

    .. dbapiattributeextension::

.. autodata:: paramstyle

.. autodata:: threadsafety

.. autodata:: __version__

    .. dbapiattributeextension::

.. _constants:

Oracledb Constants
==================

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

.. autodata:: MSG_BUFFERED

.. autodata:: MSG_PERSISTENT

.. autodata:: MSG_PERSISTENT_OR_BUFFERED


Advanced Queuing: Dequeue Modes
-------------------------------

The AQ Dequeue mode constants are possible values for the
:attr:`~DeqOptions.mode` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. autodata:: DEQ_BROWSE

.. autodata:: DEQ_LOCKED

.. autodata:: DEQ_REMOVE

.. autodata:: DEQ_REMOVE_NODATA


Advanced Queuing: Dequeue Navigation Modes
------------------------------------------

The AQ Dequeue Navigation mode constants are possible values for the
:attr:`~DeqOptions.navigation` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. autodata:: DEQ_FIRST_MSG

.. autodata:: DEQ_NEXT_MSG

.. autodata:: DEQ_NEXT_TRANSACTION


Advanced Queuing: Dequeue Visibility Modes
------------------------------------------

The AQ Dequeue Visibility mode constants are possible values for the
:attr:`~DeqOptions.visibility` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. autodata:: DEQ_IMMEDIATE

.. autodata:: DEQ_ON_COMMIT


Advanced Queuing: Dequeue Wait Modes
------------------------------------

The AQ Dequeue Wait mode constants are possible values for the
:attr:`~DeqOptions.wait` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. autodata:: DEQ_NO_WAIT

.. autodata:: DEQ_WAIT_FOREVER

Advanced Queuing: Enqueue Visibility Modes
------------------------------------------

The AQ Enqueue Visibility mode constants are possible values for the
:attr:`~EnqOptions.visibility` attribute of the
:ref:`enqueue options object <enqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.enqone()`, :meth:`Queue.enqmany()`,
:meth:`AsyncQueue.enqone()`, or :meth:`AsyncQueue.enqmany()` methods.

.. dbapiconstantextension::

.. autodata:: ENQ_IMMEDIATE

    .. seealso::

        :ref:`Bulk Enqueuing <bulkenqdeq>`.

.. autodata:: ENQ_ON_COMMIT

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

.. autodata:: MSG_EXPIRED

.. autodata:: MSG_PROCESSED

.. autodata:: MSG_READY

.. autodata:: MSG_WAITING

Advanced Queuing: Other Constants
---------------------------------

This section contains other constants that are used for Advanced Queueing.

.. dbapiconstantextension::

.. autodata:: MSG_NO_DELAY

.. autodata:: MSG_NO_EXPIRATION

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

.. autodata:: AUTH_MODE_DEFAULT

.. autodata:: AUTH_MODE_PRELIM

.. autodata:: AUTH_MODE_SYSASM

.. autodata:: AUTH_MODE_SYSBKP

.. autodata:: AUTH_MODE_SYSDBA

.. autodata:: AUTH_MODE_SYSDGD

.. autodata:: AUTH_MODE_SYSKMT

.. autodata:: AUTH_MODE_SYSOPER

.. autodata:: AUTH_MODE_SYSRAC


.. _pipeline-operation-types:

Pipeline Operation Types
------------------------

The Pipeline Operation type constants belong to the enumeration called
``PipelineOpType``. The pipelining constants listed below are used to identify
the type of operation added. They are possible values for the
:attr:`PipelineOp.op_type` attribute.

.. versionadded:: 2.4.0

.. autodata:: oracledb.PIPELINE_OP_TYPE_CALL_FUNC

.. autodata:: oracledb.PIPELINE_OP_TYPE_CALL_PROC

.. autodata:: oracledb.PIPELINE_OP_TYPE_COMMIT

.. autodata:: oracledb.PIPELINE_OP_TYPE_EXECUTE

.. autodata:: oracledb.PIPELINE_OP_TYPE_EXECUTE_MANY

.. autodata:: oracledb.PIPELINE_OP_TYPE_FETCH_ALL

.. autodata:: oracledb.PIPELINE_OP_TYPE_FETCH_MANY

.. autodata:: oracledb.PIPELINE_OP_TYPE_FETCH_ONE


Database Shutdown Modes
-----------------------

The Database Shutdown mode constants are possible values for the ``mode``
parameter of the :meth:`Connection.shutdown()` method.

.. dbapiconstantextension::

.. autodata:: DBSHUTDOWN_ABORT

.. autodata:: DBSHUTDOWN_FINAL

.. autodata:: DBSHUTDOWN_IMMEDIATE

.. autodata:: DBSHUTDOWN_TRANSACTIONAL

.. autodata:: DBSHUTDOWN_TRANSACTIONAL_LOCAL

.. _eventtypes:

Event Types
-----------

The Event type constants are possible values for the :attr:`Message.type`
attribute of the messages that are sent for subscriptions created by the
:meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. autodata:: EVENT_AQ

.. autodata:: EVENT_DEREG

.. autodata:: EVENT_NONE

.. autodata:: EVENT_OBJCHANGE

.. autodata:: EVENT_QUERYCHANGE

.. autodata:: EVENT_SHUTDOWN

.. autodata:: EVENT_SHUTDOWN_ANY

.. autodata:: EVENT_STARTUP

.. _cqn-operation-codes:

Operation Codes
---------------

The Operation code constants are possible values for the ``operations``
parameter for the :meth:`Connection.subscribe()` method. One or more of these
values can be OR'ed together. These values are also used by the
:attr:`MessageTable.operation` or :attr:`MessageQuery.operation` attributes of
the messages that are sent.

.. dbapiconstantextension::

.. autodata:: OPCODE_ALLOPS

.. autodata:: OPCODE_ALLROWS

.. autodata:: OPCODE_ALTER

.. autodata:: OPCODE_DELETE

.. autodata:: OPCODE_DROP

.. autodata:: OPCODE_INSERT

.. autodata:: OPCODE_UPDATE

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

.. autodata:: POOL_GETMODE_FORCEGET

.. autodata:: POOL_GETMODE_NOWAIT

.. autodata:: POOL_GETMODE_TIMEDWAIT

.. autodata:: POOL_GETMODE_WAIT


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

.. autodata:: PURITY_DEFAULT

.. autodata:: PURITY_NEW

.. autodata:: PURITY_SELF


Subscription Grouping Classes
-----------------------------

The Subscription Grouping Class constants are possible values for the
``groupingClass`` parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. autodata:: SUBSCR_GROUPING_CLASS_NONE

.. autodata:: SUBSCR_GROUPING_CLASS_TIME

Subscription Grouping Types
---------------------------

The Subscription Grouping Type constants are possible values for the
``groupingType`` parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. autodata:: SUBSCR_GROUPING_TYPE_SUMMARY

.. autodata:: SUBSCR_GROUPING_TYPE_LAST

.. _subscr-namespaces:

Subscription Namespaces
-----------------------

The Subscription Namespace constants are possible values for the ``namespace``
parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. autodata:: SUBSCR_NAMESPACE_AQ

.. autodata:: SUBSCR_NAMESPACE_DBCHANGE

.. _subscr-protocols:

Subscription Protocols
----------------------

The Subscription Protocol constants are possible values for the ``protocol``
parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. autodata:: SUBSCR_PROTO_CALLBACK

.. autodata:: SUBSCR_PROTO_HTTP

.. autodata:: SUBSCR_PROTO_MAIL

.. autodata:: SUBSCR_PROTO_SERVER

.. _subscr-qos:

Subscription Quality of Service
-------------------------------

The Subscription Quality of Service constants are possible values for the
``qos`` parameter of the :meth:`Connection.subscribe()` method. One or more of
these values can be OR'ed together.

.. dbapiconstantextension::

.. autodata:: SUBSCR_QOS_BEST_EFFORT

.. autodata:: SUBSCR_QOS_DEFAULT

.. autodata:: SUBSCR_QOS_DEREG_NFY

.. autodata:: SUBSCR_QOS_QUERY

.. autodata:: SUBSCR_QOS_RELIABLE

.. autodata:: SUBSCR_QOS_ROWIDS


.. _types:

DB API Types
------------

.. autoclass:: ApiType

    This type object is the Python type of the database API type constants.

.. autodata:: BINARY
    :no-value:

.. autodata:: DATETIME
    :no-value:

.. autodata:: NUMBER
    :no-value:

.. autodata:: ROWID
    :no-value:

.. autodata:: STRING
    :no-value:


.. _dbtypes:

Database Types
--------------

.. autoclass:: DbType

    This type object is the Python type of the database type constants.  All of
    these types are extensions to the DB API definition. They are found in
    query and object metadata. They can also be used to specify the database
    type when binding data.

    Also see the table :ref:`supporteddbtypes`.

.. autodata:: DB_TYPE_BFILE
    :no-value:

.. autodata:: DB_TYPE_BINARY_DOUBLE
    :no-value:

.. autodata:: DB_TYPE_BINARY_FLOAT
    :no-value:

.. autodata:: DB_TYPE_BINARY_INTEGER
    :no-value:

.. autodata:: DB_TYPE_BLOB
    :no-value:

.. autodata:: DB_TYPE_BOOLEAN
    :no-value:

.. autodata:: DB_TYPE_CHAR
    :no-value:

.. autodata:: DB_TYPE_CLOB
    :no-value:

.. autodata:: DB_TYPE_CURSOR
    :no-value:

.. autodata:: DB_TYPE_DATE
    :no-value:

.. autodata:: DB_TYPE_INTERVAL_DS
    :no-value:

.. autodata:: DB_TYPE_INTERVAL_YM
    :no-value:

.. autodata:: DB_TYPE_JSON
    :no-value:

.. autodata:: DB_TYPE_LONG
    :no-value:

.. autodata:: DB_TYPE_LONG_NVARCHAR
    :no-value:

.. autodata:: DB_TYPE_LONG_RAW
    :no-value:

.. autodata:: DB_TYPE_NCHAR
    :no-value:

.. autodata:: DB_TYPE_NCLOB
    :no-value:

.. autodata:: DB_TYPE_NUMBER
    :no-value:

.. autodata:: DB_TYPE_NVARCHAR
    :no-value:

.. autodata:: DB_TYPE_OBJECT
    :no-value:

.. autodata:: DB_TYPE_RAW
    :no-value:

.. autodata:: DB_TYPE_ROWID
    :no-value:

.. autodata:: DB_TYPE_TIMESTAMP
    :no-value:

.. autodata:: DB_TYPE_TIMESTAMP_LTZ
    :no-value:

.. autodata:: DB_TYPE_TIMESTAMP_TZ
    :no-value:

.. autodata:: DB_TYPE_UNKNOWN
    :no-value:

.. autodata:: DB_TYPE_UROWID
    :no-value:

    .. note::

        This type is not supported in python-oracledb Thick mode.
        See :ref:`querymetadatadiff`.


.. autodata:: DB_TYPE_VARCHAR
    :no-value:

.. autodata:: DB_TYPE_VECTOR
    :no-value:

    .. versionadded:: 2.2.0


.. autodata:: DB_TYPE_XMLTYPE
    :no-value:

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


.. _tpcconstants:

Two-Phase Commit (TPC) Constants
---------------------------------

The constants for the two-phase commit (TPC) functions
:meth:`~Connection.tpc_begin()` and :meth:`~Connection.tpc_end()` are listed
below.

.. autodata:: TPC_BEGIN_JOIN

.. autodata:: TPC_BEGIN_NEW

.. autodata:: TPC_BEGIN_PROMOTE

.. autodata:: TPC_BEGIN_RESUME

.. autodata:: TPC_END_NORMAL

.. autodata:: TPC_END_SUSPEND

.. _vectorformatconstants:

Vector Format Constants
-----------------------

These constants belong to the enumeration called ``VectorFormat`` and are
possible values for the :attr:`FetchInfo.vector_format` attribute.

.. versionadded:: 2.2.0

.. versionchanged:: 2.3.0

    The integer constants for the vector format constants were replaced with
    the enumeration ``VectorFormat``.

.. autodata:: VECTOR_FORMAT_BINARY

    .. versionadded:: 2.3.0

.. autodata:: VECTOR_FORMAT_FLOAT32

.. autodata:: VECTOR_FORMAT_FLOAT64

.. autodata:: VECTOR_FORMAT_INT8


.. _exceptions:

Oracledb Exceptions
===================

See :ref:`exception` for usage information.

.. autoexception:: Warning

.. autoexception:: Error

.. autoexception:: DataError

.. autoexception:: DatabaseError

.. autoexception:: IntegrityError

.. autoexception:: InterfaceError

.. autoexception:: InternalError

.. autoexception:: NotSupportedError

.. autoexception:: OperationalError

.. autoexception:: ProgrammingError


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

.. _futureobj:

Oracledb __future__ Object
==========================

A special object that contains attributes which control the behavior of
python-oracledb, allowing for opting in for new features.

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

.. dbapimethodextension::
