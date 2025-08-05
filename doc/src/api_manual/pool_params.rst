.. _poolparam:

***********************
API: PoolParams Objects
***********************

.. currentmodule:: oracledb

PoolParams Class
================

.. autoclass:: PoolParams

    The PoolParams class is a subclass of the :ref:`ConnectParams Class
    <connparam>`.  In addition to the parameters and attributes of the
    ConnectParams class, the PoolParams class also contains new parameters and
    attributes.

    See :ref:`usingpoolparams` for more information.

    .. versionchanged:: 3.2.0

        The ``pool_name`` parameter was added.

    .. versionchanged:: 3.0.0

        The ``use_sni``, ``instance_name``, ``thick_mode_dsn_passthrough``,
        ``extra_auth_params``, and ``instance_name`` parameters were added.

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


.. _poolparamsmeth:

PoolParams Methods
==================

.. automethod:: PoolParams.copy

.. automethod:: PoolParams.get_connect_string

.. automethod:: PoolParams.parse_connect_string

.. automethod:: PoolParams.set

    .. versionchanged:: 3.2.0

        The ``pool_name`` parameter was added.

    .. versionchanged:: 3.0.0

        The ``use_sni``, ``thick_mode_dsn_passthrough``,
        ``extra_auth_params`` and ``instance_name`` parameters were added.

    .. versionchanged:: 2.5.0

        The ``program``, ``machine``, ``terminal``, ``osuser``, and
        ``driver_name`` parameters were added. Support for ``edition`` and
        ``appcontext`` was added to python-oracledb Thin mode.

    .. versionchanged:: 2.3.0

        The ``ping_timeout`` and ``ssl_version`` parameters were added.

    .. versionchanged:: 2.1.0

        The ``pool_boundary`` and ``use_tcp_fast_open`` parameters were added.

.. _poolparamsattr:

PoolParams Attributes
=====================

All properties are read only.

.. autoproperty:: PoolParams.connectiontype

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: PoolParams.getmode

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: PoolParams.homogeneous

    This attribute is only supported in python-oracledb Thick mode. The
    python-oracledb Thin mode supports only homogeneous modes.

.. autoproperty:: PoolParams.increment

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: PoolParams.min

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: PoolParams.max

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: PoolParams.max_lifetime_session

    Connections become candidates for termination when they are acquired or
    released back to the pool, and have existed for longer than
    ``max_lifetime_session`` seconds. Connections that are in active use will
    not be closed. In python-oracledb Thick mode, Oracle Client libraries 12.1
    or later must be used and, prior to Oracle Client 21, cleanup only occurs
    when the pool is accessed.

.. autoproperty:: PoolParams.max_sessions_per_shard

    This attribute is only supported in python-oracledb Thick mode.

.. autoproperty:: PoolParams.ping_interval

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: PoolParams.ping_timeout

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 2.3.0

.. autoproperty:: PoolParams.session_callback

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: PoolParams.soda_metadata_cache

    This attribute is only supported in python-oracledb Thick mode.

.. autoproperty:: PoolParams.timeout

    This applies only when the pool has more than ``min`` connections open,
    allowing it to shrink to the specified minimum size. The default value is
    *0* seconds. A value of *0* means that there is no maximum time.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. autoproperty:: PoolParams.wait_timeout

    This attribute is supported in both python-oracledb Thin and Thick modes.
