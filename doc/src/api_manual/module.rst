.. module:: oracledb

.. _module:

****************************
API: python-oracledb Module
****************************

.. _modmeth:

Oracledb Methods
================

.. function:: Binary(string)

    Constructs an object holding a binary (long) string value.


.. function:: clientversion()

    Returns the version of the client library being used as a 5-tuple. The five
    values are the major version, minor version, update number, patch number,
    and port update number.

    This function can only be called when python-oracledb is in Thick
    mode. Using it in Thin mode will throw an exception. See
    :ref:`enablingthick`.

    .. dbapimethodextension::

.. function:: connect(dsn=None, pool=None, pool_alias=None, conn_class=None, \
        params=None, user=None, proxy_user=None, password=None, \
        newpassword=None, wallet_password=None, access_token=None, host=None, \
        port=1521, protocol="tcp", https_proxy=None, https_proxy_port=0, \
        service_name=None, instance_name=None, sid=None, server_type=None, \
        cclass=None, purity=oracledb.PURITY_DEFAULT, expire_time=0, \
        retry_count=0, retry_delay=1, tcp_connect_timeout=20.0, \
        ssl_server_dn_match=True, ssl_server_cert_dn=None, \
        wallet_location=None, events=False, externalauth=False, \
        mode=oracledb.AUTH_MODE_DEFAULT, disable_oob=False, \
        stmtcachesize=oracledb.defaults.stmtcachesize, edition=None, \
        tag=None, matchanytag=False, config_dir=oracledb.defaults.config_dir, \
        appcontext=[], shardingkey=[], supershardingkey=[], debug_jdwp=None, \
        connection_id_prefix=None, ssl_context=None, sdu=8192, \
        pool_boundary=None, use_tcp_fast_open=False, ssl_version=None, \
        program=oracledb.defaults.program, machine=oracledb.defaults.machine, \
        terminal=oracledb.defaults.terminal, osuser=oracledb.defaults.osuser, \
        driver_name=oracledb.defaults.driver_name, use_sni=False, \
        thick_mode_dsn_passthrough=oracledb.defaults.thick_mode_dsn_passthrough, \
        extra_auth_params=None, handle=0)

    Constructor for creating a connection to the database. Returns a
    :ref:`Connection Object <connobj>`. All parameters are optional and can be
    specified as keyword parameters.  See :ref:`standaloneconnection`
    information about connections.

    Not all parameters apply to both python-oracledb Thin and :ref:`Thick
    <enablingthick>` modes.

    Some values, such as the database host name, can be specified as
    parameters, as part of the connect string, and in the params object.  If a
    ``dsn`` (data source name) parameter is passed, the python-oracledb Thick
    mode will use the string to connect, otherwise a connection string is
    internally constructed from the individual parameters and params object
    values, with the individual parameters having precedence.  In
    python-oracledb's default Thin mode, a connection string is internally used
    that contains all relevant values specified.  The precedence in Thin mode
    is that values in any ``dsn`` parameter override values passed as
    individual parameters, which themselves override values set in the
    ``params`` parameter object. Similar precedence rules also apply to other
    values.

    The ``dsn`` (data source name) parameter is an :ref:`Oracle Net Services
    Connection String <connstr>`.  It can also be a string in the format
    ``user/password@connect_string``.

    The ``pool`` parameter is expected to be a pool object.  This parameter
    was deprecated in python-oracledb 3.0.0.  Use
    :meth:`ConnectionPool.acquire()` instead since the use of this parameter
    is the equivalent of calling this method.

    The ``pool_alias`` parameter is expected to be a string which indicates the
    name of the previously created pool in the :ref:`connection pool cache
    <connpoolcache>` from which to acquire the connection. This is identical to
    calling :meth:`ConnectionPool.acquire()`. When ``pool_alias`` is used,
    ``connect()`` supports the same parameters as
    :meth:`~ConnectionPool.acquire()` and has the same behavior.

    The ``conn_class`` parameter is expected to be Connection or a subclass of
    Connection.

    The ``params`` parameter is expected to be of type :ref:`ConnectParams
    <connparam>` and contains connection parameters that will be used when
    establishing the connection. If this parameter is not specified, the
    additional keyword parameters will be used to internally create an instance
    of ConnectParams. If both the params parameter and additional keyword
    parameters are specified, the values in the keyword parameters have
    precedence. Note that if a ``dsn`` is also supplied in python-oracledb Thin
    mode, then the values of the parameters specified (if any) within the
    ``dsn`` will override the values passed as additional keyword parameters,
    which themselves override the values set in the ``params`` parameter
    object.

    The ``user`` parameter is expected to be a string which indicates the name
    of the user to connect to. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``proxy_user`` parameter is expected to be a string which indicates the
    name of the proxy user to connect to. If this value is not specified, it
    will be parsed out of user if user is in the form "user[proxy_user]". This
    value is used in both the python-oracledb Thin and Thick modes.

    The ``password`` parameter expected to be a string which indicates the
    password for the user. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``newpassword`` parameter is expected to be a string which indicates
    the new password for the user. The new password will take effect
    immediately upon a successful connection to the database. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``wallet_password`` parameter is expected to be a string which
    indicates the password to use to decrypt the PEM-encoded wallet, if it is
    encrypted. This value is only used in python-oracledb Thin mode. The
    ``wallet_password`` parameter is not needed for cwallet.sso files that are
    used in the python-oracledb Thick mode.

    The ``access_token`` parameter is expected to be a string or a 2-tuple or
    a callable. If it is a string, it specifies an Azure AD OAuth2 token used
    for Open Authorization (OAuth 2.0) token based authentication. If it is a
    2-tuple, it specifies the token and private key strings used for Oracle
    Cloud Infrastructure (OCI) Identity and Access Management (IAM) token based
    authentication. If it is a callable, it returns either a string or a
    2-tuple used for OAuth 2.0 or OCI IAM token based authentication and is
    useful when the pool needs to expand and create new connections but the
    current authentication token has expired. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``host`` parameter is expected to be a string which specifies the name
    or IP address of the machine hosting the listener, which handles the
    initial connection to the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``port`` parameter is expected to be an integer which indicates the
    port number on which the listener is listening. The default value is
    *1521*. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``protocol`` parameter is expected to be one of the strings *tcp* or
    *tcps* which indicates whether to use unencrypted network traffic or
    encrypted network traffic (TLS). The default value is *tcp*. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``https_proxy`` parameter is expected to be a string which indicates
    the name or IP address of a proxy host to use for tunneling secure
    connections. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``https_proxy_port`` parameter is expected to be an integer which
    indicates the port that is to be used to communicate with the proxy host.
    The default value is *0*. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``service_name`` parameter is expected to be a string which indicates
    the service name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``instance_name`` parameter is expected to be a string which indicates
    the instance name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``sid`` parameter is expected to be a string which indicates the SID of
    the database. It is recommended to use ``service_name`` instead. This value
    is used in both the python-oracledb Thin and Thick modes.

    The ``server_type`` parameter is expected to be a string that indicates the
    type of server connection that should be established. If specified, it
    should be one of *dedicated*, *shared*, or *pooled*. This value is used in
    both the python-oracledb Thin and Thick modes.

    The ``cclass`` parameter is expected to be a string that identifies the
    connection class to use for :ref:`drcp`. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``purity`` parameter is expected to be one of the
    :ref:`oracledb.PURITY_* <drcppurityconsts>` constants that identifies the
    purity to use for DRCP. This value is used in both the python-oracledb Thin
    and Thick modes.  The purity will internally default to
    :data:`~oracledb.PURITY_SELF` for pooled connections. For standalone
    connections, the purity will internally default to
    :data:`~oracledb.PURITY_NEW`.

    The ``expire_time`` parameter is expected to be an integer which indicates
    the number of minutes between the sending of keepalive probes. If this
    parameter is set to a value greater than zero it enables keepalive. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *0*.

    The ``retry_count`` parameter is expected to be an integer that identifies
    the number of times that a connection attempt should be retried before the
    attempt is terminated. This value is used in both the python-oracledb Thin
    and Thick modes. The default value is *0*.

    The ``retry_delay`` parameter is expected to be an integer that identifies
    the number of seconds to wait before making a new connection attempt. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *1*.

    The ``tcp_connect_timeout`` parameter is expected to be a float that
    indicates the maximum number of seconds to wait for establishing a
    connection to the database host. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is *20.0*.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that
    indicates whether the server certificate distinguished name (DN) should be
    matched in addition to the regular certificate verification that is
    performed. Note that if the ``ssl_server_cert_dn`` parameter is not
    provided, host name matching is performed instead. This value is used in
    both the python-oracledb Thin and Thick modes. The default value is *True*.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that
    indicates the distinguished name (DN) which should be matched with the
    server. This value is ignored if the ``ssl_server_dn_match`` parameter is
    not set to the value *True*. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``wallet_location`` parameter is expected to be a string that
    identifies the directory where the wallet can be found. In python-oracledb
    Thin mode, this must be the directory of the PEM-encoded wallet file,
    ewallet.pem.  In python-oracledb Thick mode, this must be the directory of
    the file, cwallet.sso. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``events`` parameter is expected to be a boolean that specifies whether
    the events mode should be enabled. This value is only used in the
    python-oracledb Thick mode and is ignored in the Thin mode. This parameter
    is needed for continuous query notification and high availability event
    notifications. The default value is *False*.

    The ``externalauth`` parameter is a boolean that specifies whether external
    authentication should be used. This value is only used in the
    python-oracledb Thick mode and is ignored in the Thin mode. The default
    value is *False*. For standalone connections, external authentication
    occurs when the ``user`` and ``password`` attributes are not used. If these
    attributes are not used, you can optionally set the ``externalauth``
    attribute to *True*, which may aid code auditing.

    If the ``mode`` parameter is specified, it must be one of the
    :ref:`connection authorization modes <connection-authorization-modes>`
    which are defined at the module level. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is
    :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value is only used
    in the python-oracledb Thin mode and has no effect on Windows which
    does not support this functionality. The default value is *False*.

    The ``stmtcachesize`` parameter is expected to be an integer which
    specifies the initial size of the statement cache. This value is used in
    both the python-oracledb Thin and Thick modes. The default is the value of
    :attr:`defaults.stmtcachesize`.

    The ``edition`` parameter is expected to be a string that indicates the
    edition to use for the connection. It requires Oracle Database 11.2, or
    later. This parameter cannot be used simultaneously with the ``cclass``
    parameter.

    The ``tag`` parameter is expected to be a string that identifies the type
    of connection that should be returned from a pool. This value is only used
    in the python-oracledb Thick mode and is ignored in the Thin mode.

    The ``matchanytag`` parameter is expected to be a boolean specifying
    whether any tag can be used when acquiring a connection from the pool. This
    value is only used in the python-oracledb Thick mode when acquiring a
    connection from a pool. This value is ignored in the python-oracledb Thin
    mode. The default value is *False*.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which :ref:`optional configuration files <optconfigfiles>` are
    found. The default is the value of :attr:`defaults.config_dir`.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that
    identifies the application context used by the connection. This parameter
    should contain namespace, name, and value and each entry in the tuple
    should be a string.

    The ``shardingkey`` parameter and ``supershardingkey`` parameters, if
    specified, are expected to be a sequence of values which identifies the
    database shard to connect to. The key values can be a list of strings,
    numbers, bytes, or dates.  These values are only used in the
    python-oracledb Thick mode and are ignored in the Thin mode. See
    :ref:`connsharding`.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL
    debugger.  This allows using the Java Debug Wire Protocol (JDWP) to debug
    PL/SQL code called by python-oracledb. This value is only used in the
    python-oracledb Thin mode.  For python-oracledb Thick mode, set the
    ``ORA_DEBUG_JDWP`` environment variable which has the same syntax. For more
    information, see :ref:`applntracing`.

    The ``connection_id_prefix`` parameter is expected to be a string and is
    added to the beginning of the generated ``connection_id`` that is sent to
    the database for `tracing <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-B0FC69F9-2EBC-44E8-ACB2-62FBA14ABD5C>`__.  This value
    is only used in the python-oracledb Thin mode.

    The ``ssl_context`` parameter is expected to be an `SSLContext object
    <https://docs.python.org/3/library/ssl.html#ssl-contexts>`__ which is used
    for connecting to the database using TLS.  This SSL context will be
    modified to include the private key or any certificates found in a
    separately supplied wallet.  This parameter should only be specified if
    the default SSLContext object cannot be used.  This value is only used in
    the python-oracledb Thin mode.

    The ``sdu`` parameter is expected to be an integer that returns the
    requested size of the Session Data Unit (SDU), in bytes. The value tunes
    internal buffers used for communication to the database. Bigger values can
    increase throughput for large queries or bulk data loads, but at the cost
    of higher memory use. The SDU size that will actually be used is negotiated
    down to the lower of this value and the database network SDU configuration
    value. See the `Database Net Services documentation <https://www.oracle.
    com/pls/topic/lookup?ctx=dblatest&id=GUID-86D61D6F-AD26-421A-BABA-
    77949C8A2B04>`__ for more details. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is *8192* bytes.

    The ``pool_boundary`` parameter is expected to be one of the strings
    *statement* or *transaction* which indicates when pooled :ref:`DRCP <drcp>`
    or PRCP connections can be returned to the pool.  If the value is
    *statement*, then pooled DRCP or PRCP connections are implicitly released
    back to the DRCP or PRCP pool when the connection is stateless (that is,
    there are no active cursors, active transactions, temporary tables, or
    temporary LOBs).  If the value is *transaction*, then pooled DRCP or PRCP
    connections are implicitly released back to the DRCP or PRCP pool when
    either one of the methods :meth:`Connection.commit()` or
    :meth:`Connection.rollback()` are called.  This parameter requires the use
    of DRCP or PRCP with Oracle Database 23ai (or later).  See
    :ref:`implicitconnpool` for more information.  This value is used in both
    the python-oracledb Thin and Thick modes.

    The ``use_tcp_fast_open`` parameter is expected to be a boolean which
    indicates whether to use TCP Fast Open which is an `Oracle Autonomous
    Database Serverless (ADB-S) <https://docs.oracle.com/en/cloud/paas/
    autonomous-database/serverless/adbsb/connection-tcp-fast-open.html#
    GUID-34654005-DBBA-4C49-BC6D-717F9C16A17C>`__ specific feature that can
    reduce the latency in round-trips to the database after a connection has
    been established.  This feature is only available with certain versions of
    ADB-S.  This value is used in both python-oracledb Thin and Thick modes.
    The default value is *False*.

    The ``ssl_version`` parameter is expected to be one of the constants
    *ssl.TLSVersion.TLSv1_2* or *ssl.TLSVersion.TLSv1_3* which identifies the
    TLS protocol version used.  These constants are defined in the Python
    `ssl <https://docs.python.org/3/library/ssl.html>`__ module.  This
    parameter can be specified when establishing connections with the protocol
    *tcps*.  This value is used in both python-oracledb Thin and Thick modes.
    The value *ssl.TLSVersion.TLSv1_3* requires Oracle Database 23ai.  If you
    are using python-oracledb Thick mode, Oracle Client 23ai is additionally
    required.

    The ``use_sni`` parameter is expected to be a boolean which indicates
    whether to use the TLS Server Name Indication (SNI) extension to bypass the
    second TLS negotiation that would otherwise be required. This parameter is
    used in both python-oracledb Thin and Thick modes. This parameter requires
    Oracle Database 23.7. The default value is *False*. See the `Database Net
    Services documentation
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
    GUID-E98F42D0-DC9D-4B52-9C66-6DE7EC5F64D6>`__ for more details.

    The ``program`` parameter is expected to be a string which specifies the
    name of the executable program or application connected to Oracle
    Database.  This value is only used in the python-oracledb Thin mode. The
    default is the value of :attr:`defaults.program`.

    The ``machine`` parameter is expected to be a string which specifies the
    machine name of the client connecting to Oracle Database.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.machine`.

    The ``terminal`` parameter is expected to be a string which specifies the
    terminal identifier from which the connection originates.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.terminal`.

    The ``osuser`` parameter is expected to be a string which specifies the
    operating system user that initiates the database connection.  This value
    is only used in the python-oracledb Thin mode.  The default value is the
    value of :attr:`defaults.osuser`.

    The ``driver_name`` parameter is expected to be a string which specifies
    the driver used by the client to connect to Oracle Database.  This value
    is used in both the python-oracledb Thin and Thick modes.  The default is
    the value of :attr:`defaults.driver_name`.

    The ``thick_mode_dsn_passthrough`` parameter is expected to be a boolean
    which indicates whether the connect string should be passed unchanged to
    the Oracle Client libraries for parsing when using python-oracledb Thick
    mode. If this parameter is set to *False* in Thick mode, connect strings
    are parsed by python-oracledb itself and a generated connect descriptor is
    sent to the Oracle Client libraries. This value is only used in the
    python-oracledb Thick mode. The default value is the value of
    :attr:`defaults.thick_mode_dsn_passthrough`. For more information, see
    :ref:`usingconfigfiles`.

    The ``extra_auth_params`` parameter is expected to be a dictionary
    containing the configuration parameters necessary for Oracle Database
    authentication using :ref:`OCI <cloudnativeauthoci>` or :ref:`Azure
    <cloudnativeauthoauth>` cloud native authentication plugins.  This value is
    used in both the python-oracledb Thin and Thick modes. See
    :ref:`tokenauth`.

    If the ``handle`` parameter is specified, it must be of type OCISvcCtx\*
    and is only of use when embedding Python in an application (like
    PowerBuilder) which has already made the connection. The connection thus
    created should *never* be used after the source handle has been closed or
    destroyed. This value is only used in the python-oracledb Thick mode and
    is ignored in the Thin mode.  It should be used with extreme caution. The
    default value is *0*.

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

