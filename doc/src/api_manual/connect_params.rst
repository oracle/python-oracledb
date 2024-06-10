.. _connparam:

**************************
API: ConnectParams Objects
**************************

.. note::

    This object is an extension to the DB API.

These objects are created by :meth:`oracledb.ConnectParams()`.  See
:ref:`usingconnparams` for more information.

.. _connparamsmeth:

ConnectParams Methods
=====================

.. method:: ConnectParams.copy()

    Creates a copy of the ConnectParams instance and returns it.

.. method:: ConnectParams.get_connect_string()

    Returns the connection string associated with the ConnectParams instance.

.. method:: ConnectParams.get_network_service_names()

    Returns a list of the network service names found in the
    :ref:`tnsnames.ora <optnetfiles>` file which is inside the directory
    that can be identified by the attribute :attr:`~ConnectParams.config_dir`.
    If a tnsnames.ora file does not exist, then an exception is raised.

.. method:: ConnectParams.parse_connect_string(connect_string)

    Parses the connect string into its components and stores the parameters.

    The ``connect string`` parameter can be an Easy Connect string, name-value
    pairs, or a simple alias which is looked up in ``tnsnames.ora``. Parameters
    that are found in the connect string override any currently stored values.

.. method:: ConnectParams.parse_dsn_with_credentials(dsn)

    Parses a DSN in the form <user>/<password>@<connect_string> or in the form
    <user>/<password> and returns a 3-tuple containing the parsed user,
    password and connect string. Empty strings are returned as the value
    ``None``.

    .. versionadded:: 1.3.0

.. method:: ConnectParams.set(user=None, proxy_user=None, password=None, \
        newpassword=None, wallet_password=None, access_token=None, host=None, \
        port=None, protocol=None, https_proxy=None, https_proxy_port=None, \
        service_name=None, sid=None, server_type=None, cclass=None, \
        purity=None, expire_time=None, retry_count=None, retry_delay=None, \
        tcp_connect_timeout=None, ssl_server_dn_match=None, \
        ssl_server_cert_dn=None, wallet_location=None, events=None, \
        externalauth=None, mode=None, disable_oob=None, stmtcachesize=None, \
        edition=None, tag=None, matchanytag=None, config_dir=None, \
        appcontext=[], shardingkey=[], supershardingkey=[], debug_jdwp=None, \
        connection_id_prefix=None, ssl_context=None, sdu=None, \
        pool_boundary=None, use_tcp_fast_open=False, handle=None)

    Sets the default values for one or more of the parameters of an empty
    ConnectParams object.  A default will be overriden when a connection string
    with that attribute is parsed.  After a ConnectParams object has been
    populated by parsing a connection string, ``ConnectParams.set()`` will not
    override any values.

    .. versionchanged:: 2.1.0

        The ``pool_boundary`` and ``use_tcp_fast_open`` parameters were added.

    .. versionchanged:: 2.0.0

        The ``ssl_context`` and ``sdu`` parameters were added.

    .. versionchanged:: 1.4.0

        The ``connection_id_prefix`` parameter was added.


.. _connparamsattr:

ConnectParams Attributes
========================

.. attribute:: ConnectParams.appcontext

    This read-only attribute is a list that specifies the application context
    used by the connection. It is a list of 3-tuples that includes the
    namespace, name, and value.  Each entry in the tuple is a string.

    This attribute is only supported in python-oracledb Thick mode.

.. attribute:: ConnectParams.cclass

    This read-only attribute is a string that specifies the connection class
    to use for Database Resident Connection Pooling (DRCP).

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.config_dir

    This read-only attribute is a string that identifies the directory in which
    the configuration files such as tnsnames.ora are found. The default is the
    value of :attr:`defaults.config_dir`.

    This attribute is only supported in python-oracledb Thin mode.

    For python-oracledb Thick mode, use the ``config_dir`` parameter of
    :meth:`oracledb.init_oracle_client()`.

.. attribute:: ConnectParams.connection_id_prefix

    This read-only attribute is a string that is added to the beginning of the
    generated ``connection_id`` that is sent to the database for
    `tracing <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-B0FC69F9-2EBC-44E8-ACB2-62FBA14ABD5C>`__.

    This attribute is only supported in python-oracledb Thin mode.

    .. versionadded:: 1.4.0

