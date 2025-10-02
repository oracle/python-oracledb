.. _deprecations:

***********************************
Deprecated and Desupported Features
***********************************

The following tables contain the deprecated and desupported features of the
python-oracledb API, and the replacement to be used instead, if applicable.
The desupported API feature is a previous deprecation that has been removed
and is no longer available in python-oracledb. The most recent deprecated and
desupported features are listed first.

The previous cx_Oracle deprecation announcements remain in force for
python-oracledb. The relevant functionality may be removed in a future version
of python-oracledb. The cx_Oracle driver itself is obsolete and should not be
used for new development.

.. list-table-with-summary:: Deprecated in python-oracledb 3.4
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated feature. The second column, Comments, includes information about the deprecation and the replacement to use, if applicable.
    :name: _deprecations_3_4

    * - Name
      - Comments
    * - The x86_64 macOS and 32-bit Windows platforms are deprecated. They will be desupported before, or when, the `cryptography <https://pypi.org/project/cryptography/>`__ package desupports them. See the `cryptography deprecation announcement <https://mail.python.org/archives/list/python-announce-list@python.org/thread/R4BZNC36MSFLKULA74KILLFY6GP3VCPA/>`__.
      - Use arm64 macOS or 64-bit Windows instead.
    * - Connectivity and interoperability with Oracle Database and Oracle Client libraries older than version 19 is deprecated and will be removed in a future version of python-oracledb. Production use, and availability of database and client software, is detailed in `Release Schedule of Current Database Releases <https://support.oracle.com/epmos/faces/ DocumentDisplay?id=742060.1>`__.
      - Upgrade the database and client library versions.

.. list-table-with-summary:: Deprecated in python-oracledb 3.0
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated feature. The second column, Comments, includes information about the deprecation and the replacement to use, if applicable.
    :name: _deprecations_3_0

    * - Name
      - Comments
    * - Parameter ``pool`` of :meth:`oracledb.connect()` and :meth:`oracledb.connect_async()`
      - Use :meth:`ConnectionPool.acquire()`, or make use of the :ref:`connection pool cache <connpoolcache>` instead

.. list-table-with-summary:: Desupported in python-oracledb 2.0
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the desupported feature. The second column, Comments, includes information about the desupport and the replacement to use, if applicable.
    :name: _desupported_2_0

    * - Name
      - Comments
    * - ``oracledb.__future__.old_json_col_as_obj``
      - VARCHAR2 and LOB columns created with the ``IS JSON`` check constraint are now always fetched as JSON.  Use an :ref:`output type handler <outputtypehandlers>` if the old behavior is required.
    * - Parameters ``encoding`` and ``nencoding`` of :func:`oracledb.connect()` and :func:`oracledb.create_pool()`, and the related attributes on the objects created
      - The driver encodings are always UTF-8. Remove uses of ``encoding`` and ``nencoding`` from your code.
    * - Parameter ``threaded`` of :func:`oracledb.connect()` and :func:`oracledb.create_pool()`
      - Threading is always used. Remove uses of ``threaded`` from your code.
    * - Parameter ``waitTimeout`` of :func:`oracledb.create_pool()` and ``oracledb.SessionPool()``
      - Replace with parameter ``wait_timeout``
    * - Parameter ``maxLifetimeSession`` of :func:`oracledb.create_pool()` and ``oracledb.SessionPool()``
      - Replace with parameter ``max_lifetime_session``
    * - Parameter ``sessionCallback`` of :func:`oracledb.create_pool()` and ``oracledb.SessionPool()``
      - Replace with parameter ``session_callback``
    * - Parameter ``maxSessionsPerShard`` of :func:`oracledb.create_pool()` and ``oracledb.SessionPool()``
      - Replace with parameter ``max_sessions_per_shard``
    * - Attribute ``maxBytesPerCharacter`` of the :ref:`Connection object <connobj>`
      - The driver encodings are always UTF-8 so this attribute can be replaced by the constant value 4
    * - ``Connection.tnsentry``
      - Replace with :attr:`Connection.dsn`
    * - ``SessionPool.tnsentry``
      - Replace with :attr:`ConnectionPool.dsn`

