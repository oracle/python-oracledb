.. module:: oracledb

.. _module:

****************************
API: python-oracledb Module
****************************

.. _modmeth:

Oracledb Methods
================

.. data:: __future__

    Special object which contains attributes which control the behavior of
    python-oracledb, allowing for opting in for new features. No attributes are
    currently supported so all attributes will silently ignore being set and
    will always appear to have the value None.

    .. note::

        This method is an extension to the DB API definition.


.. function:: Binary(string)

    Constructs an object holding a binary (long) string value.


.. function:: clientversion()

    Returns the version of the client library being used as a 5-tuple. The five
    values are the major version, minor version, update number, patch number,
    and port update number.

    .. note::

        This function can only be called when python-oracledb is in Thick
        mode. See :ref:`enablingthick`.

    If ``clientversion()`` is called when in python-oracledb Thin mode, that
    is, if :func:`oracledb.init_oracle_client()` is not called first, then an
    exception will be thrown.

    .. note::

        This method is an extension to the DB API definition.

.. function:: connect(dsn=None, pool=None, conn_class=None, params=None, user=None, \
    proxy_user=None, password=None, newpassword=None, wallet_password=None, access_token=None, \
    host=None, port=1521, protocol="tcp", https_proxy=None, https_proxy_port=0, \
    service_name=None, sid=None, server_type=None, cclass=None, purity=oracledb.PURITY_DEFAULT, \
    expire_time=0, retry_count=0, retry_delay=0, tcp_connect_timeout=60.0, \
    ssl_server_dn_match=True, ssl_server_cert_dn=None, wallet_location=None, events=False, \
    externalauth=False, mode=oracledb.AUTH_MODE_DEFAULT, disable_oob=False, \
    stmtcachesize=oracledb.defaults.stmtcachesize, edition=None, tag=None, matchanytag=False, \
    config_dir=oracledb.defaults.config_dir, appcontext=[], shardingkey=[], supershardingkey=[], \
    debug_jdwp=None, handle=0)

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

    The ``dsn`` (data source name) parameter can be a string in the format
    ``user/password@connect_string`` or can simply be the connect string (in
    which case authentication credentials such as the username and password
    need to be specified separately). See :ref:`connstr` for more information.

    The ``pool`` parameter is expected to be a pool object. The use of this
    parameter is the equivalent of calling :meth:`ConnectionPool.acquire()`.

    The ``conn_class`` parameter is expected to be Connection or a subclass of
    Connection.

    The ``params`` parameter is expected to be of type :ref:`ConnectParams
    <connparam>` and contains connection parameters that will be used when
    establishing the connection. If this parameter is not specified, the
    additional keyword parameters will be used to create an instance of
    ConnectParams. If both the params parameter and additional keyword
    parameters are specified, the values in the keyword parameters have
    precedence. Note that if a ``dsn`` is also supplied, then in the
    python-oracledb Thin mode, the values of the parameters specified (if any)
    within the ``dsn`` will override the values passed as additional keyword
    parameters, which themselves override the values set in the ``params``
    parameter object.

    The ``user`` parameter is expected to be a string which indicates the name
    of the user to connect to. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``proxy_user`` parameter is expected to be a string which indicates the
    name of the proxy user to connect to. If this value is not specified, it will
    be parsed out of user if user is in the form "user[proxy_user]". This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``password`` parameter expected to be a string which indicates the password
    for the user. This value is used in both the python-oracledb Thin and Thick modes.

    The ``newpassword`` parameter is expected to be a string which indicates the new
    password for the user. The new password will take effect immediately upon a
    successful connection to the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``wallet_password`` parameter is expected to be a string which indicates the
    password to use to decrypt the PEM-encoded wallet, if it is encrypted. This
    value is only used in python-oracledb Thin mode. The ``wallet_password`` parameter
    is not needed for cwallet.sso files that are used in the python-oracledb Thick
    mode.

    The ``access_token`` parameter is expected to be a string or a 2-tuple or
    a callable. If it is a string, it specifies an Azure AD OAuth2 token used
    for Open Authorization (OAuth 2.0) token based authentication. If it is a
    2-tuple, it specifies the token and private key strings used for Oracle
    Cloud Infrastructure (OCI) Identity and Access Management (IAM) token based
    authentication. If it is a callable, it returns either a string or a 2-tuple
    used for OAuth 2.0 or OCI IAM token based authentication and is useful when
    the pool needs to expand and create new connections but the current
    authentication token has expired. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``host`` parameter is expected to be a string which specifies the name or IP
    address of the machine hosting the listener, which handles the initial
    connection to the database. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``port`` parameter is expected to be an integer which indicates the port number
    on which the listener is listening. The default value is 1521. This value is used
    in both the python-oracledb Thin and Thick modes.

    The ``protocol`` parameter is expected to be one of the strings "tcp" or "tcps"
    which indicates whether to use unencrypted network traffic or encrypted network
    traffic (TLS). The default value is tcp. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``https_proxy`` parameter is expected to be a string which indicates the name
    or IP address of a proxy host to use for tunneling secure connections. This value
    is used in both the python-oracledb Thin and Thick modes.

    The ``https_proxy_port`` parameter is expected to be an integer which indicates
    the port that is to be used to communicate with the proxy host. The default
    value is 0. This value is used in both the python-oracledb Thin and Thick modes.

    The ``service_name`` parameter is expected to be a string which indicates the service
    name of the database. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``sid`` parameter is expected to be a string which indicates the SID of the
    database. It is recommended to use ``service_name`` instead. This value is used
    in both the python-oracledb Thin and Thick modes.

    The ``server_type`` parameter is expected to be a string that indicates the type
    of server connection that should be established. If specified, it should be one
    of `dedicated`, `shared`, or `pooled`. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``cclass`` parameter is expected to be a string that identifies the connection
    class to use for Database Resident Connection Pooling (DRCP). This value is used
    in both the python-oracledb Thin and Thick modes.

    The ``purity`` parameter is expected to be one of the :ref:`oracledb.PURITY_*
    <drcppurityconsts>` constants that identifies the purity to use for
    DRCP. This value is used in both the python-oracledb Thin and Thick modes.
    The purity will internally default to :data:`~oracledb.PURITY_SELF`
    for pooled connections. For standalone connections, the purity will
    internally default to :data:`~oracledb.PURITY_NEW`.

    The ``expire_time`` parameter is expected to be an integer which indicates the
    number of minutes between the sending of keepalive probes. If this parameter
    is set to a value greater than zero it enables keepalive. This value is used
    in both the python-oracledb Thin and Thick modes. The default value is 0.

    The ``retry_count`` parameter is expected to be an integer that identifies
    the number of times that a connection attempt should be retried before the
    attempt is terminated. This value is used in both the python-oracledb Thin
    and Thick modes. The default value is 0.

    The ``retry_delay`` parameter is expected to be an integer that identifies the
    number of seconds to wait before making a new connection attempt. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is 0.

    The ``tcp_connect_timeout`` parameter is expected to be a float that indicates
    the maximum number of seconds to wait for establishing a connection to the
    database host. This value is used in both the python-oracledb Thin and Thick
    modes. The default value is 60.0.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that indicates
    whether the server certificate distinguished name (DN) should be matched in
    addition to the regular certificate verification that is performed. Note that
    if the ``ssl_server_cert_dn`` parameter is not provided, host name matching
    is performed instead. This value is used in both the python-oracledb Thin and
    Thick modes. The default value is True.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that indicates
    the distinguished name (DN) which should be matched with the server. This
    value is ignored if the ``ssl_server_dn_match`` parameter is not set to the
    value True. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``wallet_location`` parameter is expected to be a string that identifies
    the directory where the wallet can be found. In python-oracledb Thin mode,
    this must be the directory of the PEM-encoded wallet file, ewallet.pem.
    In python-oracledb Thick mode, this must be the directory of the file,
    cwallet.sso. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``events`` parameter is expected to be a boolean that specifies whether
    the events mode should be enabled. This value is only used in the
    python-oracledb Thick mode. This parameter is needed for continuous
    query notification and high availability event notifications. The default
    value is False.

    The ``externalauth`` parameter is a boolean that specifies whether external
    authentication should be used. This value is only used in the python-oracledb
    Thick mode. The default value is False. For standalone connections,
    external authentication occurs when the ``user`` and ``password`` attributes
    are not used. If these attributes are not used, you can optionally set the
    ``externalauth`` attribute to True, which may aid code auditing.

    If the ``mode`` parameter is specified, it must be one of the
    :ref:`connection authorization modes <connection-authorization-modes>`
    which are defined at the module level. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is
    :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value is only used
    in the python-oracledb Thin mode and has no effect on Windows which
    does not support this functionality. The default value is False.

    The ``stmtcachesize`` parameter is expected to be an integer which specifies
    the initial size of the statement cache. This value is used in both the
    python-oracledb Thin and Thick modes. The default is the value of
    :attr:`defaults.stmtcachesize`.

    The ``edition`` parameter is expected to be a string that indicates the
    edition to use for the connection. This parameter cannot be used
    simultaneously with the ``cclass`` parameter. This value is used in the
    python-oracledb Thick mode.

    The ``tag`` parameter is expected to be a string that identifies the type of
    connection that should be returned from a pool. This value is only used
    in the python-oracledb Thick mode.

    The ``matchanytag`` parameter is expected to be a boolean specifying whether
    any tag can be used when acquiring a connection from the pool. This value
    is only used in the python-oracledb Thick mode when acquiring a connection
    from a pool. The default value is False.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which configuration files (tnsnames.ora) are found. This value
    is only used in python-oracledb Thin mode. The default is the value of
    :attr:`defaults.config_dir`. For python-oracledb Thick mode, use the
    ``config_dir`` parameter of :func:`oracledb.init_oracle_client()`.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that identifies
    the application context used by the connection. This parameter should contain
    namespace, name, and value and each entry in the tuple should be a string.
    This value is only used in the python-oracledb Thick mode.

    The ``shardingkey`` parameter and ``supershardingkey`` parameters, if specified,
    are expected to be a sequence of values which identifies the database shard to
    connect to. The key values can be a list of strings, numbers, bytes, or dates.
    This value is only used in the python-oracledb Thick mode.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL debugger.
    This allows using the Java Debug Wire Protocol (JDWP) to debug PL/SQL code called
    by python-oracledb. This value is only used in the python-oracledb Thin mode.
    For python-oracledb Thick mode, set the ``ORA_DEBUG_JDWP`` environment variable
    which has the same syntax. For more information, see :ref:`applntracing`.

    If the ``handle`` parameter is specified, it must be of type OCISvcCtx\*
    and is only of use when embedding Python in an application (like
    PowerBuilder) which has already made the connection. The connection thus
    created should *never* be used after the source handle has been closed or
    destroyed. This value is only used in the python-oracledb Thick mode.  It
    should be used with extreme caution. The default value is 0.