.. function:: connect_async(dsn=None, pool=None, pool_alias=None, \
        conn_class=None, params=None, user=None, proxy_user=None, \
        password=None, newpassword=None, wallet_password=None, \
        access_token=None, host=None, port=1521, protocol="tcp", \
        https_proxy=None, https_proxy_port=0, service_name=None, \
        instance_name=None, sid=None, server_type=None, cclass=None, \
        purity=oracledb.PURITY_DEFAULT, expire_time=0, retry_count=0, \
        retry_delay=1, tcp_connect_timeout=20.0, ssl_server_dn_match=True, \
        ssl_server_cert_dn=None, wallet_location=None, events=False, \
        externalauth=False, mode=oracledb.AUTH_MODE_DEFAULT, \
        disable_oob=False,  stmtcachesize=oracledb.defaults.stmtcachesize, \
        edition=None, tag=None, matchanytag=False, \
        config_dir=oracledb.defaults.config_dir, appcontext=[], \
        shardingkey=[], supershardingkey=[], debug_jdwp=None, \
        connection_id_prefix=None, ssl_context=None, sdu=8192, \
        pool_boundary=None, use_tcp_fast_open=False, ssl_version=None, \
        program=oracledb.defaults.program, machine=oracledb.defaults.machine, \
        terminal=oracledb.defaults.terminal, osuser=oracledb.defaults.osuser, \
        driver_name=oracledb.defaults.driver_name, use_sni=False, \
        thick_mode_dsn_passthrough=oracledb.defaults.thick_mode_dsn_passthrough, \
        extra_auth_params=None, handle=0)

    Constructor for creating a connection to the database. Returns an
    :ref:`AsyncConnection Object <asyncconnobj>`. All parameters are optional
    and can be specified as keyword parameters.  See
    :ref:`standaloneconnection` information about connections.

    This method can only be used in python-oracledb Thin mode.

    When connecting to Oracle Autonomous Database, use Python 3.11, or later.

    .. versionadded:: 2.0.0

    Some values, such as the database host name, can be specified as
    parameters, as part of the connect string, and in the params object.
    The precedence is that values in the ``dsn`` parameter override values
    passed as individual parameters, which themselves override values set in
    the ``params`` parameter object. Similar precedence rules also apply to
    other values.

    The ``dsn`` (data source name) parameter is an :ref:`Oracle Net Services
    Connection String <connstr>`.  It can also be a string in the format
    ``user/password@connect_string``.

    The ``pool`` parameter is expected to be an AsyncConnectionPool object.
    This parameter was deprecated in python-oracledb 3.0.0.  Use
    :meth:`AsyncConnectionPool.acquire()` instead since the
    use of this parameter is the equivalent of calling this method.

    The ``pool_alias`` parameter is expected to be a string which indicates the
    name of the previously created pool in the :ref:`connection pool cache
    <connpoolcache>` from which to acquire the connection. This is identical to
    calling :meth:`AsyncConnectionPool.acquire()`. When ``pool_alias`` is used,
    ``connect_async()`` supports the same parameters as
    :meth:`~AsyncConnectionPool.acquire()` and has the same behavior.

    The ``conn_class`` parameter is expected to be AsyncConnection or a
    subclass of AsyncConnection.

    The ``params`` parameter is expected to be of type :ref:`ConnectParams
    <connparam>` and contains connection parameters that will be used when
    establishing the connection. If this parameter is not specified, the
    additional keyword parameters will be used to create an instance of
    ConnectParams. If both the params parameter and additional keyword
    parameters are specified, the values in the keyword parameters have
    precedence. Note that if a ``dsn`` is also supplied, then the values of the
    parameters specified (if any) within the ``dsn`` will override the values
    passed as additional keyword parameters, which themselves override the
    values set in the ``params`` parameter object.

    The ``user`` parameter is expected to be a string which indicates the name
    of the user to connect to.

    The ``proxy_user`` parameter is expected to be a string which indicates the
    name of the proxy user to connect to. If this value is not specified, it
    will be parsed out of user if user is in the form "user[proxy_user]".

    The ``password`` parameter expected to be a string which indicates the
    password for the user.

    The ``newpassword`` parameter is expected to be a string which indicates
    the new password for the user. The new password will take effect
    immediately upon a successful connection to the database.

    The ``wallet_password`` parameter is expected to be a string which
    indicates the password to use to decrypt the PEM-encoded wallet, if it is
    encrypted.

    The ``access_token`` parameter is expected to be a string or a 2-tuple or
    a callable. If it is a string, it specifies an Azure AD OAuth2 token used
    for Open Authorization (OAuth 2.0) token based authentication. If it is a
    2-tuple, it specifies the token and private key strings used for Oracle
    Cloud Infrastructure (OCI) Identity and Access Management (IAM) token based
    authentication. If it is a callable, it returns either a string or a
    2-tuple used for OAuth 2.0 or OCI IAM token based authentication and is
    useful when the pool needs to expand and create new connections but the
    current authentication token has expired.

    The ``host`` parameter is expected to be a string which specifies the name
    or IP address of the machine hosting the listener, which handles the
    initial connection to the database.

    The ``port`` parameter is expected to be an integer which indicates the
    port number on which the listener is listening. The default value is
    *1521*.

    The ``protocol`` parameter is expected to be one of the strings *tcp* or
    *tcps* which indicates whether to use unencrypted network traffic or
    encrypted network traffic (TLS). The default value is *tcp*.

    The ``https_proxy`` parameter is expected to be a string which indicates
    the name or IP address of a proxy host to use for tunneling secure
    connections.

    The ``https_proxy_port`` parameter is expected to be an integer which
    indicates the port that is to be used to communicate with the proxy host.
    The default value is *0*.

    The ``service_name`` parameter is expected to be a string which indicates
    the service name of the database.

    The ``instance_name`` parameter is expected to be a string which indicates
    the instance name of the database.

    The ``sid`` parameter is expected to be a string which indicates the SID of
    the database. It is recommended to use ``service_name`` instead.

    The ``server_type`` parameter is expected to be a string that indicates the
    type of server connection that should be established. If specified, it
    should be one of *dedicated*, *shared*, or *pooled*.

    The ``cclass`` parameter is expected to be a string that identifies the
    connection class to use for :ref:`drcp`.

    The ``purity`` parameter is expected to be one of the
    :ref:`oracledb.PURITY_* <drcppurityconsts>` constants that identifies the
    purity to use for DRCP. The purity will internally default to
    :data:`~oracledb.PURITY_SELF` for pooled connections. For standalone
    connections, the purity will internally default to
    :data:`~oracledb.PURITY_NEW`.

    The ``expire_time`` parameter is expected to be an integer which indicates
    the number of minutes between the sending of keepalive probes. If this
    parameter is set to a value greater than zero it enables keepalive. The
    default value is *0*.

    The ``retry_count`` parameter is expected to be an integer that identifies
    the number of times that a connection attempt should be retried before the
    attempt is terminated. The default value is *0*.

    The ``retry_delay`` parameter is expected to be an integer that identifies
    the number of seconds to wait before making a new connection attempt. The
    default value is *1*.

    The ``tcp_connect_timeout`` parameter is expected to be a float that
    indicates the maximum number of seconds to wait for establishing a
    connection to the database host. The default value is *20.0*.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that
    indicates whether the server certificate distinguished name (DN) should be
    matched in addition to the regular certificate verification that is
    performed. Note that if the ``ssl_server_cert_dn`` parameter is not
    provided, host name matching is performed instead. The default value is
    *True*.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that
    indicates the distinguished name (DN) which should be matched with the
    server. This value is ignored if the ``ssl_server_dn_match`` parameter is
    not set to the value *True*.

    The ``wallet_location`` parameter is expected to be a string that
    identifies the directory where the wallet can be found. In python-oracledb
    Thin mode, this must be the directory of the PEM-encoded wallet file,
    ewallet.pem.

    The ``events`` parameter is ignored in the python-oracledb Thin mode.

    The ``externalauth`` parameter is ignored in the python-oracledb Thin mode.

    If the ``mode`` parameter is specified, it must be one of the
    :ref:`connection authorization modes <connection-authorization-modes>`
    which are defined at the module level. The default value is
    :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value has no effect on
    Windows which does not support this functionality. The default value is
    *False*.

    The ``stmtcachesize`` parameter is expected to be an integer which
    specifies the initial size of the statement cache. The default is the
    value of :attr:`defaults.stmtcachesize`.

    The ``tag`` parameter is ignored in the python-oracledb Thin mode.

    The ``matchanytag`` parameter is ignored in the python-oracledb Thin mode.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which :ref:`optional configuration files <optconfigfiles>` are
    found. The default is the value of :attr:`defaults.config_dir`.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that
    identifies the application context used by the connection. This parameter
    should contain namespace, name, and value and each entry in the tuple
    should be a string.

    The ``shardingkey`` parameter and ``supershardingkey`` parameters are
    ignored in the python-oracledb Thin mode.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL
    debugger.  This allows using the Java Debug Wire Protocol (JDWP) to debug
    PL/SQL code called by python-oracledb.

    The ``connection_id_prefix`` parameter is expected to be a string and is
    added to the beginning of the generated ``connection_id`` that is sent to
    the database for `tracing <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-B0FC69F9-2EBC-44E8-ACB2-62FBA14ABD5C>`__.

    The ``ssl_context`` parameter is expected to be an SSLContext object used
    for connecting to the database using TLS.  This SSL context will be
    modified to include the private key or any certificates found in a
    separately supplied wallet. This parameter should only be specified if
    the default SSLContext object cannot be used.

    The ``sdu`` parameter is expected to be an integer that returns the
    requested size of the Session Data Unit (SDU), in bytes. The value tunes
    internal buffers used for communication to the database. Bigger values can
    increase throughput for large queries or bulk data loads, but at the cost
    of higher memory use. The SDU size that will actually be used is negotiated
    down to the lower of this value and the database network SDU configuration
    value. See the `Database Net Services documentation <https://www.oracle.
    com/pls/topic/lookup?ctx=dblatest&id=GUID-86D61D6F-AD26-421A-BABA-
    77949C8A2B04>`__ for more details. The default value is *8192* bytes.

    The ``pool_boundary`` parameter is expected to be one of the strings
    *statement* or *transaction* which indicates when pooled :ref:`DRCP <drcp>`
    or PRCP connections can be returned to the pool.  If the value is
    *statement*, then pooled DRCP or PRCP connections are implicitly released
    back to the DRCP or PRCP pool when the connection is stateless (that is,
    there are no active cursors, active transactions, temporary tables, or
    temporary LOBs).  If the value is *transaction*, then pooled DRCP or PRCP
    connections are implicitly released back to the DRCP or PRCP pool when
    either one of the methods :meth:`AsyncConnection.commit()` or
    :meth:`AsyncConnection.rollback()` are called.  This parameter requires the
    use of DRCP or PRCP with Oracle Database 23ai (or later).  See
    :ref:`implicitconnpool` for more information.  This value is used in both
    the python-oracledb Thin and Thick modes.

    The ``use_tcp_fast_open`` parameter is expected to be a boolean which
    indicates whether to use TCP Fast Open which is an `Oracle Autonomous
    Database Serverless (ADB-S) <https://docs.oracle.com/en/cloud/paas/
    autonomous-database/serverless/adbsb/connection-tcp-fast-open.html#
    GUID-34654005-DBBA-4C49-BC6D-717F9C16A17C>`__ specific feature that can
    reduce the latency in round-trips to the database after a connection has
    been established.  This feature is only available with certain versions of
    ADB-S.  This value is used in both python-oracledb Thin and Thick modes.
    The default value is *False*.

    The ``ssl_version`` parameter is expected to be one of the constants
    *ssl.TLSVersion.TLSv1_2* or *ssl.TLSVersion.TLSv1_3* which identifies the
    TLS protocol version used.  These constants are defined in the Python
    `ssl <https://docs.python.org/3/library/ssl.html>`__ module.  This
    parameter can be specified when establishing connections with the protocol
    *tcps*.  This value is used in both python-oracledb Thin and Thick modes.
    The value *ssl.TLSVersion.TLSv1_3* requires Oracle Database 23ai.  If you
    are using python-oracledb Thick mode, Oracle Client 23ai is additionally
    required.

    The ``use_sni`` parameter is expected to be a boolean which indicates
    whether to use the TLS Server Name Indication (SNI) extension to bypass the
    second TLS negotiation that would otherwise be required. This parameter is
    used in both python-oracledb Thin and Thick modes. This parameter requires
    Oracle Database 23.7. The default value is *False*. See the `Database Net
    Services documentation
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
    GUID-E98F42D0-DC9D-4B52-9C66-6DE7EC5F64D6>`__ for more details.

    The ``program`` parameter is expected to be a string which specifies the
    name of the executable program or application connected to Oracle
    Database.  This value is only used in the python-oracledb Thin mode. The
    default is the value of :attr:`defaults.program`.

    The ``machine`` parameter is expected to be a string which specifies the
    machine name of the client connecting to Oracle Database.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.machine`.

    The ``terminal`` parameter is expected to be a string which specifies the
    terminal identifier from which the connection originates.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.terminal`.

    The ``osuser`` parameter is expected to be a string which specifies the
    operating system user that initiates the database connection.  This value
    is only used in the python-oracledb Thin mode.  The default value is the
    value of :attr:`defaults.osuser`.

    The ``driver_name`` parameter is expected to be a string which specifies
    the driver used by the client to connect to Oracle Database.  This value
    is used in both the python-oracledb Thin and Thick modes.  The default is
    the value of :attr:`defaults.driver_name`.

    The ``extra_auth_params`` parameter is expected to be a dictionary
    containing the configuration parameters necessary for Oracle Database
    authentication using :ref:`OCI <cloudnativeauthoci>` or :ref:`Azure
    <cloudnativeauthoauth>` cloud native authentication plugins.
    This value is used in both the python-oracledb Thin and Thick modes. See
    :ref:`tokenauth`.

    The ``thick_mode_dsn_passthrough`` and ``handle`` parameters are ignored in
    python-oracledb Thin mode.

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