.. attribute:: ConnectParams.debug_jdwp

    This read-only attribute is a string with the format
    "host=<host>;port=<port>" that specifies the host and port of the PL/SQL
    debugger. This allows the Java Debug Wire Protocol (JDWP) to debug the
    PL/SQL code invoked by the python-oracledb driver. The default value is the
    value of the environment variable ``ORA_DEBUG_JDWP``.

    This attribute is only supported in python-oracledb Thin mode.

    For python-oracledb Thick mode, set the ``ORA_DEBUG_JDWP`` environment
    variable which has the same syntax. See :ref:`applntracing` for more
    information.

.. attribute:: ConnectParams.disable_oob

    This read-only attribute is a boolean that indicates whether out-of-band
    breaks should be disabled. The default value is False. Note that this value
    has no effect on Windows, which does not support this functionality.

    This attribute is only supported in python-oracledb Thin mode.

    For python-oracledb Thick mode, set the equivalent option in a
    ``sqlnet.ora`` file.

.. attribute:: ConnectParams.edition

    This read-only attribute is a string that specifies the edition to use
    for the connection. This attribute cannot be used simultaneously with the
    :attr:`ConnectParams.cclass` attribute.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.events

    This read-only attribute is a boolean that specifies whether the events
    mode should be enabled.

    This attribute is needed for continuous query notification (CQN) and high
    availability event notifications. The default value is False.

    This attribute is only supported in python-oracledb Thick mode.

.. attribute:: ConnectParams.expire_time

    This read-only attribute is an integer that returns the number of minutes
    between the sending of keepalive probes.

    The default value is 0. If this attribute is set to a value greater than
    zero, it enables keepalive.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.externalauth

    This read-only attribute is a boolean that specifies whether external
    authentication should be used. The default value is False.

    For standalone connections, external authentication occurs when the
    ``user`` and ``password`` attributes are not used. If these attributes,
    are not used, you can optionally set the ``externalauth`` attribute to
    True, which may aid code auditing.

    This attribute is only supported in python-oracledb Thick mode.

.. attribute:: ConnectParams.host

    This read-only attribute is a string that returns the name or IP address of
    the machine hosting the database.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.https_proxy

    This read-only attribute is a string that returns the name or IP address of
    a proxy host that is to be used for tunneling secure connections.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.https_proxy_port

    This read-only attribute is an integer that returns the port to be used to
    communicate with the proxy host. The default value is 0.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.matchanytag

    This read-only attribute is a boolean that specifies whether any tag can be
    used when acquiring a connection from the pool. The default value is False.

    This attribute is only supported in python-oracledb Thick mode.

.. attribute:: ConnectParams.mode

    This read-only attribute is an integer that specifies the authorization mode
    to use. The default value is :data:`~oracledb.AUTH_MODE_DEFAULT`.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.pool_boundary

    This read-only attribute is one of the strings "statement" or
    "transaction" which indicates when pooled DRCP or PRCP connections can be
    returned to the pool. If the value is "statement", then pooled DRCP or
    PRCP connections are implicitly released back to the DRCP or PRCP pool
    when the connection is stateless (that is, there are no active cursors,
    active transactions, temporary tables, or temporary LOBs). If the value is
    "transaction", then pooled DRCP or PRCP connections are implicitly
    released back to the DRCP or PRCP pool when either one of the methods
    :meth:`Connection.commit()` or :meth:`Connection.rollback()` are called.
    This attribute requires the use of DRCP or PRCP with Oracle Database 23ai
    (or later). See :ref:`implicitconnpool` for more information.

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 2.1.0

.. attribute:: ConnectParams.port

    This read-only attribute is an integer that returns the port number on
    which the database listener is listening. The default value is 1521.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.protocol

    This read-only attribute is a string that indicates whether unencrypted
    network traffic or encrypted network traffic (TLS) is used and it can have
    the value "tcp" or "tcps". The default value is "tcp".

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.proxy_user

    This read-only attribute is a string that specifies the name of the proxy
    user to connect to.  If this value is not specified, then it will be parsed
    out of the user if the user attribute is in the form "user[proxy_user]".

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.purity

    This read-only attribute is an integer that returns the purity used for
    DRCP.  When the value of this attribute is :attr:`oracledb.PURITY_DEFAULT`,
    then any standalone connection will use :attr:`oracledb.PURITY_NEW` and any
    pooled connection will use :attr:`oracledb.PURITY_SELF`. The default value
    is :data:`~oracledb.PURITY_DEFAULT`.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.retry_count

    This read-only attribute is an integer that returns the number of times
    that a connection attempt should be retried before the attempt is
    terminated. The default value is 0.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.retry_delay

    This read-only attribute is an integer that returns the number of seconds
    to wait before making a new connection attempt. The default value is 1.

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionchaged:: 2.3.0

        The default value of this attribute was changed from 0 seconds to 1
        second.