.. function:: ConnectParams(user=None, proxy_user=None, password=None, \
    newpassword=None, wallet_password=None, access_token=None, host=None, \
    port=1521, protocol="tcp", https_proxy=None, https_proxy_port=0, service_name=None, \
    sid=None, server_type=None, cclass=None, purity=oracledb.PURITY_DEFAULT, expire_time=0, \
    retry_count=0, retry_delay=0, tcp_connect_timeout=60.0, ssl_server_dn_match=True, \
    ssl_server_cert_dn=None, wallet_location=None, events=False, externalauth=False, \
    mode=oracledb.AUTH_MODE_DEFAULT, disable_oob=False, stmtcachesize=oracledb.defaults.stmtcachesize, \
    edition=None, tag=None, matchanytag=False, config_dir=oracledb.defaults.config_dir, \
    appcontext=[], shardingkey=[], supershardingkey=[], debug_jdwp=None, handle=0)

    Contains all the parameters that can be used to establish a connection to the database.

    Creates and returns a :ref:`ConnectParams Object <connparam>`. The object
    can be passed to :meth:`oracledb.connect()`.

    All the parameters are optional.

    The ``user`` parameter is expected to be a string which indicates the name
    of the user to connect to. This value is used in both the python-oracledb
    Thin and :ref:`Thick <enablingthick>` modes.

    The ``proxy_user`` parameter is expected to be a string which indicates the name of the
    proxy user to connect to. If this value is not specified, it will be parsed out of
    user if user is in the form "user[proxy_user]". This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``password`` parameter expected to be a string which indicates the password for
    the user. This value is used in both the python-oracledb Thin and Thick modes.

    The ``newpassword`` parameter is expected to be a string which indicates the new
    password for the user. The new password will take effect immediately upon a
    successful connection to the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``wallet_password`` parameter is expected to be a string which indicates the
    password to use to decrypt the PEM-encoded wallet, if it is encrypted. This
    value is only used in python-oracledb Thin mode. The ``wallet_password`` parameter
    is not needed for cwallet.sso files that are used in the python-oracledb Thick
    mode.

    The ``access_token`` parameter is expected to be a string or a 2-tuple or
    a callable. If it is a string, it specifies an Azure AD OAuth2 token used
    for Open Authorization (OAuth 2.0) token based authentication. If it is a
    2-tuple, it specifies the token and private key strings used for Oracle
    Cloud Infrastructure (OCI) Identity and Access Management (IAM) token based
    authentication. If it is a callable, it returns either a string or a 2-tuple
    used for OAuth 2.0 or OCI IAM token based authentication and is useful when
    the pool needs to expand and create new connections but the current
    authentication token has expired. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``host`` parameter is expected to be a string which specifies the name or IP
    address of the machine hosting the listener, which handles the initial
    connection to the database. This value is used in both the python-oracledb
    Thin and Thick modes.

    The ``port`` parameter is expected to be an integer which indicates the port number
    on which the listener is listening. The default value is 1521. This value is used
    in both the python-oracledb Thin and Thick modes.

    The ``protocol`` parameter is expected to be one of the strings "tcp" or "tcps"
    which indicates whether to use unencrypted network traffic or encrypted network
    traffic (TLS). The default value is tcp. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``https_proxy`` parameter is expected to be a string which indicates the name or
    IP address of a proxy host to use for tunneling secure connections. This value
    is used in both the python-oracledb Thin and Thick modes.

    The ``https_proxy_port`` parameter is expected to be an integer which indicates
    the port that is to be used to communicate with the proxy host. The default
    value is 0. This value is used in both the python-oracledb Thin and Thick modes.

    The ``service_name`` parameter is expected to be a string which indicates the service
    name of the database. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``sid`` parameter is expected to be a string which indicates the SID of the
    database. It is recommended to use ``service_name`` instead. This value is used
    in both the python-oracledb Thin and Thick modes.

    The ``server_type`` parameter is expected to be a string that indicates the type of
    server connection that should be established. If specified, it should be one of
    "dedicated", "shared", or "pooled". This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``cclass`` parameter is expected to be a string that identifies the connection
    class to use for Database Resident Connection Pooling (DRCP). This value is used
    in both the python-oracledb Thin and Thick modes.

    The ``purity`` parameter is expected to be one of the :ref:`oracledb.PURITY_*
    <drcppurityconsts>` constants that identifies the purity to use for
    DRCP. This value is used in both the python-oracledb Thin and Thick modes.
    The purity will internally default to :data:`~oracledb.PURITY_SELF` for pooled
    connections . For standalone connections, the purity will internally default
    to :data:`~oracledb.PURITY_NEW`.

    The ``expire_time`` parameter is expected to be an integer which indicates the
    number of minutes between the sending of keepalive probes. If this parameter
    is set to a value greater than zero it enables keepalive. This value is used
    in both the python-oracledb Thin and Thick modes. The default value is 0.

    The ``retry_count`` parameter is expected to be an integer that identifies the
    number of times that a connection attempt should be retried before the
    attempt is terminated. This value is used in both the python-oracledb Thin
    and Thick modes. The default value is 0.

    The ``retry_delay`` parameter is expected to be an integer that identifies the
    number of seconds to wait before making a new connection attempt. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is 0.

    The ``tcp_connect_timeout`` parameter is expected to be a float that indicates
    the maximum number of seconds to wait for establishing a connection to the
    database host. This value is used in both the python-oracledb Thin and Thick
    modes. The default value is 60.0.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that indicates
    whether the server certificate distinguished name (DN) should be matched in
    addition to the regular certificate verification that is performed. Note that
    if the ``ssl_server_cert_dn`` parameter is not provided, host name matching
    is performed instead. This value is used in both the python-oracledb Thin and
    Thick modes. The default value is True.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that indicates
    the distinguished name (DN) which should be matched with the server. This
    value is ignored if the ``ssl_server_dn_match`` parameter is not set to the
    value True. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``wallet_location`` parameter is expected to be a string that identifies
    the directory where the wallet can be found. In python-oracledb Thin mode,
    this must be the directory of the PEM-encoded wallet file, ewallet.pem.
    In python-oracledb Thick mode, this must be the directory of the file,
    cwallet.sso. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``events`` parameter is expected to be a boolean that specifies whether
    the events mode should be enabled. This value is only used in the
    python-oracledb Thick mode. This parameter is needed for continuous
    query notification and high availability event notifications. The default
    value is False.

    The ``externalauth`` parameter is a boolean that specifies whether external
    authentication should be used. This value is only used in the python-oracledb
    Thick mode. The default value is False. For standalone connections,
    external authentication occurs when the ``user`` and ``password`` attributes
    are not used. If these attributes are not used, you can optionally set the
    ``externalauth`` attribute to True, which may aid code auditing.

    The ``mode`` parameter is expected to be an integer that identifies the
    authorization mode to use. This value is used in both the python-oracledb
    Thin and Thick modes.The default value is :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value is only used
    in the python-oracledb Thin mode and has no effect on Windows which
    does not support this functionality. The default value is False.

    The ``stmtcachesize`` parameter is expected to be an integer that identifies
    the initial size of the statement cache. This value is used in both the
    python-oracledb Thin and Thick modes. The default is the value of
    :attr:`defaults.stmtcachesize`.

    The ``edition`` parameter is expected to be a string that indicates the
    edition to use for the connection. This parameter cannot be used
    simultaneously with the ``cclass`` parameter. This value is used in the
    python-oracledb Thick mode.

    The ``tag`` parameter is expected to be a string that identifies the type of
    connection that should be returned from a pool. This value is only used
    in the python-oracledb Thick mode.

    The ``matchanytag`` parameter is expected to be a boolean specifying whether
    any tag can be used when acquiring a connection from the pool. This value
    is only used in the python-oracledb Thick mode when acquiring a connection
    from a pool. The default value is False.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which configuration files (tnsnames.ora) are found. This value
    is only used in python-oracledb Thin mode. The default is the value of
    :attr:`defaults.config_dir`.  For python-oracledb Thick mode, use
    the ``config_dir`` parameter of :func:`oracledb.init_oracle_client()`.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that identifies
    the application context used by the connection. This parameter should contain
    namespace, name, and value and each entry in the tuple should be a string.
    This value is only used inthe python-oracledb Thick mode.

    The ``shardingkey`` parameter is expected to be a list of strings, numbers, bytes
    or dates that identifies the database shard to connect to. This value is only
    used in the python-oracledb Thick mode.

    The ``supershardingkey`` parameter is expected to be a list of strings, numbers,
    bytes or dates that identifies the database shard to connect to. This value is
    only used in the python-oracledb Thick mode.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL debugger.
    This allows using the Java Debug Wire Protocol (JDWP) to debug PL/SQL code invoked
    by python-oracledb. This value is only used in the python-oracledb Thin mode.
    For python-oracledb Thick mode, set the ``ORA_DEBUG_JDWP`` environment variable
    which has the same syntax. For more information, see :ref:`applntracing`.

    The ``handle`` parameter is expected to be an integer which represents a
    pointer to a valid service context handle. This value is only used in the
    python-oracledb Thick mode.  It should be used with extreme caution. The
    default value is 0.


