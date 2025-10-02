.. _connparam:

**************************
API: ConnectParams Objects
**************************

.. currentmodule:: oracledb

ConnectParams Class
===================

.. autoclass:: ConnectParams

    See :ref:`usingconnparams` for more information.

    .. dbapiobjectextension::

    .. versionchanged:: 3.2.0

        The ``pool_name`` parameter was added.

    .. versionchanged:: 3.0.0

        The ``instance_name``, ``use_sni``, ``thick_mode_dsn_passthrough`` and
        ``extra_auth_params`` parameters were added.

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


.. _connparamsmeth:

ConnectParams Methods
=====================

.. automethod:: ConnectParams.copy

.. automethod:: ConnectParams.get_connect_string

.. automethod:: ConnectParams.get_network_service_names

.. automethod:: ConnectParams.parse_connect_string

.. automethod:: ConnectParams.parse_dsn_with_credentials

    .. versionadded:: 1.3.0

.. automethod:: ConnectParams.set

    .. versionchanged:: 3.2.0

        The ``pool_name`` parameter was added.

    .. versionchanged:: 3.0.0

        The ``use_sni``, ``thick_mode_dsn_passthrough``, ``extra_auth_params``
        and ``instance_name`` parameters were added.

    .. versionchanged:: 2.5.0

        The ``program``, ``machine``, ``terminal``, ``osuser``, and
        ``driver_name`` parameters were added. Support for ``edition`` and
        ``appcontext`` was added to python-oracledb Thin mode.

    .. versionchanged:: 2.3.0

        The ``ssl_version`` parameter was added.

    .. versionchanged:: 2.1.0

        The ``pool_boundary`` and ``use_tcp_fast_open`` parameters were added.

    .. versionchanged:: 2.0.0

        The ``ssl_context`` and ``sdu`` parameters were added.

    .. versionchanged:: 1.4.0

        The ``connection_id_prefix`` parameter was added.

.. automethod:: ConnectParams.set_from_config

    .. versionadded:: 3.0.0

.. _connparamsattr:

ConnectParams Attributes
========================

All properties are read only.

.. autoproperty:: ConnectParams.appcontext

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.cclass

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.config_dir

.. autoproperty:: ConnectParams.connection_id_prefix

    This attribute is only supported in python-oracledb Thin mode.

    .. versionadded:: 1.4.0

.. autoproperty:: ConnectParams.debug_jdwp

    See :ref:`applntracing` for more information.

.. autoproperty:: ConnectParams.disable_oob

    For python-oracledb Thick mode, set the equivalent option in a
    ``sqlnet.ora`` file.

.. autoproperty:: ConnectParams.driver_name

    This is an arbitrary value set by the user in the
    :meth:`oracledb.ConnectParams()` method or the
    :attr:`oracledb.defaults.driver_name <Defaults.driver_name>` attribute
    which is the default value. This is the value shown in the CLIENT_DRIVER
    column of the V$SESSION_CONNECT_INFO view.

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 2.5.0

.. autoproperty:: ConnectParams.edition

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.events

.. autoproperty:: ConnectParams.expire_time

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.externalauth

    For standalone connections, external authentication occurs when the
    ``user`` and ``password`` attributes are not used. If these attributes,
    are not used, you can optionally set the ``externalauth`` attribute to
    *True*, which may aid code auditing.

    This attribute is only supported in python-oracledb Thick mode.

.. autoproperty:: ConnectParams.extra_auth_params

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 3.0.0

.. autoproperty:: ConnectParams.host

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.https_proxy

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.https_proxy_port

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.instance_name

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 3.0.0

.. autoproperty:: ConnectParams.machine

    This is an arbitrary value set by the user in the
    :meth:`oracledb.ConnectParams()` method or the
    :attr:`oracledb.defaults.machine <Defaults.machine>` attribute which is the
    default value. This is the value shown in the MACHINE column of the
    V$SESSION view.

    This attribute is only supported in python-oracledb Thin mode.

    .. versionadded:: 2.5.0

.. autoproperty:: ConnectParams.matchanytag

