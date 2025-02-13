.. _defaults:

********************
API: Defaults Object
********************

This object contains attributes that can be used to adjust the behavior of the
python-oracledb driver.

All attributes are supported in Thin and Thick modes, subject to noted details.

An example of changing a default value is:

.. code-block:: python

    import oracledb

    oracledb.defaults.fetch_lobs = False  # return LOBs directly as strings or bytes

Defaults Attributes
===================

.. attribute:: defaults.arraysize

    The default value for :attr:`Cursor.arraysize`. This is a query tuning
    attribute, see :ref:`Tuning Fetch Performance <tuningfetch>`.

    This attribute has an initial value of *100*.

.. attribute:: defaults.config_dir

    The directory in which optional configuration files such as
    ``tnsnames.ora`` will be read in python-oracledb Thin mode.  This attribute
    takes its initial value from the environment variable ``TNS_ADMIN``.

    This attribute is not used by the python-oracledb Thick mode: the usual
    Oracle Client search path behavior for configuration files is followed, see
    :ref:`optnetfiles`.

.. attribute:: defaults.driver_name

    The default value that represents the driver used by the client to connect
    to Oracle Database. This is the value used in the CLIENT_DRIVER column
    of the V$SESSION_CONNECT_INFO view.

    This attribute has an initial value of *None*. It is used as required in
    python-oracledb Thick and Thin mode.

    In python-oracledb Thick mode, this attribute is used if the
    ``driver_name`` parameter is not specified in
    :meth:`oracledb.init_oracle_client()`. In Thin mode, this attribute is
    used if the ``driver_name`` parameter is not specified in
    :meth:`oracledb.connect()`, :meth:`oracledb.connect_async()`,
    :meth:`oracledb.create_pool()`, or :meth:`oracledb.create_pool_async()`.
    If the value of this attribute is *None*, the value set when connecting in
    python-oracledb Thick mode is like "python-oracledb thk : <version>" and
    in Thin mode is like "python-oracledb thn : <version>". See
    :ref:`otherinit`.

    .. versionadded:: 2.5.0

.. attribute:: defaults.fetch_decimals

    Identifies whether numbers should be fetched as `decimal.Decimal
    <https://docs.python.org/3/library/decimal.html#decimal-objects>`__ values.
    This can help avoid issues with converting numbers from Oracle Database's
    decimal format to Python's binary format.

    An output type handler such as previously required in cx_Oracle (see
    `return_numbers_as_decimals.py <https://github.com/oracle/python-cx_Oracle/
    blob/main/samples/return_numbers_as_decimals.py>`__) can alternatively be
    used to adjust the returned type.  If a type handler exists and returns a
    variable (that is, ``cursor.var(...)``), then that return variable is used.
    If the type handler returns *None*, then the value of
    ``oracledb.defaults.fetch_decimals`` is used to determine whether to return
    ``decimal.Decimal`` values.

    This attribute has an initial value of *False*.

.. attribute:: defaults.fetch_lobs

    When the value of this attribute is *True*, then queries to LOB columns
    return LOB locators. When the value of this attribute is *False*, then
    CLOBs and NCLOBs are fetched as strings, and BLOBs are fetched as bytes. If
    LOBs are larger than 1 GB, then this attribute should be set to *True* and
    the LOBs should be streamed.  See :ref:`lobdata`.

    An output type handler such as the one previously required in cx_Oracle
    (see `return_lobs_as_strings.py <https://github.com/oracle/
    python-cx_Oracle/blob/main/samples/return_lobs_as_strings.py>`__) can
    alternatively be used to adjust the returned type.  If a type handler
    exists and returns a variable (that is, `cursor.var(...)`), then that
    return variable is used. If the type handler returns *None*, then the value
    of ``oracledb.defaults.fetch_lobs`` is used.

    The value of ``oracledb.defaults.fetch_lobs`` does not affect LOBs returned
    as OUT binds.

    This attribute has an initial value of *True*.

.. attribute:: defaults.machine

    The default value that represents the machine name of the client
    connecting to Oracle Database. This is the value used in the
    MACHINE column of the V$SESSION view.

    This attribute takes the host name where the application is running as its
    initial value.

    This attribute is only used in python-oracledb Thin mode.

    .. versionadded:: 2.5.0

.. attribute:: defaults.osuser

    The default value that represents the operating system user that initiates
    the database connection. This is the value used in the OSUSER
    column of the V$SESSION view.

    This attribute takes the login name of the user as its initial value.

    This attribute is only used in python-oracledb Thin mode.

    .. versionadded:: 2.5.0

.. attribute:: defaults.prefetchrows

    The default value for :attr:`Cursor.prefetchrows`. This is a query tuning
    attribute, see :ref:`Tuning Fetch Performance <tuningfetch>`.

    This attribute has an initial value of *2*.

.. attribute:: defaults.program

    The default value that represents the program name connected to the
    database. This is the value used in the PROGRAM column of the
    V$SESSION view.

    This attribute has an initial value that is populated by `sys.executable
    <https://docs.python.org/3/library/sys.html#sys.executable>`__.

    This attribute is only used in python-oracledb Thin mode.

    .. versionadded:: 2.5.0

.. attribute:: defaults.stmtcachesize

    The default value for :attr:`Connection.stmtcachesize` and
    :attr:`ConnectionPool.stmtcachesize`. This is a tuning attribute, see
    :ref:`stmtcache`.

    This attribute has an initial value of *20*.

.. attribute:: defaults.terminal

    The default value that represents the terminal identifier from which the
    connection originates. This is the value used in the TERMINAL
    column of the V$SESSION view.

    This attribute has an initial value of *unknown*.

    This attribute is only used in python-oracledb Thin mode.

    .. versionadded:: 2.5.0

.. attribute:: defaults.thick_mode_dsn_passthrough

    The default value that determines whether :ref:`connection strings
    <connstr>` passed to :meth:`oracledb.connect()` and
    :meth:`oracledb.create_pool()` in python-oracledb Thick mode will be parsed
    by Oracle Client libraries or by python-oracledb itself.

    When the value of this attribute is *True*, then connection strings passed
    to these methods will be sent unchanged to the Oracle Client libraries.

    Setting this attribute to *False* makes Thick and Thin mode applications
    behave similarly regarding connection string parameter handling and
    locating any optional :ref:`tnsnames.ora files <optnetfiles>` configuration
    file, see :ref:`usingconfigfiles`. Connection strings used in connection
    and pool creation methods in Thick mode are parsed by python-oracledb
    itself and a generated connect descriptor is sent to the Oracle Client
    libraries. The location of any optional :ref:`tnsnames.ora file
    <optnetfiles>` used to resolve a :ref:`TNS Alias <netservice>` is
    determined by python-oracledb heuristics instead of by the Oracle Client
    libraries.

    This attribute has an initial value of *True*.

    This attribute is ignored in python-oracledb Thin mode.

    .. versionadded:: 3.0.0