.. function:: create_pool(dsn=None, pool_class=oracledb.ConnectionPool, \
        params=None, min=1, max=2, increment=1, connectiontype=oracledb.Connection, \
        getmode=oracledb.POOL_GETMODE_WAIT, homogeneous=True, timeout=0, \
        wait_timeout=0, max_lifetime_session=0, session_callback=None, \
        max_sessions_per_shard=0, soda_metadata_cache=False, ping_interval=60, \
        user=None, proxy_user=None, password=None, newpassword=None, \
        wallet_password=None, access_token=None, host=None, port=1521, \
        protocol="tcp", https_proxy=None, https_proxy_port=0, service_name=None, \
        sid=None, server_type=None, cclass=None, purity=oracledb.PURITY_DEFAULT, \
        expire_time=0, retry_count=0, retry_delay=0, tcp_connect_timeout=60.0, \
        ssl_server_dn_match=True, ssl_server_cert_dn=None, wallet_location=None, \
        events=False, externalauth=False, mode=oracledb.AUTH_MODE_DEFAULT, \
        disable_oob=False, stmtcachesize=oracledb.defaults.stmtcachesize, edition=None, \
        tag=None, matchanytag=False, config_dir=oracledb.defaults.config_dir, \
        appcontext=[], shardingkey=[], supershardingkey=[], debug_jdwp=None, handle=0)

    Creates a connection pool with the supplied parameters and returns the
    :ref:`ConnectionPool object <connpool>` for the pool.  See :ref:`Connection
    pooling <connpooling>` for more information.

    This function is the equivalent of the `cx_Oracle.SessionPool()
    <https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`__
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

    The ``user``, ``password``, and ``dsn`` parameters are the same as for
    :meth:`oracledb.connect()`.

    The ``pool_class`` parameter is expected to be a
    :ref:`ConnectionPool Object <connpool>` or a subclass of ConnectionPool.

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
    ``min`` parameter is 1. The ``increment`` parameter is the number of connections
    that are opened whenever a connection request exceeds the number of currently
    open connections. The default value of the ``increment`` parameter is 1.
    The ``max`` parameter is the maximum number of connections that can be open
    in the connection pool. The default value of the ``max`` parameter is 2.

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
    users). The default value is True.

    The ``timeout`` parameter is the length of time (in seconds) that a
    connection may remain idle in the pool before it is terminated. If the
    value of this parameter is 0, then the connections are never terminated.
    The default value is 0.

    The ``wait_timeout`` parameter is the length of time (in milliseconds) that
    a caller should wait when acquiring a connection from the pool with
    ``getmode`` set to :data:`oracledb.POOL_GETMODE_TIMEDWAIT`. The default
    value is 0.

    The ``max_lifetime_session`` parameter is the length of time (in seconds)
    that connections can remain in the pool. If the value of this parameter is
    0, then the connections may remain in the pool indefinitely. The default
    value is 0.

    The ``session_callback`` parameter is a callable that is invoked when a
    connection is returned from the pool for the first time, or when the
    connection tag differs from the one requested.

    The ``max_sessions_per_shard`` parameter is the maximum number of
    connections that may be associated with a particular shard. The default
    value is 0.

    The ``soda_metadata_cache`` parameter is a boolean that indicates whether
    or not the SODA metadata cache should be enabled. The default value is
    False.

    The ``ping_interval`` parameter is the length of time (in seconds) after
    which an unused connection in the pool will be a candidate for pinging when
    :meth:`ConnectionPool.acquire()` is called. If the ping to the database
    indicates the connection is not alive a replacement connection will be
    returned by :meth:`~ConnectionPool.acquire()`. If ``ping_interval`` is a
    negative value, then the ping functionality will be disabled. The default
    value is 60 seconds.

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
    authentication. If it is a callable, it returns either a string or a 2-tuple
    used for OAuth 2.0 or OCI IAM token based authentication and is useful when
    the pool needs to expand and create new connections but the current
    authentication token has expired. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``host`` parameter is expected to be a string which specifies the name
    or IP address of the machine hosting the listener, which handles the
    initial connection to the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``port`` parameter is expected to be an integer which indicates the
    port number on which the listener is listening. The default value is 1521.
    This value is used in both the python-oracledb Thin and Thick modes.

    The ``protocol`` parameter is expected to be one of the strings "tcp" or
    "tcps" which indicates whether to use unencrypted network traffic or
    encrypted network traffic (TLS). The default value is tcp. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``https_proxy`` parameter is expected to be a string which indicates
    the name or IP address of a proxy host to use for tunneling secure
    connections. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``https_proxy_port`` parameter is expected to be an integer which
    indicates the port that is to be used to communicate with the proxy host.
    The default value is 0. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``service_name`` parameter is expected to be a string which indicates
    the service name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``sid`` parameter is expected to be a string which indicates the SID of
    the database. It is recommended to use ``service_name`` instead. This value
    is used in both the python-oracledb Thin and Thick modes.

    The ``server_type`` parameter is expected to be a string that indicates the
    type of server connection that should be established. If specified, it
    should be one of `dedicated`, `shared`, or `pooled`. This value is used in
    both the python-oracledb Thin and Thick modes.

    The ``cclass`` parameter is expected to be a string that identifies the
    connection class to use for Database Resident Connection Pooling (DRCP).
    This value is used in both the python-oracledb Thin and Thick modes.

    The ``purity`` parameter is expected to be one of the
    :ref:`oracledb.PURITY_* <drcppurityconsts>` constants that identifies the
    purity to use for DRCP. This value is used in both the python-oracledb Thin
    and Thick modes.  The purity will internally default to
    :data:`~oracledb.PURITY_SELF` for pooled connections.

    The ``expire_time`` parameter is expected to be an integer which indicates
    the number of minutes between the sending of keepalive probes. If this
    parameter is set to a value greater than zero it enables keepalive. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is 0.

    The ``retry_count`` parameter is expected to be an integer that identifies
    the number of times that a connection attempt should be retried before the
    attempt is terminated. This value is used in both the python-oracledb Thin
    and Thick modes. The default value is 0.

    The ``retry_delay`` parameter is expected to be an integer that identifies
    the number of seconds to wait before making a new connection attempt. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is 0.

    The ``tcp_connect_timeout`` parameter is expected to be a float that
    indicates the maximum number of seconds to wait for establishing a
    connection to the database host. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is 60.0.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that
    indicates whether the server certificate distinguished name (DN) should be
    matched in addition to the regular certificate verification that is
    performed. Note that if the ``ssl_server_cert_dn`` parameter is not
    provided, host name matching is performed instead. This value is used in
    both the python-oracledb Thin and Thick modes. The default value is True.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that
    indicates the distinguished name (DN) which should be matched with the
    server. This value is ignored if the ``ssl_server_dn_match`` parameter is
    not set to the value True. This value is used in both the python-oracledb
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
    value is False.

    The ``externalauth`` parameter is a boolean that determines whether to use
    external authentication. This value is only used in the python-oracledb Thick
    mode. The default value is False.

    If the ``mode`` parameter is specified, it must be one of the
    :ref:`connection authorization modes <connection-authorization-modes>`
    which are defined at the module level. This value is used in both the
    python-oracledb Thin and Thick modes.The default value is
    :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value is only used
    in the python-oracledb Thin mode and has no effect on Windows which
    does not support this functionality. The default value is False.

    The ``stmtcachesize`` parameter is expected to be an integer which
    specifies the initial size of the statement cache. This value is used in
    both the python-oracledb Thin and Thick modes. The default is the value of
    :attr:`defaults.stmtcachesize`.

    The ``edition`` parameter is expected to be a string that indicates the
    edition to use for the connection. This parameter cannot be used
    simultaneously with the ``cclass`` parameter. This value is used in the
    python-oracledb Thick mode.

    The ``tag`` parameter is expected to be a string that identifies the type
    of connection that should be returned from a pool. This value is only used
    in the python-oracledb Thick mode.

    The ``matchanytag`` parameter is expected to be a boolean specifying
    whether any tag can be used when acquiring a connection from the pool. This
    value is only used in the python-oracledb Thick mode when acquiring a
    connection from a pool. The default value is False.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which configuration files (tnsnames.ora) are found. This value
    is only used in python-oracledb Thin mode. The default is the value of
    :attr:`defaults.config_dir`. For python-oracledb Thick mode, use
    the ``config_dir`` parameter of :func:`oracledb.init_oracle_client()`.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that
    identifies the application context used by the connection. This parameter
    should contain namespace, name, and value and each entry in the tuple
    should be a string.  This value is only used inthe python-oracledb Thick
    mode.

    The ``shardingkey`` parameter and ``supershardingkey`` parameters, if
    specified, are expected to be a sequence of values which identifies the
    database shard to connect to. The key values can be a list of strings,
    numbers, bytes, or dates.  This value is only used in the python-oracledb
    Thick mode.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL
    debugger.  This allows using the Java Debug Wire Protocol (JDWP) to debug
    PL/SQL code invoked by python-oracledb. This value is only used in the
    python-oracledb Thin mode.  For python-oracledb Thick mode, set the
    ``ORA_DEBUG_JDWP`` environment variable which has the same syntax. For more
    information, see :ref:`applntracing`.

    If the ``handle`` parameter is specified, it must be of type OCISvcCtx\*
    and is only of use when embedding Python in an application (like
    PowerBuilder) which has already made the connection. The connection thus
    created should *never* be used after the source handle has been closed or
    destroyed. This value is only used in the python-oracledb Thick mode. It
    should be used with extreme caution. The deault value is 0.

    In the python-oracledb Thick mode, connection pooling is handled by
    Oracle's `Session pooling <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-F9662FFB-EAEF-495C-96FC-49C6D1D9625C>`__ technology.
    This allows python-oracledb applications to support features like
    `Application Continuity <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-A8DD9422-2F82-42A9-9555-134296416E8F>`__.


