.. _deprecations:

************
Deprecations
************

The following tables contain all of the deprecations in the python-oracledb API,
when they were first deprecated and a comment on what should be used instead,
if applicable. The most recent deprecations are listed first.


.. list-table-with-summary:: Deprecated in python-oracledb 1.0
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated API name. The second column, Comments, includes information about when the API was deprecated and what API to use, if applicable.
    :name: _deprecations_1

    * - Name
      - Comments
    * - `SessionPool class <https://cx-oracle.readthedocs.io/en/latest/api_manual/session_pool.html#sessionpool-object>`_ and use of `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_.
      - Replace by the equivalent :ref:`ConnectionPool Class <connpool>`. Use the new method :meth:`oracledb.create_pool()` to create connection pools.
    * - :meth:`Connection.begin()`
      - Replace by the new :ref:`tcp` functionality.
    * - :meth:`Connection.prepare()`
      - Replace by the new :ref:`tcp` functionality.
    * - Parameters ``encoding`` and ``nencoding`` of the :func:`oracledb.connect()`, :func:`oracledb.create_pool()` and ``oracledb.SessionPool()`` methods
      - The encodings in use are always UTF-8.
    * - Parameter ``threaded`` of the :meth:`oracledb.connect()` method
      - This was used to allow the Oracle Client libraries to support threaded applications. This value is ignored in python-oracledb because the threaded OCI is always enabled in the Thick mode, and the option is not relevant to the Thin mode. The equivalent parameter was already deprecated for `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_ in cx_Oracle 8.2.
    * - Attribute :attr:`Connection.maxBytesPerCharacter` of the Connection object
      - This was previously deprecated.  In python-oracledb 1.0 it will return a constant value of 4 since encodings are always UTF-8.
    * - Size argument, ``numRows`` of the :meth:`Cursor.fetchmany()` method
      - Rename the parameter to ``size``.
    * - `cx_Oracle.makedsn() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.makedsn>`_
      - Pass the connection string components as connection creation, or pool creation, parameters.  Or use a :ref:`ConnectParams Class <connparam>` object.
    * - oracledb.Connection()
      - This method is no longer recommended for creating connections. Use the equivalent function :meth:`oracledb.connect()` instead.
    * - Attribute ``Cursor.bindarraysize`` of the Cursor object
      - Remove this attribute since it is no longer needed.
    * - Constant :data:`~oracledb.ATTR_PURITY_DEFAULT`
      - Replace by :data:`~oracledb.PURITY_DEFAULT`.
    * - Constant :data:`~oracledb.ATTR_PURITY_NEW`
      - Replace by :data:`~oracledb.PURITY_NEW`.
    * - Constant :data:`~oracledb.ATTR_PURITY_SELF`
      - Replace by :data:`~oracledb.PURITY_SELF`.
    * - Constant :data:`~oracledb.SPOOL_ATTRVAL_WAIT`
      - Replace by :data:`~oracledb.POOL_GETMODE_WAIT`.
    * - Constant :data:`~oracledb.SPOOL_ATTRVAL_NOWAIT`
      - Replace by :data:`~oracledb.POOL_GETMODE_NOWAIT`.
    * - Constant :data:`~oracledb.SPOOL_ATTRVAL_FORCEGET`
      - Replace by :data:`~oracledb.POOL_GETMODE_FORCEGET`.
    * - Constant :data:`~oracledb.SPOOL_ATTRVAL_TIMEDWAIT`
      - Replace by :data:`~oracledb.POOL_GETMODE_TIMEDWAIT`.
    * - Constant :data:`~oracledb.DEFAULT_AUTH`
      - Replace by :data:`~oracledb.AUTH_MODE_DEFAULT`.
    * - Constant :data:`~oracledb.SYSASM`
      - Replace by :data:`~oracledb.AUTH_MODE_SYSASM`.
    * - Constant :data:`~oracledb.SYSBKP`
      - Replace by :data:`~oracledb.AUTH_MODE_SYSBKP`.
    * - Constant :data:`~oracledb.SYSDBA`
      - Replace by :data:`~oracledb.AUTH_MODE_SYSDBA`.
    * - Constant :data:`~oracledb.SYSDGD`
      - Replace by :data:`~oracledb.AUTH_MODE_SYSDGD`.
    * - Constant :data:`~oracledb.SYSKMT`
      - Replace by :data:`~oracledb.AUTH_MODE_SYSKMT`.
    * - Constant :data:`~oracledb.SYSOPER`
      - Replace by :data:`~oracledb.AUTH_MODE_SYSOPER`.
    * - Constant :data:`~oracledb.SYSRAC`
      - Replace by :data:`~oracledb.AUTH_MODE_SYSRAC`.
    * - Constant :data:`~oracledb.PRELIM_AUTH`
      - Replace by :data:`~oracledb.AUTH_MODE_PRELIM`.
    * - Constant :data:`~oracledb.SUBSCR_PROTO_OCI`
      - Replace by :data:`~oracledb.SUBSCR_PROTO_CALLBACK`.
    * - Class name `ObjectType <https://cx-oracle.readthedocs.io/en/latest/api_manual/object_type.html#object-type-objects>`_
      - Replace by the equivalent :ref:`DbObjectType<dbobjecttype>`.
    * - Class name `Object <https://cx-oracle.readthedocs.io/en/latest/api_manual/object_type.html#object-objects>`_
      - Replace by the equivalent :ref:`DbObject <dbobject>`.