.. autoproperty:: ConnectParams.mode

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.osuser

    This is an arbitrary value set by the user in the
    :meth:`oracledb.ConnectParams()` method or the
    :attr:`oracledb.defaults.osuser <Defaults.osuser>` attribute which is the
    default value. This is the value shown in the OSUSER column of the
    V$SESSION view.

    This attribute is only supported in python-oracledb Thin mode.

    .. versionadded:: 2.5.0

.. autoproperty:: ConnectParams.pool_boundary

    If the value is *statement*, then pooled DRCP or PRCP connections are
    implicitly released back to the DRCP or PRCP pool when the connection is
    stateless (that is, there are no active cursors, active transactions,
    temporary tables, or temporary LOBs). If the value is *transaction*, then
    pooled DRCP or PRCP connections are implicitly released back to the DRCP or
    PRCP pool when either one of the methods :meth:`Connection.commit()` or
    :meth:`Connection.rollback()` are called.  This attribute requires the use
    of DRCP or PRCP with Oracle Database version 23, or later. See
    :ref:`implicitconnpool` for more information.

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 2.1.0

.. autoproperty:: ConnectParams.pool_name

    See :ref:`DRCP Pool Names <poolnames>`.

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 3.2.0

.. autoproperty:: ConnectParams.port

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.program

    This is an arbitrary value set by the user in the
    :meth:`oracledb.ConnectParams()` method or the
    :attr:`oracledb.defaults.program <Defaults.program>` attribute which is the
    default value. This is the value shown in the PROGRAM column of the
    V$SESSION view.

    This attribute is supported in python-oracledb Thin mode.

    .. versionadded:: 2.5.0

.. autoproperty:: ConnectParams.protocol

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.proxy_user

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.purity

    When the value of this attribute is :attr:`oracledb.PURITY_DEFAULT`, then
    any standalone connection will use :attr:`oracledb.PURITY_NEW` and any
    pooled connection will use :attr:`oracledb.PURITY_SELF`. The default value
    is :data:`~oracledb.PURITY_DEFAULT`.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.retry_count

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.retry_delay

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionchanged:: 2.3.0

        The default value of this attribute was changed from *0* seconds to *1*
        second.

.. autoproperty:: ConnectParams.sdu

    See the `Database Net Services documentation
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
    id=GUID-86D61D6F-AD26-421A-BABA-77949C8A2B04>`__ for more details.

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 2.0.0

.. autoproperty:: ConnectParams.server_type

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.service_name

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.shardingkey

.. autoproperty:: ConnectParams.sid

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.ssl_context

    This attribute is only supported in python-oracledb Thin mode.

    .. versionadded:: 2.0.0

.. autoproperty:: ConnectParams.ssl_server_cert_dn

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.ssl_server_dn_match

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.ssl_version

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 2.3.0

.. autoproperty:: ConnectParams.stmtcachesize

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.supershardingkey

.. autoproperty:: ConnectParams.tag

    This attribute is only supported in python-oracledb Thick mode.

.. autoproperty:: ConnectParams.tcp_connect_timeout

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionchanged:: 2.3.0

        The default value of this attribute was changed from *60.0* seconds to
        *20.0* seconds.

.. autoproperty:: ConnectParams.terminal

    This is an arbitrary value set by the user in the
    :meth:`oracledb.ConnectParams()` method or the
    :attr:`oracledb.defaults.terminal <Defaults.terminal>` attribute which is
    the default value. This is the value shown in the TERMINAL column of the
    V$SESSION view.

    This attribute is only supported in python-oracledb Thin mode.

    .. versionadded:: 2.5.0

.. autoproperty:: ConnectParams.use_sni

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 3.0.0

.. autoproperty:: ConnectParams.thick_mode_dsn_passthrough

    This attribute is only supported in python-oracledb Thick mode.

    .. versionadded:: 3.0.0

.. autoproperty:: ConnectParams.use_tcp_fast_open

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 2.1.0

.. autoproperty:: ConnectParams.user

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: ConnectParams.wallet_location

    This attribute is supported in both python-oracledb Thin and Thick modes.