.. list-table-with-summary:: Deprecated in python-oracledb 2.0
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated feature. The second column, Comments, includes information about the deprecation and the replacement to use, if applicable.
    :name: _deprecations_2_0

    * - Name
      - Comments
    * - Calling :meth:`Variable.setvalue()` with a string value when the variable type is one of :data:`oracledb.DB_TYPE_BLOB`,
        :data:`oracledb.DB_TYPE_CLOB` or :data:`oracledb.DB_TYPE_NCLOB`.
      - Call :meth:`Connection.createlob()` with the value instead and pass the result to :meth:`Variable.setvalue()`.
    * - Setting an attribute of type :data:`oracledb.DB_TYPE_BLOB`, :data:`oracledb.DB_TYPE_CLOB` or :data:`oracledb.DB_TYPE_NCLOB` on a database object to a string value.
      - Call :meth:`Connection.createlob()` with the value instead and set the attribute with the result.

.. list-table-with-summary:: Deprecated in python-oracledb 1.4
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated feature. The second column, Comments, includes information about the deprecation and the replacement to use, if applicable.
    :name: _deprecations_1_4

    * - Name
      - Comments
    * - Output type handler with arguments ``handler(cursor, name, default_type, length, precision, scale)``
      - Replace with ``handler(cursor, metadata)``. See :ref:`outputtypehandlers`.