Many of the usages deprecated in cx_Oracle (see tables below) are still
supported by python-oracledb to ease upgrade from cx_Oracle.  However, these
previous cx_Oracle deprecation announcements remain in force for
python-oracledb.  The relevant functionality may be removed in a future version
of python-oracledb.

Some of the previous deprecations that have been removed and are not available in
python-oracledb are listed below:

- The previously deprecated function `Cursor.fetchraw() <https://cx-oracle.readthedocs.io/en/latest/api_manual/cursor.html#Cursor.fetchraw>`__ has been removed in
  python-oracledb. Use one of the other fetch methods such as :meth:`Cursor.fetchmany()`
  instead.

- The previously deprecated function `Cursor.executemanyprepared() <https://cx-oracle.readthedocs.io/en/latest/api_manual/cursor.html#Cursor.executemanyprepared>`__ has been removed
  in python-oracledb. Use :meth:`Cursor.executemany()` instead.

- The previously deprecated function `Cursor.rowcount() <https://cx-oracle.readthedocs.io/en/latest/api_manual/cursor.html#Cursor.rowcount>`__ has been removed
  in python-oracledb. Use :meth:`Cursor.executemany()` instead.

- The previously deprecated Advanced Queuing (AQ) API has been removed in
  python-oracledb.  Use the new AQ API instead.  AQ is only available in the
  python-oracledb Thick mode.

  - Replace `Connection.deq() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.deq>`__ with :meth:`Queue.deqone()` or :meth:`Queue.deqmany()`.

  - Replace `Connection.deqoptions() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.deqoptions>`__  with :meth:`Queue.deqoptions()`.

  - Replace `Connection.enq() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.enq>`__ with :meth:`Queue.enqone()` or :meth:`Queue.enqmany()`.

  - Replace `Connection.enqoptions() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.enqoptions>`__ with :meth:`Queue.enqoptions()`.