.. function:: ConnectParams(user=None, proxy_user=None, password=None, \
        newpassword=None, wallet_password=None, access_token=None, host=None, \
        port=1521, protocol="tcp", https_proxy=None, https_proxy_port=0, \
        service_name=None, instance_name=None, sid=None, server_type=None, \
        cclass=None, purity=oracledb.PURITY_DEFAULT, expire_time=0, \
        retry_count=0, retry_delay=1, tcp_connect_timeout=20.0, \
        ssl_server_dn_match=True, ssl_server_cert_dn=None, \
        wallet_location=None, events=False, externalauth=False, \
        mode=oracledb.AUTH_MODE_DEFAULT, disable_oob=False, \
        stmtcachesize=oracledb.defaults.stmtcachesize, edition=None, \
        tag=None, matchanytag=False, config_dir=oracledb.defaults.config_dir, \
        appcontext=[], shardingkey=[], supershardingkey=[], debug_jdwp=None, \
        connection_id_prefix=None, ssl_context=None, sdu=8192, \
        pool_boundary=None, use_tcp_fast_open=False, ssl_version=None, \
        program=oracledb.defaults.program, machine=oracledb.defaults.machine, \
        terminal=oracledb.defaults.terminal, osuser=oracledb.defaults.osuser, \
        driver_name=oracledb.defaults.driver_name, use_sni=False, \
        thick_mode_dsn_passthrough=oracledb.defaults.thick_mode_dsn_passthrough, \
        extra_auth_params=None, handle=0)

    Contains all the parameters that can be used to establish a connection to
    the database.

    Creates and returns a :ref:`ConnectParams Object <connparam>`. The object
    can be passed to :meth:`oracledb.connect()`.

    All the parameters are optional.

    The ``user`` parameter is expected to be a string which indicates the name
    of the user to connect to. This value is used in both the python-oracledb
    Thin and :ref:`Thick <enablingthick>` modes.

    The ``proxy_user`` parameter is expected to be a string which indicates the
    name of the proxy user to connect to. If this value is not specified, it
    will be parsed out of user if user is in the form "user[proxy_user]". This
    value is used in both the python-oracledb Thin and Thick modes.

    The ``password`` parameter expected to be a string which indicates the
    password for the user. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``newpassword`` parameter is expected to be a string which indicates
    the new password for the user. The new password will take effect
    immediately upon a successful connection to the database. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``wallet_password`` parameter is expected to be a string which
    indicates the password to use to decrypt the PEM-encoded wallet, if it is
    encrypted. This value is only used in python-oracledb Thin mode. The
    ``wallet_password`` parameter is not needed for cwallet.sso files that are
    used in the python-oracledb Thick mode.

    The ``access_token`` parameter is expected to be a string or a 2-tuple or
    a callable. If it is a string, it specifies an Azure AD OAuth2 token used
    for Open Authorization (OAuth 2.0) token based authentication. If it is a
    2-tuple, it specifies the token and private key strings used for Oracle
    Cloud Infrastructure (OCI) Identity and Access Management (IAM) token based
    authentication. If it is a callable, it returns either a string or a
    2-tuple used for OAuth 2.0 or OCI IAM token based authentication and is
    useful when the pool needs to expand and create new connections but the
    current authentication token has expired. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``host`` parameter is expected to be a string which specifies the name
    or IP address of the machine hosting the listener, which handles the
    initial connection to the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``port`` parameter is expected to be an integer which indicates the
    port number on which the listener is listening. The default value is
    *1521*. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``protocol`` parameter is expected to be one of the strings *tcp* or
    *tcps* which indicates whether to use unencrypted network traffic or
    encrypted network traffic (TLS). The default value is *tcp*. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``https_proxy`` parameter is expected to be a string which indicates
    the name or IP address of a proxy host to use for tunneling secure
    connections. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``https_proxy_port`` parameter is expected to be an integer which
    indicates the port that is to be used to communicate with the proxy host.
    The default value is *0*. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``service_name`` parameter is expected to be a string which indicates
    the service name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``instance_name`` parameter is expected to be a string which indicates
    the instance name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``sid`` parameter is expected to be a string which indicates the SID of
    the database. It is recommended to use ``service_name`` instead. This value
    is used in both the python-oracledb Thin and Thick modes.

    The ``server_type`` parameter is expected to be a string that indicates the
    type of server connection that should be established. If specified, it
    should be one of *dedicated*, *shared*, or *pooled*. This value is used in
    both the python-oracledb Thin and Thick modes.

    The ``cclass`` parameter is expected to be a string that identifies the
    connection class to use for :ref:`drcp`. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``purity`` parameter is expected to be one of the
    :ref:`oracledb.PURITY_* <drcppurityconsts>` constants that identifies the
    purity to use for DRCP. This value is used in both the python-oracledb Thin
    and Thick modes.  The purity will internally default to
    :data:`~oracledb.PURITY_SELF` for pooled connections . For standalone
    connections, the purity will internally default to
    :data:`~oracledb.PURITY_NEW`.

    The ``expire_time`` parameter is expected to be an integer which indicates
    the number of minutes between the sending of keepalive probes. If this
    parameter is set to a value greater than zero it enables keepalive. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *0*.

    The ``retry_count`` parameter is expected to be an integer that identifies
    the number of times that a connection attempt should be retried before the
    attempt is terminated. This value is used in both the python-oracledb Thin
    and Thick modes. The default value is *0*.

    The ``retry_delay`` parameter is expected to be an integer that identifies
    the number of seconds to wait before making a new connection attempt. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *1*.

    The ``tcp_connect_timeout`` parameter is expected to be a float that
    indicates the maximum number of seconds to wait for establishing a
    connection to the database host. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is *20.0*.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that
    indicates whether the server certificate distinguished name (DN) should be
    matched in addition to the regular certificate verification that is
    performed. Note that if the ``ssl_server_cert_dn`` parameter is not
    provided, host name matching is performed instead. This value is used in
    both the python-oracledb Thin and Thick modes. The default value is *True*.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that
    indicates the distinguished name (DN) which should be matched with the
    server. This value is ignored if the ``ssl_server_dn_match`` parameter is
    not set to the value *True*. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``wallet_location`` parameter is expected to be a string that
    identifies the directory where the wallet can be found. In python-oracledb
    Thin mode, this must be the directory of the PEM-encoded wallet file,
    ewallet.pem.  In python-oracledb Thick mode, this must be the directory of
    the file, cwallet.sso. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``events`` parameter is expected to be a boolean that specifies whether
    the events mode should be enabled. This value is only used in the
    python-oracledb Thick mode. This parameter is needed for continuous
    query notification and high availability event notifications. The default
    value is *False*.

    The ``externalauth`` parameter is a boolean that specifies whether external
    authentication should be used. This value is only used in the
    python-oracledb Thick mode. The default value is *False*. For standalone
    connections, external authentication occurs when the ``user`` and
    ``password`` attributes are not used. If these attributes are not used, you
    can optionally set the ``externalauth`` attribute to *True*, which may aid
    code auditing.

    The ``mode`` parameter is expected to be an integer that identifies the
    authorization mode to use. This value is used in both the python-oracledb
    Thin and Thick modes.The default value is
    :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value is only used
    in the python-oracledb Thin mode and has no effect on Windows which
    does not support this functionality. The default value is *False*.

    The ``stmtcachesize`` parameter is expected to be an integer that
    identifies the initial size of the statement cache. This value is used in
    both the python-oracledb Thin and Thick modes. The default is the value of
    :attr:`defaults.stmtcachesize`.

    The ``edition`` parameter is expected to be a string that indicates the
    edition to use for the connection. It requires Oracle Database 11.2, or
    later. This parameter cannot be used simultaneously with the ``cclass``
    parameter.

    The ``tag`` parameter is expected to be a string that identifies the type of
    connection that should be returned from a pool. This value is only used
    in the python-oracledb Thick mode.

    The ``matchanytag`` parameter is expected to be a boolean specifying
    whether any tag can be used when acquiring a connection from the pool. This
    value is only used in the python-oracledb Thick mode when acquiring a
    connection from a pool. The default value is *False*.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which the :ref:`tnsnames.ora <optnetfiles>` configuration file
    is located.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that
    identifies the application context used by the connection. This parameter
    should contain namespace, name, and value and each entry in the tuple
    should be a string.

    The ``shardingkey`` parameter and ``supershardingkey`` parameters, if
    specified, are expected to be a sequence of values which identifies the
    database shard to connect to. The key values can be a list of strings,
    numbers, bytes, or dates.  These values are only used in the
    python-oracledb Thick mode and are ignored in the Thin mode.  See
    :ref:`connsharding`.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL
    debugger.  This allows using the Java Debug Wire Protocol (JDWP) to debug
    PL/SQL code invoked by python-oracledb. This value is only used in the
    python-oracledb Thin mode.  For python-oracledb Thick mode, set the
    ``ORA_DEBUG_JDWP`` environment variable which has the same syntax. For more
    information, see :ref:`applntracing`.

    The ``connection_id_prefix`` parameter is expected to be a string and is
    added to the beginning of the generated ``connection_id`` that is sent to
    the database for `tracing <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-B0FC69F9-2EBC-44E8-ACB2-62FBA14ABD5C>`__.  This value
    is only used in the python-oracledb Thin mode.

    The ``ssl_context`` parameter is expected to be an `SSLContext object
    <https://docs.python.org/3/library/ssl.html#ssl-contexts>`__ which is used
    for connecting to the database using TLS.  This SSL context will be
    modified to include the private key or any certificates found in a
    separately supplied wallet.  This parameter should only be specified if
    the default SSLContext object cannot be used.  This value is only used in
    the python-oracledb Thin mode.

    The ``sdu`` parameter is expected to be an integer that returns the
    requested size of the Session Data Unit (SDU), in bytes. The value tunes
    internal buffers used for communication to the database. Bigger values can
    increase throughput for large queries or bulk data loads, but at the cost
    of higher memory use. The SDU size that will actually be used is negotiated
    down to the lower of this value and the database network SDU configuration
    value. See the `Database Net Services documentation <https://www.oracle.
    com/pls/topic/lookup?ctx=dblatest&id=GUID-86D61D6F-AD26-421A-BABA-
    77949C8A2B04>`__ for more details. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is *8192* bytes.

    The ``pool_boundary`` parameter is expected to be one of the strings
    *statement* or *transaction* which indicates when pooled :ref:`DRCP <drcp>`
    or PRCP connections can be returned to the pool.  If the value is
    *statement*, then pooled DRCP or PRCP connections are implicitly released
    back to the DRCP or PRCP pool when the connection is stateless (that is,
    there are no active cursors, active transactions, temporary tables, or
    temporary LOBs).  If the value is *transaction*, then pooled DRCP or PRCP
    connections are implicitly released back to the DRCP or PRCP pool when
    either one of the methods :meth:`Connection.commit()` or
    :meth:`Connection.rollback()` are called.  This parameter requires the use
    of DRCP or PRCP with Oracle Database 23ai (or later).  See
    :ref:`implicitconnpool` for more information.  This value is used in both
    the python-oracledb Thin and Thick modes.

    The ``use_tcp_fast_open`` parameter is expected to be a boolean which
    indicates whether to use TCP Fast Open which is an `Oracle Autonomous
    Database Serverless (ADB-S) <https://docs.oracle.com/en/cloud/paas/
    autonomous-database/serverless/adbsb/connection-tcp-fast-open.html#
    GUID-34654005-DBBA-4C49-BC6D-717F9C16A17C>`__ specific feature that can
    reduce the latency in round-trips to the database after a connection has
    been established.  This feature is only available with certain versions of
    ADB-S.  This value is used in both python-oracledb Thin and Thick modes.
    The default value is *False*.

    The ``ssl_version`` parameter is expected to be one of the constants
    *ssl.TLSVersion.TLSv1_2* or *ssl.TLSVersion.TLSv1_3* which identifies the
    TLS protocol version used.  These constants are defined in the Python
    `ssl <https://docs.python.org/3/library/ssl.html>`__ module.  This
    parameter can be specified when establishing connections with the protocol
    "tcps".  This value is used in both python-oracledb Thin and Thick modes.
    The value *ssl.TLSVersion.TLSv1_3* requires Oracle Database 23ai.  If you
    are using python-oracledb Thick mode, Oracle Client 23ai is additionally
    required.

    The ``use_sni`` parameter is expected to be a boolean which indicates
    whether to use the TLS Server Name Indication (SNI) extension to bypass the
    second TLS negotiation that would otherwise be required. This parameter is
    used in both python-oracledb Thin and Thick modes. This parameter requires
    Oracle Database 23.7. The default value is *False*. See the `Database Net
    Services documentation
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
    GUID-E98F42D0-DC9D-4B52-9C66-6DE7EC5F64D6>`__ for more details.

    The ``program`` parameter is expected to be a string which specifies the
    name of the executable program or application connected to Oracle
    Database.  This value is only used in the python-oracledb Thin mode. The
    default is the value of :attr:`defaults.program`.

    The ``machine`` parameter is expected to be a string which specifies the
    machine name of the client connecting to Oracle Database.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.machine`.

    The ``terminal`` parameter is expected to be a string which specifies the
    terminal identifier from which the connection originates.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.terminal`.

    The ``osuser`` parameter is expected to be a string which specifies the
    operating system user that initiates the database connection.  This value
    is only used in the python-oracledb Thin mode.  The default value is the
    value of :attr:`defaults.osuser`.

    The ``driver_name`` parameter is expected to be a string which specifies
    the driver used by the client to connect to Oracle Database.  This value
    is used in both the python-oracledb Thin and Thick modes.  The default is
    the value of :attr:`defaults.driver_name`.

    The ``thick_mode_dsn_passthrough`` parameter is expected to be a boolean
    which indicates whether the connect string should be passed unchanged to
    the Oracle Client libraries for parsing when using python-oracledb Thick
    mode. If this parameter is set to *False* in Thick mode, connect strings
    are parsed by python-oracledb itself and a generated connect descriptor is
    sent to the Oracle Client libraries. This value is only used in the
    python-oracledb Thick mode. The default value is the value of
    :attr:`defaults.thick_mode_dsn_passthrough`. For more information, see
    :ref:`usingconfigfiles`.

    The ``extra_auth_params`` parameter is expected to be a dictionary
    containing the configuration parameters necessary for Oracle Database
    authentication using :ref:`OCI <cloudnativeauthoci>` or :ref:`Azure
    <cloudnativeauthoauth>` cloud native authentication plugins.  This value is
    used in both the python-oracledb Thin and Thick modes. See
    :ref:`tokenauth`.

    The ``handle`` parameter is expected to be an integer which represents a
    pointer to a valid service context handle. This value is only used in the
    python-oracledb Thick mode.  It should be used with extreme caution. The
    default value is *0*.

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

.. function:: create_pipeline()

    Creates a :ref:`pipeline object <pipelineobjs>` which can be used to
    process a set of operations against a database.

    .. versionadded:: 2.4.0