.. function:: Cursor(connection)

    Constructor for creating a cursor.  Returns a new
    :ref:`cursor object <cursorobj>` using the connection.

    .. note::

        This method is an extension to the DB API definition.


.. function:: Date(year, month, day)

    Constructs an object holding a date value.


.. function:: DateFromTicks(ticks)

    Constructs an object holding a date value from the given ticks value
    (number of seconds since the epoch; see the documentation of the standard
    Python time module for details).

.. function:: init_oracle_client(lib_dir=None, config_dir=None, \
        error_url=None, driver_name=None)

    Enables python-oracledb Thick mode by initializing the Oracle Client
    library, see :ref:`enablingthick`.  The method must be called before any
    standalone connection or pool is created.  If a connection or pool is first
    created in Thin mode, then ``init_oracle_client()`` will raise an exception
    and Thick mode cannot be enabled.

    The ``init_oracle_client()`` method can be called multiple times in each
    Python process as long as the arguments are the same each time.

    See :ref:`initialization` for more information.

    If the ``lib_dir`` parameter is not None or the empty string,
    the specified directory is the only one searched for the Oracle Client
    libraries; otherwise, the standard way of locating the Oracle Client
    library is used.

    If the ``config_dir`` parameter is not None or the empty string, the
    specified directory is used to find Oracle Client library configuration
    files. This is equivalent to setting the environment variable ``TNS_ADMIN``
    and overrides any value already set in ``TNS_ADMIN``. If this parameter is
    not set, the standard way of locating Oracle Client library configuration
    files is used.

    If the ``error_url`` parameter is not None or the empty string, the
    specified value is included in the message of the exception raised when the
    Oracle Client library cannot be loaded; otherwise, the :ref:`installation`
    URL is included.

    If the ``driver_name`` parameter is not None or the empty string, the
    specified value can be found in database views that give information about
    connections. For example, it is in the ``CLIENT_DRIVER`` column of
    ``V$SESSION_CONNECT_INFO``. The standard is to set this value to
    ``"<name> : version>"``, where <name> is the name of the driver and
    <version> is its version. There should be a single space character before
    and after the colon. If this value is not specified, then the default value
    in python-oracledb Thick mode is like "python-oracledb thk : <version>".

    .. note::

        This method is an extension to the DB API definition.


