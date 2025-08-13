.. _defaults:

********************
API: Defaults Object
********************

.. currentmodule:: oracledb

Defaults Class
==============

.. autoclass:: Defaults

    See :ref:`settingdefaults`.

.. _defaultsattributes:

Defaults Attributes
===================

.. autoproperty:: Defaults.arraysize

    See :ref:`Tuning Fetch Performance <tuningfetch>`.

.. autoproperty:: Defaults.config_dir

    See :ref:`optnetfiles`.

    .. versionchanged:: 3.0.0

        The directory ``$ORACLE_HOME/network/admin`` was added to the
        heuristic.

.. autoproperty:: Defaults.driver_name

    See :ref:`otherinit` and :ref:`dbviews`.

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.fetch_decimals

    See `decimal.Decimal <https://docs.python.org
    /3/library/decimal.html#decimal-objects>`__.

.. autoproperty:: Defaults.fetch_lobs

    See :ref:`lobdata`.

.. autoproperty:: Defaults.machine

    See :ref:`dbviews`.

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.osuser

    See :ref:`dbviews`.

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.prefetchrows

    See :ref:`tuningfetch`.

.. autoproperty:: Defaults.program

    See :ref:`dbviews`.

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.stmtcachesize

    See :ref:`stmtcache`.

.. autoproperty:: Defaults.terminal

    See :ref:`dbviews`.

    .. versionadded:: 2.5.0

.. autoproperty:: Defaults.thick_mode_dsn_passthrough

    When ``thick_mode_dsn_passthrough`` is the default value `True`, the
    behavior of python-oracledb 2.5 and earlier versions occurs:
    python-oracledb Thick mode passes connect strings unchanged to the Oracle
    Client libraries to handle. Those libraries have their own heuristics for
    locating the optional :ref:`tnsnames.ora <optnetfiles>`, if used.

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
