.. _defaults:

********************
API: Defaults Object
********************

.. currentmodule:: oracledb

Defaults Class
==============

.. autoclass:: Defaults

    A Defaults object contains attributes that can be used to adjust the
    behavior of the python-oracledb driver.

An example of changing a default value is:

.. code-block:: python

    import oracledb

    oracledb.defaults.fetch_lobs = False  # return LOBs directly as strings or bytes

Defaults Attributes
===================

.. autoproperty:: Defaults.arraysize

    This is an attribute for tuning the performance of fetching rows from
    Oracle Database. It does not affect data insertion. See :ref:`Tuning Fetch
    Performance <tuningfetch>`.

.. autoproperty:: Defaults.config_dir

    At time of ``import oracledb`` the value of
    ``oracledb.defaults.config_dir`` will be set to (first one wins):

    - the value of ``$TNS_ADMIN``, if ``TNS_ADMIN`` is set.

    - ``$ORACLE_HOME/network/admin``, if ``$ORACLE_HOME`` is set.

    Otherwise, ``oracledb.defaults.config_dir`` will not be set.

    See :ref:`optnetfiles`.

    .. versionchanged:: 3.0.0

        The directory ``$ORACLE_HOME/network/admin`` was added to the
        heuristic.

        At completion of a call to :meth:`oracledb.init_oracle_client()` in
        Thick mode, the value of :attr:`defaults.config_dir` may get changed
        by python-oracledb.

.. autoproperty:: Defaults.driver_name

    See :ref:`otherinit`.

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.fetch_decimals

    An output type handler such as previously required in the obsolete
    cx_Oracle driver can alternatively be used to adjust the returned type.  If
    a type handler exists and returns a variable (that is,
    ``cursor.var(...)``), then that return variable is used.  If the type
    handler returns *None*, then the value of
    ``oracledb.defaults.fetch_decimals`` is used to determine whether to return
    ``decimal.Decimal`` values.

.. autoproperty:: Defaults.fetch_lobs

    See :ref:`lobdata`.

    An output type handler such as the one previously required in the obsolete
    cx_Oracle driver can alternatively be used to adjust the returned type.  If
    a type handler exists and returns a variable (that is, `cursor.var(...)`),
    then that return variable is used. If the type handler returns *None*, then
    the value of ``oracledb.defaults.fetch_lobs`` is used.

.. autoproperty:: Defaults.machine

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.osuser

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.prefetchrows

    This is an attribute for tuning the performance of fetching rows from
    Oracle Database. It does not affect data insertion. See :ref:`Tuning Fetch
    Performance <tuningfetch>`.

.. autoproperty:: Defaults.program

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.stmtcachesize

    This is a tuning attribute, see :ref:`stmtcache`.

.. autoproperty:: Defaults.terminal

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.thick_mode_dsn_passthrough

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

    .. versionadded:: 3.0.0