.. function:: is_thin_mode()

    Returns a boolean indicating if Thin mode is in use.

    Immediately after python-oracledb is imported, this function will return
    True indicating that python-oracledb defaults to Thin mode. If
    :func:`oracledb.init_oracle_client()` is called, then a subsequent call to
    ``is_thin_mode()`` will return False indicating that Thick mode is
    enabled. Once the first standalone connection or connection pool is
    created, or a call to ``oracledb.init_oracle_client()`` is made, then
    python-oracledb’s mode is fixed and the value returned by
    ``is_thin_mode()`` will never change for the lifetime of the process.

    The attribute :attr:`Connection.thin` can be used to check a connection's
    mode.

    .. note::

        This method is an extension to the DB API definition.

    .. versionadded:: 1.1.0


.. function:: makedsn(host, port, sid=None, service_name=None, region=None, \
        sharding_key=None, super_sharding_key=None)

    Returns a string suitable for use as the ``dsn`` parameter for
    :meth:`~oracledb.connect()`. This string is identical to the strings that
    are defined by the Oracle names server or defined in the tnsnames.ora file.

    .. deprecated:: python-oracledb 1.0

    Use :ref:`ConnectParams class <connparam>` instead.

    .. note::

        This method is an extension to the DB API definition.

.. function:: PoolParams(min=1, max=2, increment=1, connectiontype=None, \
    getmode=oracledb.POOL_GETMODE_WAIT, homogeneous=True, timeout=0, \
    wait_timeout=0, max_lifetime_session=0, session_callback=None, \
    max_sessions_per_shard=0, soda_metadata_cache=False, ping_interval=60, \
    user=None, proxy_user=Nonde, password=None, newpassword=None, \
    wallet_password=None, access_token=None, host=None, port=1521, protocol="tcp", \
    https_proxy=None, https_proxy_port=0, service_name=None, sid=None, \
    server_type=None, cclass=None, purity=oracledb.PURITY_DEFAULT, \
    expire_time=0, retry_count=0, retry_delay=0, tcp_connect_timeout=60.0, \
    ssl_server_dn_match=True, ssl_server_cert_dn=None, wallet_location=None, \
    events=False, externalauth=False, mode=oracledb.AUTH_MODE_DEFAULT, \
    disable_oob=False, stmtcachesize=oracledb.defaults.stmtcachesize, edition=None, \
    tag=None, matchanytag=False, config_dir=oracledb.defaults.config_dir, \
    appcontext=[], shardingkey=[], supershardingkey=[], debug_jdwp=None, handle=0)

    Creates and returns a :ref:`PoolParams Object <poolparam>`. The object
    can be passed to :meth:`oracledb.create_pool()`.

    All the parameters are optional.

    The ``min`` parameter is the minimum number of connections that the pool
    should contain. The default value is 1.

    The ``max`` parameter is the maximum number of connections that the pool
    should contain. The default value is 2.

    The ``increment`` parameter is the number of connections that should be
    added to the pool whenever a new connection needs to be created. The
    default value is 1.

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
    The default value is True.

    The ``timeout`` parameter is the length of time (in seconds) that a
    connection may remain idle in the pool before it is terminated. If the
    value of this parameter is 0, then the connections are never terminated.
    The default value is 0.

    The ``wait_timeout`` parameter is the length of time (in milliseconds) that
    a caller should wait when acquiring a connection from the pool with
    ``getmode`` set to :data:`oracledb.POOL_GETMODE_TIMEDWAIT`. The default
    value is 0.

    The ``max_lifetime_session`` parameter is the length of time (in seconds)
    that connections can remain in the pool. If the value of this parameter is
    0, then the connections may remain in the pool indefinitely. The default
    value is 0.

    The ``session_callback`` parameter is a callable that is invoked when a
    connection is returned from the pool for the first time, or when the
    connection tag differs from the one requested.

    The ``max_sessions_per_shard`` parameter is the maximum number of
    connections that may be associated with a particular shard. The default
    value is 0.

    The ``soda_metadata_cache`` parameter is a boolean that indicates whether
    or not the SODA metadata cache should be enabled. The default value is
    False.

    The ``ping_interval`` parameter is the length of time (in seconds) after
    which an unused connection in the pool will be a candidate for pinging when
    :meth:`ConnectionPool.acquire()` is called. If the ping to the database
    indicates the connection is not alive a replacement connection will be
    returned by :meth:`ConnectionPool.acquire()`. If ping_interval is a
    negative value, then the ping functionality will be disabled. The default
    value is 60 seconds.

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
    authentication. If it is a callable, it returns either a string or a 2-tuple
    used for OAuth 2.0 or OCI IAM token based authentication and is useful when
    the pool needs to expand and create new connections but the current
    authentication token has expired. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``host`` parameter is expected to be a string which specifies the name
    or IP address of the machine hosting the listener, which handles the
    initial connection to the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``port`` parameter is expected to be an integer which indicates the
    port number on which the listener is listening. The default value is 1521.
    This value is used in both the python-oracledb Thin and Thick modes.

    The ``protocol`` parameter is expected to be one of the strings "tcp" or
    "tcps" which indicates whether to use unencrypted network traffic or
    encrypted network traffic (TLS). The default value is tcp. This value is
    used in both the python-oracledb Thin and Thick modes.

    The ``https_proxy`` parameter is expected to be a string which indicates
    the name or IP address of a proxy host to use for tunneling secure
    connections. This value is used in both the python-oracledb Thin and Thick
    modes.

    The ``https_proxy_port`` parameter is expected to be an integer which
    indicates the port that is to be used to communicate with the proxy host.
    The default value is 0. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``service_name`` parameter is expected to be a string which indicates
    the service name of the database. This value is used in both the
    python-oracledb Thin and Thick modes.

    The ``sid`` parameter is expected to be a string which indicates the SID of
    the database. It is recommended to use ``service_name`` instead. This value
    is used in both the python-oracledb Thin and Thick modes.

    The ``server_type`` parameter is expected to be a string that indicates the
    type of server connection that should be established. If specified, it
    should be one of `dedicated`, `shared`, or `pooled`. This value is used in
    both the python-oracledb Thin and Thick modes.

    The ``cclass`` parameter is expected to be a string that identifies the
    connection class to use for Database Resident Connection Pooling (DRCP).
    This value is used in both the python-oracledb Thin and Thick modes.

    The ``purity`` parameter is expected to be one of the
    :ref:`oracledb.PURITY_* <drcppurityconsts>` constants that identifies the
    purity to use for DRCP. This value is used in both the python-oracledb Thin
    and Thick modes.  Internally pooled connections will default to a purity of
    :data:`~oracledb.PURITY_SELF`.

    The ``expire_time`` parameter is expected to be an integer which indicates
    the number of minutes between the sending of keepalive probes. If this
    parameter is set to a value greater than zero it enables keepalive. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is 0.

    The ``retry_count`` parameter is expected to be an integer that identifies
    the number of times that a connection attempt should be retried before the
    attempt is terminated. This value is used in both the python-oracledb Thin
    and Thick modes. The default value is 0.

    The ``retry_delay`` parameter is expected to be an integer that identifies
    the number of seconds to wait before making a new connection attempt. This
    value is used in both the python-oracledb Thin and Thick modes. The default
    value is 0.

    The ``tcp_connect_timeout`` parameter is expected to be a float that
    indicates the maximum number of seconds to wait for establishing a
    connection to the database host. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is 60.0.

    The ``ssl_server_dn_match`` parameter is expected to be a boolean that
    indicates whether the server certificate distinguished name (DN) should be
    matched in addition to the regular certificate verification that is
    performed. Note that if the ssl_server_cert_dn parameter is not provided,
    host name matching is performed instead. This value is used in both the
    python-oracledb Thin and Thick modes. The default value is True.

    The ``ssl_server_cert_dn`` parameter is expected to be a string that
    indicates the distinguished name (DN) which should be matched with the
    server. This value is ignored if the ssl_server_dn_match parameter is not
    set to the value True. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``wallet_location`` parameter is expected to be a string that
    identifies the directory where the wallet can be found. In python-oracledb
    Thin mode, this must be the directory of the PEM-encoded wallet file,
    ewallet.pem.  In python-oracledb Thick mode, this must be the directory of
    the file, cwallet.sso. This value is used in both the python-oracledb Thin
    and Thick modes.

    The ``externalauth`` parameter is a boolean that determines whether to use
    external authentication. This value is only used in the python-oracledb Thick
    mode. The default value is False.

    The ``events`` parameter is expected to be a boolean that specifies whether
    the events mode should be enabled. This value is only used in the
    python-oracledb Thick mode. This parameter is needed for continuous
    query notification and high availability event notifications. The default
    value is False.

    The ``mode`` parameter is expected to be an integer that identifies the
    authorization mode to use. This value is used in both the python-oracledb
    Thin and Thick modes.The default value is :data:`oracledb.AUTH_MODE_DEFAULT`.

    The ``disable_oob`` parameter is expected to be a boolean that indicates
    whether out-of-band breaks should be disabled. This value is only used
    in the python-oracledb Thin mode and has no effect on Windows which
    does not support this functionality. The default value is False.

    The ``stmtcachesize`` parameter is expected to be an integer that
    identifies the initial size of the statement cache. This value is used in
    both the python-oracledb Thin and Thick modes. The default is the value of
    :attr:`defaults.stmtcachesize`.

    The ``edition`` parameter is expected to be a string that indicates the
    edition to use for the connection. This parameter cannot be used
    simultaneously with the ``cclass`` parameter. This value is used in the
    python-oracledb Thick mode.

    The ``tag`` parameter is expected to be a string that identifies the type
    of connection that should be returned from a pool. This value is only used
    in the python-oracledb Thick mode.

    The ``matchanytag`` parameter is expected to be a boolean specifying
    whether any tag can be used when acquiring a connection from the pool. This
    value is only used in the python-oracledb Thick mode when acquiring a
    connection from a pool. The default value is False.

    The ``config_dir`` parameter is expected to be a string that indicates the
    directory in which configuration files (tnsnames.ora) are found. This value
    is only used in python-oracledb Thin mode. The default is the value of
    :attr:`defaults.config_dir`. For python-oracledb Thick mode, use the
    ``config_dir`` parameter of :func:`oracledb.init_oracle_client()`.

    The ``appcontext`` parameter is expected to be a list of 3-tuples that
    identifies the application context used by the connection. This parameter
    should contain namespace, name, and value and each entry in the tuple
    should be a string.  This value is only used inthe python-oracledb Thick
    mode.

    The ``shardingkey`` parameter is expected to be a list of strings, numbers,
    bytes or dates that identifies the database shard to connect to. This value
    is only used in the python-oracledb Thick mode.

    The ``supershardingkey`` parameter is expected to be a list of strings,
    numbers, bytes or dates that identifies the database shard to connect to.
    This value is only used in the python-oracledb Thick mode.

    The ``debug_jdwp`` parameter is expected to be a string with the format
    `host=<host>;port=<port>` that specifies the host and port of the PL/SQL
    debugger.  This allows using the Java Debug Wire Protocol (JDWP) to debug
    PL/SQL code invoked by python-oracledb. This value is only used in the
    python-oracledb Thin mode.  For python-oracledb Thick mode, set the
    ``ORA_DEBUG_JDWP`` environment variable which has the same syntax. For more
    information, see :ref:`jdwp`.

    The ``handle`` parameter is expected to be an integer which represents a
    pointer to a valid service context handle. This value is only used in the
    python-oracledb Thick mode. It should be used with extreme caution. The
    default value is 0.