.. list-table-with-summary:: Deprecated in cx_Oracle 8.2
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated API name. The second column,
     Comments, includes information about when the API was deprecated and what API to use,
     if applicable.
    :name: _deprecations_8_2

    * - Name
      - Comments
    * - ``encoding`` parameter to `cx_Oracle.connect() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.connect>`_
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated. Encoding is handled internally between python-oracledb and Oracle
        Database.
    * - ``nencoding`` parameter to `cx_Oracle.connect() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.connect>`_
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated.
    * - ``encoding`` parameter to `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated.
    * - ``nencoding`` parameter to `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated.
    * - Connection.maxBytesPerCharacter
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated. The constant value 4 can be used instead.
    * - Positional parameters to `cx_Oracle.connect() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.connect>`_
      - Replace with keyword parameters in order to comply with the Python
        database API.
    * - Positional parameters to `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_
      - Replace with keyword parameters in order to comply with the Python
        database API.
    * - ``threaded`` parameter to `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_
      - The value of this parameter is ignored. Threading is now always used.
    * - ``waitTimeout`` parameter to `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_
      - Replace with parameter name ``wait_timeout``
    * - ``maxLifetimeSession`` parameter to `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_
      - Replace with parameter name ``max_lifetime_session``
    * - ``sessionCallback`` parameter to `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_
      - Replace with parameter name ``session_callback``
    * - ``maxSessionsPerShard`` parameter to `cx_Oracle.SessionPool() <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_
      - Replace with parameter name ``max_sessions_per_shard``
    * - ``SessionPool.tnsentry``
      - Replace with `SessionPool.dsn <https://cx-oracle.readthedocs.io/en/latest/api_manual/session_pool.html#SessionPool.dsn>`_
    * - ``payloadType`` parameter to `Connection.queue() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.queue>`_
      - Replace with parameter name ``payload_type`` if using keyword parameters.
    * - ``ipAddress`` parameter to `Connection.subscribe() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.subscribe>`_
      - Replace with parameter name ``ip_address``
    * - ``groupingClass`` parameter to `Connection.subscribe() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.subscribe>`_
      - Replace with parameter name ``grouping_class``
    * - ``groupingValue`` parameter to `Connection.subscribe() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.subscribe>`_
      - Replace with parameter name ``grouping_value``
    * - ``groupingType`` parameter to `Connection.subscribe() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.subscribe>`_
      - Replace with parameter name ``grouping_type``
    * - ``clientInitiated`` parameter to `Connection.subscribe() <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.subscribe>`_
      - Replace with parameter name ``client_initiated``
    * - ``Connection.callTimeout``
      - Replace with `Connection.call_timeout <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.call_timeout>`_
    * - ``Connection.tnsentry``
      - Replace with `Connection.dsn <https://cx-oracle.readthedocs.io/en/latest/api_manual/connection.html#Connection.dsn>`_
    * - `keywordParameters` parameter to `Cursor.callfunc() <https://cx-oracle.readthedocs.io/en/latest/api_manual/cursor.html#Cursor.callfunc>`_
      - Replace with parameter name ``keyword_parameters``
    * - ``keywordParameters`` parameter to `Cursor.callproc() <https://cx-oracle.readthedocs.io/en/latest/api_manual/cursor.html#Cursor.callproc>`_
      - Replace with parameter name ``keyword_parameters``
    * - ``encodingErrors`` parameter to `Cursor.var() <https://cx-oracle.readthedocs.io/en/latest/api_manual/cursor.html#Cursor.var>`_
      - Replace with parameter name ``encoding_errors``
    * - ``Cursor.fetchraw()``
      - Replace with `Cursor.fetchmany() <https://cx-oracle.readthedocs.io/en/latest/api_manual/cursor.html#Cursor.fetchmany>`_
    * - ``newSize`` parameter to `LOB.trim() <https://cx-oracle.readthedocs.io/en/latest/api_manual/lob.html#LOB.trim>`_
      - Replace with parameter name ``new_size``
    * - ``Queue.deqMany``
      - Replace with `Queue.deqmany() <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.deqmany>`_
    * - ``Queue.deqOne``
      - Replace with `Queue.deqone() <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.deqone>`_
    * - ``Queue.enqMany``
      - Replace with `Queue.enqmany() <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.enqmany>`_
    * - ``Queue.enqOne``
      - Replace with `Queue.enqone() <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.enqone>`_
    * - ``Queue.deqOptions``
      - Replace with `Queue.deqoptions <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.deqoptions>`_
    * - ``Queue.enqOptions``
      - Replace with `Queue.enqoptions <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.enqoptions>`_
    * - ``Queue.payloadType``
      - Replace with `Queue.payload_type <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.payload_type>`_
    * - ``Subscription.ipAddress``
      - Replace with `Subscription.ip_address <https://cx-oracle.readthedocs.io/en/latest/api_manual/subscription.html#Subscription.ip_address>`_
    * - ``Message.consumerName``
      - Replace with `Message.consumer_name <https://cx-oracle.readthedocs.io/en/latest/api_manual/subscription.html?highlight=Message.consumer_name#Message.consumer_name>`_
    * - ``Message.queueName``
      - Replace with `Message.queue_name <https://cx-oracle.readthedocs.io/en/latest/api_manual/subscription.html?highlight=Message.consumer_name#Message.queue_name>`_
    * - ``Variable.actualElements``
      - Replace with `Variable.actual_elements <https://cx-oracle.readthedocs.io/en/latest/api_manual/variable.html#Variable.actual_elements>`_
    * - ``Variable.bufferSize``
      - Replace with `Variable.buffer_size <https://cx-oracle.readthedocs.io/en/latest/api_manual/variable.html#Variable.buffer_size>`_
    * - ``Variable.numElements``
      - Replace with `Variable.num_elements <https://cx-oracle.readthedocs.io/en/latest/api_manual/variable.html#Variable.num_elements>`_


