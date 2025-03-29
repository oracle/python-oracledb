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

    The directory in which the optional configuration file ``tnsnames.ora``
    will be read in python-oracledb Thin mode.

    At time of ``import oracledb`` the value of
    ``oracledb.defaults.config_dir`` will be set to (first one wins):

    - the value of ``$TNS_ADMIN``, if ``TNS_ADMIN`` is set.

    - ``$ORACLE_HOME/network/admin``, if ``$ORACLE_HOME`` is set.

    Otherwise, ``oracledb.defaults.config_dir`` will not be set.

    This attribute is used in python-oracledb Thin mode.  It is also used in
    Thick mode if :attr:`defaults.thick_mode_dsn_passthrough` is *False*, see
    :ref:`optnetfiles`.

    .. versionchanged:: 3.0.0

        The directory ``$ORACLE_HOME/network/admin`` was added to the
        heuristic.

        At completion of a call to :meth:`oracledb.init_oracle_client()` in
        Thick mode, the value of :attr:`defaults.config_dir` may get changed
        by python-oracledb.

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

    An output type handler such as previously required in the obsolete
    cx_Oracle driver can alternatively be used to adjust the returned type.  If
    a type handler exists and returns a variable (that is,
    ``cursor.var(...)``), then that return variable is used.  If the type
    handler returns *None*, then the value of
    ``oracledb.defaults.fetch_decimals`` is used to determine whether to return
    ``decimal.Decimal`` values.

    This attribute has an initial value of *False*.

.. attribute:: defaults.fetch_lobs

    When the value of this attribute is *True*, then queries to LOB columns
    return LOB locators. When the value of this attribute is *False*, then
    CLOBs and NCLOBs are fetched as strings, and BLOBs are fetched as bytes. If
    LOBs are larger than 1 GB, then this attribute should be set to *True* and
    the LOBs should be streamed.  See :ref:`lobdata`.

    An output type handler such as the one previously required in the obsolete
    cx_Oracle driver can alternatively be used to adjust the returned type.  If
    a type handler exists and returns a variable (that is, `cursor.var(...)`),
    then that return variable is used. If the type handler returns *None*, then
    the value of ``oracledb.defaults.fetch_lobs`` is used.

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

    This attribute is ignored when using :meth:`Connection.fetch_df_all()` or
    :meth:`Connection.fetch_df_batches()` since these methods always set the
    internal prefetch size to the relevant arraysize or size value.

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

    The value that determines whether :ref:`connection strings <connstr>`
    passed as the ``dsn`` parameter to :meth:`oracledb.connect()`,
    :meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, and
    :meth:`oracledb.create_pool_async()` in python-oracledb Thick mode will be
    parsed by Oracle Client libraries or by python-oracledb itself.

    When ``thick_mode_dsn_passthrough`` is the default value `True`, the
    behavior of python-oracledb 2.5 and earlier versions occurs: Thick mode
    passes connect strings unchanged to the Oracle Client libraries to
    handle. Those libraries have their own heuristics for locating the optional
    :ref:`tnsnames.ora <optnetfiles>`, if used.

    When ``thick_mode_dsn_passthrough`` is `False`, python-oracledb Thick mode
    behaves similarly to Thin mode, which can be helpful for applications that
    may be run in either mode:

    - The search path used to locate and read any optional :ref:`tnsnames.ora
      <optnetfiles>` file is handled in the python-oracledb driver. Different
      :ref:`tnsnames.ora <optnetfiles>` files can be used by each
      connection. Note loading of optional Thick mode files such as
      ``sqlnet.ora`` and ``oraaccess.xml`` is always handled by Oracle Client
      libraries regardless of the value of ``thick_mode_dsn_passthrough``
      because it is those libraries that use these files.

    - All connect strings will be parsed by the python-oracledb driver and a
      generated connect descriptor is sent to the database. Parameters
      unrecognized by python-oracledb in :ref:`Easy Connect strings
      <easyconnect>` are discarded. In :ref:`full connect descriptors
      <conndescriptor>` passed explicitly as the ``dsn`` parameter value or
      stored in a :ref:`tnsnames.ora <optnetfiles>` file, any parameters that
      are unrecognized by python-oracledb in the ``DESCRIPTION``,
      ``CONNECT_DATA`` and ``SECURITY`` sections will be passed through to the
      database unchanged, while unrecognized parameters in other sections are
      discarded.

    - If a :ref:`Centralized Configuration Provider <configurationproviders>`
      is used for connection configuration, any :ref:`python-oracledb parameter
      values <pyoparams>` in the configuration will be used.

    The value of ``thick_mode_dsn_passthrough`` is ignored in python-oracledb
    Thin mode, which always parses all connect strings (including reading a
    :ref:`tnsnames.ora <optnetfiles>` file, if required).

    This attribute has an initial value of *True*.

    .. versionadded:: 3.0.0