.. function:: Time(hour, minute, second)

    Constructs an object holding a time value.

    .. note::

        The time only data type is not supported by Oracle. Calling this
        function will raise a NotSupportedError exception.


.. function:: TimeFromTicks(ticks)

    Constructs an object holding a time value from the given ticks value
    (number of seconds since the epoch; see the documentation of the standard
    Python time module for details).

    .. note::

        The time only data type is not supported by Oracle. Calling this
        function will raise a NotSupportedError exception.

.. function:: Timestamp(year, month, day, hour, minute, second)

    Constructs an object holding a time stamp value.

.. function:: TimestampFromTicks(ticks)

    Constructs an object holding a time stamp value from the given ticks value
    (number of seconds since the epoch; see the documentation of the standard
    Python time module for details).


.. _constants:

Oracledb Constants
==================

General
-------

.. data:: apilevel

    String constant stating the supported DB API level. Currently '2.0'.


.. data:: buildtime

    String constant stating the time when the binary was built.

    .. note::

        This constant is an extension to the DB API definition.


.. data:: paramstyle

    String constant stating the type of parameter marker formatting expected by
    the interface. Currently 'named' as in 'where name = :name'.


.. data:: threadsafety

    Integer constant stating the level of thread safety that the interface
    supports.  Currently 2, which means that threads may share the module and
    connections, but not cursors. Sharing means that a thread may use a
    resource without wrapping it using a mutex semaphore to implement resource
    locking.

    Note that in order to make use of multiple threads in a program which
    intends to connect and disconnect in different threads, the ``threaded``
    parameter to :meth:`connect()` must be True.