.. function:: create_pool(dsn=None, pool_class=oracledb.ConnectionPool, \
        pool_alias=None, params=None, min=1, max=2, increment=1, \
        connectiontype=oracledb.Connection, \
        getmode=oracledb.POOL_GETMODE_WAIT, homogeneous=True, timeout=0, \
        wait_timeout=0, max_lifetime_session=0, session_callback=None, \
        max_sessions_per_shard=0, soda_metadata_cache=False, ping_interval=60, \
        ping_timeout=5000, user=None, proxy_user=None, password=None, \
        newpassword=None, wallet_password=None, access_token=None, host=None, \
        port=1521, protocol="tcp", https_proxy=None, https_proxy_port=0, \
        service_name=None, instance_name=None, sid=None, server_type=None, \
        cclass=None, purity=oracledb.PURITY_DEFAULT, expire_time=0, \
        retry_count=0, retry_delay=1, tcp_connect_timeout=20.0, \
        ssl_server_dn_match=True, ssl_server_cert_dn=None, \
        wallet_location=None, events=False, externalauth=False, \
        mode=oracledb.AUTH_MODE_DEFAULT, disable_oob=False, \
        stmtcachesize=oracledb.defaults.stmtcachesize, edition=None, \
        tag=None, matchanytag=False, config_dir=oracledb.defaults.config_dir, \
        appcontext=[], shardingkey=[], supershardingkey=[], debug_jdwp=None, \
        connection_id_prefix=None, ssl_context=None, sdu=8192, \
        pool_boundary=None, use_tcp_fast_open=False, ssl_version=None, \
        program=oracledb.defaults.program, machine=oracledb.defaults.machine, \
        terminal=oracledb.defaults.terminal, osuser=oracledb.defaults.osuser, \
        driver_name=oracledb.defaults.driver_name, use_sni=False, \
        thick_mode_dsn_passthrough=oracledb.defaults.thick_mode_dsn_passthrough, \
        extra_auth_params=None, handle=0)

    Creates a connection pool with the supplied parameters and returns the
    :ref:`ConnectionPool object <connpool>` for the pool.  See :ref:`Connection
    pooling <connpooling>` for more information.

    This function is the equivalent of the ``cx_Oracle.SessionPool()``
    function.  The use of ``SessionPool()`` has been deprecated in
    python-oracledb.

    Not all parameters apply to both python-oracledb Thin and :ref:`Thick
    <enablingthick>` modes.

    Some values, such as the database host name, can be specified as
    parameters, as part of the connect string, and in the params object.  If a
    ``dsn`` (data source name) parameter is passed, the python-oracledb Thick
    mode will use the string to connect, otherwise a connection string is
    internally constructed from the individual parameters and params object
    values, with the individual parameters having precedence.  In
    python-oracledb's default Thin mode, a connection string is internally used
    that contains all relevant values specified.  The precedence in Thin mode
    is that values in any ``dsn`` parameter override values passed as
    individual parameters, which themselves override values set in the
    ``params`` parameter object. Similar precedence rules also apply to other
    values.

    Python-oracledb connection pools must be created, used and closed within
    the same process. Sharing pools or connections across processes has
    unpredictable behavior.  Using connection pools in multi-threaded
    architectures is supported.  Multi-process architectures that cannot be
    converted to threading may get some benefit from :ref:`drcp`.

    In python-oracledb Thick mode, connection pooling is handled by Oracle's
    `Session pooling <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-F9662FFB-EAEF-495C-96FC-49C6D1D9625C>`__ technology.
    This allows python-oracledb applications to support features like
    `Application Continuity <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-A8DD9422-2F82-42A9-9555-134296416E8F>`__.

    The ``user``, ``password``, and ``dsn`` parameters are the same as for
    :meth:`oracledb.connect()`.

    The ``pool_class`` parameter is expected to be a
    :ref:`ConnectionPool Object <connpool>` or a subclass of ConnectionPool.

    The ``pool_alias`` parameter is expected to be a string representing the
    name used to store and reference the pool in the python-oracledb connection
    pool cache. If this parameter is not specified, then the pool will not be
    added to the cache. The value of this parameter can be used with the
    :meth:`oracledb.get_pool()` and :meth:`oracledb.connect()` methods to
    access the pool.  See :ref:`connpoolcache`.

    The ``params`` parameter is expected to be of type :ref:`PoolParams
    <poolparam>` and contains parameters that are used to create the pool.
    If this parameter is not specified, the additional keyword parameters will
    be used to create an instance of PoolParams. If both the params parameter
    and additional keyword parameters are specified, the values in the keyword
    parameters have precedence. Note that if a ``dsn`` is also supplied, then
    in the python-oracledb Thin mode, the values of the parameters specified
    (if any) within the ``dsn`` will override the values passed as additional
    keyword parameters, which themselves override the values set in the
    ``params`` parameter object.

    The ``min``, ``max`` and ``increment`` parameters control pool growth
    behavior. A fixed pool size where ``min`` equals ``max`` is
    :ref:`recommended <connpoolsize>` to help prevent connection storms and to
    help overall system stability. The ``min`` parameter is the number of
    connections opened when the pool is created. The default value of the
    ``min`` parameter is *1*. The ``increment`` parameter is the number of
    connections that are opened whenever a connection request exceeds the
    number of currently open connections. The default value of the
    ``increment`` parameter is *1*.  The ``max`` parameter is the maximum number
    of connections that can be open in the connection pool. The default value
    of the ``max`` parameter is *2*.

    If the ``connectiontype`` parameter is specified, all calls to
    :meth:`ConnectionPool.acquire()` will create connection objects of that
    type, rather than the base type defined at the module level.

    The ``getmode`` parameter determines the behavior of
    :meth:`ConnectionPool.acquire()`.  One of the constants
    :data:`oracledb.POOL_GETMODE_WAIT`, :data:`oracledb.POOL_GETMODE_NOWAIT`,
    :data:`oracledb.POOL_GETMODE_FORCEGET`, or
    :data:`oracledb.POOL_GETMODE_TIMEDWAIT`. The default value is
    :data:`oracledb.POOL_GETMODE_WAIT`.

    The ``homogeneous`` parameter is a boolean that indicates whether the
    connections are homogeneous (same user) or heterogeneous (multiple
    users). The default value is *True*.

    The ``timeout`` parameter is the length of time (in seconds) that a
    connection may remain idle in the pool before it is terminated. This
    applies only when the pool has more than ``min`` connections open, allowing
    it to shrink to the specified minimum size. The default value is *0*
    seconds. A value of *0* means there is no limit.

    The ``wait_timeout`` parameter is the length of time (in milliseconds) that
    a caller should wait when acquiring a connection from the pool with
    ``getmode`` set to :data:`oracledb.POOL_GETMODE_TIMEDWAIT`. The default
    value is *0* milliseconds.

    The ``max_lifetime_session`` parameter is the length of time (in seconds)
    that a pooled connection may exist since first being created. The default
    value is *0*. A value of *0* means that there is no limit. Connections
    become candidates for termination when they are acquired or released back
    to the pool and have existed for longer than ``max_lifetime_session``
    seconds. In python-oracledb Thick mode, Oracle Client libraries 12.1 or
    later must be used and, prior to Oracle Client 21, cleanup only occurs when
    the pool is accessed.

    The ``session_callback`` parameter is a callable that is invoked when a
    connection is returned from the pool for the first time, or when the
    connection tag differs from the one requested.

    The ``max_sessions_per_shard`` parameter is the maximum number of
    connections that may be associated with a particular shard. This value is
    only used in the python-oracledb Thick mode and is ignored in the
    python-oracledb Thin mode. The default value is *0*.

    The ``soda_metadata_cache`` parameter is a boolean that indicates whether
    or not the SODA metadata cache should be enabled. This value is only used
    in the python-oracledb Thick mode and is ignored in the python-oracledb
    Thin mode. The default value is *False*.

    The ``ping_interval`` parameter is the length of time (in seconds) after
    which an unused connection in the pool will be a candidate for pinging when
    :meth:`ConnectionPool.acquire()` is called. If the ping to the database
    indicates the connection is not alive a replacement connection will be
    returned by :meth:`~ConnectionPool.acquire()`. If ``ping_interval`` is a
    negative value, then the ping functionality will be disabled. The default
    value is *60* seconds.

    The ``ping_timeout`` parameter is the maximum length of time (in
    milliseconds) that :meth:`ConnectionPool.acquire()` waits for a connection
    to respond to any internal ping to the database. If the ping does not
    respond within the specified time, then the connection is destroyed and
    :meth:`~ConnectionPool.acquire()` returns a different connection. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *5000* milliseconds.

    The ``proxy_user`` parameter is expected to be a string which indicates the
    name of the proxy user to connect to. If this value is not specified, it
    will be parsed out of user if user is in the form "user[proxy_user]". This
    value is used in both the python-oracledb Thin and Thick modes.

    The ``newpassword`` parameter is expected to be a string which indicates
    the new password for the user. The new password will take effect
    immediately upon a successful connection to the database. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``wallet_password`` parameter is expected to be a string which
    indicates the password to use to decrypt the PEM-encoded wallet, if it is
    encrypted. This value is only used in python-oracledb Thin mode. The
    ``wallet_password`` parameter is not needed for cwallet.sso files that are
    used in the python-oracledb Thick mode.

    The ``access_token`` parameter is expected to be a string or a 2-tuple or
    a callable. If it is a string, it specifies an Azure AD OAuth2 token used
    for Open Authorization (OAuth 2.0) token based authentication. If it is a
    2-tuple, it specifies the token and private key strings used for Oracle
    Cloud Infrastructure (OCI) Identity and Access Management (IAM) token based
    authentication. If it is a callable, it returns either a string or a
    2-tuple used for OAuth 2.0 or OCI IAM token based authentication and is
    useful when the pool needs to expand and create new connections but the
    current authentication token has expired. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``host`` parameter is expected to be a string which specifies the name
    or IP address of the machine hosting the listener, which handles the
    initial connection to the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``port`` parameter is expected to be an integer which indicates the
    port number on which the listener is listening. The default value is
    *1521*. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``protocol`` parameter is expected to be one of the strings *tcp* or
    *tcps* which indicates whether to use unencrypted network traffic or
    encrypted network traffic (TLS). The default value is *tcp*. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``https_proxy`` parameter is expected to be a string which indicates
    the name or IP address of a proxy host to use for tunneling secure
    connections. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``https_proxy_port`` parameter is expected to be an integer which
    indicates the port that is to be used to communicate with the proxy host.
    The default value is *0*. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``service_name`` parameter is expected to be a string which indicates
    the service name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``instance_name`` parameter is expected to be a string which indicates
    the instance name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``sid`` parameter is expected to be a string which indicates the SID of
    the database. It is recommended to use ``service_name`` instead. This value
    is used in both the python-oracledb Thin and Thick modes.

    The ``server_type`` parameter is expected to be a string that indicates the
    type of server connection that should be established. If specified, it
    should be one of *dedicated*, *shared*, or *pooled*. This value is used in
    both the python-oracledb Thin and Thick modes.

    The ``cclass`` parameter is expected to be a string that identifies the
    connection class to use for :ref:`drcp`. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``purity`` parameter is expected to be one of the
    :ref:`oracledb.PURITY_* <drcppurityconsts>` constants that identifies the
    purity to use for DRCP. This value is used in both the python-oracledb Thin
    and Thick modes.  The purity will internally default to
    :data:`~oracledb.PURITY_SELF` for pooled connections.

    The ``expire_time`` parameter is expected to be an integer which indicates
    the number of minutes between the sending of keepalive probes. If this
    parameter is set to a value greater than zero it enables keepalive. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *0* minutes.

    The ``retry_count`` parameter is expected to be an integer that identifies
    the number of times that a connection attempt should be retried before the
    attempt is terminated. This value is used in both the python-oracledb Thin
    and Thick modes. The default value is *0*.

    The ``retry_delay`` parameter is expected to be an integer that identifies
    the number of seconds to wait before making a new connection attempt. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *1* seconds.

    The ``tcp_connect_timeout`` parameter is expected to be a float that
    indicates the maximum number of seconds to wait for establishing a
    connection to the database host. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is *20.0* seconds.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that
    indicates whether the server certificate distinguished name (DN) should be
    matched in addition to the regular certificate verification that is
    performed. Note that if the ``ssl_server_cert_dn`` parameter is not
    provided, host name matching is performed instead. This value is used in
    both the python-oracledb Thin and Thick modes. The default value is *True*.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that
    indicates the distinguished name (DN) which should be matched with the
    server. This value is ignored if the ``ssl_server_dn_match`` parameter is
    not set to the value *True*. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``wallet_location`` parameter is expected to be a string that
    identifies the directory where the wallet can be found. In python-oracledb
    Thin mode, this must be the directory of the PEM-encoded wallet file,
    ewallet.pem.  In python-oracledb Thick mode, this must be the directory of
    the file, cwallet.sso. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``events`` parameter is expected to be a boolean that specifies whether
    the events mode should be enabled. This value is only used in the
    python-oracledb Thick mode and is ignored in the Thin mode. This parameter
    is needed for continuous query notification and high availability event
    notifications. The default value is *False*.

    The ``externalauth`` parameter is a boolean that determines whether to use
    external authentication. This value is only used in python-oracledb Thick
    mode and is ignored in Thin mode. The default value is *False*. For pooled
    connections in Thick mode, external authentication requires the use of a
    heterogeneous pool. For this reason, you must set the ``homogeneous``
    parameter to *False*. See :ref:`extauth`.

    If the ``mode`` parameter is specified, it must be one of the
    :ref:`connection authorization modes <connection-authorization-modes>`
    which are defined at the module level. This value is used in both the
    python-oracledb Thin and Thick modes.The default value is
    :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value is only used
    in the python-oracledb Thin mode and has no effect on Windows which
    does not support this functionality. The default value is *False*.

    The ``stmtcachesize`` parameter is expected to be an integer which
    specifies the initial size of the statement cache. This value is used in
    both the python-oracledb Thin and Thick modes. The default is the value of
    :attr:`defaults.stmtcachesize`.

    The ``edition`` parameter is expected to be a string that indicates the
    edition to use for the connection. It requires Oracle Database 11.2, or
    later. This parameter cannot be used simultaneously with the ``cclass``
    parameter.

    The ``tag`` parameter is expected to be a string that identifies the type
    of connection that should be returned from a pool. This value is only used
    in the python-oracledb Thick mode and is ignored in the Thin mode.

    The ``matchanytag`` parameter is expected to be a boolean specifying
    whether any tag can be used when acquiring a connection from the pool. This
    value is only used in the python-oracledb Thick mode when acquiring a
    connection from a pool. This value is ignored in the python-oracledb Thin
    mode.  The default value is *False*.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which the :ref:`tnsnames.ora <optnetfiles>` configuration file
    is located. The default is the value of :attr:`defaults.config_dir`.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that
    identifies the application context used by the connection. This parameter
    should contain namespace, name, and value and each entry in the tuple
    should be a string.

    The ``shardingkey`` parameter and ``supershardingkey`` parameters, if
    specified, are expected to be a sequence of values which identifies the
    database shard to connect to. The key values can be a list of strings,
    numbers, bytes, or dates.  These values are only used in the
    python-oracledb Thick mode and are ignored in the Thin mode.  See
    :ref:`connsharding`.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL
    debugger.  This allows using the Java Debug Wire Protocol (JDWP) to debug
    PL/SQL code invoked by python-oracledb. This value is only used in the
    python-oracledb Thin mode.  For python-oracledb Thick mode, set the
    ``ORA_DEBUG_JDWP`` environment variable which has the same syntax. For more
    information, see :ref:`applntracing`.

    The ``connection_id_prefix`` parameter is expected to be a string and is
    added to the beginning of the generated ``connection_id`` that is sent to
    the database for `tracing <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-B0FC69F9-2EBC-44E8-ACB2-62FBA14ABD5C>`__.  This value
    is only used in the python-oracledb Thin mode.

    The ``ssl_context`` parameter is expected to be an `SSLContext object
    <https://docs.python.org/3/library/ssl.html#ssl-contexts>`__ which is used
    for connecting to the database using TLS.  This SSL context will be
    modified to include the private key or any certificates found in a
    separately supplied wallet.  This parameter should only be specified if
    the default SSLContext object cannot be used.  This value is only used in
    the python-oracledb Thin mode.

    The ``sdu`` parameter is expected to be an integer that returns the
    requested size of the Session Data Unit (SDU), in bytes. The value tunes
    internal buffers used for communication to the database. Bigger values can
    increase throughput for large queries or bulk data loads, but at the cost
    of higher memory use. The SDU size that will actually be used is negotiated
    down to the lower of this value and the database network SDU configuration
    value. See the `Database Net Services documentation <https://www.oracle.
    com/pls/topic/lookup?ctx=dblatest&id=GUID-86D61D6F-AD26-421A-BABA-
    77949C8A2B04>`__ for more details. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is *8192* bytes.

    The ``pool_boundary`` parameter is expected to be one of the strings
    *statement* or *transaction* which indicates when pooled :ref:`DRCP <drcp>`
    or PRCP connections can be returned to the pool.  If the value is
    *statement*, then pooled DRCP or PRCP connections are implicitly released
    back to the DRCP or PRCP pool when the connection is stateless (that is,
    there are no active cursors, active transactions, temporary tables, or
    temporary LOBs).  If the value is *transaction*, then pooled DRCP or PRCP
    connections are implicitly released back to the DRCP or PRCP pool when
    either one of the methods :meth:`Connection.commit()` or
    :meth:`Connection.rollback()` are called.  This parameter requires the use
    of DRCP or PRCP with Oracle Database 23ai (or later).  See
    :ref:`implicitconnpool` for more information.  This value is used in both
    the python-oracledb Thin and Thick modes.

    The ``use_tcp_fast_open`` parameter is expected to be a boolean which
    indicates whether to use TCP Fast Open which is an `Oracle Autonomous
    Database Serverless (ADB-S) <https://docs.oracle.com/en/cloud/paas/
    autonomous-database/serverless/adbsb/connection-tcp-fast-open.html#
    GUID-34654005-DBBA-4C49-BC6D-717F9C16A17C>`__ specific feature that can
    reduce the latency in round-trips to the database after a connection has
    been established.  This feature is only available with certain versions of
    ADB-S.  This value is used in both python-oracledb Thin and Thick modes.
    The default value is *False*.

    The ``ssl_version`` parameter is expected to be one of the constants
    *ssl.TLSVersion.TLSv1_2* or *ssl.TLSVersion.TLSv1_3* which identifies the
    TLS protocol version used.  These constants are defined in the Python
    `ssl <https://docs.python.org/3/library/ssl.html>`__ module.  This
    parameter can be specified when establishing connections with the protocol
    "tcps".  This value is used in both python-oracledb Thin and Thick modes.
    The value *ssl.TLSVersion.TLSv1_3* requires Oracle Database 23ai.  If you
    are using python-oracledb Thick mode, Oracle Client 23ai is additionally
    required.

    The ``use_sni`` parameter is expected to be a boolean which indicates
    whether to use the TLS Server Name Indication (SNI) extension to bypass the
    second TLS negotiation that would otherwise be required. This parameter is
    used in both python-oracledb Thin and Thick modes. This parameter requires
    Oracle Database 23.7. The default value is *False*. See the `Database Net
    Services documentation
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
    GUID-E98F42D0-DC9D-4B52-9C66-6DE7EC5F64D6>`__ for more details.

    The ``program`` parameter is expected to be a string which specifies the
    name of the executable program or application connected to Oracle
    Database.  This value is only used in the python-oracledb Thin mode. The
    default is the value of :attr:`defaults.program`.

    The ``machine`` parameter is expected to be a string which specifies the
    machine name of the client connecting to Oracle Database.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.machine`.

    The ``terminal`` parameter is expected to be a string which specifies the
    terminal identifier from which the connection originates.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.terminal`.

    The ``osuser`` parameter is expected to be a string which specifies the
    operating system user that initiates the database connection.  This value
    is only used in the python-oracledb Thin mode.  The default value is the
    value of :attr:`defaults.osuser`.

    The ``driver_name`` parameter is expected to be a string which specifies
    the driver used by the client to connect to Oracle Database.  This value
    is used in both the python-oracledb Thin and Thick modes.  The default is
    the value of :attr:`defaults.driver_name`.

    The ``thick_mode_dsn_passthrough`` parameter is expected to be a boolean
    which indicates whether the connect string should be passed unchanged to
    the Oracle Client libraries for parsing when using python-oracledb Thick
    mode. If this parameter is set to *False* in Thick mode, connect strings
    are parsed by python-oracledb itself and a generated connect descriptor is
    sent to the Oracle Client libraries. This value is only used in the
    python-oracledb Thick mode. The default value is
    :attr:`defaults.thick_mode_dsn_passthrough`. For more information, see
    :ref:`usingconfigfiles`.

    The ``extra_auth_params`` parameter is expected to be a dictionary
    containing the configuration parameters necessary for Oracle Database
    authentication using :ref:`OCI <cloudnativeauthoci>` or :ref:`Azure
    <cloudnativeauthoauth>` cloud native authentication plugins.  This value is
    used in both the python-oracledb Thin and Thick modes. See
    :ref:`tokenauth`.

    If the ``handle`` parameter is specified, it must be of type OCISvcCtx\*
    and is only of use when embedding Python in an application (like
    PowerBuilder) which has already made the connection. The connection thus
    created should *never* be used after the source handle has been closed or
    destroyed. This value is only used in the python-oracledb Thick mode and
    is ignored in the Thin mode. It should be used with extreme caution. The
    default value is *0*.

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