.. list-table-with-summary:: Deprecated in cx_Oracle 8.0
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated API name. The second column, Comments, includes information about when the API was deprecated and what API to use, if applicable.
    :name: _deprecations_8_0

    * - Name
      - Comments
    * - ``cx_Oracle.BFILE``
      - Replace with `cx_Oracle.DB_TYPE_BFILE <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_BFILE>`_
    * - ``cx_Oracle.BLOB``
      - Replace with `cx_Oracle.DB_TYPE_BLOB <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_BLOB>`_
    * - ``cx_Oracle.BOOLEAN``
      - Replace with `cx_Oracle.DB_TYPE_BOOLEAN <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_BOOLEAN>`_
    * - ``cx_Oracle.CLOB``
      - Replace with `cx_Oracle.DB_TYPE_CLOB <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_CLOB>`_
    * - ``cx_Oracle.CURSOR``
      - Replace with `cx_Oracle.DB_TYPE_CURSOR <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_CURSOR>`_
    * - ``cx_Oracle.FIXED_CHAR``
      - Replace with `cx_Oracle.DB_TYPE_CHAR <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_CHAR>`_
    * - ``cx_Oracle.FIXED_NCHAR``
      - Replace with `cx_Oracle.DB_TYPE_NCHAR <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_NCHAR>`_
    * - ``cx_Oracle.INTERVAL``
      - Replace with `cx_Oracle.DB_TYPE_INTERVAL_DS <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_INTERVAL_DS>`_
    * - ``cx_Oracle.LONG_BINARY``
      - Replace with `cx_Oracle.DB_TYPE_LONG_RAW <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_LONG_RAW>`_
    * - ``cx_Oracle.LONG_STRING``
      - Replace with `cx_Oracle.DB_TYPE_LONG <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_LONG>`_
    * - ``cx_Oracle.NATIVE_FLOAT``
      - Replace with `cx_Oracle.DB_TYPE_BINARY_DOUBLE <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_BINARY_DOUBLE>`_
    * - ``cx_Oracle.NATIVE_INT``
      - Replace with `cx_Oracle.DB_TYPE_BINARY_INTEGER <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_BINARY_INTEGER>`_
    * - ``cx_Oracle.NCHAR``
      - Replace with `cx_Oracle.DB_TYPE_NVARCHAR <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_NVARCHAR>`_
    * - ``cx_Oracle.NCLOB``
      - Replace with `cx_Oracle.DB_TYPE_NCLOB <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_NCLOB>`_
    * - ``cx_Oracle.OBJECT``
      - Replace with `cx_Oracle.DB_TYPE_OBJECT <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_OBJECT>`_
    * - ``cx_Oracle.TIMESTAMP``
      - Replace with `cx_Oracle.DB_TYPE_TIMESTAMP <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.DB_TYPE_TIMESTAMP>`_


.. list-table-with-summary:: Deprecated in cx_Oracle 7.2
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated API name. The second column, Comments, includes information about when the API was deprecated and what API to use, if applicable.
    :name: _deprecations_7_2

    * - Name
      - Comments
    * - ``Connection.deq()``
      - Replace with `Queue.deqone() <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.deqone>`_ or `Queue.deqmany() <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.deqmany>`_.
    * - ``Connection.deqoptions()``
      - Replace with attribute `Queue.deqoptions <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.deqoptions>`_.
    * - ``Connection.enq()``
      - Replace with `Queue.enqone() <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.enqone>`_ or `Queue.enqmany() <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.enqmany>`_.
    * - ``Connection.enqoptions()``
      - Replace with attribute `Queue.enqoptions <https://cx-oracle.readthedocs.io/en/latest/api_manual/aq.html#Queue.enqoptions>`_.


.. list-table-with-summary:: Deprecated in cx_Oracle 6.4
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated API name. The second column, Comments, includes information about when the API was deprecated and what API to use, if applicable.
    :name: _deprecations_6_4

    * - Name
      - Comments
    * - ``Cursor.executemanyprepared()``
      - Replace with `~Cursor.executemany() <https://cx-oracle.readthedocs.io/en/latest/api_manual/cursor.html#Cursor.executemany>`_     with  None for the statement argument and an integer for the parameters argument.