.. data:: version
.. data:: __version__

    String constant stating the version of the module. Currently '|release|'.

    .. note::

        This attribute is an extension to the DB API definition.


Advanced Queuing: Delivery Modes
--------------------------------

These constants are extensions to the DB API definition. They are possible
values for the :attr:`~DeqOptions.deliverymode` attribute of the
:ref:`dequeue options object <deqoptions>` passed as the ``options`` parameter to
the :meth:`Queue.deqone()` or :meth:`Queue.deqmany()` methods as well as the
:attr:`~EnqOptions.deliverymode` attribute of the
:ref:`enqueue options object <enqoptions>` passed as the ``options`` parameter to
the :meth:`Queue.enqone()` or :meth:`Queue.enqmany()` methods. They are also
possible values for the :attr:`~MessageProperties.deliverymode` attribute of the
:ref:`message properties object <msgproperties>` passed as the ``msgproperties``
parameter to the :meth:`Queue.deqone()` or :meth:`Queue.deqmany()` and
:meth:`Queue.enqone()` or :meth:`Queue.enqmany()` methods.


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

These constants are extensions to the DB API definition. They are possible
values for the :attr:`~DeqOptions.mode` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()` or :meth:`Queue.deqmany()` methods.


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

These constants are extensions to the DB API definition. They are possible
values for the :attr:`~DeqOptions.navigation` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()` or :meth:`Queue.deqmany()` methods.


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

These constants are extensions to the DB API definition. They are possible
values for the :attr:`~DeqOptions.visibility` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()` or :meth:`Queue.deqmany()` methods.


.. data:: DEQ_IMMEDIATE

    This constant is used to specify that dequeue should perform its work as
    part of an independent transaction.


.. data:: DEQ_ON_COMMIT

    This constant is used to specify that dequeue should be part of the current
    transaction. This is the default value.


Advanced Queuing: Dequeue Wait Modes
------------------------------------

These constants are extensions to the DB API definition. They are possible
values for the :attr:`~DeqOptions.wait` attribute of the
:ref:`dequeue options object <deqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.deqone()` or :meth:`Queue.deqmany()` methods.


.. data:: DEQ_NO_WAIT

    This constant is used to specify that dequeue not wait for messages to be
    available for dequeuing.


.. data:: DEQ_WAIT_FOREVER

    This constant is used to specify that dequeue should wait forever for
    messages to be available for dequeuing. This is the default value.


Advanced Queuing: Enqueue Visibility Modes
------------------------------------------

These constants are extensions to the DB API definition. They are possible
values for the :attr:`~EnqOptions.visibility` attribute of the
:ref:`enqueue options object <enqoptions>`. This object is the ``options``
parameter for the :meth:`Queue.enqone()` or :meth:`Queue.enqmany()` methods.


.. data:: ENQ_IMMEDIATE

    This constant is used to specify that enqueue should perform its work as
    part of an independent transaction.


.. data:: ENQ_ON_COMMIT

    This constant is used to specify that enqueue should be part of the current
    transaction. This is the default value.


Advanced Queuing: Message States
--------------------------------

These constants are extensions to the DB API definition. They are possible
values for the :attr:`~MessageProperties.state` attribute of the
:ref:`message properties object <msgproperties>`. This object is the
``msgproperties`` parameter for the :meth:`Connection.deq()` and
:meth:`Queue.enqone()` or :meth:`Queue.enqmany()` methods.


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


Advanced Queuing: Other
-----------------------

These constants are extensions to the DB API definition. They are special
constants used in advanced queuing.


.. data:: MSG_NO_DELAY

    This constant is a possible value for the :attr:`~MessageProperties.delay`
    attribute of the :ref:`message properties object <msgproperties>` passed
    as the ``msgproperties`` parameter to the :meth:`Queue.deqone()` or
    :meth:`Queue.deqmany()` and :meth:`Queue.enqone()` or :meth:`Queue.enqmany()`
    methods. It specifies that no delay should be imposed and the message should
    be immediately available for dequeuing. This is also the default value.


.. data:: MSG_NO_EXPIRATION

    This constant is a possible value for the
    :attr:`~MessageProperties.expiration` attribute of the
    :ref:`message properties object <msgproperties>` passed as the ``msgproperties``
    parameter to the :meth:`Queue.deqone()` or :meth:`Queue.deqmany()` and
    :meth:`Queue.enqone()` or :meth:`Queue.enqmany()` methods. It specifies
    that the message never expires. This is also the default value.


.. _connection-authorization-modes:

Connection Authorization Modes
------------------------------

These constants are extensions to the DB API definition and have deprecated the
`authorization modes <https://cx-oracle.readthedocs.io/en/latest/api_manual/
module.html#connection-authorization-modes>`_ used in cx_Oracle 8.3. They are
possible values for the ``mode`` parameter of the :meth:`connect()` method.


.. data:: AUTH_MODE_DEFAULT

    This constant is used to specify that default authentication is to take
    place. This is the default value if no mode is passed at all.

    .. note::

        This constant can be used for standalone and pooled connections in the
        python-oracledb Thin mode, and for standalone connections in the Thick
        mode.

        This constant deprecates the ``DEFAULT_AUTH`` constant that was used in
        cx_Oracle 8.3.

.. data:: AUTH_MODE_PRELIM

    This constant is used to specify that preliminary authentication is to be
    used. This is needed for performing database startup and shutdown.

    .. note::

        This constant can only be used in the python-oracledb Thick mode for
        standalone connections.

        This constant deprecates the ``PRELIM_AUTH`` constant that was used in
        cx_Oracle 8.3.

.. data:: AUTH_MODE_SYSASM

    This constant is used to specify that SYSASM access is to be acquired.

    .. note::

        This constant can be used for standalone and pooled connections in the
        python-oracledb Thin mode, and for standalone connections in the Thick
        mode.

        This constant deprecates the ``SYSASM`` constant that was used in
        cx_Oracle 8.3.

.. data:: AUTH_MODE_SYSBKP

    This constant is used to specify that SYSBACKUP access is to be acquired.

    .. note::

        This constant can be used for standalone and pooled connections in the
        python-oracledb Thin mode, and for standalone connections in the Thick
        mode.

        This constant deprecates the ``SYSBKP`` constant that was used in
        cx_Oracle 8.3.

.. data:: AUTH_MODE_SYSDBA

    This constant is used to specify that SYSDBA access is to be acquired.

    .. note::

        This constant can be used for standalone and pooled connections in the
        python-oracledb Thin mode, and for standalone connections in the Thick
        mode.

        This constant deprecates the ``SYSDBA`` constant that was used in
        cx_Oracle 8.3.

.. data:: AUTH_MODE_SYSDGD

    This constant is used to specify that SYSDG access is to be acquired.

    .. note::

        This constant can be used for standalone and pooled connections in the
        python-oracledb Thin mode, and for standalone connections in the Thick
        mode.

        This constant deprecates the ``SYSDGD`` constant that was used in
        cx_Oracle 8.3.