.. function:: create_pool_async(dsn=None, \
        pool_class=oracledb.AsyncConnectionPool, pool_alias=None, \
        params=None, min=1, max=2, increment=1, \
        connectiontype=oracledb.AsyncConnection, \
        getmode=oracledb.POOL_GETMODE_WAIT, homogeneous=True, timeout=0, \
        wait_timeout=0, max_lifetime_session=0, session_callback=None, \
        max_sessions_per_shard=0, soda_metadata_cache=False, ping_interval=60, \
        ping_timeout=5000, user=None, proxy_user=None, password=None, \
        newpassword=None, wallet_password=None, access_token=None, host=None, \
        port=1521, protocol="tcp", https_proxy=None, https_proxy_port=0, \
        service_name=None, instance_name=None, sid=None, server_type=None, \
        cclass=None, purity=oracledb.PURITY_DEFAULT, expire_time=0, \
        retry_count=0, retry_delay=1, tcp_connect_timeout=20.0, \
        ssl_server_dn_match=True, ssl_server_cert_dn=None, \
        wallet_location=None, events=False, externalauth=False, \
        mode=oracledb.AUTH_MODE_DEFAULT, disable_oob=False, \
        stmtcachesize=oracledb.defaults.stmtcachesize, edition=None, \
        tag=None, matchanytag=False, config_dir=oracledb.defaults.config_dir, \
        appcontext=[], shardingkey=[], supershardingkey=[], debug_jdwp=None, \
        connection_id_prefix=None, ssl_context=None, sdu=8192, \
        pool_boundary=None, use_tcp_fast_open=False, ssl_version=None, \
        program=oracledb.defaults.program, machine=oracledb.defaults.machine, \
        terminal=oracledb.defaults.terminal, osuser=oracledb.defaults.osuser, \
        driver_name=oracledb.defaults.driver_name, use_sni=False, \
        thick_mode_dsn_passthrough=oracledb.defaults.thick_mode_dsn_passthrough, \
        extra_auth_params=None, handle=0)

    Creates a connection pool with the supplied parameters and returns the
    :ref:`AsyncConnectionPool object <asyncconnpoolobj>` for the pool.
    ``create_pool_async()`` is a synchronous method. See
    :ref:`Connection pooling <asyncconnpool>` for more information.

    This method can only be used in python-oracledb Thin mode.

    When connecting to Oracle Autonomous Database, use Python 3.11, or later.

    .. versionadded:: 2.0.0

    Some values, such as the database host name, can be specified as
    parameters, as part of the connect string, and in the params object.
    The precedence is that values in the ``dsn`` parameter override values
    passed as individual parameters, which themselves override values set in
    the ``params`` parameter object. Similar precedence rules also apply to
    other values.

    The ``user``, ``password``, and ``dsn`` parameters are the same as for
    :meth:`oracledb.connect()`.

    The ``pool_class`` parameter is expected to be an
    :ref:`AsyncConnectionPool Object <asyncconnpoolobj>` or a subclass of
    AsyncConnectionPool.

    The ``pool_alias`` parameter is expected to be a string representing the
    name used to store and reference the pool in the python-oracledb connection
    pool cache. If this parameter is not specified, then the pool will not be
    added to the cache. The value of this parameter can be used with the
    :meth:`oracledb.get_pool()` and :meth:`oracledb.connect_async()` methods to
    access the pool.  See :ref:`connpoolcache`.

    The ``params`` parameter is expected to be of type :ref:`PoolParams
    <poolparam>` and contains parameters that are used to create the pool.
    If this parameter is not specified, the additional keyword parameters will
    be used to create an instance of PoolParams. If both the params parameter
    and additional keyword parameters are specified, the values in the keyword
    parameters have precedence. Note that if a ``dsn`` is also supplied, then
    the values of the parameters specified (if any) within the ``dsn`` will
    override the values passed as additional keyword parameters, which
    themselves override the values set in the ``params`` parameter object.

    The ``min``, ``max`` and ``increment`` parameters control pool growth
    behavior. A fixed pool size where ``min`` equals ``max`` is
    :ref:`recommended <connpoolsize>` to help prevent connection storms and to
    help overall system stability. The ``min`` parameter is the number of
    connections opened when the pool is created. The default value of the
    ``min`` parameter is *1*. The ``increment`` parameter is the number of
    connections that are opened whenever a connection request exceeds the
    number of currently open connections. The default value of the
    ``increment`` parameter is *1*.  The ``max`` parameter is the maximum number
    of connections that can be open in the connection pool. The default value
    of the ``max`` parameter is *2*.

    If the ``connectiontype`` parameter is specified, all calls to
    :meth:`AsyncConnectionPool.acquire()` will create connection objects of
    that type, rather than the base type defined at the module level.

    The ``getmode`` parameter determines the behavior of
    :meth:`AsyncConnectionPool.acquire()`.  One of the constants
    :data:`oracledb.POOL_GETMODE_WAIT`, :data:`oracledb.POOL_GETMODE_NOWAIT`,
    :data:`oracledb.POOL_GETMODE_FORCEGET`, or
    :data:`oracledb.POOL_GETMODE_TIMEDWAIT`. The default value is
    :data:`oracledb.POOL_GETMODE_WAIT`.

    The ``homogeneous`` parameter is a boolean that indicates whether the
    connections are homogeneous (same user) or heterogeneous (multiple
    users). The default value is *True*.

    The ``timeout`` parameter is the length of time (in seconds) that a
    connection may remain idle in the pool before it is terminated. This
    applies only when the pool has more than ``min`` connections open, allowing
    it to shrink to the specified minimum size. The default value is *0*
    seconds. A value of *0* means there is no limit.

    The ``wait_timeout`` parameter is the length of time (in milliseconds) that
    a caller should wait when acquiring a connection from the pool with
    ``getmode`` set to :data:`oracledb.POOL_GETMODE_TIMEDWAIT`. The default
    value is *0* milliseconds.

    The ``max_lifetime_session`` parameter is the length of time (in seconds)
    that a pooled connection may exist since first being created. The default
    value is *0*. A value of *0* means that there is no limit. Connections
    become candidates for termination when they are acquired or released back
    to the pool and have existed for longer than ``max_lifetime_session``
    seconds. In python-oracledb Thick mode, Oracle Client libraries 12.1 or
    later must be used and, prior to Oracle Client 21, cleanup only occurs when
    the pool is accessed.

    The ``session_callback`` parameter is a callable that is invoked when a
    connection is returned from the pool for the first time, or when the
    connection tag differs from the one requested.

    The ``max_sessions_per_shard`` parameter is ignored in the python-oracledb
    Thin mode.

    The ``soda_metadata_cache`` parameter is ignored in the python-oracledb
    Thin mode.

    The ``ping_interval`` parameter is the length of time (in seconds) after
    which an unused connection in the pool will be a candidate for pinging when
    :meth:`AsyncConnectionPool.acquire()` is called. If the ping to the
    database indicates the connection is not alive a replacement connection
    will be returned by :meth:`~AsyncConnectionPool.acquire()`. If
    ``ping_interval`` is a negative value, then the ping functionality will be
    disabled. The default value is *60* seconds.

    The ``ping_timeout`` parameter is the maximum length of time (in
    milliseconds) that :meth:`AsyncConnectionPool.acquire()` waits for a
    connection to respond to any internal ping to the database. If the ping
    does not respond within the specified time, then the connection is
    destroyed and :meth:`~AsyncConnectionPool.acquire()` returns a different
    connection. This value is used in both the python-oracledb Thin and Thick
    modes. The default value is *5000* milliseconds.

    The ``proxy_user`` parameter is expected to be a string which indicates the
    name of the proxy user to connect to. If this value is not specified, it
    will be parsed out of user if user is in the form "user[proxy_user]".

    The ``newpassword`` parameter is expected to be a string which indicates
    the new password for the user. The new password will take effect
    immediately upon a successful connection to the database.

    The ``wallet_password`` parameter is expected to be a string which
    indicates the password to use to decrypt the PEM-encoded wallet, if it is
    encrypted.

    The ``access_token`` parameter is expected to be a string or a 2-tuple or
    a callable. If it is a string, it specifies an Azure AD OAuth2 token used
    for Open Authorization (OAuth 2.0) token based authentication. If it is a
    2-tuple, it specifies the token and private key strings used for Oracle
    Cloud Infrastructure (OCI) Identity and Access Management (IAM) token based
    authentication. If it is a callable, it returns either a string or a
    2-tuple used for OAuth 2.0 or OCI IAM token based authentication and is
    useful when the pool needs to expand and create new connections but the
    current authentication token has expired.

    The ``host`` parameter is expected to be a string which specifies the name
    or IP address of the machine hosting the listener, which handles the
    initial connection to the database.

    The ``port`` parameter is expected to be an integer which indicates the
    port number on which the listener is listening. The default value is
    *1521*.

    The ``protocol`` parameter is expected to be one of the strings *tcp* or
    *tcps* which indicates whether to use unencrypted network traffic or
    encrypted network traffic (TLS). The default value is *tcp*.

    The ``https_proxy`` parameter is expected to be a string which indicates
    the name or IP address of a proxy host to use for tunneling secure
    connections.

    The ``https_proxy_port`` parameter is expected to be an integer which
    indicates the port that is to be used to communicate with the proxy host.
    The default value is *0*.

    The ``service_name`` parameter is expected to be a string which indicates
    the service name of the database.

    The ``instance_name`` parameter is expected to be a string which indicates
    the instance name of the database.

    The ``sid`` parameter is expected to be a string which indicates the SID of
    the database. It is recommended to use ``service_name`` instead.

    The ``server_type`` parameter is expected to be a string that indicates the
    type of server connection that should be established. If specified, it
    should be one of *dedicated*, *shared*, or *pooled*.

    The ``cclass`` parameter is expected to be a string that identifies the
    connection class to use for :ref:`drcp`.

    The ``purity`` parameter is expected to be one of the
    :ref:`oracledb.PURITY_* <drcppurityconsts>` constants that identifies the
    purity to use for DRCP. The purity will internally default to
    :data:`~oracledb.PURITY_SELF` for pooled connections.

    The ``expire_time`` parameter is expected to be an integer which indicates
    the number of minutes between the sending of keepalive probes. If this
    parameter is set to a value greater than zero it enables keepalive. The
    default value is *0* minutes.

    The ``retry_count`` parameter is expected to be an integer that identifies
    the number of times that a connection attempt should be retried before the
    attempt is terminated. The default value is *0*.

    The ``retry_delay`` parameter is expected to be an integer that identifies
    the number of seconds to wait before making a new connection attempt. The
    default value is *1* seconds.

    The ``tcp_connect_timeout`` parameter is expected to be a float that
    indicates the maximum number of seconds to wait for establishing a
    connection to the database host. The default value is *20.0* seconds.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that
    indicates whether the server certificate distinguished name (DN) should be
    matched in addition to the regular certificate verification that is
    performed. Note that if the ``ssl_server_cert_dn`` parameter is not
    provided, host name matching is performed instead. The default value is
    *True*.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that
    indicates the distinguished name (DN) which should be matched with the
    server. This value is ignored if the ``ssl_server_dn_match`` parameter is
    not set to the value *True*.

    The ``wallet_location`` parameter is expected to be a string that
    identifies the directory where the wallet can be found. In python-oracledb
    Thin mode, this must be the directory of the PEM-encoded wallet file,
    ewallet.pem.

    The ``events`` parameter is ignored in the python-oracledb Thin mode.

    The ``externalauth`` parameter is ignored in the python-oracledb Thin mode.

    If the ``mode`` parameter is specified, it must be one of the
    :ref:`connection authorization modes <connection-authorization-modes>`
    which are defined at the module level. The default value is
    :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value has no effect
    on Windows which does not support this functionality. The default value
    is *False*.

    The ``stmtcachesize`` parameter is expected to be an integer which
    specifies the initial size of the statement cache. The default is the
    value of :attr:`defaults.stmtcachesize`.

    The ``tag`` parameter is ignored in the python-oracledb Thin mode.

    The ``matchanytag`` parameter is ignored in the python-oracledb Thin mode.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which the :ref:`tnsnames.ora <optnetfiles>` configuration file
    is located.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that
    identifies the application context used by the connection. This parameter
    should contain namespace, name, and value and each entry in the tuple
    should be a string.

    The ``shardingkey`` parameter and ``supershardingkey`` parameters are
    ignored in the python-oracledb Thin mode.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL
    debugger.  This allows using the Java Debug Wire Protocol (JDWP) to debug
    PL/SQL code invoked by python-oracledb.

    The ``connection_id_prefix`` parameter is expected to be a string and is
    added to the beginning of the generated ``connection_id`` that is sent to
    the database for `tracing <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-B0FC69F9-2EBC-44E8-ACB2-62FBA14ABD5C>`__.

    The ``ssl_context`` parameter is expected to be an SSLContext object used
    for connecting to the database using TLS.  This SSL context will be
    modified to include the private key or any certificates found in a
    separately supplied wallet. This parameter should only be specified if
    the default SSLContext object cannot be used.

    The ``sdu`` parameter is expected to be an integer that returns the
    requested size of the Session Data Unit (SDU), in bytes. The value tunes
    internal buffers used for communication to the database. Bigger values can
    increase throughput for large queries or bulk data loads, but at the cost
    of higher memory use. The SDU size that will actually be used is negotiated
    down to the lower of this value and the database network SDU configuration
    value. See the `Database Net Services documentation <https://www.oracle.
    com/pls/topic/lookup?ctx=dblatest&id=GUID-86D61D6F-AD26-421A-BABA-
    77949C8A2B04>`__ for more details. The default value is *8192* bytes.

    The ``pool_boundary`` parameter is expected to be one of the strings
    *statement* or *transaction* which indicates when pooled :ref:`DRCP <drcp>`
    or PRCP connections can be returned to the pool.  If the value is
    *statement*, then pooled DRCP or PRCP connections are implicitly released
    back to the DRCP or PRCP pool when the connection is stateless (that is,
    there are no active cursors, active transactions, temporary tables, or
    temporary LOBs).  If the value is *transaction*, then pooled DRCP or PRCP
    connections are implicitly released back to the DRCP or PRCP pool when
    either one of the methods :meth:`AsyncConnection.commit()` or
    :meth:`AsyncConnection.rollback()` are called.  This parameter requires the
    use of DRCP or PRCP with Oracle Database 23ai (or later).  See
    :ref:`implicitconnpool` for more information.  This value is used in both
    the python-oracledb Thin and Thick modes.

    The ``use_tcp_fast_open`` parameter is expected to be a boolean which
    indicates whether to use TCP Fast Open which is an `Oracle Autonomous
    Database Serverless (ADB-S) <https://docs.oracle.com/en/cloud/paas/
    autonomous-database/serverless/adbsb/connection-tcp-fast-open.html#
    GUID-34654005-DBBA-4C49-BC6D-717F9C16A17C>`__ specific feature that can
    reduce the latency in round-trips to the database after a connection has
    been established.  This feature is only available with certain versions of
    ADB-S.  This value is used in both python-oracledb Thin and Thick modes.
    The default value is *False*.

    The ``ssl_version`` parameter is expected to be one of the constants
    *ssl.TLSVersion.TLSv1_2* or *ssl.TLSVersion.TLSv1_3* which identifies the
    TLS protocol version used.  These constants are defined in the Python
    `ssl <https://docs.python.org/3/library/ssl.html>`__ module.  This
    parameter can be specified when establishing connections with the protocol
    *tcps*.  This value is used in both python-oracledb Thin and Thick modes.
    The value *ssl.TLSVersion.TLSv1_3* requires Oracle Database 23ai.  If you
    are using python-oracledb Thick mode, Oracle Client 23ai is additionally
    required.

    The ``use_sni`` parameter is expected to be a boolean which indicates
    whether to use the TLS Server Name Indication (SNI) extension to bypass the
    second TLS negotiation that would otherwise be required. This parameter is
    used in both python-oracledb Thin and Thick modes. This parameter requires
    Oracle Database 23.7. The default value is *False*. See the `Database Net
    Services documentation
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
    GUID-E98F42D0-DC9D-4B52-9C66-6DE7EC5F64D6>`__ for more details.

    The ``program`` parameter is expected to be a string which specifies the
    name of the executable program or application connected to Oracle
    Database.  This value is only used in the python-oracledb Thin mode. The
    default is the value of :attr:`defaults.program`.

    The ``machine`` parameter is expected to be a string which specifies the
    machine name of the client connecting to Oracle Database.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.machine`.

    The ``terminal`` parameter is expected to be a string which specifies the
    terminal identifier from which the connection originates.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.terminal`.

    The ``osuser`` parameter is expected to be a string which specifies the
    operating system user that initiates the database connection.  This value
    is only used in the python-oracledb Thin mode.  The default value is the
    value of :attr:`defaults.osuser`.

    The ``driver_name`` parameter is expected to be a string which specifies
    the driver used by the client to connect to Oracle Database.  This value
    is used in both the python-oracledb Thin and Thick modes.  The default is
    the value of :attr:`defaults.driver_name`.

    The ``extra_auth_params`` parameter is expected to be a dictionary
    containing the configuration parameters necessary for Oracle Database
    authentication using :ref:`OCI <cloudnativeauthoci>` or :ref:`Azure
    <cloudnativeauthoauth>` cloud native authentication plugins.  This value is
    used in both the python-oracledb Thin and Thick modes. See
    :ref:`tokenauth`.

    The ``handle`` and ``thick_mode_dsn_passthrough`` parameters are ignored in
    python-oracledb Thin mode.

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

.. function:: Cursor(connection)

    Constructor for creating a cursor.  Returns a new
    :ref:`cursor object <cursorobj>` using the connection.

    .. dbapimethodextension::

.. function:: Date(year, month, day)

    Constructs an object holding a date value.


.. function:: DateFromTicks(ticks)

    Constructs an object holding a date value from the given ticks value
    (number of seconds since the epoch; see the documentation of the standard
    Python time module for details).


.. function:: enable_thin_mode()

    Makes python-oracledb be in Thin mode. After this method is called, Thick
    mode cannot be enabled. If python-oracledb is already in Thick mode, then
    calling ``enable_thin_mode()`` will fail. If Thin mode connections have
    already been opened, or a connection pool created in Thin mode, then
    calling ``enable_thin_mode()`` is a no-op.

    Since python-oracledb defaults to Thin mode, almost all applications do not
    need to call this method. However, because it bypasses python-oracledb's
    internal mode-determination heuristic, it may be useful for applications
    with multiple threads that concurrently create :ref:`standalone connections
    <standaloneconnection>` when the application starts.

    See :ref:`enablingthin` for more information.

    .. versionadded:: 2.5.0

.. function:: get_pool(pool_alias)

    Returns a :ref:`ConnectionPool object <connpool>` from the python-oracledb
    pool cache. The pool must have been previously created by passing the same
    ``pool_alias`` value to :meth:`oracledb.create_pool()` or
    :meth:`oracledb.create_pool_async()`.

    If a pool with the given name does not exist, *None* is returned.

    See :ref:`connpoolcache` for more information.

    .. versionadded:: 3.0.0

.. function:: init_oracle_client(lib_dir=None, config_dir=None, \
        error_url=None, driver_name=None)

    Enables python-oracledb Thick mode by initializing the Oracle Client
    library, see :ref:`enablingthick`. If a standalone connection or pool has
    already been created in Thin mode, ``init_oracle_client()`` will raise an
    exception and python-oracledb will remain in Thin mode.

    If a standalone connection or pool has *not* already been created in Thin
    mode, but ``init_oracle_client()`` raises an exception, python-oracledb
    will remain in Thin mode but further calls to ``init_oracle_client()`` can
    be made, if desired.

    The ``init_oracle_client()`` method can be called multiple times in each
    Python process as long as the arguments are the same each time.

    The ``lib_dir`` parameter is a string or a bytes object that specifies the
    directory containing Oracle Client libraries.  If the ``lib_dir`` parameter
    is set, then the specified directory is the only one searched for the
    Oracle Client libraries; otherwise, the operating system library search
    path is used to locate the Oracle Client library.  If you are using Python
    3.11 and later, then the value specified in this parameter is encoded
    using `locale.getencoding() <https://docs.python.org/3/library/locale.html
    #locale.getencoding>`__.  For all other Python versions, the encoding
    "utf-8" is used.  If a bytes object is specified in this parameter, then
    this value will be used as is without any encoding.

    The ``config_dir`` parameter is a string or a bytes object that specifies
    the directory in which the
    :ref:`Optional Oracle Net Configuration <optnetfiles>` and
    :ref:`Optional Oracle Client Configuration <optclientfiles>` files reside.
    If the ``config_dir`` parameter is set, then the specified directory is
    used to find Oracle Client library configuration files.  This is
    equivalent to setting the environment variable ``TNS_ADMIN`` and overrides
    any value already set in ``TNS_ADMIN``.  If this parameter is not set, the
    :ref:`Oracle standard <usingconfigfiles>` way of locating Oracle Client
    library configuration files is used.  If you are using Python 3.11 and
    later, then the value specified in this parameter is encoded using
    `locale.getencoding() <https://docs.python.org/3/library/locale.html#
    locale.getencoding>`__.  For all other Python versions, the encoding
    "utf-8" is used.  If a bytes object is specified in this parameter, then
    this value will be used as is without any encoding.

    The ``error_url`` parameter is a string that specifies the URL which is
    included in the python-oracledb exception message if the Oracle Client
    libraries cannot be loaded.  If the ``error_url`` parameter is set, then
    the specified value is included in the message of the exception raised
    when the Oracle Client library cannot be loaded; otherwise, the
    :ref:`installation` URL is included.  This parameter lets your application
    display custom installation instructions.

    The ``driver_name`` parameter is a string that specifies the driver name
    value. If the ``driver_name`` parameter is set, then the specified value
    can be found in database views that give information about connections.
    For example, it is in the CLIENT_DRIVER column of the
    V$SESSION_CONNECT_INFO view. From Oracle Database 12.2, the name displayed
    can be 30 characters.  The standard is to set this value to ``"<name> :
    version>"``, where <name> is the name of the driver and <version> is its
    version. There should be a single space character before and after the
    colon. If this parameter is not set, then the value specified in
    :attr:`oracledb.defaults.driver_name <defaults.driver_name>` is used. If
    the value of this attribute is *None*, then the default value in
    python-oracledb Thick mode is like "python-oracledb thk : <version>". See
    :ref:`otherinit`.

    At successful completion of a call to ``oracledb.init_oracle_client()``,
    the attribute :attr:`defaults.config_dir` will be set as determined below
    (first one wins):

    - the value of the ``oracledb.init_oracle_client()`` parameter
      ``config_dir``, if one was passed.

    - the value of :attr:`defaults.config_dir` if it has one. I.e.
      :attr:`defaults.config_dir` remains unchanged after
      ``oracledb.init_oracle_client()`` completes.

    - the value of the environment variable ``$TNS_ADMIN``, if it is set.

    - the value of ``$ORACLE_HOME/network/admin`` if the environment variable
      ``$ORACLE_HOME`` is set.

    - the directory of the loaded Oracle Client library, appended with
      ``network/admin``. Note this directory is not determinable on AIX.

    - otherwise the value *None* is used. (Leaving :attr:`defaults.config_dir`
      unchanged).

    .. dbapimethodextension::

    .. versionchanged:: 3.0.0

        At completion of the method, the value of :attr:`defaults.config_dir`
        may get changed by python-oracledb.

    .. versionchanged:: 2.5.0

        The values supplied to the ``lib_dir`` and ``config_dir`` parameters
        are encoded using the encoding returned by `locale.getencoding()
        <https://docs.python.org/3/library/locale.html#locale.getencoding>`__
        for Python 3.11 and higher; for all other versions, the encoding
        "utf-8" is used.  These values may also be supplied as a ``bytes``
        object, in which case they will be used as is.

.. function:: is_thin_mode()

    Returns a boolean indicating if Thin mode is in use.

    Immediately after python-oracledb is imported, this function will return
    *True* indicating that python-oracledb defaults to Thin mode. If
    :func:`oracledb.init_oracle_client()` is called, then a subsequent call to
    ``is_thin_mode()`` will return False indicating that Thick mode is
    enabled. Once the first standalone connection or connection pool is
    created, or a call to ``oracledb.init_oracle_client()`` is made, then
    python-oracledb’s mode is fixed and the value returned by
    ``is_thin_mode()`` will never change for the lifetime of the process.

    The attribute :attr:`Connection.thin` can be used to check a connection's
    mode. The attribute :attr:`ConnectionPool.thin` can be used to check a
    pool's mode.

    .. dbapimethodextension::

    .. versionadded:: 1.1.0


.. function:: makedsn(host, port, sid=None, service_name=None, region=None, \
        sharding_key=None, super_sharding_key=None)

    Returns a string suitable for use as the ``dsn`` parameter for
    :meth:`~oracledb.connect()`. This string is identical to the strings that
    are defined by the Oracle names server or defined in the ``tnsnames.ora``
    file.

    .. deprecated:: python-oracledb 1.0

    Use the :meth:`oracledb.ConnectParams()` method instead.

    .. dbapimethodextension::