.. list-table-with-summary:: Deprecated in python-oracledb 1.0
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated feature. The second column, Comments, includes information about the deprecation and the replacement to use, if applicable.
    :name: _deprecations_1

    * - Name
      - Comments
    * - SessionPool class and use of ``cx_Oracle.SessionPool()``
      - Replace by the equivalent :ref:`ConnectionPool Class <connpool>`. Use the new method :meth:`oracledb.create_pool()` to create connection pools.
    * - :meth:`Connection.begin()`
      - Replace by the new :ref:`Two-Phase Commits (TPC) <tpc>` functionality.
    * - :meth:`Connection.prepare()`
      - Replace by the new :ref:`Two-Phase Commits (TPC) <tpc>` functionality.
    * - Parameters ``encoding`` and ``nencoding`` of the :func:`oracledb.connect()`, :func:`oracledb.create_pool()` and ``oracledb.SessionPool()`` methods
      - The encodings in use are always UTF-8.
    * - Parameter ``threaded`` of the :meth:`oracledb.connect()` method
      - This was used to allow the Oracle Client libraries to support threaded applications. This value is ignored in python-oracledb because the threaded OCI is always enabled in the Thick mode, and the option is not relevant to the Thin mode. The equivalent parameter was already deprecated for ``cx_Oracle.SessionPool()`` in cx_Oracle 8.2.
    * - Attribute :attr:`Connection.maxBytesPerCharacter` of the Connection object
      - This was previously deprecated.  In python-oracledb 1.0 it will return a constant value of 4 since encodings are always UTF-8.
    * - Size argument, ``numRows`` of the :meth:`Cursor.fetchmany()` method
      - Rename the parameter to ``size``.
    * - ``cx_Oracle.makedsn()``
      - Pass the connection string components as connection creation, or pool creation, parameters.  Or use a :ref:`ConnectParams Class <connparam>` object.
    * - ``oracledb.Connection()``
      - This method is no longer recommended for creating connections. Use the equivalent function :meth:`oracledb.connect()` instead.
    * - Attribute ``Cursor.bindarraysize`` of the Cursor object
      - Remove this attribute since it is no longer needed.
    * - Constant :data:`~oracledb.ATTR_PURITY_DEFAULT`
      - Replace by :data:`oracledb.PURITY_DEFAULT`.
    * - Constant :data:`~oracledb.ATTR_PURITY_NEW`
      - Replace by :data:`oracledb.PURITY_NEW`.
    * - Constant :data:`~oracledb.ATTR_PURITY_SELF`
      - Replace by :data:`oracledb.PURITY_SELF`.
    * - Constant :data:`~oracledb.SPOOL_ATTRVAL_WAIT`
      - Replace by :data:`oracledb.POOL_GETMODE_WAIT`.
    * - Constant :data:`~oracledb.SPOOL_ATTRVAL_NOWAIT`
      - Replace by :data:`oracledb.POOL_GETMODE_NOWAIT`.
    * - Constant :data:`~oracledb.SPOOL_ATTRVAL_FORCEGET`
      - Replace by :data:`oracledb.POOL_GETMODE_FORCEGET`.
    * - Constant :data:`~oracledb.SPOOL_ATTRVAL_TIMEDWAIT`
      - Replace by :data:`oracledb.POOL_GETMODE_TIMEDWAIT`.
    * - Constant :data:`~oracledb.DEFAULT_AUTH`
      - Replace by :data:`oracledb.AUTH_MODE_DEFAULT`.
    * - Constant :data:`~oracledb.SYSASM`
      - Replace by :data:`oracledb.AUTH_MODE_SYSASM`.
    * - Constant :data:`~oracledb.SYSBKP`
      - Replace by :data:`oracledb.AUTH_MODE_SYSBKP`.
    * - Constant :data:`~oracledb.SYSDBA`
      - Replace by :data:`oracledb.AUTH_MODE_SYSDBA`.
    * - Constant :data:`~oracledb.SYSDGD`
      - Replace by :data:`oracledb.AUTH_MODE_SYSDGD`.
    * - Constant :data:`~oracledb.SYSKMT`
      - Replace by :data:`oracledb.AUTH_MODE_SYSKMT`.
    * - Constant :data:`~oracledb.SYSOPER`
      - Replace by :data:`oracledb.AUTH_MODE_SYSOPER`.
    * - Constant :data:`~oracledb.SYSRAC`
      - Replace by :data:`oracledb.AUTH_MODE_SYSRAC`.
    * - Constant :data:`~oracledb.PRELIM_AUTH`
      - Replace by :data:`oracledb.AUTH_MODE_PRELIM`.
    * - Constant :data:`~oracledb.SUBSCR_PROTO_OCI`
      - Replace by :data:`oracledb.SUBSCR_PROTO_CALLBACK`.
    * - Class name ObjectType
      - Replace by the equivalent :ref:`DbObjectType<dbobjecttype>`.
    * - Class name Object
      - Replace by the equivalent :ref:`DbObject <dbobject>`.

.. list-table-with-summary:: Desupported in python-oracledb 1.0
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the desupported feature. The second column, Comments, includes information about the desupport and the replacement to use, if applicable.
    :name: _desupported_1

    * - Name
      - Comments
    * - ``Cursor.fetchraw()``
      - Use one of the other fetch methods such as :meth:`Cursor.fetchmany()` instead.
    * - ``Cursor.executemanyprepared()``
      - Use :meth:`Cursor.executemany()` instead.
    * - Previously deprecated Advanced Queuing (AQ) API
      - Use the new :ref:`AQ API <aq>` instead.  AQ is only available in python-oracledb Thick mode.
    * - ``Connection.deq()``
      - Replace with :meth:`Queue.deqone()` or :meth:`Queue.deqmany()`
    * - ``Connection.deqoptions()``
      - Replace with :attr:`Queue.deqoptions`
    * - ``Connection.enq()``
      - Replace with :meth:`Queue.enqone()` or :meth:`Queue.enqmany()`
    * - ``Connection.enqoptions()``
      - Replace with :attr:`Queue.enqoptions`