.. data:: AUTH_MODE_SYSKMT

    This constant is used to specify that SYSKM access is to be acquired.

    .. note::

        This constant can be used for standalone and pooled connections in the
        python-oracledb Thin mode, and for standalone connections in the Thick
        mode.

        This constant deprecates the ``SYSKMT`` constant that was used in
        cx_Oracle 8.3.

.. data:: AUTH_MODE_SYSOPER

    This constant is used to specify that SYSOPER access is to be acquired.

    .. note::

        This constant can be used for standalone and pooled connections in the
        python-oracledb Thin mode, and for standalone connections in the Thick
        mode.

        This constant deprecates the ``SYSOPER`` constant that was used in
        cx_Oracle 8.3.

.. data:: AUTH_MODE_SYSRAC

    This constant is used to specify that SYSRAC access is to be acquired.

    .. note::

        This constant can be used for standalone and pooled connections in the
        python-oracledb Thin mode, and for standalone connections in the Thick
        mode.

        This constant deprecates the ``SYSRAC`` constant that was used in
        cx_Oracle 8.3.


Database Shutdown Modes
-----------------------

These constants are extensions to the DB API definition. They are possible
values for the ``mode`` parameter of the :meth:`Connection.shutdown()` method.


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

These constants are extensions to the DB API definition. They are possible
values for the :attr:`Message.type` attribute of the messages that are sent
for subscriptions created by the :meth:`Connection.subscribe()` method.


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

These constants are extensions to the DB API definition. They are possible
values for the ``operations`` parameter for the :meth:`Connection.subscribe()`
method. One or more of these values can be OR'ed together. These values are
also used by the :attr:`MessageTable.operation` or
:attr:`MessageQuery.operation` attributes of the messages that are sent.


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

These constants are extensions to the DB API definition and have deprecated the
`Session Pool Get Modes <https://cx-oracle.readthedocs.io/en/latest/api_manual/
module.html#session-pool-get-modes>`_ constants that were used in cx_Oracle
8.3.  They are possible values for the ``getmode`` parameter of the
:meth:`oracledb.create_pool()` method.


.. data:: POOL_GETMODE_FORCEGET

    This constant is used to specify that a new connection will be returned if
    there are no free sessions available in the pool.

    .. note::

        This constant deprecates the ``SPOOL_ATTRVAL_FORCEGET`` constant that
        was used in cx_Oracle 8.3.


.. data:: POOL_GETMODE_NOWAIT

    This constant is used to specify that an exception should be raised if
    there are no free sessions available in the pool.

    .. note::

        This constant deprecates the ``SPOOL_ATTRVAL_NOWAIT`` constant that was
        used in cx_Oracle 8.3.


.. data:: POOL_GETMODE_WAIT

    This constant is used to specify that the caller should wait until a
    session is available if there are no free sessions available in the pool.
    This is the default value.

    .. note::

        This constant deprecates the ``SPOOL_ATTRVAL_WAIT`` constant that was
        used in cx_Oracle 8.3.


.. data:: POOL_GETMODE_TIMEDWAIT

    This constant is used to specify that the caller should wait for a period
    of time (defined by the ``wait_timeout`` parameter) for a session to become
    available before returning with an error.

    .. note::

        This constant deprecates the ``SPOOL_ATTRVAL_TIMEDWAIT`` constant that
        was used in cx_Oracle 8.3.

.. _drcppurityconsts:

Connection Pool Purity Constants
--------------------------------

These constants are extensions to the DB API definition and have deprecated the
`Session Pool Purity <https://cx-oracle.readthedocs.io/en/latest/api_manual/
module.html#session-pool-purity>`_ constants that were used in cx_Oracle 8.3.
They are possible values for the ``purity`` parameter of the :meth:`connect()`
method, which is used in Database Resident Connection Pooling (DRCP).

.. data:: PURITY_DEFAULT

    This constant is used to specify that the purity of the session is the
    default value identified by Oracle (see Oracle's documentation for more
    information). This is the default value.

    .. note::

        This constant deprecates the ``ATTR_PURITY_DEFAULT`` constant that was
        used in cx_Oracle 8.3.

.. data:: PURITY_NEW

    This constant is used to specify that the session acquired from the pool
    should be new and not have any prior session state.

    .. note::

        This constant deprecates the ``ATTR_PURITY_NEW`` constant that was used
        in cx_Oracle 8.3.


.. data:: PURITY_SELF

    This constant is used to specify that the session acquired from the pool
    need not be new and may have prior session state.

    .. note::

        This constant deprecates the ``ATTR_PURITY_SELF`` constant that was
        used in cx_Oracle 8.3.

Subscription Grouping Classes
-----------------------------

These constants are extensions to the DB API definition. They are possible
values for the ``groupingClass`` parameter of the :meth:`Connection.subscribe()`
method.

.. data:: SUBSCR_GROUPING_CLASS_TIME

    This constant is used to specify that events are to be grouped by the
    period of time in which they are received.


Subscription Grouping Types
---------------------------

These constants are extensions to the DB API definition. They are possible
values for the ``groupingType`` parameter of the :meth:`Connection.subscribe()`
method.

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

These constants are extensions to the DB API definition. They are possible
values for the ``namespace`` parameter of the :meth:`Connection.subscribe()`
method.

.. data:: SUBSCR_NAMESPACE_AQ

    This constant is used to specify that notifications should be sent when a
    queue has messages available to dequeue.

.. data:: SUBSCR_NAMESPACE_DBCHANGE

    This constant is used to specify that database change notification or query
    change notification messages are to be sent. This is the default value.


.. _subscr-protocols:

Subscription Protocols
----------------------

These constants are extensions to the DB API definition. They are possible
values for the ``protocol`` parameter of the :meth:`Connection.subscribe()` method.

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

These constants are extensions to the DB API definition. They are possible
values for the ``qos`` parameter of the :meth:`Connection.subscribe()` method. One
or more of these values can be OR'ed together.

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

.. data:: DB_TYPE_BFILE

    Describes columns, attributes or array elements in a database that are of
    type BFILE. It will compare equal to the DB API type :data:`BINARY`.

    .. note::

        DB_TYPE_BFILE database type is only supported in the python-oracledb
        Thick mode.  See :ref:`enablingthick`.

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
    type INTERVAL YEAR TO MONTH. This database type is not currently supported
    by python-oracledb.


.. data:: DB_TYPE_JSON

    Describes columns in a database that are of type JSON (with Oracle Database
    21 or later).

    .. note::

        DB_TYPE_JSON database type is only supported in the python-oracledb
        Thick mode. See :ref:`enablingthick`.

        In python-oracledb Thin mode, the JSON database type can be fetched
        with an output type handler as described in :ref:`Fetching JSON
        <fetchJSON>`.


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


.. data:: DB_TYPE_UROWID

    Describes columns, attributes or array elements in a database that are of
    type UROWID. It will compare equal to the DB API type :data:`ROWID`.

    .. note::

        This type is not supported in python-oracledb Thick mode.
        See :ref:`querymetadatadiff`.


.. data:: DB_TYPE_VARCHAR

    Describes columns, attributes or array elements in a database that are of
    type VARCHAR2. It will compare equal to the DB API type :data:`STRING`.


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

    A synonym for :data:`DB_TYPE_NVARCHAR`.

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

Oracledb._Error Objects
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
    This is False in all cases unless both Oracle Database 12.1 (or later) and
    Oracle Client 12.1 (or later) are being used.