.. function:: PoolParams(min=1, max=2, increment=1, connectiontype=None, \
        getmode=oracledb.POOL_GETMODE_WAIT, homogeneous=True, timeout=0, \
        wait_timeout=0, max_lifetime_session=0, session_callback=None, \
        max_sessions_per_shard=0, soda_metadata_cache=False, \
        ping_interval=60, ping_timeout=5000, user=None, proxy_user=Nonde, \
        password=None, newpassword=None, wallet_password=None, \
        access_token=None, host=None, port=1521, protocol="tcp", \
        https_proxy=None, https_proxy_port=0, service_name=None, \
        instance_name=None, sid=None, server_type=None, cclass=None, \
        purity=oracledb.PURITY_DEFAULT, expire_time=0, retry_count=0, \
        retry_delay=1, tcp_connect_timeout=20.0, ssl_server_dn_match=True, \
        ssl_server_cert_dn=None, wallet_location=None, events=False, \
        externalauth=False, mode=oracledb.AUTH_MODE_DEFAULT, \
        disable_oob=False, stmtcachesize=oracledb.defaults.stmtcachesize, \
        edition=None, tag=None, matchanytag=False, \
        config_dir=oracledb.defaults.config_dir, appcontext=[], \
        shardingkey=[], supershardingkey=[], debug_jdwp=None, \
        connection_id_prefix=None, ssl_context=None, sdu=8192, \
        pool_boundary=None, use_tcp_fast_open=False, ssl_version=None, \
        program=oracledb.defaults.program, machine=oracledb.defaults.machine, \
        terminal=oracledb.defaults.terminal, osuser=oracledb.defaults.osuser, \
        driver_name=oracledb.defaults.driver_name, use_sni=False, \
        thick_mode_dsn_passthrough=oracledb.defaults.thick_mode_dsn_passthrough, \
        extra_auth_params=None, handle=0)

    Creates and returns a :ref:`PoolParams Object <poolparam>`. The object
    can be passed to :meth:`oracledb.create_pool()`.

    All the parameters are optional.

    The ``min`` parameter is the minimum number of connections that the pool
    should contain. The default value is *1*.

    The ``max`` parameter is the maximum number of connections that the pool
    should contain. The default value is *2*.

    The ``increment`` parameter is the number of connections that should be
    added to the pool whenever a new connection needs to be created. The
    default value is *1*.

    The ``connectiontype`` parameter is the class of the connection that should
    be returned during calls to :meth:`ConnectionPool.acquire()`. It must be a
    Connection or a subclass of Connection.

    The ``getmode`` parameter determines the behavior of
    :meth:`ConnectionPool.acquire()`.  One of the constants
    :data:`oracledb.POOL_GETMODE_WAIT`, :data:`oracledb.POOL_GETMODE_NOWAIT`,
    :data:`oracledb.POOL_GETMODE_FORCEGET`, or
    :data:`oracledb.POOL_GETMODE_TIMEDWAIT`. The default value is
    :data:`oracledb.POOL_GETMODE_WAIT`.

    The ``homogeneous`` parameter is a boolean that indicates whether the
    connections are homogeneous (same user) or heterogeneous (multiple users).
    The default value is *True*.

    The ``timeout`` parameter is the length of time (in seconds) that a
    connection may remain idle in the pool before it is terminated. This
    applies only when the pool has more than ``min`` connections open, allowing
    it to shrink to the specified minimum size. The default value is *0*
    seconds. A value of *0* means there is no limit.

    The ``wait_timeout`` parameter is the length of time (in milliseconds) that
    a caller should wait when acquiring a connection from the pool with
    ``getmode`` set to :data:`oracledb.POOL_GETMODE_TIMEDWAIT`. The default
    value is *0* milliseconds.

    The ``max_lifetime_session`` parameter is the length of time (in seconds)
    that a pooled connection may exist since first being created. The default
    value is *0*. A value of *0* means that there is no limit. Connections
    become candidates for termination when they are acquired or released back
    to the pool and have existed for longer than ``max_lifetime_session``
    seconds. In python-oracledb Thick mode, Oracle Client libraries 12.1 or
    later must be used and, prior to Oracle Client 21, cleanup only occurs when
    the pool is accessed.

    The ``session_callback`` parameter is a callable that is invoked when a
    connection is returned from the pool for the first time, or when the
    connection tag differs from the one requested.

    The ``max_sessions_per_shard`` parameter is the maximum number of
    connections that may be associated with a particular shard. The default
    value is *0*.

    The ``soda_metadata_cache`` parameter is a boolean that indicates whether
    or not the SODA metadata cache should be enabled. The default value is
    *False*.

    The ``ping_interval`` parameter is the length of time (in seconds) after
    which an unused connection in the pool will be a candidate for pinging when
    :meth:`ConnectionPool.acquire()` is called. If the ping to the database
    indicates the connection is not alive a replacement connection will be
    returned by :meth:`ConnectionPool.acquire()`. If ping_interval is a
    negative value, then the ping functionality will be disabled. The default
    value is *60* seconds.

    The ``ping_timeout`` parameter is the maximum length of time (in
    milliseconds) that :meth:`ConnectionPool.acquire()` waits for a connection
    to respond to any internal ping to the database. If the ping does not
    respond within the specified time, then the connection is destroyed and
    :meth:`~ConnectionPool.acquire()` returns a different connection. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *5000* milliseconds.

    The ``user`` parameter is expected to be a string which indicates the name
    of the user to connect to. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``proxy_user`` parameter is expected to be a string which indicates the
    name of the proxy user to connect to. If this value is not specified, it
    will be parsed out of user if user is in the form "user[proxy_user]". This
    value is used in both the python-oracledb Thin and Thick modes.

    The ``password`` parameter expected to be a string which indicates the
    password for the user. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``newpassword`` parameter is expected to be a string which indicates
    the new password for the user. The new password will take effect
    immediately upon a successful connection to the database. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``wallet_password`` parameter is expected to be a string which
    indicates the password to use to decrypt the PEM-encoded wallet, if it is
    encrypted. This value is only used in python-oracledb Thin mode. The
    ``wallet_password`` parameter is not needed for cwallet.sso files that are
    used in the python-oracledb Thick mode.

    The ``access_token`` parameter is expected to be a string or a 2-tuple or
    a callable. If it is a string, it specifies an Azure AD OAuth2 token used
    for Open Authorization (OAuth 2.0) token based authentication. If it is a
    2-tuple, it specifies the token and private key strings used for Oracle
    Cloud Infrastructure (OCI) Identity and Access Management (IAM) token based
    authentication. If it is a callable, it returns either a string or a
    2-tuple used for OAuth 2.0 or OCI IAM token based authentication and is
    useful when the pool needs to expand and create new connections but the
    current authentication token has expired. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``host`` parameter is expected to be a string which specifies the name
    or IP address of the machine hosting the listener, which handles the
    initial connection to the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``port`` parameter is expected to be an integer which indicates the
    port number on which the listener is listening. The default value is
    *1521*. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``protocol`` parameter is expected to be one of the strings *tcp* or
    *tcps* which indicates whether to use unencrypted network traffic or
    encrypted network traffic (TLS). The default value is *tcp*. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``https_proxy`` parameter is expected to be a string which indicates
    the name or IP address of a proxy host to use for tunneling secure
    connections. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``https_proxy_port`` parameter is expected to be an integer which
    indicates the port that is to be used to communicate with the proxy host.
    The default value is *0*. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``service_name`` parameter is expected to be a string which indicates
    the service name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``instance_name`` parameter is expected to be a string which indicates
    the instance name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``sid`` parameter is expected to be a string which indicates the SID of
    the database. It is recommended to use ``service_name`` instead. This value
    is used in both the python-oracledb Thin and Thick modes.

    The ``server_type`` parameter is expected to be a string that indicates the
    type of server connection that should be established. If specified, it
    should be one of *dedicated*, *shared*, or *pooled*. This value is used in
    both the python-oracledb Thin and Thick modes.

    The ``cclass`` parameter is expected to be a string that identifies the
    connection class to use for :ref:`drcp`. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``purity`` parameter is expected to be one of the
    :ref:`oracledb.PURITY_* <drcppurityconsts>` constants that identifies the
    purity to use for DRCP. This value is used in both the python-oracledb Thin
    and Thick modes.  Internally pooled connections will default to a purity of
    :data:`~oracledb.PURITY_SELF`.

    The ``expire_time`` parameter is expected to be an integer which indicates
    the number of minutes between the sending of keepalive probes. If this
    parameter is set to a value greater than zero it enables keepalive. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *0* minutes.

    The ``retry_count`` parameter is expected to be an integer that identifies
    the number of times that a connection attempt should be retried before the
    attempt is terminated. This value is used in both the python-oracledb Thin
    and Thick modes. The default value is *0*.

    The ``retry_delay`` parameter is expected to be an integer that identifies
    the number of seconds to wait before making a new connection attempt. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is *1* seconds.

    The ``tcp_connect_timeout`` parameter is expected to be a float that
    indicates the maximum number of seconds to wait for establishing a
    connection to the database host. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is *20.0* seconds.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that
    indicates whether the server certificate distinguished name (DN) should be
    matched in addition to the regular certificate verification that is
    performed. Note that if the ssl_server_cert_dn parameter is not provided,
    host name matching is performed instead. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is *True*.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that
    indicates the distinguished name (DN) which should be matched with the
    server. This value is ignored if the ssl_server_dn_match parameter is not
    set to the value *True*. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``wallet_location`` parameter is expected to be a string that
    identifies the directory where the wallet can be found. In python-oracledb
    Thin mode, this must be the directory of the PEM-encoded wallet file,
    ewallet.pem.  In python-oracledb Thick mode, this must be the directory of
    the file, cwallet.sso. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``externalauth`` parameter is a boolean that determines whether to use
    external authentication. This value is only used in the python-oracledb
    Thick mode. The default value is *False*.

    The ``events`` parameter is expected to be a boolean that specifies whether
    the events mode should be enabled. This value is only used in the
    python-oracledb Thick mode. This parameter is needed for continuous
    query notification and high availability event notifications. The default
    value is *False*.

    The ``mode`` parameter is expected to be an integer that identifies the
    authorization mode to use. This value is used in both the python-oracledb
    Thin and Thick modes.The default value is
    :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value is only used
    in the python-oracledb Thin mode and has no effect on Windows which
    does not support this functionality. The default value is *False*.

    The ``stmtcachesize`` parameter is expected to be an integer that
    identifies the initial size of the statement cache. This value is used in
    both the python-oracledb Thin and Thick modes. The default is the value of
    :attr:`defaults.stmtcachesize`.

    The ``edition`` parameter is expected to be a string that indicates the
    edition to use for the connection. It requires Oracle Database 11.2, or
    later. This parameter cannot be used simultaneously with the ``cclass``
    parameter.

    The ``tag`` parameter is expected to be a string that identifies the type
    of connection that should be returned from a pool. This value is only used
    in the python-oracledb Thick mode.

    The ``matchanytag`` parameter is expected to be a boolean specifying
    whether any tag can be used when acquiring a connection from the pool. This
    value is only used in the python-oracledb Thick mode when acquiring a
    connection from a pool. The default value is *False*.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which the :ref:`tnsnames.ora <optnetfiles>` configuration file
    is located.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that
    identifies the application context used by the connection. This parameter
    should contain namespace, name, and value and each entry in the tuple
    should be a string.

    The ``shardingkey`` parameter and ``supershardingkey`` parameters, if
    specified, are expected to be a sequence of values which identifies the
    database shard to connect to. The key values can be a list of strings,
    numbers, bytes, or dates.  These values are only used in the
    python-oracledb Thick mode and are ignored in the Thin mode. See
    :ref:`connsharding`.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL
    debugger.  This allows using the Java Debug Wire Protocol (JDWP) to debug
    PL/SQL code invoked by python-oracledb. This value is only used in the
    python-oracledb Thin mode.  For python-oracledb Thick mode, set the
    ``ORA_DEBUG_JDWP`` environment variable which has the same syntax. For more
    information, see :ref:`jdwp`.

    The ``connection_id_prefix`` parameter is expected to be a string and is
    added to the beginning of the generated ``connection_id`` that is sent to
    the database for `tracing <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-B0FC69F9-2EBC-44E8-ACB2-62FBA14ABD5C>`__.  This value
    is only used in the python-oracledb Thin mode.

    The ``ssl_context`` parameter is expected to be an `SSLContext object
    <https://docs.python.org/3/library/ssl.html#ssl-contexts>`__ which is used
    for connecting to the database using TLS.  This SSL context will be
    modified to include the private key or any certificates found in a
    separately supplied wallet.  This parameter should only be specified if
    the default SSLContext object cannot be used.  This value is only used in
    the python-oracledb Thin mode.

    The ``sdu`` parameter is expected to be an integer that returns the
    requested size of the Session Data Unit (SDU), in bytes. The value tunes
    internal buffers used for communication to the database. Bigger values can
    increase throughput for large queries or bulk data loads, but at the cost
    of higher memory use. The SDU size that will actually be used is negotiated
    down to the lower of this value and the database network SDU configuration
    value. See the `Database Net Services documentation <https://www.oracle.
    com/pls/topic/lookup?ctx=dblatest&id=GUID-86D61D6F-AD26-421A-BABA-
    77949C8A2B04>`__ for more details. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is *8192* bytes.

    The ``pool_boundary`` parameter is expected to be one of the strings
    *statement* or *transaction* which indicates when pooled :ref:`DRCP <drcp>`
    or PRCP connections can be returned to the pool.  If the value is
    *statement*, then pooled DRCP or PRCP connections are implicitly released
    back to the DRCP or PRCP pool when the connection is stateless (that is,
    there are no active cursors, active transactions, temporary tables, or
    temporary LOBs).  If the value is *transaction*, then pooled DRCP or PRCP
    connections are implicitly released back to the DRCP or PRCP pool when
    either one of the methods :meth:`Connection.commit()` or
    :meth:`Connection.rollback()` are called.  This parameter requires the use
    of DRCP or PRCP with Oracle Database 23ai (or later).  See
    :ref:`implicitconnpool` for more information.  This value is used in both
    the python-oracledb Thin and Thick modes.

    The ``use_tcp_fast_open`` parameter is expected to be a boolean which
    indicates whether to use TCP Fast Open which is an `Oracle Autonomous
    Database Serverless (ADB-S) <https://docs.oracle.com/en/cloud/paas/
    autonomous-database/serverless/adbsb/connection-tcp-fast-open.html#
    GUID-34654005-DBBA-4C49-BC6D-717F9C16A17C>`__ specific feature that can
    reduce the latency in round-trips to the database after a connection has
    been established.  This feature is only available with certain versions of
    ADB-S.  This value is used in both python-oracledb Thin and Thick modes.
    The default value is *False*.

    The ``ssl_version`` parameter is expected to be one of the constants
    *ssl.TLSVersion.TLSv1_2* or *ssl.TLSVersion.TLSv1_3* which identifies the
    TLS protocol version used.  These constants are defined in the Python
    `ssl <https://docs.python.org/3/library/ssl.html>`__ module.  This
    parameter can be specified when establishing connections with the protocol
    "tcps".  This value is used in both python-oracledb Thin and Thick modes.
    The value *ssl.TLSVersion.TLSv1_3* requires Oracle Database 23ai.  If you
    are using python-oracledb Thick mode, Oracle Client 23ai is additionally
    required.

    The ``use_sni`` parameter is expected to be a boolean which indicates
    whether to use the TLS Server Name Indication (SNI) extension to bypass the
    second TLS negotiation that would otherwise be required. This parameter is
    used in both python-oracledb Thin and Thick modes. This parameter requires
    Oracle Database 23.7. The default value is *False*. See the `Database Net
    Services documentation
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
    GUID-E98F42D0-DC9D-4B52-9C66-6DE7EC5F64D6>`__ for more details.

    The ``program`` parameter is expected to be a string which specifies the
    name of the executable program or application connected to Oracle
    Database.  This value is only used in the python-oracledb Thin mode. The
    default is the value of :attr:`defaults.program`.

    The ``machine`` parameter is expected to be a string which specifies the
    machine name of the client connecting to Oracle Database.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.machine`.

    The ``terminal`` parameter is expected to be a string which specifies the
    terminal identifier from which the connection originates.  This value is
    only used in the python-oracledb Thin mode.  The default is the value of
    :attr:`defaults.terminal`.

    The ``osuser`` parameter is expected to be a string which specifies the
    operating system user that initiates the database connection.  This value
    is only used in the python-oracledb Thin mode.  The default value is the
    value of :attr:`defaults.osuser`.

    The ``driver_name`` parameter is expected to be a string which specifies
    the driver used by the client to connect to Oracle Database.  This value
    is used in both the python-oracledb Thin and Thick modes.  The default is
    the value of :attr:`defaults.driver_name`.

    The ``thick_mode_dsn_passthrough`` parameter is expected to be a boolean
    which indicates whether the connect string should be passed unchanged to
    the Oracle Client libraries for parsing when using python-oracledb Thick
    mode. If this parameter is set to *False* in Thick mode, connect strings
    are parsed by python-oracledb itself and a generated connect descriptor is
    sent to the Oracle Client libraries. This value is only used in the
    python-oracledb Thick mode. The default value is
    :attr:`defualts.thick_mode_dsn_passthrough`. For more information, see
    :ref:`usingconfigfiles`.

    The ``extra_auth_params`` parameter is expected to be a dictionary
    containing the configuration parameters necessary for Oracle Database
    authentication using :ref:`OCI <cloudnativeauthoci>` or :ref:`Azure
    <cloudnativeauthoauth>` cloud native authentication plugins.  This value is
    used in both the python-oracledb Thin and Thick modes. See
    :ref:`tokenauth`.

    The ``handle`` parameter is expected to be an integer which represents a
    pointer to a valid service context handle. This value is only used in the
    python-oracledb Thick mode. It should be used with extreme caution. The
    default value is *0*.

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

.. function:: SparseVector(num_dimensions, indices, values)

    Creates and returns a :ref:`SparseVector object <sparsevectorsobj>`.

    The ``num_dimensions`` parameter is the number of dimensions contained in
    the vector.

    The ``indices`` parameter is the indices (zero-based) of non-zero values
    in the vector.

    The ``values`` parameter is the non-zero values stored in the vector.

    .. versionadded:: 3.0.0

.. function:: register_params_hook(hook_function)

    Registers a user parameter hook function that will be called internally by
    python-oracledb prior to connection or pool creation. The hook function
    accepts a copy of the parameters that will be used to create the pool or
    standalone connection and may modify them. For example, the cloud native
    authentication plugins modify the "access_token" parameter with a function
    that will acquire the token using information found in the
    "extra_auth_parms" parameter.

    Multiple hooks may be registered. They will be invoked in order of
    registration.

    To unregister a user function, use :meth:`oracledb.unregister_params_hook`.

    See :ref:`registerparamshook`.

    .. dbapimethodextension::

    .. versionadded:: 3.0.0

.. function:: register_password_type(password_type, hook_function)

    Registers a user password hook function that will be called internally by
    python-oracledb when a password is supplied as a dictionary containing the
    given ``password_type`` as the key "type". The hook function is called for
    passwords specified as the ``password``, ``newpassword`` and
    ``wallet_parameter`` parameters in calls to :meth:`oracledb.connect()`,
    :meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, and
    :meth:`oracledb.create_pool_async()`.

    Your hook function is expected to accept the dictionary supplied by the
    application and return the valid password.

    Calling :meth:`~oracledb.register_password_type()` with the
    ``hook_function`` parameter set to *None* will result in a previously
    registered user function being removed and the default behavior restored.

    See :ref:`registerpasswordtype`.

    .. dbapimethodextension::

    .. versionadded:: 3.0.0

.. function:: register_protocol(protocol, hook_function)

    Registers a user protocol hook function that will be called internally by
    python-oracledb Thin mode prior to connection or pool creation.  The hook
    function will be invoked when :func:`oracledb.connect`,
    :func:`oracledb.create_pool`, :meth:`oracledb.connect_async()`, or
    :meth:`oracledb.create_pool_async()` are called with a ``dsn`` parameter
    value prefixed with the specified protocol. The user function will also be
    invoked when :meth:`ConnectParams.parse_connect_string()` is called in Thin
    or Thick modes with a similar ``connect_string`` parameter value.

    Your hook function is expected to construct valid connection details. For
    example, if a hook function is registered for the "ldaps" protocol, then
    calling :func:`oracledb.connect` with a connection string prefixed with
    "ldaps://" will invoke the function.  The function can then perform LDAP
    lookup to retrieve and set the actual database information that will be
    used internally by python-oracledb to complete the connection creation.

    The ``protocol`` parameter is a string that will be matched against the
    prefix appearing before "://" in connection strings.

    The ``hook_function`` parameter should be a function with the signature::

        hook_function(protocol, protocol_arg, params)

    The hook function will be called with the following arguments:

    - The ``protocol`` parameter is the value that was registered.

    - The ``protocol_arg`` parameter is the section after "://" in the
      connection string used in the connection or pool creation call, or passed
      to :meth:`~ConnectParams.parse_connect_string()`.

    - The ``params`` parameter is an instance of :ref:`ConnectParams
      <connparam>`.

      When your hook function is invoked internally prior to connection or pool
      creation, ``params`` will be the ConnectParams instance originally passed
      to the :func:`oracledb.connect`, :func:`oracledb.create_pool`,
      :meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()`
      call, if such an instance was passed.  Otherwise it will be a new
      ConnectParams instance.  The hook function should parse ``protocol`` and
      ``protocol_arg`` and take any desired action to update ``params``
      :ref:`attributes <connparamsattr>` with appropriate connection
      parameters. Attributes can be set using :meth:`ConnectParams.set()` or
      :meth:`ConnectParams.parse_connect_string()`. The ConnectParams instance
      will then be used to complete the connection or pool creation.

      When your hook function is invoked by
      :meth:`ConnectParams.parse_connect_string()`, then ``params`` will be the
      invoking ConnectParams instance that you can update using
      :meth:`ConnectParams.set()` or
      :meth:`ConnectParams.parse_connect_string()`.

    Internal hook functions for the "tcp" and "tcps" protocols are
    pre-registered but can be overridden if needed. If any other protocol has
    not been registered, then connecting will result in the error ``DPY-4021:
    invalid protocol``.

    Calling :meth:`~oracledb.register_protocol()` with the ``hook_function``
    parameter set to *None* will result in a previously registered user function
    being removed and the default behavior restored.

    See :ref:`registerprotocolhook` for more information.

    .. dbapimethodextension::

    .. versionadded:: 2.5.0