.. list-table-with-summary:: Deprecated in cx_Oracle 8.2
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated feature. The second column, Comments, includes information about the deprecation and the replacement to use, if applicable.
    :name: _deprecations_8_2

    * - Name
      - Comments
    * - ``encoding`` parameter to ``cx_Oracle.connect()``
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated. Encoding is handled internally between python-oracledb and
        Oracle Database.
    * - ``nencoding`` parameter to ``cx_Oracle.connect()``
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated.
    * - ``encoding`` parameter to ```cx_Oracle.SessionPool()``
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated.
    * - ``nencoding`` parameter to ``cx_Oracle.SessionPool()``
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated.
    * - Connection.maxBytesPerCharacter
      - No longer needed as the use of encodings other than UTF-8 is
        deprecated. The constant value 4 can be used instead.
    * - Positional parameters to ``cx_Oracle.connect()``
      - Replace with keyword parameters in order to comply with the Python
        database API.
    * - Positional parameters to ``cx_Oracle.SessionPool()``
      - Replace with keyword parameters in order to comply with the Python
        database API.
    * - ``threaded`` parameter to ``cx_Oracle.SessionPool()``
      - The value of this parameter is ignored. Threading is now always used.
    * - ``waitTimeout`` parameter to ``cx_Oracle.SessionPool()``
      - Replace with parameter name ``wait_timeout``
    * - ``maxLifetimeSession`` parameter to ``cx_Oracle.SessionPool()``
      - Replace with parameter name ``max_lifetime_session``
    * - ``sessionCallback`` parameter to ``cx_Oracle.SessionPool()``
      - Replace with parameter name ``session_callback``
    * - ``maxSessionsPerShard`` parameter to ``cx_Oracle.SessionPool()``
      - Replace with parameter name ``max_sessions_per_shard``
    * - ``SessionPool.tnsentry``
      - Replace with :attr:`ConnectionPool.dsn`
    * - ``payloadType`` parameter to ``Connection.queue()``
      - Replace with parameter name ``payload_type`` if using keyword parameters.
    * - ``ipAddress`` parameter to ``Connection.subscribe()``
      - Replace with parameter name ``ip_address``
    * - ``groupingClass`` parameter to ``Connection.subscribe()``
      - Replace with parameter name ``grouping_class``
    * - ``groupingValue`` parameter to ``Connection.subscribe()``
      - Replace with parameter name ``grouping_value``
    * - ``groupingType`` parameter to ``Connection.subscribe()``
      - Replace with parameter name ``grouping_type``
    * - ``clientInitiated`` parameter to ``Connection.subscribe()``
      - Replace with parameter name ``client_initiated``
    * - ``Connection.callTimeout``
      - Replace with :attr:`Connection.call_timeout`
    * - ``Connection.tnsentry``
      - Replace with :attr:`Connection.dsn`
    * - `keywordParameters` parameter to ``Cursor.callfunc()``
      - Replace with parameter name ``keyword_parameters``
    * - ``keywordParameters`` parameter to ``Cursor.callproc()``
      - Replace with parameter name ``keyword_parameters``
    * - ``encodingErrors`` parameter to ``Cursor.var()``
      - Replace with parameter name ``encoding_errors``
    * - ``Cursor.fetchraw()``
      - Replace with :meth:`Cursor.fetchmany()`
    * - ``newSize`` parameter to ``LOB.trim()``
      - Replace with parameter name ``new_size``
    * - ``Queue.deqMany()``
      - Replace with :meth:`Queue.deqmany()`
    * - ``Queue.deqOne()``
      - Replace with :meth:`Queue.deqone()`
    * - ``Queue.enqMany()``
      - Replace with :meth:`Queue.enqmany()`
    * - ``Queue.enqOne()``
      - Replace with :meth:`Queue.enqone()`
    * - ``Queue.deqOptions``
      - Replace with :attr:`Queue.deqoptions`
    * - ``Queue.enqOptions``
      - Replace with :attr:`Queue.enqoptions`
    * - ``Queue.payloadType``
      - Replace with :attr:`Queue.payload_type`
    * - ``Subscription.ipAddress``
      - Replace with :attr:`Subscription.ip_address`
    * - ``Message.consumerName``
      - Replace with :attr:`Message.consumer_name`
    * - ``Message.queueName``
      - Replace with :attr:`Message.queue_name`
    * - ``Variable.actualElements``
      - Replace with :attr:`Variable.actual_elements`
    * - ``Variable.bufferSize``
      - Replace with :attr:`Variable.buffer_size`
    * - ``Variable.numElements``
      - Replace with :attr:`Variable.num_elements`


.. list-table-with-summary:: Deprecated in cx_Oracle 8.0
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated feature. The second column, Comments, includes information about the deprecation and the replacement to use, if applicable.
    :name: _deprecations_8_0

    * - Name
      - Comments
    * - ``cx_Oracle.BFILE``
      - Replace with :attr:`oracledb.DB_TYPE_BFILE`
    * - ``cx_Oracle.BLOB``
      - Replace with :attr:`oracledb.DB_TYPE_BLOB`
    * - ``cx_Oracle.BOOLEAN``
      - Replace with :attr:`oracledb.DB_TYPE_BOOLEAN`
    * - ``cx_Oracle.CLOB``
      - Replace with :attr:`oracledb.DB_TYPE_CLOB`
    * - ``cx_Oracle.CURSOR``
      - Replace with :attr:`oracledb.DB_TYPE_CURSOR`
    * - ``cx_Oracle.FIXED_CHAR``
      - Replace with :attr:`oracledb.DB_TYPE_CHAR`
    * - ``cx_Oracle.FIXED_NCHAR``
      - Replace with :attr:`oracledb.DB_TYPE_NCHAR`
    * - ``cx_Oracle.INTERVAL``
      - Replace with :attr:`oracledb.DB_TYPE_INTERVAL_DS`
    * - ``cx_Oracle.LONG_BINARY``
      - Replace with :attr:`oracledb.DB_TYPE_LONG_RAW`
    * - ``cx_Oracle.LONG_STRING``
      - Replace with :attr:`oracledb.DB_TYPE_LONG`
    * - ``cx_Oracle.NATIVE_FLOAT``
      - Replace with :attr:`oracledb.DB_TYPE_BINARY_DOUBLE`
    * - ``cx_Oracle.NATIVE_INT``
      - Replace with :attr:`oracledb.DB_TYPE_BINARY_INTEGER`
    * - ``cx_Oracle.NCHAR``
      - Replace with :attr:`oracledb.DB_TYPE_NVARCHAR`
    * - ``cx_Oracle.NCLOB``
      - Replace with :attr:`oracledb.DB_TYPE_NCLOB`
    * - ``cx_Oracle.OBJECT``
      - Replace with :attr:`oracledb.DB_TYPE_OBJECT`
    * - ``cx_Oracle.TIMESTAMP``
      - Replace with :attr:`oracledb.DB_TYPE_TIMESTAMP`


.. list-table-with-summary:: Deprecated in cx_Oracle 7.2
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated feature. The second column, Comments, includes information about the deprecation and the replacement to use, if applicable.
    :name: _deprecations_7_2

    * - Name
      - Comments
    * - ``Connection.deq()``
      - Replace with :meth:`Queue.deqone()` or :meth:`Queue.deqmany()`
    * - ``Connection.deqoptions()``
      - Replace with attribute :attr:`Queue.deqoptions`
    * - ``Connection.enq()``
      - Replace with :meth:`Queue.enqone()` or :meth:`Queue.enqmany()`
    * - ``Connection.enqoptions()``
      - Replace with attribute :attr:`Queue.enqoptions`


.. list-table-with-summary:: Deprecated in cx_Oracle 6.4
    :header-rows: 1
    :class: wy-table-responsive
    :summary: The first column, Name, displays the deprecated feature. The second column, Comments, includes information about the deprecation and the replacement to use, if applicable.
    :name: _deprecations_6_4

    * - Name
      - Comments
    * - ``Cursor.executemanyprepared()``
      - Replace with :meth:`Cursor.executemany()` using None for the ``statement`` argument and an integer for the ``parameters`` argument.