.. attribute:: ConnectParams.sdu

    This read-only attribute is an integer that returns the requested size of
    the Session Data Unit (SDU), in bytes. The value tunes internal buffers
    used for communication to the database. Bigger values can increase
    throughput for large queries or bulk data loads, but at the cost of higher
    memory use. The SDU size that will actually be used is negotiated down to
    the lower of this value and the database network SDU configuration value.
    See the `SQL*Net documentation
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
    id=GUID-86D61D6F-AD26-421A-BABA-77949C8A2B04>`__ for more details.

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 2.0.0

.. attribute:: ConnectParams.server_type

    This read-only attribute is a string that returns the type of server
    connection that should be established. If specified, it should be one of
    `dedicated`, `shared`, or `pooled`.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.service_name

    This read-only attribute is a string that returns the service name of the
    database.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.shardingkey

    This read-only attribute is a list that specifies a sequence of strings,
    numbers, bytes, or dates that identify the database shard to connect to.

    This attribute is only supported in python-oracledb Thick mode.

.. attribute:: ConnectParams.sid

    This read-only attribute is a string that returns the SID of the database.
    It is recommended to use the :attr:`ConnectParams.service_name` instead.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.ssl_context

    This read-only attribute is an `SSLContext object
    <https://docs.python.org/3/library/ssl.html#ssl-contexts>`__ which is used
    for connecting to the database using TLS. This SSL context will be modified
    to include the private key or any certificates found in a separately
    supplied wallet. This parameter should only be specified if the default
    SSLContext object cannot be used.

    This attribute is only supported in python-oracledb Thin mode.

    .. versionadded:: 2.0.0

.. attribute:: ConnectParams.ssl_server_cert_dn

    This read-only attribute is a string that returns the distinguished name
    (DN), which should be matched with the server.  If this value is specified,
    then it is used for any verification. Otherwise, the hostname will be used.

    This value is ignored if the :attr:`~ConnectParams.ssl_server_dn_match`
    attribute is not set to the value `True`.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.ssl_server_dn_match

    This read-only attribute is a boolean that indicates whether the server
    certificate distinguished name (DN) should be matched in addition to the
    regular certificate verification that is performed. The default value is
    True.

    Note that if the :attr:`~ConnectParams.ssl_server_cert_dn` attribute is not
    specified, then host name matching is performed instead.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.stmtcachesize

    This read-only attribute is an integer that identifies the initial size of
    the statement cache.  The default is the value of
    :attr:`defaults.stmtcachesize`.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.supershardingkey

    This read-only attribute is a list that specifies a sequence of strings,
    numbers, bytes, or dates that identify the database shard to connect to.

    This attribute is only supported in python-oracledb Thick mode.

.. attribute:: ConnectParams.tag

    This read-only attribute is a string that identifies the type of connection
    that should be returned from a pool.

    This attribute is only supported in python-oracledb Thick mode.

.. attribute:: ConnectParams.tcp_connect_timeout

    This read-only attribute is a float that indicates the maximum number of
    seconds to wait for a connection to be established to the database host.
    The default value is 20.0.

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionchanged:: 2.3.0

        The default value of this attribute was changed from 60.0 seconds to
        20.0 seconds.

.. attribute:: ConnectParams.use_tcp_fast_open

    This read-only attribute is a boolean which indicates whether to use an
    an `Oracle Autonomous Database Serverless (ADB-S)
    <https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/
    adbsb/adbsb-overview.html#GUID-A7435462-9D74-44B4-8240-4A6F06E92348>`__
    specific feature that can reduce the latency in round-trips to the database
    after a connection has been established. This feature is only available
    with certain versions of ADB-S. The default value is False.

    This attribute is supported in both python-oracledb Thin and Thick modes.

    .. versionadded:: 2.1.0

.. attribute:: ConnectParams.user

    This read-only attribute is a string that specifies the name of the user to
    connect to.

    This attribute is supported in both python-oracledb Thin and Thick modes.

.. attribute:: ConnectParams.wallet_location

    This read-only attribute is a string that specifies the directory where the
    wallet can be found.

    In python-oracledb Thin mode, this attribute is the directory containing
    the PEM-encoded wallet file, ewallet.pem. In python-oracledb Thick mode,
    this attribute is the directory containing the file, cwallet.sso.

    This attribute is supported in both python-oracledb Thin and Thick modes.