.. function:: Time(hour, minute, second)

    Constructs an object holding a time value.

    .. note::

        A time-only data type is not supported by Oracle Database. Calling this
        function raises a NotSupportedError exception.


.. function:: TimeFromTicks(ticks)

    Constructs an object holding a time value from the given ticks value
    (number of seconds since the epoch; see the documentation of the standard
    Python time module for details).

    .. note::

        A time-only data type is not supported by Oracle Database. Calling this
        function raises a NotSupportedError exception.

.. function:: Timestamp(year, month, day, hour, minute, second)

    Constructs an object holding a time stamp value.

.. function:: TimestampFromTicks(ticks)

    Constructs an object holding a time stamp value from the given ticks value
    (number of seconds since the epoch; see the documentation of the standard
    Python time module for details).

.. function:: unregister_params_hook(hook_function)

    Unregisters a user parameter function that was earlier registered with a
    call to :meth:`oracledb.register_params_hook()`.

    .. dbapimethodextension::

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


.. _futureobj:

Oracledb __future__ Object
==========================

Special object that contains attributes which control the behavior of
python-oracledb, allowing for opting in for new features.

.. dbapimethodextension::

.. _constants:

Oracledb Constants
==================

General
-------

.. data:: apilevel

    String constant stating the supported DB API level. Currently '2.0'.


.. data:: paramstyle

    String constant stating the type of parameter marker formatting expected by
    the interface. Currently 'named' as in 'where name = :name'.


.. data:: threadsafety

    Integer constant stating the level of thread safety that the interface
    supports.  Currently 2, which means that threads may share the module and
    connections, but not cursors. Sharing means that a thread may use a
    resource without wrapping it using a mutex semaphore to implement resource
    locking.

.. data:: version
.. data:: __version__

    String constant stating the version of the module. Currently '|release|'.

    .. dbapiattributeextension::


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

.. data:: MSG_BUFFERED

    This constant is used to specify that enqueue/dequeue operations should
    enqueue or dequeue buffered messages.


.. data:: MSG_PERSISTENT

    This constant is used to specify that enqueue/dequeue operations should
    enqueue or dequeue persistent messages. This is the default value.


.. data:: MSG_PERSISTENT_OR_BUFFERED

    This constant is used to specify that dequeue operations should dequeue
    either persistent or buffered messages.


Advanced Queuing: Dequeue Modes
-------------------------------

The AQ Dequeue mode constants are possible values for the
:attr:`~DeqOptions.mode` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. data:: DEQ_BROWSE

    This constant is used to specify that dequeue should read the message
    without acquiring any lock on the message (equivalent to a select
    statement).


.. data:: DEQ_LOCKED

    This constant is used to specify that dequeue should read and obtain a
    write lock on the message for the duration of the transaction (equivalent
    to a select for update statement).


.. data:: DEQ_REMOVE

    This constant is used to specify that dequeue should read the message and
    update or delete it. This is the default value.


.. data:: DEQ_REMOVE_NODATA

    This constant is used to specify that dequeue should confirm receipt of the
    message but not deliver the actual message content.


Advanced Queuing: Dequeue Navigation Modes
------------------------------------------

The AQ Dequeue Navigation mode constants are possible values for the
:attr:`~DeqOptions.navigation` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. data:: DEQ_FIRST_MSG

    This constant is used to specify that dequeue should retrieve the first
    available message that matches the search criteria. This resets the
    position to the beginning of the queue.


.. data:: DEQ_NEXT_MSG

    This constant is used to specify that dequeue should retrieve the next
    available message that matches the search criteria. If the previous message
    belongs to a message group, AQ retrieves the next available message that
    matches the search criteria and belongs to the message group. This is the
    default.


.. data:: DEQ_NEXT_TRANSACTION

    This constant is used to specify that dequeue should skip the remainder of
    the transaction group and retrieve the first message of the next
    transaction group. This option can only be used if message grouping is
    enabled for the current queue.


Advanced Queuing: Dequeue Visibility Modes
------------------------------------------

The AQ Dequeue Visibility mode constants are possible values for the
:attr:`~DeqOptions.visibility` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. data:: DEQ_IMMEDIATE

    This constant is used to specify that dequeue should perform its work as
    part of an independent transaction.


.. data:: DEQ_ON_COMMIT

    This constant is used to specify that dequeue should be part of the current
    transaction. This is the default value.


Advanced Queuing: Dequeue Wait Modes
------------------------------------

The AQ Dequeue Wait mode constants are possible values for the
:attr:`~DeqOptions.wait` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.deqone()`, or :meth:`AsyncQueue.deqmany()` methods.

.. dbapiconstantextension::

.. data:: DEQ_NO_WAIT

    This constant is used to specify that dequeue not wait for messages to be
    available for dequeuing.


.. data:: DEQ_WAIT_FOREVER

    This constant is used to specify that dequeue should wait forever for
    messages to be available for dequeuing. This is the default value.


Advanced Queuing: Enqueue Visibility Modes
------------------------------------------

The AQ Enqueue Visibility mode constants are possible values for the
:attr:`~EnqOptions.visibility` attribute of the
:ref:`enqueue options object <enqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.enqone()`, :meth:`Queue.enqmany()`,
:meth:`AsyncQueue.enqone()`, or :meth:`AsyncQueue.enqmany()` methods.

.. dbapiconstantextension::

.. data:: ENQ_IMMEDIATE

    This constant is used to specify that enqueue should perform its work as
    part of an independent transaction.

    The use of this constant with :ref:`bulk enqueuing <bulkenqdeq>` is only
    supported in python-oracledb :ref:`Thick mode <enablingthick>`.


.. data:: ENQ_ON_COMMIT

    This constant is used to specify that enqueue should be part of the current
    transaction. This is the default value.


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

.. data:: MSG_EXPIRED

    This constant is used to specify that the message has been moved to the
    exception queue.


.. data:: MSG_PROCESSED

    This constant is used to specify that the message has been processed and
    has been retained.


.. data:: MSG_READY

    This constant is used to specify that the message is ready to be processed.


.. data:: MSG_WAITING

    This constant is used to specify that the message delay has not yet been
    reached.


Advanced Queuing: Other Constants
---------------------------------

This section contains other constants that are used for Advanced Queueing.

.. dbapiconstantextension::

.. data:: MSG_NO_DELAY

    This constant is a possible value for the :attr:`~MessageProperties.delay`
    attribute of the :ref:`message properties object <msgproperties>` passed
    as the ``msgproperties`` parameter to the :meth:`Queue.deqone()` or
    :meth:`Queue.deqmany()` and :meth:`Queue.enqone()` or
    :meth:`Queue.enqmany()` methods. It specifies that no delay should be
    imposed and the message should be immediately available for dequeuing. This
    is also the default value.


.. data:: MSG_NO_EXPIRATION

    This constant is a possible value for the
    :attr:`~MessageProperties.expiration` attribute of the
    :ref:`message properties object <msgproperties>` passed as the
    ``msgproperties`` parameter to the :meth:`Queue.deqone()` or
    :meth:`Queue.deqmany()` and :meth:`Queue.enqone()` or
    :meth:`Queue.enqmany()` methods. It specifies that the message never
    expires. This is also the default value.


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

.. data:: AUTH_MODE_DEFAULT

    This constant is used to specify that default authentication is to take
    place. This is the default value if no mode is passed at all.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.DEFAULT``.

    This constant deprecates the ``DEFAULT_AUTH`` constant that was used in the
    obsolete cx_Oracle driver, and was the default ``mode`` value.

.. data:: AUTH_MODE_PRELIM

    This constant is used to specify that preliminary authentication is to be
    used. This is needed for performing database startup and shutdown.

    It can only be used in python-oracledb Thick mode for standalone
    connections.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.PRELIM``.

    This constant deprecates the ``PRELIM_AUTH`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSASM

    This constant is used to specify that SYSASM access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSASM``.

    This constant deprecates the ``SYSASM`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSBKP

    This constant is used to specify that SYSBACKUP access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSBKP``.

    This constant deprecates the ``SYSBKP`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSDBA

    This constant is used to specify that SYSDBA access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSDBA``.

    This constant deprecates the ``SYSDBA`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSDGD

    This constant is used to specify that SYSDG access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSDGD``.

    This constant deprecates the ``SYSDGD`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSKMT

    This constant is used to specify that SYSKM access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSKMT``.

    This constant deprecates the ``SYSKMT`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSOPER

    This constant is used to specify that SYSOPER access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSOPER``.

    This constant deprecates the ``SYSOPER`` constant that was used in the
    obsolete cx_Oracle driver.

.. data:: AUTH_MODE_SYSRAC

    This constant is used to specify that SYSRAC access is to be acquired.

    It can be used for standalone and pooled connections in python-oracledb
    Thin mode, and for standalone connections in Thick mode.

    Its enumerated value can also be identified by
    ``oracledb.AuthMode.SYSRAC``.

    This constant deprecates the ``SYSRAC`` constant that was used in the
    obsolete cx_Oracle driver.

.. _pipeline-operation-types:

Pipeline Operation Types
------------------------

The Pipeline Operation type constants belong to the enumeration called
``PipelineOpType``. The pipelining constants listed below are used to identify
the type of operation added. They are possible values for the
:attr:`PipelineOp.op_type` attribute.

.. versionadded:: 2.4.0

.. data:: oracledb.PIPELINE_OP_TYPE_CALL_FUNC

    This constant identifies the type of operation as the calling of a stored
    function.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.CALL_FUNC``.

.. data:: oracledb.PIPELINE_OP_TYPE_CALL_PROC

    This constant identifies the type of operation as the calling of a stored
    procedure.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.CALL_PROC``.

.. data:: oracledb.PIPELINE_OP_TYPE_COMMIT

    This constant identifies the type of operation as the performing of a
    commit.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.COMMIT``.

.. data:: oracledb.PIPELINE_OP_TYPE_EXECUTE

    This constant identifies the type of operation as the executing of a
    statement.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.EXECUTE``.

.. data:: oracledb.PIPELINE_OP_TYPE_EXECUTE_MANY

    This constant identifies the type of operations as the executing of a
    statement multiple times.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.EXECUTE_MANY``.

.. data:: oracledb.PIPELINE_OP_TYPE_FETCH_ALL

    This constant identifies the type of operation as the executing of a
    query and returning all of the rows from the result set.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.FETCH_ALL``.

.. data:: oracledb.PIPELINE_OP_TYPE_FETCH_MANY

    This constant identifies the type of operation as the executing of a
    query and returning up to the specified number of rows from the result
    set.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.FETCH_MANY``.

.. data:: oracledb.PIPELINE_OP_TYPE_FETCH_ONE

    This constant identifies the type of operation as the executing of a query
    and returning the first row of the result set.

    This enumerated value can also be identified by
    ``oracledb.PipelineOpType.FETCH_ONE``.

Database Shutdown Modes
-----------------------

The Database Shutdown mode constants are possible values for the ``mode``
parameter of the :meth:`Connection.shutdown()` method.

.. dbapiconstantextension::

.. data:: DBSHUTDOWN_ABORT

    This constant is used to specify that the caller should not wait for
    current processing to complete or for users to disconnect from the
    database. This should only be used in unusual circumstances since database
    recovery may be necessary upon next startup.


.. data:: DBSHUTDOWN_FINAL

    This constant is used to specify that the instance can be truly halted.
    This should only be done after the database has been shutdown with one of
    the other modes (except abort) and the database has been closed and
    dismounted using the appropriate SQL commands.


.. data:: DBSHUTDOWN_IMMEDIATE

    This constant is used to specify that all uncommitted transactions should
    be rolled back and any connected users should be disconnected.


.. data:: DBSHUTDOWN_TRANSACTIONAL

    This constant is used to specify that further connections to the database
    should be prohibited and no new transactions should be allowed. It then
    waits for all active transactions to complete.


.. data:: DBSHUTDOWN_TRANSACTIONAL_LOCAL

    This constant is used to specify that further connections to the database
    should be prohibited and no new transactions should be allowed. It then
    waits for only local active transactions to complete.


Event Types
-----------

The Event type constants are possible values for the :attr:`Message.type`
attribute of the messages that are sent for subscriptions created by the
:meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: EVENT_AQ

    This constant is used to specify that one or more messages are available
    for dequeuing on the queue specified when the subscription was created.


.. data:: EVENT_DEREG

    This constant is used to specify that the subscription has been
    deregistered and no further notifications will be sent.


.. data:: EVENT_NONE

    This constant is used to specify no information is available about the
    event.


.. data:: EVENT_OBJCHANGE

    This constant is used to specify that a database change has taken place on
    a table registered with the :meth:`Subscription.registerquery()` method.


.. data:: EVENT_QUERYCHANGE

    This constant is used to specify that the result set of a query registered
    with the :meth:`Subscription.registerquery()` method has been changed.


.. data:: EVENT_SHUTDOWN

    This constant is used to specify that the instance is in the process of
    being shut down.


.. data:: EVENT_SHUTDOWN_ANY

    This constant is used to specify that any instance (when running RAC) is in
    the process of being shut down.


.. data:: EVENT_STARTUP

    This constant is used to specify that the instance is in the process of
    being started up.


.. _cqn-operation-codes:

Operation Codes
---------------

The Operation code constants are possible values for the ``operations``
parameter for the :meth:`Connection.subscribe()` method. One or more of these
values can be OR'ed together. These values are also used by the
:attr:`MessageTable.operation` or :attr:`MessageQuery.operation` attributes of
the messages that are sent.

.. dbapiconstantextension::

.. data:: OPCODE_ALLOPS

    This constant is used to specify that messages should be sent for all
    operations.


.. data:: OPCODE_ALLROWS

    This constant is used to specify that the table or query has been
    completely invalidated.


.. data:: OPCODE_ALTER

    This constant is used to specify that messages should be sent when a
    registered table has been altered in some fashion by DDL, or that the
    message identifies a table that has been altered.


.. data:: OPCODE_DELETE

    This constant is used to specify that messages should be sent when data is
    deleted, or that the message identifies a row that has been deleted.


.. data:: OPCODE_DROP

    This constant is used to specify that messages should be sent when a
    registered table has been dropped, or that the message identifies a table
    that has been dropped.


.. data:: OPCODE_INSERT

    This constant is used to specify that messages should be sent when data is
    inserted, or that the message identifies a row that has been inserted.


.. data:: OPCODE_UPDATE

    This constant is used to specify that messages should be sent when data is
    updated, or that the message identifies a row that has been updated.

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

.. data:: POOL_GETMODE_FORCEGET

    This constant is used to specify that a new connection should be created
    and returned by :meth:`ConnectionPool.acquire()` if there are no free
    connections available in the pool and the pool is already at its maximum
    size.

    When a connection acquired in this mode is eventually released back to the
    pool, it will be dropped and not added to the pool if the pool is still at
    its maximum size.

    This enumerated value can also be identified by
    ``oracledb.PoolGetMode.FORCEGET``.

    This constant deprecates the ``SPOOL_ATTRVAL_FORCEGET`` constant that was
    used in the obsolete cx_Oracle driver.


.. data:: POOL_GETMODE_NOWAIT

    This constant is used to specify that an exception should be raised by
    :meth:`ConnectionPool.acquire()` when all currently created connections are
    already in use and so :meth:`~ConnectionPool.acquire()` cannot immediately
    return a connection. Note the exception may occur even if the pool is
    smaller than its maximum size.

    This enumerated value can also be identified by
    ``oracledb.PoolGetMode.NOWAIT``.

    This constant deprecates the ``SPOOL_ATTRVAL_NOWAIT`` constant that was
    used in the obsolete cx_Oracle driver, and was the default ``getmode``
    value.


.. data:: POOL_GETMODE_WAIT

    This constant is used to specify that :meth:`ConnectionPool.acquire()`
    should wait until a connection is available if there are currently no free
    connections available in the pool.  This is the default value.

    This enumerated value can also be identified by
    ``oracledb.PoolGetMode.WAIT``.

    This constant deprecates the ``SPOOL_ATTRVAL_WAIT`` constant that was used
    in the obsolete cx_Oracle driver.


.. data:: POOL_GETMODE_TIMEDWAIT

    This constant is used to specify that :meth:`ConnectionPool.acquire()`
    should wait for a period of time (defined by the ``wait_timeout``
    parameter) for a connection to become available before returning with an
    error.

    This enumerated value can also be identified by
    ``oracledb.PoolGetMode.TIMEDWAIT``.

    This constant deprecates the ``SPOOL_ATTRVAL_TIMEDWAIT`` constant that was
    used in the obsolete cx_Oracle driver.

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

.. data:: PURITY_DEFAULT

    This constant is used to specify that the purity of the session is the
    default value identified by Oracle (see Oracle's documentation for more
    information). This is the default value.

    This enumerated value can also be identified by
    ``oracledb.Purity.DEFAULT``.

    This constant deprecates the ``ATTR_PURITY_DEFAULT`` constant that was used
    in the obsolete cx_Oracle driver, and was the default ``purity`` value.

.. data:: PURITY_NEW

    This constant is used to specify that the session acquired from the pool
    should be new and not have any prior session state.

    This enumerated value can also be identified by ``oracledb.Purity.NEW``.

    This constant deprecates the ``ATTR_PURITY_NEW`` constant that was used in
    the obsolete cx_Oracle driver.


.. data:: PURITY_SELF

    This constant is used to specify that the session acquired from the pool
    need not be new and may have prior session state.

    This enumerated value can also be identified by ``oracledb.Purity.SELF``.

    This constant deprecates the ``ATTR_PURITY_SELF`` constant that was used in
    the obsolete cx_Oracle driver.

Subscription Grouping Classes
-----------------------------

The Subscription Grouping Class constants are possible values for the
``groupingClass`` parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: SUBSCR_GROUPING_CLASS_TIME

    This constant is used to specify that events are to be grouped by the
    period of time in which they are received.


Subscription Grouping Types
---------------------------

The Subscription Grouping Type constants are possible values for the
``groupingType`` parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: SUBSCR_GROUPING_TYPE_SUMMARY

    This constant is used to specify that when events are grouped a summary of
    the events should be sent instead of the individual events. This is the
    default value.

.. data:: SUBSCR_GROUPING_TYPE_LAST

    This constant is used to specify that when events are grouped the last
    event that makes up the group should be sent instead of the individual
    events.


.. _subscr-namespaces:

Subscription Namespaces
-----------------------

The Subscription Namespace constants are possible values for the ``namespace``
parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: SUBSCR_NAMESPACE_AQ

    This constant is used to specify that notifications should be sent when a
    queue has messages available to dequeue.

.. data:: SUBSCR_NAMESPACE_DBCHANGE

    This constant is used to specify that database change notification or query
    change notification messages are to be sent. This is the default value.


.. _subscr-protocols:

Subscription Protocols
----------------------

The Subscription Protocol constants are possible values for the ``protocol``
parameter of the :meth:`Connection.subscribe()` method.

.. dbapiconstantextension::

.. data:: SUBSCR_PROTO_CALLBACK

    This constant is used to specify that notifications will be sent to the
    callback routine identified when the subscription was created. It is the
    default value and the only value currently supported.


.. data:: SUBSCR_PROTO_HTTP

    This constant is used to specify that notifications will be sent to an
    HTTP URL when a message is generated. This value is currently not
    supported.


.. data:: SUBSCR_PROTO_MAIL

    This constant is used to specify that notifications will be sent to an
    e-mail address when a message is generated. This value is currently not
    supported.


.. data:: SUBSCR_PROTO_OCI

    This constant is used to specify that notifications will be sent to the
    callback routine identified when the subscription was created. It is the
    default value and the only value currently supported.

    .. deprecated:: python-oracledb 1.0

     Use :data:`~oracledb.SUBSCR_PROTO_CALLBACK` instead.


.. data:: SUBSCR_PROTO_SERVER

    This constant is used to specify that notifications will be sent to a
    PL/SQL procedure when a message is generated. This value is currently not
    supported.


.. _subscr-qos:

Subscription Quality of Service
-------------------------------

The Subscription Quality of Service constants are possible values for the
``qos`` parameter of the :meth:`Connection.subscribe()` method. One or more of
these values can be OR'ed together.

.. dbapiconstantextension::

.. data:: SUBSCR_QOS_BEST_EFFORT

    This constant is used to specify that best effort filtering for query
    result set changes is acceptable. False positive notifications may be
    received.  This behaviour may be suitable for caching applications.


.. data:: SUBSCR_QOS_DEREG_NFY

    This constant is used to specify that the subscription should be
    automatically unregistered after the first notification is received.


.. data:: SUBSCR_QOS_QUERY

    This constant is used to specify that notifications should be sent if the
    result set of the registered query changes. By default, no false positive
    notifications will be generated.


.. data:: SUBSCR_QOS_RELIABLE

    This constant is used to specify that notifications should not be lost in
    the event of database failure.


.. data:: SUBSCR_QOS_ROWIDS

    This constant is used to specify that the rowids of the inserted, updated
    or deleted rows should be included in the message objects that are sent.


.. _types:

DB API Types
------------

.. data:: BINARY

    This type object is used to describe columns in a database that contain
    binary data. The database types :data:`DB_TYPE_RAW` and
    :data:`DB_TYPE_LONG_RAW` will compare equal to this value. If a variable is
    created with this type, the database type :data:`DB_TYPE_RAW` will be used.


.. data:: DATETIME

    This type object is used to describe columns in a database that are dates.
    The database types :data:`DB_TYPE_DATE`, :data:`DB_TYPE_TIMESTAMP`,
    :data:`DB_TYPE_TIMESTAMP_LTZ` and :data:`DB_TYPE_TIMESTAMP_TZ` will all
    compare equal to this value. If a variable is created with this
    type, the database type :data:`DB_TYPE_DATE` will be used.


.. data:: NUMBER

    This type object is used to describe columns in a database that are
    numbers. The database types :data:`DB_TYPE_BINARY_DOUBLE`,
    :data:`DB_TYPE_BINARY_FLOAT`, :data:`DB_TYPE_BINARY_INTEGER` and
    :data:`DB_TYPE_NUMBER` will all compare equal to this value. If a variable
    is created with this type, the database type :data:`DB_TYPE_NUMBER` will be
    used.


.. data:: ROWID

    This type object is used to describe the pseudo column "rowid". The
    database types :data:`DB_TYPE_ROWID` and :data:`DB_TYPE_UROWID` will
    compare equal to this value. If a variable is created with this type, the
    database type :data:`DB_TYPE_VARCHAR` will be used.


.. data:: STRING

    This type object is used to describe columns in a database that are
    strings. The database types :data:`DB_TYPE_CHAR`, :data:`DB_TYPE_LONG`,
    :data:`DB_TYPE_NCHAR`, :data:`DB_TYPE_NVARCHAR` and :data:`DB_TYPE_VARCHAR`
    will all compare equal to this value. If a variable is created with this
    type, the database type :data:`DB_TYPE_VARCHAR` will be used.


.. _dbtypes:

Database Types
--------------

All of these types are extensions to the DB API definition. They are found in
query and object metadata. They can also be used to specify the database type
when binding data.

Also see the table :ref:`supporteddbtypes`.

.. data:: DB_TYPE_BFILE

    Describes columns, attributes or array elements in a database that are of
    type BFILE. It will compare equal to the DB API type :data:`BINARY`.


.. data:: DB_TYPE_BINARY_DOUBLE

    Describes columns, attributes or array elements in a database that are of
    type BINARY_DOUBLE. It will compare equal to the DB API type
    :data:`NUMBER`.


.. data:: DB_TYPE_BINARY_FLOAT

    Describes columns, attributes or array elements in a database that are
    of type BINARY_FLOAT. It will compare equal to the DB API type
    :data:`NUMBER`.


.. data:: DB_TYPE_BINARY_INTEGER

    Describes attributes or array elements in a database that are of type
    BINARY_INTEGER. It will compare equal to the DB API type :data:`NUMBER`.


.. data:: DB_TYPE_BLOB

    Describes columns, attributes or array elements in a database that are of
    type BLOB. It will compare equal to the DB API type :data:`BINARY`.


.. data:: DB_TYPE_BOOLEAN

    Describes attributes or array elements in a database that are of type
    BOOLEAN. It is only available in Oracle 12.1 and higher and only within
    PL/SQL.


.. data:: DB_TYPE_CHAR

    Describes columns, attributes or array elements in a database that are of
    type CHAR. It will compare equal to the DB API type :data:`STRING`.

    Note that these are fixed length string values and behave differently from
    VARCHAR2.


.. data:: DB_TYPE_CLOB

    Describes columns, attributes or array elements in a database that are of
    type CLOB. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_CURSOR

    Describes columns in a database that are of type CURSOR. In PL/SQL, these
    are known as REF CURSOR.


.. data:: DB_TYPE_DATE

    Describes columns, attributes or array elements in a database that are of
    type DATE. It will compare equal to the DB API type :data:`DATETIME`.


.. data:: DB_TYPE_INTERVAL_DS

    Describes columns, attributes or array elements in a database that are of
    type INTERVAL DAY TO SECOND.


.. data:: DB_TYPE_INTERVAL_YM

    Describes columns, attributes or array elements in a database that are of
    type INTERVAL YEAR TO MONTH.


.. data:: DB_TYPE_JSON

    Describes columns in a database that are of type JSON (with Oracle Database
    21 or later).

.. data:: DB_TYPE_LONG

    Describes columns, attributes or array elements in a database that are of
    type LONG. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_LONG_RAW

    Describes columns, attributes or array elements in a database that are of
    type LONG RAW. It will compare equal to the DB API type :data:`BINARY`.


.. data:: DB_TYPE_LONG_NVARCHAR

    This constant can be used in output type handlers when fetching NCLOB
    columns as a string. (Note a type handler is not needed if
    :ref:`oracledb.defaults.fetch_lobs <defaults>` is set to False).  For IN
    binds, this constant can be used to create a bind variable in
    :meth:`Cursor.var()` or via :meth:`Cursor.setinputsizes()`.  The
    ``DB_TYPE_LONG_NVARCHAR`` value won't be shown in query metadata since it
    is not a database type.

    It will compare equal to the DB API type :data:`STRING`.

.. data:: DB_TYPE_NCHAR

    Describes columns, attributes or array elements in a database that are of
    type NCHAR. It will compare equal to the DB API type :data:`STRING`.

    Note that these are fixed length string values and behave differently from
    NVARCHAR2.


.. data:: DB_TYPE_NCLOB

    Describes columns, attributes or array elements in a database that are of
    type NCLOB. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_NUMBER

    Describes columns, attributes or array elements in a database that are of
    type NUMBER. It will compare equal to the DB API type :data:`NUMBER`.


.. data:: DB_TYPE_NVARCHAR

    Describes columns, attributes or array elements in a database that are of
    type NVARCHAR2. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_OBJECT

    Describes columns, attributes or array elements in a database that are an
    instance of a named SQL or PL/SQL type.


.. data:: DB_TYPE_RAW

    Describes columns, attributes or array elements in a database that are of
    type RAW. It will compare equal to the DB API type :data:`BINARY`.


.. data:: DB_TYPE_ROWID

    Describes columns, attributes or array elements in a database that are of
    type ROWID or UROWID. It will compare equal to the DB API type
    :data:`ROWID`.


.. data:: DB_TYPE_TIMESTAMP

    Describes columns, attributes or array elements in a database that are of
    type TIMESTAMP. It will compare equal to the DB API type :data:`DATETIME`.


.. data:: DB_TYPE_TIMESTAMP_LTZ

    Describes columns, attributes or array elements in a database that are of
    type TIMESTAMP WITH LOCAL TIME ZONE. It will compare equal to the DB API
    type :data:`DATETIME`.


.. data:: DB_TYPE_TIMESTAMP_TZ

    Describes columns, attributes or array elements in a database that are of
    type TIMESTAMP WITH TIME ZONE. It will compare equal to the DB API type
    :data:`DATETIME`.


.. data:: DB_TYPE_UNKNOWN

    Describes columns, attributes or array elements in a database that are
    of an unknown type.


.. data:: DB_TYPE_UROWID

    Describes columns, attributes or array elements in a database that are of
    type UROWID. It will compare equal to the DB API type :data:`ROWID`.

    .. note::

        This type is not supported in python-oracledb Thick mode.
        See :ref:`querymetadatadiff`.


.. data:: DB_TYPE_VARCHAR

    Describes columns, attributes or array elements in a database that are of
    type VARCHAR2. It will compare equal to the DB API type :data:`STRING`.


.. data:: DB_TYPE_VECTOR

    Describes columns, attributes or array elements in a database that are of
    type VECTOR.

    .. versionadded:: 2.2.0


.. data:: DB_TYPE_XMLTYPE

    Describes columns, attributes or array elements in a database that are of
    type SYS.XMLTYPE.

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


Other Types
-----------

All of these types are extensions to the DB API definition.

.. data:: ApiType

    This type object is the Python type of the database API type constants
    :data:`BINARY`, :data:`DATETIME`, :data:`NUMBER`, :data:`ROWID` and
    :data:`STRING`.


.. data:: DbType

    This type object is the Python type of the
    :ref:`database type constants <dbtypes>`.


.. data:: LOB

    This type object is the Python type of :data:`DB_TYPE_BLOB`,
    :data:`DB_TYPE_BFILE`, :data:`DB_TYPE_CLOB` and :data:`DB_TYPE_NCLOB` data
    that is returned from cursors.

.. _tpcconstants:

Two-Phase Commit (TPC) Constants
---------------------------------

The constants for the two-phase commit (TPC) functions
:meth:`~Connection.tpc_begin()` and :meth:`~Connection.tpc_end()` are listed
below.

.. data:: TPC_BEGIN_JOIN

    Joins an existing TPC transaction.

.. data:: TPC_BEGIN_NEW

    Creates a new TPC transaction.

.. data:: TPC_BEGIN_PROMOTE

    Promotes a local transaction to a TPC transaction.

.. data:: TPC_BEGIN_RESUME

    Resumes an existing TPC transaction.

.. data:: TPC_END_NORMAL

    Ends the TPC transaction participation normally.

.. data:: TPC_END_SUSPEND

    Suspends the TPC transaction.

.. _vectorformatconstants:

Vector Format Constants
-----------------------

These constants belong to the enumeration called ``VectorFormat`` and are
possible values for the :attr:`FetchInfo.vector_format` attribute.

.. versionadded:: 2.2.0

.. versionchanged:: 2.3.0

    The integer constants for the vector format constants were replaced with
    the enumeration ``VectorFormat``.

.. data:: VECTOR_FORMAT_BINARY

    This constant is used to represent the storage format of VECTOR columns
    using 8-bit unsigned integers.

    This enumerated value can also be identified by
    ``oracledb.VectorFormat.BINARY``.

    .. versionadded:: 2.3.0

.. data:: VECTOR_FORMAT_FLOAT32

    This constant is used to represent the storage format of VECTOR columns
    using 32-bit floating point numbers.

    This enumerated value can also be identified by
    ``oracledb.VectorFormat.FLOAT32``.

.. data:: VECTOR_FORMAT_FLOAT64

    This constant is used to represent the storage format of VECTOR columns
    using 64-bit floating point numbers.

    This enumerated value can also be identified by
    ``oracledb.VectorFormat.FLOAT64``.

.. data:: VECTOR_FORMAT_INT8

    This constant is used to represent the storage format of VECTOR columns
    using 8-bit signed integers.

    This enumerated value can also be identified by
    ``oracledb.VectorFormat.INT8``.

.. _exceptions:

Oracledb Exceptions
===================

See :ref:`exception` for usage information.

.. exception:: Warning

    Exception raised for important warnings and defined by the DB API but not
    actually used by python-oracledb.

.. exception:: Error

    Exception that is the base class of all other exceptions defined by
    python-oracledb and is a subclass of the Python StandardError exception
    (defined in the module exceptions).

.. exception:: InterfaceError

    Exception raised for errors that are related to the database interface
    rather than the database itself. It is a subclass of Error.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 1000 - 1999.

.. exception:: DatabaseError

    Exception raised for errors that are related to the database. It is a
    subclass of Error.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 4000 - 4999.

.. exception:: DataError

    Exception raised for errors that are due to problems with the processed
    data. It is a subclass of DatabaseError.

    Exception messages of this class are generated by the database and will
    have a prefix such as ORA

.. exception:: OperationalError

    Exception raised for errors that are related to the operation of the
    database but are not necessarily under the control of the programmer. It is
    a subclass of DatabaseError.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 6000 - 6999.

.. exception:: IntegrityError

    Exception raised when the relational integrity of the database is affected.
    It is a subclass of DatabaseError.

    Exception messages of this class are generated by the database and will
    have a prefix such as ORA

.. exception:: InternalError

    Exception raised when the database encounters an internal error. It is a
    subclass of DatabaseError.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 5000 - 5999.

.. exception:: ProgrammingError

    Exception raised for programming errors. It is a subclass of DatabaseError.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 2000 - 2999.

.. exception:: NotSupportedError

    Exception raised when a method or database API was used which is not
    supported by the database. It is a subclass of DatabaseError.

    Exception messages of this class will have the prefix DPY and an error
    number in the range 3000 - 3999.

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
:attr:`defaults.thick_mode_dsn_passthrough` to *False*. Alternatively use
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
:attr:`defaults.thick_mode_dsn_passthrough` to *False*. Alternatively use
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
